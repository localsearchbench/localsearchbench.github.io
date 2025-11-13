"""
RAG Server - 部署在有 GPU 的服务器上
支持 Web Search、RAG Search 和 Agentic Search

运行方式：
    python rag_server.py --port 8000 --host 0.0.0.0 --config /path/to/config.yaml

环境变量配置：
    export OPENAI_API_KEY="your-key"
    export DASHSCOPE_API_KEY="your-key"  # 如果使用 Qwen 模型
    export TUANSOU_CONFIG="/path/to/config.yaml"  # LLM 配置文件路径

检索与重排策略：
    本服务器与 interactive_merchant_search_vllm.py 保持高度一致：
    - 候选文档倍数：candidate_multiplier = 5
    - 相似度计算：(max_distance - distance) / max_distance
    - 重排序文本格式：name - category/subcategory - address + 地理位置（必须）+ 多个可选字段
    - 地理位置字段（必须参与重排）：city, district, business_area, landmark
    - subcategory 字段：如果存在，会拼接到 category 后面（格式：category/subcategory）

LLM 精排（新增）：
    - 在 rerank 后，使用 LLM 从 20 个候选中选出最终的 5 个结果
    - 可通过请求参数 use_llm_ranking 控制是否启用（默认启用）
    - LLM 会综合考虑用户查询意图、商户信息完整性、评分等因素
    - 配置文件需包含 LLM API keys 和相关配置（参考 auto_rag_merchant_search.py）
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Tuple
import uvicorn
import argparse
import os
import time
from datetime import datetime
from pathlib import Path
import threading

# 基础依赖
import json
import yaml
import requests
import numpy as np
import aiohttp
import asyncio

# 如果使用 GPU 加载模型
try:
    import torch
    from sentence_transformers import SentenceTransformer, CrossEncoder
    import faiss
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🚀 Using device: {DEVICE}")
    HAS_GPU = torch.cuda.is_available()
except ImportError as e:
    DEVICE = "cpu"
    HAS_GPU = False
    print(f"⚠️ PyTorch/FAISS not found: {e}, using CPU mode")

app = FastAPI(
    title="LocalSearchBench RAG API",
    description="RAG Search API with GPU support",
    version="1.0.0"
)

# 配置 CORS - 允许 Gradio 客户端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================

class RAGSearchRequest(BaseModel):
    query: str
    city: str = "上海"  # 支持的城市（中文）
    top_k: int = 5  # 最终返回5个结果
    retriever: str = "qwen3-embedding-8b"  # 默认使用 Qwen3-Embedding-8B
    reranker: str = "qwen3-reranker-8b"    # 默认使用 Qwen3-Reranker-8B
    use_llm_ranking: bool = True  # 是否启用 LLM 精排（默认启用）

class WebSearchRequest(BaseModel):
    query: str
    top_k: int = 5

class AgenticSearchRequest(BaseModel):
    query: str
    model: str = "gpt-4.1"
    max_iterations: int = 5

class SearchResult(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    metrics: Dict[str, Any]  # 改为 Any 以支持混合类型（float、int、str）
    reasoning_steps: Optional[List[str]] = None
    processing_time: float

# ==================== 城市向量数据库加载器 ====================

class CityVectorDB:
    """管理所有城市的FAISS向量数据库（1028版本）"""
    
    def __init__(self, data_dir: str, use_gpu: bool = True):
        self.data_dir = data_dir
        self.use_gpu = use_gpu and torch.cuda.is_available()
        # 城市映射：中文 -> 英文（用于文件名）
        self.city_to_en = {
            "上海": "shanghai",
            "北京": "beijing",
            "广州": "guangzhou",
            "深圳": "shenzhen",
            "杭州": "hangzhou",
            "苏州": "suzhou",
            "成都": "chengdu",
            "重庆": "chongqing",
            "武汉": "wuhan"
        }
        self.indexes = {}  # key 为中文城市名
        self.metadata = {}  # key 为中文城市名
        self.gpu_resources = None
        
        # 初始化 GPU 资源
        # 注意：GPU 兼容性检查应该在启动脚本中完成（start_rag_server.sh）
        # 因为 FAISS 的 C++ 断言失败会导致进程崩溃，Python 无法捕获
        if self.use_gpu:
            try:
                self.gpu_resources = faiss.StandardGpuResources()
                print(f"🚀 GPU resources initialized for FAISS")
            except Exception as e:
                print(f"⚠️  Failed to initialize GPU resources: {e}")
                print(f"⚠️  Falling back to CPU mode")
                self.use_gpu = False
                self.gpu_resources = None
        
        self.load_all_cities()
    
    def load_all_cities(self):
        """加载所有城市的向量数据库"""
        device_info = "GPU" if self.use_gpu else "CPU"
        print(f"\n📦 Loading vector databases from: {self.data_dir}")
        print(f"💻 Device: {device_info}")
        
        for city_cn, city_en in self.city_to_en.items():
            try:
                # 加载 1028 版本的数据（文件名使用英文）
                index_path = os.path.join(self.data_dir, f"faiss_merchant_index_vllm_{city_en}_1028.faiss")
                meta_path = os.path.join(self.data_dir, f"faiss_merchant_index_vllm_{city_en}_1028_metadata.json")
                
                if not os.path.exists(index_path) or not os.path.exists(meta_path):
                    print(f"⚠️  {city_cn}: Files not found")
                    continue
                
                # 加载 FAISS 索引 (先加载到CPU)
                cpu_index = faiss.read_index(index_path)
                
                # 如果启用GPU，将索引转移到GPU
                if self.use_gpu:
                    try:
                        # 将CPU索引转换为GPU索引（使用中文作为 key）
                        self.indexes[city_cn] = faiss.index_cpu_to_gpu(self.gpu_resources, 0, cpu_index)
                        device_tag = "🚀 GPU"
                    except Exception as e:
                        print(f"⚠️  {city_cn}: GPU transfer failed ({e}), using CPU")
                        self.indexes[city_cn] = cpu_index
                        device_tag = "💻 CPU"
                else:
                    self.indexes[city_cn] = cpu_index
                    device_tag = "💻 CPU"
                
                # 加载元数据（使用中文作为 key）
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata[city_cn] = json.load(f)
                
                print(f"✅ {city_cn}: {self.indexes[city_cn].ntotal} vectors, {len(self.metadata[city_cn])} merchants [{device_tag}]")
            except Exception as e:
                print(f"❌ Failed to load {city_cn}: {e}")
        
        print(f"\n🎉 Loaded {len(self.indexes)}/{len(self.city_to_en)} cities successfully on {device_info}!\n")
    
    def search(self, query_embedding: np.ndarray, city: str = "上海", top_k: int = 20):
        """在指定城市的向量数据库中搜索
        
        Args:
            query_embedding: 查询向量
            city: 城市名（中文），如 "上海"、"北京"
            top_k: 返回结果数量
        """
        if city not in self.indexes:
            raise ValueError(f"City '{city}' not loaded. Available cities: {list(self.indexes.keys())}")
        
        # 使用 FAISS 进行向量检索
        query_vec = query_embedding.reshape(1, -1).astype('float32')
        distances, indices = self.indexes[city].search(query_vec, top_k)
        
        # 获取对应的元数据
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.metadata[city]):
                merchant = self.metadata[city][idx].copy()
                merchant["vector_score"] = float(dist)
                results.append(merchant)
        
        return results

# ==================== LLM 精排器 ====================

class LLMRanker:
    """LLM 精排器：从 rerank 的候选中筛选出最终结果"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.llm = self._init_llm_config()
        self._api_keys: List[str] = self.llm.get("api_keys", [])
        self._key_index = 0
        # 延迟初始化锁，避免在事件循环外创建
        self._key_lock = None
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        candidates: List[str] = []
        
        # 优先使用传入的路径
        if config_path:
            candidates.append(os.path.abspath(os.path.expanduser(config_path)))
        
        # 尝试环境变量
        env_cfg = os.getenv("TUANSOU_CONFIG") or os.getenv("CONFIG_PATH")
        if env_cfg:
            candidates.append(os.path.abspath(os.path.expanduser(env_cfg)))
        
        # 硬编码的服务器配置文件路径（优先级高）
        candidates.append("/mnt/dolphinfs/hdd_pool/docker/user/hadoop-mtsearch-assistant/ai-search/hehang03/config/config.yaml")
        
        # 尝试相对路径（Mac 本地开发）
        candidates.append("config/config.yaml")
        candidates.append("../config/config.yaml")
        
        for cfg_path in candidates:
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        return yaml.safe_load(f)
                except Exception as e:
                    print(f"⚠️ Failed to load config from {cfg_path}: {e}")
        
        # 如果找不到配置文件，返回默认配置
        print("⚠️ No config file found, using default LLM config")
        return {}
    
    def _init_llm_config(self) -> Dict[str, Any]:
        """初始化 LLM 配置"""
        llm_config = self.config.get("llm", {})
        defaults = {
            "provider": "openai",
            "model": "deepseek-v31-meituan",
            "base_url": "https://aigc.sankuai.com/v1/openai/native",
            "timeout": 300,
            "max_retries": 3,
            "temperature": 0.2,
        }
        for k, v in defaults.items():
            llm_config.setdefault(k, v)
        
        # 获取 API Keys
        api_keys = llm_config.get("api_keys") or []
        if not api_keys:
            env_key = os.getenv("OPENAI_API_KEY")
            if env_key:
                api_keys = [env_key]
        
        if not api_keys:
            llm_config["enabled"] = False
            print("⚠️ No API keys found, LLM ranking disabled")
        else:
            llm_config["api_keys"] = api_keys
            llm_config["enabled"] = True
            print(f"✅ LLM ranking enabled with {len(api_keys)} API key(s)")
        
        return llm_config
    
    def _next_key(self) -> Optional[str]:
        """轮询获取下一个 API Key"""
        if not self._api_keys:
            return None
        key = self._api_keys[self._key_index % len(self._api_keys)]
        self._key_index += 1
        return key
    
    async def select_top_k_async(
        self, 
        query: str, 
        candidates: List[Dict[str, Any]], 
        top_k: int = 5,
        city: str = "上海"
    ) -> List[Dict[str, Any]]:
        """
        使用 LLM 从候选中筛选出 top_k 个最相关的商户
        
        Args:
            query: 用户查询
            candidates: 候选商户列表（通常是 rerank 后的结果）
            top_k: 返回结果数量
            city: 城市名称
            
        Returns:
            筛选后的商户列表
        """
        if not self.llm.get("enabled", False):
            print("⚠️ LLM ranking disabled, returning top_k candidates as-is")
            return candidates[:top_k]
        
        if len(candidates) <= top_k:
            print(f"📋 Candidates count ({len(candidates)}) <= top_k ({top_k}), no LLM ranking needed")
            return candidates
        
        try:
            # 构建提示词
            prompt = self._build_selection_prompt(query, candidates[:20], top_k, city)
            
            # 调用 LLM
            content = await self._call_llm_async(prompt, temperature=0.0, max_tokens=8192)
            
            # 解析结果
            selected_indices = self._parse_selection_result(content, len(candidates), top_k)
            
            # 根据索引返回结果
            result = []
            for idx in selected_indices:
                if 0 <= idx < len(candidates):
                    merchant = candidates[idx].copy()
                    merchant['llm_selected'] = True
                    merchant['llm_rank'] = len(result) + 1
                    result.append(merchant)
            
            # 如果 LLM 成功解析但选择了较少的商户（包括0个），尊重这个判断
            if len(selected_indices) > 0:
                # LLM 成功返回了选择（即使少于 top_k）
                print(f"✅ LLM selected {len(result)} merchants from {len(candidates)} candidates (requested: {top_k})")
                return result if result else candidates[:min(1, len(candidates))]  # 至少返回1个，避免完全为空
            else:
                # LLM 返回空列表，说明没有符合条件的，但为了保证用户体验，返回top 1
                print(f"⚠️ LLM returned empty selection, returning top 1 candidate")
                return candidates[:min(1, len(candidates))]
                
        except Exception as e:
            print(f"❌ LLM ranking error: {e}, falling back to top_k")
            return candidates[:top_k]
    
    def _build_selection_prompt(
        self, 
        query: str, 
        candidates: List[Dict[str, Any]], 
        top_k: int,
        city: str
    ) -> str:
        """构建 LLM 筛选提示词"""
        # 格式化候选商户信息
        formatted_candidates = []
        for i, doc in enumerate(candidates, 0):
            name = doc.get('name', '未知')
            category = doc.get('category', '')
            subcategory = doc.get('subcategory', '')
            address = doc.get('address', '')
            rating = doc.get('rating', '')
            price = doc.get('price_range', '')
            district = doc.get('district', '')
            business_area = doc.get('business_area', '')
            tags = doc.get('tags', [])
            products = doc.get('products', '')
            hours = doc.get('business_hours', '')
            rerank_score = doc.get('rerank_score', 0)
            
            tags_str = ','.join(tags[:5]) if isinstance(tags, list) else str(tags)
            cat_str = f"{category}/{subcategory}" if subcategory else category
            
            formatted_candidates.append(
                f"{i}. 名称：{name} | 类别：{cat_str} | 地址：{address} | "
                f"区域：{district} {business_area} | 评分：{rating} | 价格：{price} | "
                f"标签：{tags_str} | 服务：{products} | 营业：{hours} | 重排分：{rerank_score:.4f}"
            )
        
        candidates_text = '\n'.join(formatted_candidates)
        
        prompt = f"""任务：从下方候选商户中，筛选出真正符合用户查询需求的商户（最多 {top_k} 个）。

用户查询：{query}
城市：{city}

候选商户（共 {len(candidates)} 个）：
{candidates_text}

筛选要求：
1. **严格匹配**用户查询中的关键条件（如地点、价格、类型、特殊需求等）
2. **只选择真正符合条件的商户**，不要为了凑数而选择不太相关的
3. 优先选择评分高、信息完整、相关度高的商户
4. 考虑重排分数（rerank_score）作为参考，但最终以用户需求为准
5. 如果用户查询中提到具体区域/商圈，优先选择该区域的商户
6. 确保选出的商户信息充分、不重复

数量要求：
- 最多选择 {top_k} 个商户
- 如果只有 2 家真正符合条件，就只返回 2 家，不要凑数
- 如果没有完全符合条件的，可以返回空列表

输出格式：
仅输出一个 JSON 对象，包含字段 "selected_indices"，值为选中的商户索引列表（0-based）。
例如：
- 5家符合：{{"selected_indices": [0, 3, 5, 8, 12]}}
- 2家符合：{{"selected_indices": [0, 5]}}
- 0家符合：{{"selected_indices": []}}

注意：
- 只输出 JSON，不要其他文字
- selected_indices 必须是整数列表
- 索引范围：0 到 {len(candidates)-1}
- 宁缺毋滥，质量优先于数量
"""
        
        return prompt
    
    def _parse_selection_result(
        self, 
        content: str, 
        max_index: int, 
        top_k: int
    ) -> List[int]:
        """解析 LLM 返回的选择结果"""
        try:
            # 尝试直接解析 JSON
            data = json.loads(content)
            if isinstance(data, dict) and "selected_indices" in data:
                indices = data["selected_indices"]
                if isinstance(indices, list):
                    # 验证并过滤索引
                    valid_indices = []
                    for idx in indices:
                        if isinstance(idx, int) and 0 <= idx < max_index:
                            if idx not in valid_indices:  # 去重
                                valid_indices.append(idx)
                    return valid_indices[:top_k]
        except json.JSONDecodeError:
            pass
        
        # 如果 JSON 解析失败，尝试从文本中提取数字
        import re
        numbers = re.findall(r'\b(\d+)\b', content)
        valid_indices = []
        for num_str in numbers:
            try:
                idx = int(num_str)
                if 0 <= idx < max_index and idx not in valid_indices:
                    valid_indices.append(idx)
                    if len(valid_indices) >= top_k:
                        break
            except ValueError:
                continue
        
        if valid_indices:
            return valid_indices
        
        # 如果完全失败，返回前 top_k 个索引
        return list(range(min(top_k, max_index)))
    
    async def _call_llm_async(
        self, 
        prompt: str, 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """异步调用 LLM"""
        if not self.llm.get("enabled", False):
            return '{"selected_indices": []}'
        
        url = f"{self.llm['base_url']}/chat/completions"
        retries = max(1, int(self.llm.get("max_retries", 3)))
        timeout = int(self.llm.get("timeout", 300))
        
        last_err = None
        
        for attempt in range(retries):
            # 获取 API Key
            if self._key_lock is None:
                try:
                    loop = asyncio.get_running_loop()
                    self._key_lock = asyncio.Lock()
                except RuntimeError:
                    pass
            
            if self._key_lock:
                async with self._key_lock:
                    api_key = self._next_key()
            else:
                api_key = self._next_key()
            
            if not api_key:
                return '{"selected_indices": []}'
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
            body = {
                "model": self.llm["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            try:
                timeout_cfg = aiohttp.ClientTimeout(total=timeout)
                start_ts = time.time()
                print(f"[LLM] Attempt {attempt+1}/{retries}, model={self.llm['model']}, prompt_len={len(prompt)}")
                
                async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
                    async with session.post(url, headers=headers, json=body) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = data["choices"][0]["message"]["content"].strip()
                            latency = (time.time() - start_ts) * 1000.0
                            print(f"[LLM] Success: {resp.status}, latency={latency:.0f}ms")
                            return content
                        else:
                            txt = await resp.text()
                            last_err = f"{resp.status} {txt[:200]}"
                            latency = (time.time() - start_ts) * 1000.0
                            print(f"[LLM] Error: {resp.status}, latency={latency:.0f}ms, detail={last_err[:100]}")
                            
                            # 429 时退避
                            if resp.status == 429 and attempt < retries - 1:
                                backoff = 2 ** attempt
                                await asyncio.sleep(backoff)
                                continue
            except Exception as e:
                last_err = str(e)
                latency = (time.time() - start_ts) * 1000.0
                print(f"[LLM] Exception: latency={latency:.0f}ms, error={last_err[:100]}")
            
            # 简单退避
            if attempt < retries - 1:
                await asyncio.sleep(1.5 * (attempt + 1))
        
        raise Exception(f"LLM 调用失败: {last_err}")

# ==================== 模型加载（GPU）====================

class RAGModels:
    """在服务器启动时加载模型到 GPU"""
    
    def __init__(self, data_dir: str = None, use_gpu: bool = True, config_path: str = None):
        self.embedding_model = None
        self.reranker_model = None
        self.llm = None
        self.vector_db = None
        self.llm_ranker = None
        
        # 初始化向量数据库（支持 GPU 加速）
        if data_dir and os.path.exists(data_dir):
            try:
                self.vector_db = CityVectorDB(data_dir, use_gpu=use_gpu)
            except Exception as e:
                print(f"⚠️ Failed to load vector databases: {e}")
        
        # 初始化 LLM 精排器
        try:
            self.llm_ranker = LLMRanker(config_path=config_path)
        except Exception as e:
            print(f"⚠️ Failed to initialize LLM ranker: {e}")
        
    def load_embedding_model(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """加载 Embedding 模型到 GPU"""
        if self.embedding_model is None:
            print(f"📥 Loading embedding model: {model_name}")
            # 这里使用 sentence-transformers 作为示例
            # 你可以替换为 Qwen3-Embedding-8B 或其他模型
            try:
                self.embedding_model = SentenceTransformer(model_name, device=DEVICE)
                print(f"✅ Embedding model loaded on {DEVICE}")
            except Exception as e:
                print(f"❌ Failed to load embedding model: {e}")
                self.embedding_model = None
        return self.embedding_model
    
    def load_reranker_model(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """加载 Reranker 模型到 GPU"""
        if self.reranker_model is None:
            print(f"📥 Loading reranker model: {model_name}")
            try:
                from sentence_transformers import CrossEncoder
                self.reranker_model = CrossEncoder(model_name, device=DEVICE)
                print(f"✅ Reranker model loaded on {DEVICE}")
            except Exception as e:
                print(f"❌ Failed to load reranker model: {e}")
                self.reranker_model = None
        return self.reranker_model
    
    def encode_query(self, query: str):
        """使用 GPU 进行查询编码"""
        if self.embedding_model is None:
            self.load_embedding_model()
        
        if self.embedding_model:
            with torch.no_grad():
                embedding = self.embedding_model.encode(query, convert_to_tensor=True)
            return embedding.cpu().numpy()
        else:
            # Fallback: 使用简单的方法
            return None

# 全局模型实例（稍后在 startup 时初始化）
models = None

# ==================== RAG 实现 ====================

async def perform_rag_search(query: str, city: str, top_k: int, retriever: str, reranker: str, use_llm_ranking: bool = True) -> Dict:
    """
    真实的 RAG 搜索实现（使用1028版本向量数据库）
    
    流程：
    1. 使用 Embedding 模型编码查询
    2. 在指定城市的 FAISS 索引中检索（候选文档数量 = top_k × candidate_multiplier）
    3. 使用 Reranker 模型重排序
    4. 返回 top_k 结果
    
    参考策略（与 interactive_merchant_search_vllm.py 保持一致）：
    - 候选文档倍数：5倍（即检索 top_k × 5 个候选文档）
    - 相似度转换：将 L2 距离转换为 0-1 范围的相似度分数
    - 重排序文本：构建包含地理位置（city/district/business_area/landmark）+ 多个关键字段的丰富文本表示
    - 保留排名信息：记录原始排名、重排序分数和最终排名
    """
    start_time = time.time()
    
    # 检查向量数据库是否已加载
    if not models.vector_db:
        raise HTTPException(status_code=503, detail="Vector database not loaded. Please check server configuration.")
    
    if city not in models.vector_db.indexes:
        available_cities = list(models.vector_db.indexes.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"City '{city}' not available. Available cities: {available_cities}"
        )
    
    try:
        # 1. 使用 Embedding 模型编码查询
        embedding_start = time.time()
        query_embedding = models.encode_query(query)
        if query_embedding is None:
            raise HTTPException(status_code=503, detail="Embedding model not loaded")
        embedding_time = time.time() - embedding_start
        
        # 2. 从 FAISS 向量数据库检索
        # 候选文档策略：如果使用重排序，检索 top_k × 5 个候选文档
        candidate_multiplier = 5  # 候选文档倍数（与 VLLM 脚本保持一致）
        use_reranker = models.reranker_model is not None
        
        if use_reranker:
            # 使用重排序：检索更多候选文档
            retrieval_k = min(top_k * candidate_multiplier, models.vector_db.indexes[city].ntotal)
            print(f"🔍 Retrieving {retrieval_k} candidates (top_k={top_k} × multiplier={candidate_multiplier}) for reranking")
        else:
            # 不使用重排序：直接检索 top_k 个
            retrieval_k = top_k
            print(f"🔍 Retrieving {retrieval_k} candidates (no reranking)")
        
        retrieval_start = time.time()
        retrieved_docs = models.vector_db.search(query_embedding, city=city, top_k=retrieval_k)
        retrieval_time = time.time() - retrieval_start
        
        if not retrieved_docs:
            return {
                "answer": f"未找到与「{query}」相关的商户信息",
                "sources": [],
                "metrics": {
                    "latency_ms": (time.time() - start_time) * 1000,
                    "embedding_time_ms": embedding_time * 1000,
                    "retrieval_time_ms": retrieval_time * 1000
                },
                "processing_time": time.time() - start_time
            }
        
        # 2.5. 转换相似度分数（将 L2 距离转换为 0-1 范围的相似度）
        # 参考 VLLM 系统的相似度转换策略
        if retrieved_docs:
            max_distance = max(doc.get('vector_score', 0) for doc in retrieved_docs)
            for i, doc in enumerate(retrieved_docs):
                distance = doc.get('vector_score', 0)
                # 将 L2 距离转换为相似度：距离越小，相似度越高
                similarity_score = max(0.0, (max_distance - distance) / max_distance) if max_distance > 0 else 0.0
                doc['distance'] = float(distance)  # 保留原始 L2 距离
                doc['similarity'] = float(similarity_score)  # 转换后的相似度 (0-1)
                doc['rank'] = i + 1  # 原始检索排名
                doc['original_rank'] = i + 1  # 保存原始排名
        
        # 3. 使用 Reranker 模型重排序
        rerank_time = 0
        if use_reranker and len(retrieved_docs) > 1:
            try:
                rerank_start = time.time()
                
                # 构建查询-文档对（使用更丰富的文档表示）
                pairs = []
                for doc in retrieved_docs:
                    # 参考 VLLM 系统的文档格式化策略：包含多个关键字段
                    doc_text = _format_document_for_rerank(doc)
                    pairs.append([query, doc_text])
                
                # 使用 Reranker 重新打分 (使用 batch_size=1 避免 padding 问题)
                rerank_scores = models.reranker_model.predict(pairs, batch_size=1)
                
                # 更新分数
                for doc, score in zip(retrieved_docs, rerank_scores):
                    doc["rerank_score"] = float(score)
                
                # 按重排序分数排序
                retrieved_docs = sorted(retrieved_docs, key=lambda x: x.get("rerank_score", 0), reverse=True)
                
                # 更新最终排名
                for i, doc in enumerate(retrieved_docs):
                    doc['final_rank'] = i + 1
                
                rerank_time = time.time() - rerank_start
                print(f"🔄 Reranked {len(retrieved_docs)} documents in {rerank_time:.2f}s")
                
            except Exception as e:
                print(f"⚠️ Reranking failed: {e}, using vector scores only")
                # 重排序失败，使用原始排名
                for i, doc in enumerate(retrieved_docs):
                    doc['final_rank'] = doc.get('rank', i + 1)
        else:
            # 不使用重排序，直接使用原始排名
            for i, doc in enumerate(retrieved_docs):
                doc['final_rank'] = doc.get('rank', i + 1)
        
        # 调试：打印第一个文档的字段
        if retrieved_docs:
            print(f"📋 First document fields: {list(retrieved_docs[0].keys())}")
            print(f"📋 Merchant name: {retrieved_docs[0].get('name', 'NOT FOUND')}")
        
        # 4. 使用 LLM 精排（从 rerank 的结果中选出 top_k 个）
        llm_ranking_time = 0
        if use_llm_ranking and models.llm_ranker and len(retrieved_docs) > top_k:
            try:
                llm_start = time.time()
                print(f"🤖 LLM ranking: selecting {top_k} from {len(retrieved_docs)} candidates")
                retrieved_docs = await models.llm_ranker.select_top_k_async(
                    query=query,
                    candidates=retrieved_docs,
                    top_k=top_k,
                    city=city
                )
                llm_ranking_time = time.time() - llm_start
                print(f"✅ LLM ranking completed in {llm_ranking_time:.2f}s")
            except Exception as e:
                print(f"⚠️ LLM ranking failed: {e}, using reranked results")
                retrieved_docs = retrieved_docs[:top_k]
        else:
            # 不使用 LLM 精排，直接取 top_k
            if not use_llm_ranking:
                print(f"📋 LLM ranking disabled by request")
            elif not models.llm_ranker:
                print(f"⚠️ LLM ranker not initialized")
            retrieved_docs = retrieved_docs[:top_k]
        
        # 5. 生成答案摘要（city 已经是中文）
        answer = f"在{city}找到相关商户，为您推荐以下 {len(retrieved_docs)} 家："
        
        # 6. 计算评估指标
        metrics = {
            "retrieved_count": len(retrieved_docs),
            "returned_count": len(retrieved_docs),
            "city": city,
            "latency_ms": (time.time() - start_time) * 1000,
            "embedding_time_ms": embedding_time * 1000,
            "retrieval_time_ms": retrieval_time * 1000,
            "rerank_time_ms": rerank_time * 1000 if use_reranker else 0,
            "llm_ranking_time_ms": llm_ranking_time * 1000,
            "used_reranker": use_reranker,
            "used_llm_ranking": use_llm_ranking and llm_ranking_time > 0,
            "candidate_multiplier": candidate_multiplier if use_reranker else 1
        }
        
        # 调试：打印返回的商店名称
        print(f"📦 Returning {len(retrieved_docs)} merchants:")
        for i, doc in enumerate(retrieved_docs[:3], 1):  # 只打印前3个
            score_info = f"rerank={doc.get('rerank_score', 0):.4f}" if use_reranker else f"similarity={doc.get('similarity', 0):.4f}"
            llm_rank = f", llm_rank={doc.get('llm_rank', '-')}" if doc.get('llm_selected') else ""
            print(f"   {i}. {doc.get('name', 'NO_NAME')} ({score_info}, rank: {doc.get('original_rank', '?')}→{doc.get('final_rank', '?')}{llm_rank})")
        
        return {
            "answer": answer,
            "sources": retrieved_docs,
            "metrics": metrics,
            "processing_time": time.time() - start_time
        }
        
    except Exception as e:
        print(f"❌ RAG search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def _format_document_for_rerank(doc_info: Dict[str, Any]) -> str:
    """
    格式化文档用于重排序（增强版：使用清晰的中文标签）
    
    增强版：在 VLLM 脚本基础上，强制包含地理位置信息（city, district, business_area, landmark）
    构建包含多个关键字段的丰富文本表示，提高重排序准确性
    
    格式示例：
        店名：星巴克咖啡 - 类型：餐饮/咖啡厅 - 地址：北京市朝阳区建国门外大街1号 - 城市：北京 - 区域：朝阳区 - 商圈：国贸
    
    Args:
        doc_info: 文档信息字典
        
    Returns:
        格式化后的文档文本（带中文标签）
    """
    parts = []
    
    # 1. 店名（必填）
    if doc_info.get('name'):
        parts.append(f"店名：{doc_info['name']}")
    
    # 2. 类型（类别 + 子类别）
    category_parts = []
    if doc_info.get('category'):
        category_parts.append(doc_info['category'])
    if doc_info.get('subcategory'):
        category_parts.append(doc_info['subcategory'])
    
    if category_parts:
        parts.append(f"类型：{'/'.join(category_parts)}")
    
    # 3. 地址（必填）
    if doc_info.get('address'):
        parts.append(f"地址：{doc_info['address']}")
    
    # 4. 🔥 地理位置信息（必须参与重排）
    if doc_info.get('city'):
        parts.append(f"城市：{doc_info['city']}")
    
    if doc_info.get('district'):
        parts.append(f"区域：{doc_info['district']}")
    
    if doc_info.get('business_area'):
        parts.append(f"商圈：{doc_info['business_area']}")
    
    if doc_info.get('landmark'):
        parts.append(f"地标：{doc_info['landmark']}")
    
    # 使用 " - " 连接所有部分
    return ' - '.join(parts)

def perform_web_search(query: str, top_k: int) -> Dict:
    """传统 Web 搜索"""
    start_time = time.time()
    
    # 实现你的 Web 搜索逻辑
    # 例如：ElasticSearch, BM25 等
    
    results = [
        {
            "merchant_name": f"商户 {i+1}",
            "address": f"上海市某区某街道{i+1}号",
            "rating": 4.5 - i * 0.1,
            "price": f"人均{100 + i*20}元"
        }
        for i in range(top_k)
    ]
    
    return {
        "answer": f"找到 {len(results)} 条结果",
        "sources": results,
        "metrics": {"latency_ms": (time.time() - start_time) * 1000},
        "processing_time": time.time() - start_time
    }

def perform_agentic_search(query: str, model: str, max_iterations: int) -> Dict:
    """智能体搜索"""
    start_time = time.time()
    
    # 实现你的 Agent 逻辑
    # 例如：使用 LangChain, AutoGPT 等
    
    reasoning_steps = [
        "🤔 分析查询意图...",
        "🔍 第1步：搜索相关商户...",
        "📊 第2步：过滤和排序结果...",
        "💡 第3步：生成推荐..."
    ]
    
    results = [
        {
            "merchant_name": "推荐商户 1",
            "address": "上海市浦东新区",
            "rating": 4.8,
            "reason": "高评分且符合您的需求"
        }
    ]
    
    return {
        "answer": "基于多步推理，为您推荐...",
        "sources": results,
        "metrics": {
            "correctness": 0.85,
            "completeness": 0.90,
            "faithfulness": 0.88,
            "latency_ms": (time.time() - start_time) * 1000
        },
        "reasoning_steps": reasoning_steps,
        "processing_time": time.time() - start_time
    }

# ==================== API 端点 ====================

@app.get("/")
def root():
    return {
        "service": "LocalSearchBench RAG API",
        "version": "1.0.0",
        "device": DEVICE,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    """健康检查"""
    cities_loaded = {}
    if models and models.vector_db:
        # CityVectorDB 使用 city_to_en 映射（中文 -> 英文）
        # indexes 和 metadata 的 key 是中文城市名
        for city_cn, city_en in models.vector_db.city_to_en.items():
            if city_cn in models.vector_db.indexes:
                cities_loaded[city_en] = {
                "name": city_cn,
                    "vectors": models.vector_db.indexes[city_cn].ntotal,
                    "merchants": len(models.vector_db.metadata.get(city_cn, []))
        }
    
    return {
        "status": "healthy",
        "device": DEVICE,
        "gpu_available": torch.cuda.is_available() if 'torch' in globals() else False,
        "models_loaded": {
            "embedding": models.embedding_model is not None if models else False,
            "reranker": models.reranker_model is not None if models else False,
            "vector_db": models.vector_db is not None if models else False
        },
        "cities": cities_loaded,
        "total_cities": len(cities_loaded)
    }

@app.post("/api/rag/search", response_model=SearchResult)
async def rag_search(request: RAGSearchRequest):
    """RAG 搜索端点（支持多城市）"""
    try:
        result = await perform_rag_search(
            query=request.query,
            city=request.city,
            top_k=request.top_k,
            retriever=request.retriever,
            reranker=request.reranker,
            use_llm_ranking=request.use_llm_ranking
        )
        return SearchResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/web/search", response_model=SearchResult)
async def web_search(request: WebSearchRequest):
    """Web 搜索端点"""
    try:
        result = perform_web_search(
            query=request.query,
            top_k=request.top_k
        )
        return SearchResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agentic/search", response_model=SearchResult)
async def agentic_search(request: AgenticSearchRequest):
    """Agentic 搜索端点"""
    try:
        result = perform_agentic_search(
            query=request.query,
            model=request.model,
            max_iterations=request.max_iterations
        )
        return SearchResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """服务启动时预加载模型和向量数据库"""
    global models
    
    print("🚀 Starting LocalSearchBench RAG Server...")
    print(f"📍 Device: {DEVICE}")
    
    # 获取配置
    data_dir = getattr(app.state, 'data_dir', None)
    embedding_model_path = getattr(app.state, 'embedding_model_path', None)
    reranker_model_path = getattr(app.state, 'reranker_model_path', None)
    use_gpu = getattr(app.state, 'use_gpu', True)  # 默认使用 GPU
    config_path = getattr(app.state, 'config_path', None)  # LLM 配置文件路径
    
    # 初始化模型（包括向量数据库和 LLM 精排器）
    models = RAGModels(data_dir=data_dir, use_gpu=use_gpu, config_path=config_path)
    
    # 预加载模型到 GPU
    if DEVICE == "cuda":
        print("\n📥 Pre-loading models to GPU...")
        
        # 加载 Embedding 模型
        if embedding_model_path:
            models.load_embedding_model(embedding_model_path)
        else:
            print("⚠️  No embedding model path specified, using default")
            models.load_embedding_model()
        
        # 加载 Reranker 模型
        if reranker_model_path:
            models.load_reranker_model(reranker_model_path)
        else:
            print("⚠️  No reranker model path specified, using default")
            models.load_reranker_model()
        
        print("✅ Models loaded successfully")
    else:
        print("⚠️ Running in CPU mode")
    
    # 检查向量数据库状态
    if models.vector_db:
        print(f"\n✅ Vector databases ready: {len(models.vector_db.indexes)} cities loaded")
    else:
        print("\n⚠️  No vector databases loaded. Please specify --data-dir")

@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭时清理资源"""
    print("👋 Shutting down LocalSearchBench RAG Server...")
    # 清理 GPU 显存
    if DEVICE == "cuda" and 'torch' in globals():
        torch.cuda.empty_cache()

# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="LocalSearchBench RAG Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--data-dir", type=str, default=None, help="Path to vector database directory (containing 1028 FAISS files)")
    parser.add_argument("--embedding-model", type=str, default=None, help="Path to Qwen3-Embedding-8B model")
    parser.add_argument("--reranker-model", type=str, default=None, help="Path to Qwen3-Reranker-8B model")
    parser.add_argument("--config", type=str, default=None, help="Path to config.yaml for LLM ranking")
    parser.add_argument("--use-gpu", action="store_true", default=True, help="Use GPU for FAISS vector search (default: True)")
    parser.add_argument("--no-gpu", action="store_true", help="Force CPU mode for FAISS vector search")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    # 从环境变量或命令行参数获取配置
    data_dir = args.data_dir or os.getenv("RAG_DATA_DIR")
    embedding_model_path = args.embedding_model or os.getenv("EMBEDDING_MODEL_PATH")
    reranker_model_path = args.reranker_model or os.getenv("RERANKER_MODEL_PATH")
    config_path = args.config or os.getenv("TUANSOU_CONFIG") or os.getenv("CONFIG_PATH")
    
    # GPU 配置
    use_gpu = args.use_gpu and not args.no_gpu
    
    # 将配置保存到全局变量供 startup_event 使用
    app.state.data_dir = data_dir
    app.state.embedding_model_path = embedding_model_path
    app.state.reranker_model_path = reranker_model_path
    app.state.use_gpu = use_gpu
    app.state.config_path = config_path
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║     LocalSearchBench RAG Server (Multi-City Support)      ║
║     Device: {DEVICE:48s} ║
║     Host: {args.host:50s} ║
║     Port: {args.port:50d} ║
║     Data Dir: {(data_dir or 'Not specified')[:45]:45s} ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,  # 直接传入 app 对象，而不是字符串
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info"
    )

if __name__ == "__main__":
    main()

