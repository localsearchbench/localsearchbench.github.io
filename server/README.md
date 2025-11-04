# LocalSearchBench RAG Server

> 基于 VLLM GPU 加速的多城市商户检索服务

## 🚀 快速启动

### 1. 准备数据目录

确保您的数据目录包含：

```
/your/data/path/
├── Qwen3-Embedding-8B/          # Embedding 模型
├── Qwen3-Reranker-8B/           # Reranker 模型
├── faiss_merchant_index_vllm_shanghai_1028.faiss
├── faiss_merchant_index_vllm_shanghai_1028_metadata.json
└── ... (其他城市索引)
```

### 2. 启动服务器

**最简单的方式（推荐）：**

```bash
cd server
./start_rag_server.sh --data-dir /your/data/path --host 0.0.0.0 --port 8000
```

**高级选项：**

```bash
# GPU 模式（默认）
./start_rag_server.sh --data-dir /path/to/data --gpu 0

# CPU 模式
./start_rag_server.sh --cpu --data-dir /path/to/data

# 指定主机和端口
./start_rag_server.sh --host 10.164.243.10 --port 8000 --data-dir /path/to/data
```

### 3. 测试 API

```bash
# 健康检查
curl http://localhost:8000/health

# 获取城市列表
curl http://localhost:8000/cities

# 搜索测试
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "推荐一家火锅店",
    "city": "shanghai",
    "top_k": 10
  }'
```

## 📋 完整命令行参数

```bash
./start_rag_server.sh [选项]

选项:
  --data-dir PATH     数据目录路径（必需）
  --host HOST         服务器地址（默认: 0.0.0.0）
  --port PORT         端口号（默认: 8000）
  --gpu GPU_ID        GPU 编号（默认: 0）
  --cpu               强制使用 CPU 模式
  --help              显示帮助信息
```

## 🐳 使用 Docker（可选）

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 🔧 故障排查

### 问题 1: 数据目录未找到

```
❌ Data directory not found: /path/to/data
```

**解决**：使用 `--data-dir` 参数指定正确的路径

### 问题 2: GPU 内存不足

```
CUDA out of memory
```

**解决**：
- 使用 CPU 模式：`./start_rag_server.sh --cpu`
- 减少 GPU 内存使用率（编辑 `start_rag_server.sh` 中的 `DEFAULT_GPU_MEMORY_UTILIZATION`）

### 问题 3: 端口被占用

```
Address already in use
```

**解决**：更换端口 `--port 8001` 或停止占用端口的进程

## 📖 系统要求

**硬件：**
- GPU: NVIDIA GPU（16GB+ 显存，推荐 A100/H100/V100）
- RAM: 32GB+
- 存储: 50GB+

**软件：**
- Python 3.8+
- CUDA 11.8+ 或 12.1+
- 依赖包见 `requirements.txt`

## 📚 API 文档

启动服务后访问：http://localhost:8000/docs

## 🔗 相关文件

- `rag_server.py` - 主服务器代码
- `start_rag_server.sh` - 启动脚本
- `requirements.txt` - Python 依赖
- `Dockerfile` - Docker 镜像定义
- `docker-compose.yml` - Docker Compose 配置

---

**提示**：首次启动需要 2-5 分钟加载模型，请耐心等待 ✨

