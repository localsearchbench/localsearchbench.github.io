"""
RAG Server - 部署在有 GPU 的服务器上
支持 Web Search、RAG Search 和 Agentic Search

运行方式：
    python rag_server.py --port 8000 --host 0.0.0.0

环境变量配置：
    export OPENAI_API_KEY="your-key"
    export DASHSCOPE_API_KEY="your-key"  # 如果使用 Qwen 模型

检索与重排策略：
    本服务器与 interactive_merchant_search_vllm.py 保持高度一致：
    - 候选文档倍数：candidate_multiplier = 5
    - 相似度计算：(max_distance - distance) / max_distance
    - 重排序文本格式：name - category/subcategory - address + 地理位置（必须）+ 多个可选字段
    - 地理位置字段（必须参与重排）：city, district, business_area, landmark
    - subcategory 字段：如果存在，会拼接到 category 后面（格式：category/subcategory）
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uvicorn
import argparse
import os
import time
from datetime import datetime

# 基础依赖
import json
import numpy as np

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
    top_k: int = 10  # 最终返回10个结果
    retriever: str = "qwen3-embedding-8b"  # 默认使用 Qwen3-Embedding-8B
    reranker: str = "qwen3-reranker-8b"    # 默认使用 Qwen3-Reranker-8B

class WebSearchRequest(BaseModel):
    query: str
    top_k: int = 10

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

# ==================== 模型加载（GPU）====================

class RAGModels:
    """在服务器启动时加载模型到 GPU"""
    
    def __init__(self, data_dir: str = None, use_gpu: bool = True):
        self.embedding_model = None
        self.reranker_model = None
        self.llm = None
        self.vector_db = None
        
        # 初始化向量数据库（支持 GPU 加速）
        if data_dir and os.path.exists(data_dir):
            try:
                self.vector_db = CityVectorDB(data_dir, use_gpu=use_gpu)
            except Exception as e:
                print(f"⚠️ Failed to load vector databases: {e}")
        
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

def perform_rag_search(query: str, city: str, top_k: int, retriever: str, reranker: str) -> Dict:
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
        
        # 3. 🔥 两阶段重排序策略：先地理过滤，再类型匹配
        rerank_time = 0
        if use_reranker and len(retrieved_docs) > 1:
            try:
                rerank_start = time.time()
                
                # 🔥 阶段1：提取查询中的地理位置关键词
                location_keywords = _extract_location_from_query(query)
                print(f"🗺️  Extracted location keywords: {location_keywords}")
                
                # 🔥 阶段2：计算地理相关性分数
                for doc in retrieved_docs:
                    location_score = _calculate_location_relevance(doc, location_keywords)
                    doc['location_score'] = location_score
                
                # 🔥 阶段3：如果有地理关键词，先按地理相关性过滤
                if location_keywords:
                    # 统计地理匹配情况
                    matched_docs = [doc for doc in retrieved_docs if doc.get('location_score', 0) > 0]
                    unmatched_docs = [doc for doc in retrieved_docs if doc.get('location_score', 0) == 0]
                    
                    print(f"📍 Location filtering: {len(matched_docs)} matched, {len(unmatched_docs)} unmatched")
                    
                    # 如果有匹配地理位置的文档，优先使用它们
                    if matched_docs:
                        # 对匹配地理位置的文档进行重排序
                        pairs = []
                        for doc in matched_docs:
                            doc_text = _format_document_for_rerank(doc)
                            pairs.append([query, doc_text])
                        
                        # 使用 Reranker 重新打分
                        rerank_scores = models.reranker_model.predict(pairs, batch_size=1)
                        
                        # 更新分数（地理分数 × 0.3 + rerank分数 × 0.7）
                        for doc, score in zip(matched_docs, rerank_scores):
                            doc["rerank_score"] = float(score)
                            # 🔥 综合分数：地理位置权重30%，语义相关性权重70%
                            doc["final_score"] = doc['location_score'] * 0.3 + float(score) * 0.7
                        
                        # 对未匹配地理位置的文档也打分（但分数降低）
                        if unmatched_docs:
                            pairs_unmatched = []
                            for doc in unmatched_docs:
                                doc_text = _format_document_for_rerank(doc)
                                pairs_unmatched.append([query, doc_text])
                            
                            rerank_scores_unmatched = models.reranker_model.predict(pairs_unmatched, batch_size=1)
                            for doc, score in zip(unmatched_docs, rerank_scores_unmatched):
                                doc["rerank_score"] = float(score)
                                # 🔥 未匹配地理位置的文档分数降低（× 0.5）
                                doc["final_score"] = float(score) * 0.5
                        
                        # 合并并按最终分数排序
                        retrieved_docs = matched_docs + unmatched_docs
                        retrieved_docs = sorted(retrieved_docs, key=lambda x: x.get("final_score", 0), reverse=True)
                    else:
                        # 如果没有匹配地理位置的文档，使用原始重排序逻辑
                        print("⚠️  No location-matched documents, using standard reranking")
                        pairs = []
                        for doc in retrieved_docs:
                            doc_text = _format_document_for_rerank(doc)
                            pairs.append([query, doc_text])
                        
                        rerank_scores = models.reranker_model.predict(pairs, batch_size=1)
                        for doc, score in zip(retrieved_docs, rerank_scores):
                            doc["rerank_score"] = float(score)
                            doc["final_score"] = float(score)
                        
                        retrieved_docs = sorted(retrieved_docs, key=lambda x: x.get("final_score", 0), reverse=True)
                else:
                    # 没有地理关键词，使用标准重排序
                    print("ℹ️  No location keywords in query, using standard reranking")
                    pairs = []
                    for doc in retrieved_docs:
                        doc_text = _format_document_for_rerank(doc)
                        pairs.append([query, doc_text])
                    
                    rerank_scores = models.reranker_model.predict(pairs, batch_size=1)
                    for doc, score in zip(retrieved_docs, rerank_scores):
                        doc["rerank_score"] = float(score)
                        doc["final_score"] = float(score)
                    
                    retrieved_docs = sorted(retrieved_docs, key=lambda x: x.get("final_score", 0), reverse=True)
                
                # 更新最终排名
                for i, doc in enumerate(retrieved_docs):
                    doc['final_rank'] = i + 1
                
                rerank_time = time.time() - rerank_start
                print(f"🔄 Two-stage reranking completed in {rerank_time:.2f}s")
                
            except Exception as e:
                print(f"⚠️ Reranking failed: {e}, using vector scores only")
                import traceback
                traceback.print_exc()
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
        
        # 4. 生成答案摘要（city 已经是中文）
        answer = f"在{city}找到 {len(retrieved_docs)} 家相关商户，为您推荐以下 {min(top_k, len(retrieved_docs))} 家："
        
        # 5. 计算评估指标
        metrics = {
            "retrieved_count": len(retrieved_docs),
            "returned_count": min(top_k, len(retrieved_docs)),
            "city": city,
            "latency_ms": (time.time() - start_time) * 1000,
            "embedding_time_ms": embedding_time * 1000,
            "retrieval_time_ms": retrieval_time * 1000,
            "rerank_time_ms": rerank_time * 1000 if use_reranker else 0,
            "used_reranker": use_reranker,
            "candidate_multiplier": candidate_multiplier if use_reranker else 1
        }
        
        # 调试：打印返回的商店名称
        top_merchants = retrieved_docs[:top_k]
        print(f"📦 Returning top {len(top_merchants)} merchants:")
        for i, doc in enumerate(top_merchants[:5], 1):  # 打印前5个
            if use_reranker:
                location_info = f"loc={doc.get('location_score', 0):.2f}" if 'location_score' in doc else ""
                rerank_info = f"rerank={doc.get('rerank_score', 0):.4f}"
                final_info = f"final={doc.get('final_score', 0):.4f}"
                score_info = f"{location_info} {rerank_info} {final_info}".strip()
                geo_info = f"{doc.get('district', '?')}/{doc.get('business_area', '?')}"
            else:
                score_info = f"similarity={doc.get('similarity', 0):.4f}"
                geo_info = f"{doc.get('district', '?')}/{doc.get('business_area', '?')}"
            
            print(f"   {i}. {doc.get('name', 'NO_NAME')} | {geo_info} | {score_info} | rank: {doc.get('original_rank', '?')}→{doc.get('final_rank', '?')}")
        
        return {
            "answer": answer,
            "sources": retrieved_docs[:top_k],
            "metrics": metrics,
            "processing_time": time.time() - start_time
        }
        
    except Exception as e:
        print(f"❌ RAG search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def _extract_location_from_query(query: str) -> List[str]:
    """
    从查询中提取地理位置关键词
    
    支持的地理层级：
    - 区级：浦东新区、黄浦区、徐汇区等
    - 商圈：陆家嘴、南京路、淮海路等
    - 地标：东方明珠、人民广场、虹桥机场等
    
    Returns:
        地理位置关键词列表
    """
    location_keywords = []
    
    # 常见区域关键词
    district_patterns = ['区', '新区', '县']
    for pattern in district_patterns:
        if pattern in query:
            # 提取"XX区"、"XX新区"等
            import re
            matches = re.findall(r'[\u4e00-\u9fa5]+' + pattern, query)
            location_keywords.extend(matches)
    
    # 常见商圈/地标关键词（可扩展）
    common_areas = [
        '陆家嘴', '南京路', '淮海路', '徐家汇', '五角场', '中山公园',
        '人民广场', '静安寺', '虹桥', '张江', '金桥', '世纪公园',
        '新天地', '田子坊', '外滩', '豫园', '七宝', '莘庄'
    ]
    
    for area in common_areas:
        if area in query:
            location_keywords.append(area)
    
    return location_keywords


def _calculate_location_relevance(doc_info: Dict[str, Any], location_keywords: List[str]) -> float:
    """
    计算文档与地理位置的相关性分数
    
    匹配优先级：
    1. 商圈 (business_area) - 权重 1.0
    2. 区域 (district) - 权重 0.8
    3. 地标 (landmark) - 权重 0.7
    4. 地址 (address) - 权重 0.6
    
    Returns:
        地理相关性分数 (0-1)
    """
    if not location_keywords:
        return 1.0  # 如果没有地理关键词，不过滤
    
    score = 0.0
    matched = False
    
    # 检查商圈匹配
    business_area = doc_info.get('business_area', '')
    for keyword in location_keywords:
        if keyword in business_area:
            score = max(score, 1.0)
            matched = True
            break
    
    # 检查区域匹配
    district = doc_info.get('district', '')
    for keyword in location_keywords:
        if keyword in district:
            score = max(score, 0.8)
            matched = True
            break
    
    # 检查地标匹配
    landmark = doc_info.get('landmark', '')
    for keyword in location_keywords:
        if keyword in landmark:
            score = max(score, 0.7)
            matched = True
            break
    
    # 检查地址匹配
    address = doc_info.get('address', '')
    for keyword in location_keywords:
        if keyword in address:
            score = max(score, 0.6)
            matched = True
            break
    
    return score if matched else 0.0


def _format_document_for_rerank(doc_info: Dict[str, Any]) -> str:
    """
    格式化文档用于重排序（地理优先策略）
    
    🔥 新策略：先地理位置，后商店类型
    
    格式示例：
        位置：浦东新区陆家嘴商圈 类型：餐饮/咖啡厅 店名：星巴克咖啡 特色：WiFi 现磨咖啡
    
    Args:
        doc_info: 文档信息字典
        
    Returns:
        格式化后的文档文本（地理位置前置）
    """
    parts = []
    
    # 🔥 1. 地理位置（最优先）
    location_parts = []
    if doc_info.get('district'):
        location_parts.append(doc_info['district'])
    if doc_info.get('business_area'):
        location_parts.append(doc_info['business_area'] + '商圈')
    if doc_info.get('landmark'):
        location_parts.append('近' + doc_info['landmark'])
    
    if location_parts:
        parts.append(f"位置：{''.join(location_parts)}")
    
    # 2. 类型（类别 + 子类别）
    category_parts = []
    if doc_info.get('category'):
        category_parts.append(doc_info['category'])
    if doc_info.get('subcategory'):
        category_parts.append(doc_info['subcategory'])
    
    if category_parts:
        parts.append(f"类型：{'/'.join(category_parts)}")
    
    # 3. 店名
    if doc_info.get('name'):
        parts.append(f"店名：{doc_info['name']}")
    
    # 4. 特色服务（重要）
    if doc_info.get('specialties'):
        parts.append(f"特色：{doc_info['specialties']}")
    
    if doc_info.get('tags'):
        parts.append(f"标签：{doc_info['tags']}")
    
    # 5. 其他信息
    if doc_info.get('products'):
        parts.append(f"服务：{doc_info['products']}")
    
    if doc_info.get('business_hours'):
        parts.append(f"营业：{doc_info['business_hours']}")
    
    # 使用单个空格连接所有部分
    return ' '.join(parts)

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
        result = perform_rag_search(
            query=request.query,
            city=request.city,
            top_k=request.top_k,
            retriever=request.retriever,
            reranker=request.reranker
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
    
    # 初始化模型（包括向量数据库，会根据 use_gpu 参数决定是否使用 GPU）
    models = RAGModels(data_dir=data_dir, use_gpu=use_gpu)
    
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
    parser.add_argument("--use-gpu", action="store_true", default=True, help="Use GPU for FAISS vector search (default: True)")
    parser.add_argument("--no-gpu", action="store_true", help="Force CPU mode for FAISS vector search")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    # 从环境变量或命令行参数获取配置
    data_dir = args.data_dir or os.getenv("RAG_DATA_DIR")
    embedding_model_path = args.embedding_model or os.getenv("EMBEDDING_MODEL_PATH")
    reranker_model_path = args.reranker_model or os.getenv("RERANKER_MODEL_PATH")
    
    # GPU 配置
    use_gpu = args.use_gpu and not args.no_gpu
    
    # 将配置保存到全局变量供 startup_event 使用
    app.state.data_dir = data_dir
    app.state.embedding_model_path = embedding_model_path
    app.state.reranker_model_path = reranker_model_path
    app.state.use_gpu = use_gpu
    
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

