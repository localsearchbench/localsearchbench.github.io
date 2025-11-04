# FAISS GPU 加速使用指南

## 🚀 功能概述

LocalSearchBench RAG Server 现在支持使用 GPU 加速 FAISS 向量检索，可以显著提升搜索性能。

## 📊 性能提升

- **检索速度**：GPU 加速可将向量检索速度提升 **10-100倍**（取决于数据规模）
- **并发处理**：更好地支持多用户同时查询
- **内存效率**：GPU 显存管理优化，支持大规模向量索引

## 🎮 使用方法

### 方法 1: 使用启动脚本（推荐）

#### 默认启用 GPU（推荐配置）
```bash
./start_rag_server.sh
```

#### 强制使用 CPU 模式
```bash
RAG_USE_GPU=false ./start_rag_server.sh
```

#### 指定 GPU 设备
```bash
# 使用 GPU 0
CUDA_VISIBLE_DEVICES=0 ./start_rag_server.sh

# 使用 GPU 1
CUDA_VISIBLE_DEVICES=1 ./start_rag_server.sh

# 使用多个 GPU（FAISS 默认使用第一个）
CUDA_VISIBLE_DEVICES=0,1 ./start_rag_server.sh
```

### 方法 2: 直接使用 Python

#### GPU 模式（默认）
```bash
python rag_server.py --data-dir /path/to/data
```

#### CPU 模式
```bash
python rag_server.py --data-dir /path/to/data --no-gpu
```

## 📋 环境变量说明

| 环境变量 | 说明 | 默认值 | 示例 |
|---------|------|--------|------|
| `RAG_USE_GPU` | 是否使用 GPU 加载向量库 | `true` | `true` / `false` |
| `CUDA_VISIBLE_DEVICES` | 指定使用的 GPU 设备 | `0` | `0`, `1`, `0,1` |

## 🔍 检查 GPU 状态

启动服务器后，查看日志输出：

### GPU 模式成功启动
```
📦 Loading vector databases from: /path/to/data
💻 Device: GPU
🚀 GPU resources initialized for FAISS
✅ 上海 (shanghai): 50000 vectors, 10000 merchants [🚀 GPU]
✅ 北京 (beijing): 45000 vectors, 9000 merchants [🚀 GPU]
...
🎉 Loaded 9/9 cities successfully on GPU!
```

### CPU 模式（降级或强制）
```
📦 Loading vector databases from: /path/to/data
💻 Device: CPU
✅ 上海 (shanghai): 50000 vectors, 10000 merchants [💻 CPU]
✅ 北京 (beijing): 45000 vectors, 9000 merchants [💻 CPU]
...
🎉 Loaded 9/9 cities successfully on CPU!
```

### GPU 转换失败（自动降级到 CPU）
```
⚠️  上海: GPU transfer failed (out of memory), using CPU
✅ 上海 (shanghai): 50000 vectors, 10000 merchants [💻 CPU]
```

## ⚠️ 常见问题

### 1. GPU 内存不足

**现象**：
```
⚠️  Failed to initialize GPU resources: out of memory, falling back to CPU
```

**解决方案**：
- 使用更大显存的 GPU
- 或者使用 CPU 模式：`RAG_USE_GPU=false ./start_rag_server.sh`

### 2. CUDA 不可用

**现象**：
```
⚠️  No NVIDIA GPU detected, will run in CPU mode
```

**解决方案**：
- 检查 CUDA 是否正确安装：`nvidia-smi`
- 检查 PyTorch 是否支持 CUDA：
  ```python
  import torch
  print(torch.cuda.is_available())
  ```

### 3. FAISS GPU 版本未安装

**现象**：
```
ImportError: cannot import name 'StandardGpuResources' from 'faiss'
```

**解决方案**：
安装 FAISS GPU 版本：
```bash
# Conda 安装（推荐）
conda install -c pytorch faiss-gpu

# Pip 安装
pip install faiss-gpu
```

## 🔧 性能优化建议

### GPU 选择
- **最小配置**：NVIDIA GPU with 4GB+ VRAM（支持单城市）
- **推荐配置**：NVIDIA GPU with 8GB+ VRAM（支持多城市）
- **最佳配置**：NVIDIA GPU with 16GB+ VRAM（全城市 + 模型并行）

### 多 GPU 环境
如果有多个 GPU，建议：
1. **FAISS 索引**：使用一个专用 GPU
2. **Embedding 模型**：使用另一个 GPU
3. **Reranker 模型**：使用第三个 GPU

示例：
```bash
# GPU 0: FAISS 向量库
# GPU 1: Embedding + Reranker 模型
CUDA_VISIBLE_DEVICES=0,1 ./start_rag_server.sh
```

### 批量查询优化
GPU 在批量查询时性能提升更明显，单次查询可能与 CPU 差距不大。

## 📈 性能测试

可以使用以下命令测试性能：

```bash
# 测试 GPU 模式
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "好吃的火锅",
    "city": "shanghai",
    "top_k": 20,
    "retriever": "Qwen3-Embedding-8B",
    "reranker": "Qwen3-Reranker-8B"
  }'
```

查看响应中的 `metrics.latency_ms` 字段对比性能。

## 🎯 推荐配置

### 生产环境（高性能）
```bash
# 启用 GPU，使用第一个 GPU 设备
CUDA_VISIBLE_DEVICES=0 ./start_rag_server.sh
```

### 开发环境（节省资源）
```bash
# 使用 CPU 模式
RAG_USE_GPU=false ./start_rag_server.sh
```

### 多服务部署
```bash
# 服务器 1: RAG Server (GPU 0)
CUDA_VISIBLE_DEVICES=0 ./start_rag_server.sh

# 服务器 2: LLM Server (GPU 1)
CUDA_VISIBLE_DEVICES=1 python llm_server.py
```

## 📝 日志示例

完整的 GPU 启动日志：
```
╔═══════════════════════════════════════════════════════════╗
║     LocalSearchBench RAG Server Startup Script            ║
╚═══════════════════════════════════════════════════════════╝

🔍 Checking environment...
✅ Python version: 3.10.12
✅ NVIDIA GPU detected:
NVIDIA A100-SXM4-40GB, 40960 MiB
✅ Data directory: /data/rag_gpu
📦 Checking vector database files...
  ✅ shanghai
  ✅ beijing
  ✅ guangzhou
  ✅ shenzhen
  ✅ hangzhou
  ✅ suzhou
  ✅ chengdu
  ✅ chongqing
  ✅ wuhan
✅ Found 9/9 cities

╔═══════════════════════════════════════════════════════════╗
║     Starting Server...                                    ║
╚═══════════════════════════════════════════════════════════╝

🚀 FAISS will use GPU acceleration
📝 Command: python rag_server.py --host 0.0.0.0 --port 8000 --data-dir /data/rag_gpu
📍 Working Directory: /path/to/server
🎮 Using GPU(s): 0

🚀 Starting LocalSearchBench RAG Server...
📍 Device: cuda

📦 Loading vector databases from: /data/rag_gpu
💻 Device: GPU
🚀 GPU resources initialized for FAISS
✅ 上海 (shanghai): 50000 vectors, 10000 merchants [🚀 GPU]
✅ 北京 (beijing): 45000 vectors, 9000 merchants [🚀 GPU]
✅ 广州 (guangzhou): 40000 vectors, 8000 merchants [🚀 GPU]
✅ 深圳 (shenzhen): 42000 vectors, 8500 merchants [🚀 GPU]
✅ 杭州 (hangzhou): 35000 vectors, 7000 merchants [🚀 GPU]
✅ 苏州 (suzhou): 30000 vectors, 6000 merchants [🚀 GPU]
✅ 成都 (chengdu): 38000 vectors, 7500 merchants [🚀 GPU]
✅ 重庆 (chongqing): 36000 vectors, 7200 merchants [🚀 GPU]
✅ 武汉 (wuhan): 32000 vectors, 6500 merchants [🚀 GPU]

🎉 Loaded 9/9 cities successfully on GPU!

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🔗 相关链接

- [FAISS GPU 文档](https://github.com/facebookresearch/faiss/wiki/Faiss-on-the-GPU)
- [CUDA 安装指南](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/)
- [PyTorch CUDA 支持](https://pytorch.org/get-started/locally/)

