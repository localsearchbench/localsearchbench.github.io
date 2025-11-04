#!/bin/bash

# LocalSearchBench RAG Server 配置文件示例
# 复制此文件为 config.sh 并根据您的环境修改配置
# cp config.example.sh config.sh

# ==================== 数据路径配置 ====================

# 向量数据库目录（包含 FAISS 索引文件）
# 示例: /data/rag_gpu 或 /home/user/localsearch/data
export RAG_DATA_DIR="/path/to/rag_gpu"

# Embedding 模型路径
# 默认模型: Qwen3-Embedding-8B（已确定）
# 留空则使用 ${RAG_DATA_DIR}/Qwen3-Embedding-8B
export EMBEDDING_MODEL_PATH=""

# Reranker 模型路径
# 默认模型: Qwen3-Reranker-8B（已确定）
# 留空则使用 ${RAG_DATA_DIR}/Qwen3-Reranker-8B
export RERANKER_MODEL_PATH=""

# ==================== 服务器配置 ====================

# 服务器主机地址
export RAG_HOST="0.0.0.0"

# 服务器端口
export RAG_PORT="8000"

# ==================== GPU 配置 ====================

# 使用的 GPU 编号（多个 GPU 用逗号分隔，如 "0,1"）
# 单 GPU: "0"
# 多 GPU: "0,1,2,3"
export CUDA_VISIBLE_DEVICES="0"

# GPU 内存使用率（0.0-1.0）
# 建议: 单GPU 0.8-0.9, 多GPU 0.7-0.8
export GPU_MEMORY_UTILIZATION="0.8"

# ==================== VLLM 高级配置 ====================

# 张量并行大小（使用的 GPU 数量）
# 留空则自动检测，建议单 GPU 设为 1
export TENSOR_PARALLEL_SIZE="1"

# ==================== 日志配置 ====================

# 日志级别: DEBUG, INFO, WARNING, ERROR
export LOG_LEVEL="INFO"

# 日志文件路径（留空则只输出到控制台）
export LOG_FILE=""

# ==================== 示例配置 ====================

# 示例 1: 单 GPU 服务器（推荐）
# export RAG_DATA_DIR="/data/rag_gpu"
# export CUDA_VISIBLE_DEVICES="0"
# export TENSOR_PARALLEL_SIZE="1"
# export GPU_MEMORY_UTILIZATION="0.85"

# 示例 2: 4-GPU 服务器（高性能）
# export RAG_DATA_DIR="/data/rag_gpu"
# export CUDA_VISIBLE_DEVICES="0,1,2,3"
# export TENSOR_PARALLEL_SIZE="4"
# export GPU_MEMORY_UTILIZATION="0.75"

# 示例 3: 仅使用第二块 GPU
# export RAG_DATA_DIR="/data/rag_gpu"
# export CUDA_VISIBLE_DEVICES="1"
# export TENSOR_PARALLEL_SIZE="1"

