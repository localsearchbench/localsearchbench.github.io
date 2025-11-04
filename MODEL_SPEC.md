# 模型规格说明

> LocalSearchBench 项目使用的模型配置（已确定）

## ✅ 确定的模型

本项目使用以下两个模型，**不可更改**：

### 1. Qwen3-Embedding-8B

**用途**: 查询和文档的向量编码

**规格**:
- 参数量: 8B
- 语言支持: 中文 + 英文
- 向量维度: 通常为 4096 或更高
- 用于: 将用户查询和商户信息编码为向量

**目录结构**:
```
Qwen3-Embedding-8B/
├── config.json
├── model.safetensors
├── tokenizer.json
├── tokenizer_config.json
├── special_tokens_map.json
└── vocab.txt
```

### 2. Qwen3-Reranker-8B

**用途**: 检索结果的重排序

**规格**:
- 参数量: 8B
- 语言支持: 中文 + 英文
- 输出: 相关性分数 (0-1)
- 用于: 对检索到的商户进行精确排序

**目录结构**:
```
Qwen3-Reranker-8B/
├── config.json
├── model.safetensors
├── tokenizer.json
├── tokenizer_config.json
├── special_tokens_map.json
└── vocab.txt
```

## 📂 部署目录结构

完整的部署目录应包含：

```bash
/path/to/rag_gpu/
├── Qwen3-Embedding-8B/                                    # Embedding 模型
│   ├── config.json
│   ├── model.safetensors
│   └── tokenizer files...
├── Qwen3-Reranker-8B/                                     # Reranker 模型
│   ├── config.json
│   ├── model.safetensors
│   └── tokenizer files...
├── faiss_merchant_index_vllm_shanghai_1028.faiss          # 上海索引
├── faiss_merchant_index_vllm_shanghai_1028_metadata.json
├── faiss_merchant_index_vllm_beijing_1028.faiss           # 北京索引
├── faiss_merchant_index_vllm_beijing_1028_metadata.json
├── faiss_merchant_index_vllm_guangzhou_1028.faiss         # 广州索引
├── faiss_merchant_index_vllm_guangzhou_1028_metadata.json
├── faiss_merchant_index_vllm_shenzhen_1028.faiss          # 深圳索引
├── faiss_merchant_index_vllm_shenzhen_1028_metadata.json
├── faiss_merchant_index_vllm_hangzhou_1028.faiss          # 杭州索引
├── faiss_merchant_index_vllm_hangzhou_1028_metadata.json
├── faiss_merchant_index_vllm_suzhou_1028.faiss            # 苏州索引
├── faiss_merchant_index_vllm_suzhou_1028_metadata.json
├── faiss_merchant_index_vllm_chengdu_1028.faiss           # 成都索引
├── faiss_merchant_index_vllm_chengdu_1028_metadata.json
├── faiss_merchant_index_vllm_chongqing_1028.faiss         # 重庆索引
├── faiss_merchant_index_vllm_chongqing_1028_metadata.json
├── faiss_merchant_index_vllm_wuhan_1028.faiss             # 武汉索引
└── faiss_merchant_index_vllm_wuhan_1028_metadata.json
```

**文件清单**:
- ✅ 2 个模型目录
- ✅ 9 个城市 × 2 个文件 = 18 个 FAISS 文件

## 🔧 配置使用

### 环境变量

```bash
export RAG_DATA_DIR="/path/to/rag_gpu"
export EMBEDDING_MODEL_PATH="${RAG_DATA_DIR}/Qwen3-Embedding-8B"
export RERANKER_MODEL_PATH="${RAG_DATA_DIR}/Qwen3-Reranker-8B"
```

### Python 代码

```python
from sentence_transformers import SentenceTransformer, CrossEncoder

# 加载 Embedding 模型
embedding_model = SentenceTransformer("Qwen3-Embedding-8B")

# 加载 Reranker 模型
reranker_model = CrossEncoder("Qwen3-Reranker-8B")
```

### 命令行启动

```bash
python rag_server.py \
  --data-dir /path/to/rag_gpu \
  --embedding-model /path/to/rag_gpu/Qwen3-Embedding-8B \
  --reranker-model /path/to/rag_gpu/Qwen3-Reranker-8B
```

## 💾 磁盘空间需求

**模型大小**（估算）:
- Qwen3-Embedding-8B: ~16 GB
- Qwen3-Reranker-8B: ~16 GB
- 9 个城市的 FAISS 索引: ~2-5 GB
- **总计**: ~35-40 GB

## 🚀 GPU 显存需求

**单 GPU 部署**:
- Embedding 模型: ~8-10 GB
- Reranker 模型: ~8-10 GB
- 推荐: 至少 **24 GB 显存**（如 RTX 4090, A5000, A100）

**多 GPU 部署** (可选):
- 使用张量并行可以分散显存负载
- 4×GPU 配置: 每张卡 ~6 GB

## 📚 相关文档

- [快速启动指南](server/README_QUICKSTART.md)
- [服务器集成指南](SERVER_INTEGRATION.md)
- [部署文档](DEPLOYMENT.md)

## ⚠️ 重要说明

1. **模型不可替换**: 必须使用 Qwen3-Embedding-8B 和 Qwen3-Reranker-8B
2. **版本一致性**: 确保使用的是 1028 版本的 FAISS 索引
3. **目录命名**: 模型目录名必须严格匹配 `Qwen3-Embedding-8B` 和 `Qwen3-Reranker-8B`
4. **文件完整性**: 确保所有 tokenizer 和 config 文件完整

