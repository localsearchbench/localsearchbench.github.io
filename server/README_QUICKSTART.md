# RAG Server 快速启动指南

> 基于 VLLM GPU 加速的多城市商户检索服务

> 📌 **使用模型**: [Qwen3-Embedding-8B 和 Qwen3-Reranker-8B](../MODEL_SPEC.md) - 点击查看详细规格

## 📋 前置要求

### 硬件要求
- **GPU**: NVIDIA GPU（推荐 A100/H100/V100，最低 16GB 显存）
- **内存**: 建议 32GB+ 
- **存储**: 至少 50GB 可用空间（用于模型和数据）

### 软件要求
- Python 3.8+
- CUDA 11.8+ 或 12.1+
- 已安装 `requirements.txt` 中的依赖

## 🚀 快速启动（三步）

### 1️⃣ 准备数据和模型

确保您有以下文件结构：

```bash
/your/data/path/
├── Qwen3-Embedding-8B/          # ✅ Embedding 模型（已确定）
│   ├── config.json
│   ├── model.safetensors
│   └── ...
├── Qwen3-Reranker-8B/           # ✅ Reranker 模型（已确定）
│   ├── config.json
│   ├── model.safetensors
│   └── ...
├── faiss_merchant_index_vllm_shanghai_1028.faiss     # 上海向量数据库
├── faiss_merchant_index_vllm_shanghai_1028_metadata.json
├── faiss_merchant_index_vllm_beijing_1028.faiss      # 北京向量数据库
├── faiss_merchant_index_vllm_beijing_1028_metadata.json
└── ... (其他 7 个城市的索引文件)
```

**必需组件**：
- ✅ **Qwen3-Embedding-8B**: 用于查询编码
- ✅ **Qwen3-Reranker-8B**: 用于结果重排序
- ✅ **9 个城市的 FAISS 索引**: 每个城市 2 个文件（.faiss + _metadata.json）

### 2️⃣ 编辑启动脚本

修改 `start_rag_server.sh` 中的 `DEFAULT_DATA_DIR`：

```bash
# 在第 22 行附近
DEFAULT_DATA_DIR="/your/data/path"  # 改为你的实际路径
```

或者使用环境变量（推荐）：

```bash
export RAG_DATA_DIR="/your/data/path"
```

### 3️⃣ 启动服务器

```bash
# 方法 1: 直接运行（使用脚本中的配置）
./start_rag_server.sh

# 方法 2: 通过环境变量
RAG_DATA_DIR=/your/data/path ./start_rag_server.sh

# 方法 3: 通过命令行参数
./start_rag_server.sh /your/data/path 0.0.0.0 8000 0
```

## 📝 配置说明

### 方式 1: 使用配置文件（推荐）

```bash
# 1. 复制配置文件模板
cp config.example.sh config.sh

# 2. 编辑 config.sh，修改必要的配置
nano config.sh

# 3. 加载配置并启动
source config.sh
./start_rag_server.sh
```

### 方式 2: 命令行参数

```bash
./start_rag_server.sh [DATA_DIR] [HOST] [PORT] [GPU_ID]
```

参数说明：
- `DATA_DIR`: 数据目录路径
- `HOST`: 服务器监听地址（默认: 0.0.0.0）
- `PORT`: 服务器端口（默认: 8000）
- `GPU_ID`: 使用的 GPU 编号（默认: 0）

### 方式 3: 环境变量

```bash
export RAG_DATA_DIR="/data/rag_gpu"
export RAG_HOST="0.0.0.0"
export RAG_PORT="8000"
export CUDA_VISIBLE_DEVICES="0"
./start_rag_server.sh
```

### 方式 4: 直接使用 Python

```bash
python rag_server.py \
  --host 0.0.0.0 \
  --port 8000 \
  --data-dir /data/rag_gpu \
  --embedding-model /data/rag_gpu/Qwen3-Embedding-8B \
  --reranker-model /data/rag_gpu/Qwen3-Reranker-8B
```

## 🎮 GPU 配置

### 单 GPU 模式（默认，推荐）

最简单、最快的启动方式：

```bash
export CUDA_VISIBLE_DEVICES="0"  # 使用第一块 GPU
./start_rag_server.sh
```

### 多 GPU 模式

如果需要使用多个 GPU 来提高性能：

```bash
# 使用 4 块 GPU
export CUDA_VISIBLE_DEVICES="0,1,2,3"
python rag_server.py --data-dir /data/rag_gpu
```

**注意**: 
- 单 GPU 模式启动更快，适合大多数场景
- 多 GPU 模式初始化较慢，但推理吞吐量更高
- 多 GPU 时建议降低 GPU 内存使用率（如 0.75）

## ✅ 验证服务

### 1. 检查服务状态

启动后，您应该看到类似输出：

```
╔═══════════════════════════════════════════════════════════╗
║     LocalSearchBench RAG Server (Multi-City Support)      ║
║     Device: cuda                                          ║
║     Host: 0.0.0.0                                         ║
║     Port: 8000                                            ║
║     Data Dir: /data/rag_gpu                               ║
╚═══════════════════════════════════════════════════════════╝

🚀 Starting LocalSearchBench RAG Server...
📍 Device: cuda

✅ Vector databases ready: 9 cities loaded
✅ Models loaded successfully
```

### 2. 测试 API

```bash
# 健康检查
curl http://localhost:8000/health

# 获取支持的城市列表
curl http://localhost:8000/cities

# 执行搜索
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "推荐一家火锅店",
    "city": "shanghai",
    "top_k": 10,
    "retriever": "faiss",
    "reranker": "qwen3"
  }'
```

### 3. 浏览器测试

打开浏览器访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 🔧 常见问题

### Q1: 找不到 FAISS 索引文件

**错误**: `No vector databases loaded`

**解决方案**:
1. 检查数据目录是否正确
2. 确认文件命名格式: `faiss_merchant_index_vllm_{city}_1028.faiss`
3. 检查文件权限

```bash
ls -lh /your/data/path/faiss_merchant_index_vllm_*_1028.faiss
```

### Q2: GPU 内存不足 (OOM)

**错误**: `CUDA out of memory`

**解决方案**:
1. 减少 GPU 内存使用率
2. 使用更少的 GPU
3. 检查是否有其他进程占用 GPU

```bash
# 查看 GPU 使用情况
nvidia-smi

# 降低内存使用率启动
python rag_server.py --data-dir /data/rag_gpu --gpu-memory-utilization 0.6
```

### Q3: 模型加载失败

**错误**: `Failed to load model`

**解决方案**:
1. 检查模型路径是否正确
2. 确认模型文件完整性
3. 检查 CUDA 和驱动版本

```bash
# 验证 CUDA
python -c "import torch; print(torch.cuda.is_available())"

# 检查模型文件
ls -lh /data/rag_gpu/Qwen3-Embedding-8B/
```

### Q4: 端口已被占用

**错误**: `Address already in use`

**解决方案**:
```bash
# 方法 1: 更换端口
./start_rag_server.sh /data/rag_gpu 0.0.0.0 8001 0

# 方法 2: 找到并终止占用进程
lsof -i :8000
kill -9 <PID>
```

## 📊 性能优化

### 单 GPU 优化

```bash
# 提高 GPU 内存使用率
export GPU_MEMORY_UTILIZATION=0.85
./start_rag_server.sh
```

### 多 GPU 优化

```bash
# 使用 4 张卡，平衡性能和稳定性
export CUDA_VISIBLE_DEVICES="0,1,2,3"
export GPU_MEMORY_UTILIZATION=0.75
python rag_server.py --data-dir /data/rag_gpu
```

### 批处理优化

修改 `rag_server.py` 中的批处理大小：

```python
# 在 RAGModels 类中调整
self.embedding_batch_size = 32  # 根据 GPU 显存调整
self.reranker_batch_size = 16
```

## 📖 相关文档

- [完整部署指南](../DEPLOYMENT.md)
- [服务集成说明](../SERVER_INTEGRATION.md)
- [API 使用文档](../QUICK_START.md)

## 🆘 获取帮助

如遇问题，请：
1. 查看服务器日志输出
2. 检查 GPU 状态: `nvidia-smi`
3. 验证数据文件完整性
4. 查阅相关文档

---

**提示**: 首次启动可能需要 2-5 分钟来加载模型和索引，请耐心等待 ✨

