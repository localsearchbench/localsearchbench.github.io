# 🚀 服务器向量数据库集成指南

> 📌 **模型配置**: [Qwen3-Embedding-8B 和 Qwen3-Reranker-8B](MODEL_SPEC.md)  
> 🚀 **快速启动**: 查看 [RAG 服务器快速启动指南](server/README_QUICKSTART.md)（推荐新手）

本文档提供服务器端详细配置说明和高级部署选项。

## 📋 服务器资源清单

### ✅ 可用的向量数据库（1028 版本）

所有城市的向量数据库都已构建完成：

```bash
# 上海
faiss_merchant_index_vllm_shanghai_1028.faiss
faiss_merchant_index_vllm_shanghai_1028_metadata.json

# 北京
faiss_merchant_index_vllm_beijing_1028.faiss
faiss_merchant_index_vllm_beijing_1028_metadata.json

# 广州
faiss_merchant_index_vllm_guangzhou_1028.faiss
faiss_merchant_index_vllm_guangzhou_1028_metadata.json

# 深圳
faiss_merchant_index_vllm_shenzhen_1028.faiss
faiss_merchant_index_vllm_shenzhen_1028_metadata.json

# 杭州
faiss_merchant_index_vllm_hangzhou_1028.faiss
faiss_merchant_index_vllm_hangzhou_1028_metadata.json

# 苏州
faiss_merchant_index_vllm_suzhou_1028.faiss
faiss_merchant_index_vllm_suzhou_1028_metadata.json

# 成都
faiss_merchant_index_vllm_chengdu_1028.faiss
faiss_merchant_index_vllm_chengdu_1028_metadata.json

# 重庆
faiss_merchant_index_vllm_chongqing_1028.faiss
faiss_merchant_index_vllm_chongqing_1028_metadata.json

# 武汉
faiss_merchant_index_vllm_wuhan_1028.faiss
faiss_merchant_index_vllm_wuhan_1028_metadata.json
```

### 🤖 使用的模型

**已确定的模型配置**：

```bash
# Embedding 模型（已确定）
Qwen3-Embedding-8B/        # ✅ 用于查询和文档编码
├── config.json
├── model.safetensors
└── tokenizer files

# Reranker 模型（已确定）
Qwen3-Reranker-8B/         # ✅ 用于结果重排序
├── config.json
├── model.safetensors
└── tokenizer files
```

**模型说明**：
- **Qwen3-Embedding-8B**: 8B 参数的高质量 Embedding 模型，支持中英双语
- **Qwen3-Reranker-8B**: 8B 参数的 Reranker 模型，用于精确重排序
- 两个模型均需放置在 `RAG_DATA_DIR` 目录下

## 🔧 服务器端配置

### 1️⃣ 环境变量配置

在服务器上创建 `.env` 文件或直接 export：

```bash
# GPU 服务器上执行
export RAG_DATA_DIR="/path/to/rag_gpu"  # 向量数据库所在目录
export EMBEDDING_MODEL_PATH="/path/to/rag_gpu/Qwen3-Embedding-8B"
export RERANKER_MODEL_PATH="/path/to/rag_gpu/Qwen3-Reranker-8B"
export CUDA_VISIBLE_DEVICES="0"  # 使用第一个 GPU
```

### 2️⃣ 依赖安装

```bash
cd /path/to/rag_gpu
pip install -r requirements.txt

# 确保安装了以下核心库
pip install faiss-gpu  # GPU 版本的 FAISS
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install sentence-transformers
pip install transformers
pip install vllm  # 如果使用 vLLM 加速
```

### 3️⃣ 测试向量数据库加载

在服务器上测试是否能正确加载：

```python
import faiss
import json
import numpy as np

# 测试加载上海的向量数据库
index = faiss.read_index("faiss_merchant_index_vllm_shanghai_1028.faiss")
print(f"✅ Index loaded: {index.ntotal} vectors, dimension: {index.d}")

# 加载元数据
with open("faiss_merchant_index_vllm_shanghai_1028_metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)
print(f"✅ Metadata loaded: {len(metadata)} merchants")
print(f"📍 Sample merchant: {metadata[0]}")
```

### 4️⃣ 启动 RAG 服务器

#### 方式 1: 使用启动脚本（推荐）

```bash
cd /path/to/your/repo/server

# 1. 编辑配置文件
cp config.example.sh config.sh
nano config.sh  # 修改 RAG_DATA_DIR 等配置

# 2. 加载配置并启动
source config.sh
./start_rag_server.sh
```

#### 方式 2: 直接运行脚本

```bash
cd /path/to/your/repo/server

# 修改 start_rag_server.sh 中的 DEFAULT_DATA_DIR
# 然后直接运行
./start_rag_server.sh
```

#### 方式 3: 使用环境变量

```bash
RAG_DATA_DIR=/path/to/rag_gpu ./start_rag_server.sh
```

#### 方式 4: 直接使用 Python

```bash
cd /path/to/your/repo/server
python rag_server.py \
  --host 0.0.0.0 \
  --port 8000 \
  --data-dir /path/to/rag_gpu \
  --embedding-model /path/to/rag_gpu/Qwen3-Embedding-8B \
  --reranker-model /path/to/rag_gpu/Qwen3-Reranker-8B
```

#### 查看帮助信息

```bash
# 脚本帮助
./start_rag_server.sh --help

# Python 帮助
python rag_server.py --help
```

#### 测试服务器

服务启动后，运行测试脚本验证：

```bash
# 运行自动化测试
./test_server.sh

# 或手动测试
curl http://localhost:8000/health
curl http://localhost:8000/cities
```

## 📝 rag_server.py 配置要点

需要在 `rag_server.py` 中实现以下功能：

### 1. 加载所有城市的向量数据库

```python
class CityVectorDB:
    def __init__(self, data_dir: str):
        self.cities = {
            "shanghai": "上海",
            "beijing": "北京", 
            "guangzhou": "广州",
            "shenzhen": "深圳",
            "hangzhou": "杭州",
            "suzhou": "苏州",
            "chengdu": "成都",
            "chongqing": "重庆",
            "wuhan": "武汉"
        }
        self.indexes = {}
        self.metadata = {}
        
        for city_en, city_cn in self.cities.items():
            index_path = f"{data_dir}/faiss_merchant_index_vllm_{city_en}_1028.faiss"
            meta_path = f"{data_dir}/faiss_merchant_index_vllm_{city_en}_1028_metadata.json"
            
            try:
                self.indexes[city_en] = faiss.read_index(index_path)
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata[city_en] = json.load(f)
                print(f"✅ Loaded {city_cn}: {self.indexes[city_en].ntotal} vectors")
            except Exception as e:
                print(f"⚠️ Failed to load {city_cn}: {e}")
```

### 2. 实现检索功能

```python
def search(self, query: str, city: str = "shanghai", top_k: int = 5):
    """在指定城市搜索商户"""
    # 1. 使用 Embedding 模型编码查询
    query_embedding = self.embedding_model.encode(query)
    
    # 2. 在 FAISS 索引中搜索
    distances, indices = self.indexes[city].search(
        query_embedding.reshape(1, -1), 
        top_k * 2  # 多检索一些用于重排序
    )
    
    # 3. 获取对应的元数据
    results = [self.metadata[city][idx] for idx in indices[0]]
    
    # 4. 使用 Reranker 重排序
    if self.reranker_model:
        pairs = [[query, doc["description"]] for doc in results]
        rerank_scores = self.reranker_model.predict(pairs)
        for doc, score in zip(results, rerank_scores):
            doc["rerank_score"] = float(score)
        results = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
    
    return results[:top_k]
```

## 🧪 测试 API

### 启动服务器后测试

```bash
# 测试 RAG 搜索（上海）
curl -X POST "http://your-server:8000/api/rag_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "陆家嘴附近有什么好吃的火锅",
    "city": "shanghai",
    "top_k": 5,
    "retriever": "qwen3-embedding-8b",
    "reranker": "qwen3-reranker-8b"
  }'

# 测试多城市搜索
curl -X POST "http://your-server:8000/api/rag_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "北京三里屯有什么推荐的餐厅",
    "city": "beijing",
    "top_k": 5
  }'
```

## 🔍 性能优化建议

### 1. GPU 显存优化

```python
# 如果显存不足，可以只加载部分城市
ACTIVE_CITIES = ["shanghai", "beijing", "guangzhou"]  # 只加载热门城市

# 或者使用 CPU 加载 FAISS，GPU 只用于模型推理
index = faiss.index_gpu_to_cpu(gpu_index)
```

### 2. 批量推理

```python
# 使用 vLLM 进行批量 Embedding
from vllm import LLM

llm = LLM(
    model="Qwen3-Embedding-8B",
    tensor_parallel_size=1,
    gpu_memory_utilization=0.5
)
```

### 3. 缓存热门查询

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_search(query: str, city: str, top_k: int):
    return self.search(query, city, top_k)
```

## 📊 监控和日志

### 添加性能监控

```python
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_with_metrics(query, city, top_k):
    start = time.time()
    
    # 执行搜索
    results = search(query, city, top_k)
    
    # 记录性能
    latency = (time.time() - start) * 1000
    logger.info(f"Search latency: {latency:.2f}ms | City: {city} | Results: {len(results)}")
    
    return results, latency
```

## 🚨 故障排查

### 常见问题

1. **FAISS 索引加载失败**
   ```bash
   # 检查文件是否存在
   ls -lh faiss_merchant_index_vllm_*_1028.faiss
   
   # 检查文件权限
   chmod 644 faiss_merchant_index_vllm_*_1028.faiss
   ```

2. **GPU 显存不足**
   ```python
   # 减少批量大小
   BATCH_SIZE = 16  # 从 32 降到 16
   
   # 或使用混合精度
   torch.set_default_dtype(torch.float16)
   ```

3. **模型加载慢**
   ```bash
   # 预热模型
   python -c "from sentence_transformers import SentenceTransformer; \
              model = SentenceTransformer('Qwen3-Embedding-8B'); \
              print('Model loaded successfully')"
   ```

## 🎯 下一步

1. ✅ 确认向量数据库文件完整性
2. ✅ 安装所需依赖
3. ✅ 更新 `rag_server.py` 加载向量数据库
4. ✅ 启动服务并测试 API
5. ✅ 配置 Gradio 前端连接到服务器
6. ✅ 部署到生产环境

## 📚 相关文档

- **[快速启动指南](server/README_QUICKSTART.md)** ⭐ 新手必读！三步启动服务器
- [快速开始指南](../QUICK_START.md) - API 使用说明
- [完整部署文档](../DEPLOYMENT.md) - 详细部署步骤
- [vLLM GPU 加速指南](README_VLLM_GPU.md) - GPU 优化配置

## 🛠️ 服务器工具

在 `server/` 目录下，我们提供了以下工具：

| 文件 | 说明 |
|------|------|
| `start_rag_server.sh` | 一键启动脚本，自动检查环境和配置 |
| `test_server.sh` | 自动化测试脚本，验证服务器功能 |
| `config.example.sh` | 配置文件模板，包含所有可配置项 |
| `README_QUICKSTART.md` | 快速启动指南，3 步启动服务器 |
| `rag_server.py` | RAG 服务器主程序 |

