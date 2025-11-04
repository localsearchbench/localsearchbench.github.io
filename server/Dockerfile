# 使用 NVIDIA CUDA 基础镜像
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 设置工作目录
WORKDIR /app

# 安装 Python 和系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip3 install --upgrade pip

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 安装 GPU 版本的包
RUN pip3 install --no-cache-dir faiss-gpu

# 复制应用代码
COPY rag_server.py .
COPY config.env.example .

# 创建必要的目录
RUN mkdir -p /app/models /app/data /app/logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python3", "rag_server.py", "--host", "0.0.0.0", "--port", "8000"]

