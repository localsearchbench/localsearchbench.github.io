#!/bin/bash

# LocalSearchBench RAG Server 启动脚本
# 使用方式：./start_rag_server.sh [选项]

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     LocalSearchBench RAG Server Startup Script            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ==================== 配置区 ====================
# 请根据您的服务器环境修改以下路径

# 默认配置 - 可以通过命令行参数覆盖
DEFAULT_DATA_DIR="/path/to/rag_gpu"
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"
DEFAULT_GPU="0"

# 从命令行参数或环境变量获取配置
DATA_DIR="${1:-${RAG_DATA_DIR:-$DEFAULT_DATA_DIR}}"
HOST="${2:-${RAG_HOST:-$DEFAULT_HOST}}"
PORT="${3:-${RAG_PORT:-$DEFAULT_PORT}}"
GPU_ID="${4:-${CUDA_VISIBLE_DEVICES:-$DEFAULT_GPU}}"

# Embedding 模型路径（在数据目录下）
EMBEDDING_MODEL="${DATA_DIR}/Qwen3-Embedding-8B"

# Reranker 模型路径（在数据目录下）
RERANKER_MODEL="${DATA_DIR}/Qwen3-Reranker-8B"

# GPU 配置
export CUDA_VISIBLE_DEVICES="$GPU_ID"

# ==================== 环境检查 ====================

echo -e "${YELLOW}🔍 Checking environment...${NC}"

# 检查 Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python version: ${PYTHON_VERSION}${NC}"

# 检查 CUDA
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✅ NVIDIA GPU detected:${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo -e "${YELLOW}⚠️  No NVIDIA GPU detected, will run in CPU mode${NC}"
fi

# 检查数据目录
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${RED}❌ Data directory not found: ${DATA_DIR}${NC}"
    echo -e "${YELLOW}💡 Please edit this script and set DATA_DIR to your vector database location${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Data directory: ${DATA_DIR}${NC}"

# 检查向量数据库文件
echo -e "${YELLOW}📦 Checking vector database files...${NC}"

CITIES=("shanghai" "beijing" "guangzhou" "shenzhen" "hangzhou" "suzhou" "chengdu" "chongqing" "wuhan")
FOUND_CITIES=0

for city in "${CITIES[@]}"; do
    FAISS_FILE="${DATA_DIR}/faiss_merchant_index_vllm_${city}_1028.faiss"
    META_FILE="${DATA_DIR}/faiss_merchant_index_vllm_${city}_1028_metadata.json"
    
    if [ -f "$FAISS_FILE" ] && [ -f "$META_FILE" ]; then
        echo -e "${GREEN}  ✅ ${city}${NC}"
        ((FOUND_CITIES++))
    else
        echo -e "${YELLOW}  ⚠️  ${city} (files not found)${NC}"
    fi
done

if [ $FOUND_CITIES -eq 0 ]; then
    echo -e "${RED}❌ No vector database files found!${NC}"
    echo -e "${YELLOW}💡 Expected files: faiss_merchant_index_vllm_*_1028.faiss${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found ${FOUND_CITIES}/${#CITIES[@]} cities${NC}"

# 检查模型
if [ -d "$EMBEDDING_MODEL" ]; then
    echo -e "${GREEN}✅ Embedding model found: ${EMBEDDING_MODEL}${NC}"
else
    echo -e "${YELLOW}⚠️  Embedding model not found, will use default${NC}"
    EMBEDDING_MODEL=""
fi

if [ -d "$RERANKER_MODEL" ]; then
    echo -e "${GREEN}✅ Reranker model found: ${RERANKER_MODEL}${NC}"
else
    echo -e "${YELLOW}⚠️  Reranker model not found, will use default${NC}"
    RERANKER_MODEL=""
fi

# ==================== 显示使用帮助 ====================

show_usage() {
    echo -e "${BLUE}使用方法:${NC}"
    echo -e "  $0 [DATA_DIR] [HOST] [PORT] [GPU_ID]"
    echo ""
    echo -e "${BLUE}示例:${NC}"
    echo -e "  $0 /data/rag_gpu 0.0.0.0 8000 0"
    echo -e "  RAG_DATA_DIR=/data/rag_gpu $0"
    echo ""
    echo -e "${BLUE}环境变量:${NC}"
    echo -e "  RAG_DATA_DIR       - 数据目录路径"
    echo -e "  RAG_HOST           - 服务器主机地址"
    echo -e "  RAG_PORT           - 服务器端口"
    echo -e "  CUDA_VISIBLE_DEVICES - 使用的GPU编号"
    echo ""
}

# 检查是否请求帮助
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# ==================== 启动服务器 ====================

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Starting Server...                                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")" || exit 1

# 构建启动命令
CMD="python rag_server.py --host ${HOST} --port ${PORT} --data-dir ${DATA_DIR}"

if [ -d "$EMBEDDING_MODEL" ]; then
    CMD="${CMD} --embedding-model ${EMBEDDING_MODEL}"
fi

if [ -d "$RERANKER_MODEL" ]; then
    CMD="${CMD} --reranker-model ${RERANKER_MODEL}"
fi

echo -e "${YELLOW}📝 Command: ${CMD}${NC}"
echo -e "${YELLOW}📍 Working Directory: $(pwd)${NC}"
echo -e "${YELLOW}🎮 Using GPU(s): ${CUDA_VISIBLE_DEVICES}${NC}"
echo ""

# 启动服务器
$CMD

# 捕获退出代码
EXIT_CODE=$?

# 如果服务器退出
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Server stopped normally${NC}"
else
    echo -e "${RED}❌ Server stopped with error code: ${EXIT_CODE}${NC}"
fi

