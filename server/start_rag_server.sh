#!/bin/bash

# LocalSearchBench RAG Server 启动脚本
# 使用方式：./start_rag_server.sh [选项]

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     LocalSearchBench RAG Server Startup Script            ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "使用方式: $0 [选项]"
    echo ""
    echo "选项："
    echo "  --help              显示此帮助信息"
    echo "  --check-gpu         仅检查GPU配置信息后退出"
    echo "  --force-gpu         强制使用GPU模式（跳过兼容性测试）"
    echo "  --skip-gpu-test     跳过GPU兼容性测试，默认启用GPU"
    echo "  --cpu               强制使用CPU模式"
    echo "  --data-dir PATH     指定数据目录"
    echo "  --host HOST         指定主机地址（默认：0.0.0.0）"
    echo "  --port PORT         指定端口（默认：8000）"
    echo "  --gpu ID            指定GPU设备ID（默认：0）"
    echo ""
    echo "示例："
    echo "  $0 --check-gpu               # 仅查看GPU配置信息"
    echo "  $0                           # 使用默认配置启动（会进行GPU兼容性测试）"
    echo "  $0 --force-gpu               # 强制使用GPU，跳过兼容性测试"
    echo "  $0 --cpu                     # 强制使用CPU模式"
    echo "  $0 --data-dir /path/to/data  # 指定数据目录"
    echo ""
    exit 0
}

# 显示GPU信息
show_gpu_info() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                GPU Configuration Check                    ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if ! command -v nvidia-smi &> /dev/null; then
        echo -e "${RED}❌ nvidia-smi not found - No NVIDIA GPU detected${NC}"
        exit 1
    fi
    
    # 获取 GPU 数量
    GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -n 1)
    echo -e "${GREEN}✅ Detected $GPU_COUNT GPU(s):${NC}"
    echo ""
    
    # 显示每个 GPU 的详细信息
    nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used,utilization.gpu,utilization.memory,temperature.gpu,compute_cap --format=csv,noheader | while IFS=, read -r idx name total free used gpu_util mem_util temp compute; do
        echo -e "${BLUE}GPU ${idx}:${NC}"
        echo -e "  Name:              ${name}"
        echo -e "  Total Memory:      ${total}"
        echo -e "  Free Memory:       ${free}"
        echo -e "  Used Memory:       ${used}"
        echo -e "  GPU Utilization:   ${gpu_util}"
        echo -e "  Memory Util:       ${mem_util}"
        echo -e "  Temperature:       ${temp}"
        echo -e "  Compute Capability:${compute}"
        echo ""
    done
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}💡 Usage Suggestions:${NC}"
    echo -e "   ⚡ Quick start (recommended):  $0"
    echo -e "   🚀 Force GPU mode:             $0 --force-gpu"
    echo -e "   💻 Force CPU mode:             $0 --cpu"
    echo -e "   🎯 Use specific GPU:           $0 --gpu 1"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    exit 0
}

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     LocalSearchBench RAG Server Startup Script            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ==================== 配置区 ====================
# 请根据您的服务器环境修改以下路径

# 默认配置
DEFAULT_DATA_DIR="/mnt/dolphinfs/hdd_pool/docker/user/hadoop-mtsearch-assistant/ai-search/hehang03/rag_gpu"
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"
DEFAULT_GPU="0"
DEFAULT_USE_GPU="true"  # 默认使用 GPU 加载向量库

# 解析命令行参数
FORCE_GPU="false"
SKIP_GPU_TEST="false"
FORCE_CPU="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            ;;
        --check-gpu)
            show_gpu_info
            ;;
        --force-gpu)
            FORCE_GPU="true"
            SKIP_GPU_TEST="true"
            shift
            ;;
        --skip-gpu-test)
            SKIP_GPU_TEST="true"
            shift
            ;;
        --cpu)
            FORCE_CPU="true"
            shift
            ;;
        --data-dir)
            DEFAULT_DATA_DIR="$2"
            shift 2
            ;;
        --host)
            DEFAULT_HOST="$2"
            shift 2
            ;;
        --port)
            DEFAULT_PORT="$2"
            shift 2
            ;;
        --gpu)
            DEFAULT_GPU="$2"
            shift 2
            ;;
        *)
            echo -e "${YELLOW}⚠️  Unknown option: $1${NC}"
            echo -e "${YELLOW}💡 Use --help to see available options${NC}"
            exit 1
            ;;
    esac
done

# 从环境变量获取配置（如果未通过命令行指定）
DATA_DIR="${RAG_DATA_DIR:-$DEFAULT_DATA_DIR}"
HOST="${RAG_HOST:-$DEFAULT_HOST}"
PORT="${RAG_PORT:-$DEFAULT_PORT}"
GPU_ID="${CUDA_VISIBLE_DEVICES:-$DEFAULT_GPU}"
USE_GPU="${RAG_USE_GPU:-$DEFAULT_USE_GPU}"

# 如果指定了 --cpu，强制使用 CPU
if [ "$FORCE_CPU" = "true" ]; then
    USE_GPU="false"
fi

# Embedding 模型路径（在数据目录下）
EMBEDDING_MODEL="${DATA_DIR}/Qwen3-Embedding-8B"

# Reranker 模型路径（在数据目录下）
RERANKER_MODEL="${DATA_DIR}/Qwen3-Reranker-8B"

# GPU 配置
export CUDA_VISIBLE_DEVICES="$GPU_ID"

# ==================== 环境检查 ====================

echo -e "${YELLOW}🔍 Checking environment...${NC}"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python version: ${PYTHON_VERSION}${NC}"

# 检查 CUDA 和 GPU
if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                  GPU Configuration Info                   ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # 获取 GPU 数量
    GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -n 1)
    echo -e "${GREEN}🖥️  Detected GPUs: ${GPU_COUNT}${NC}"
    echo ""
    
    # 显示每个 GPU 的详细信息
    GPU_INDEX=0
    nvidia-smi --query-gpu=index,name,memory.total,memory.free,memory.used,utilization.gpu,temperature.gpu,compute_cap --format=csv,noheader | while IFS=, read -r idx name total free used util temp compute; do
        echo -e "${BLUE}GPU ${idx}:${NC}"
        echo -e "  Name:        ${name}"
        echo -e "  Memory:      ${total} (Free: ${free}, Used: ${used})"
        echo -e "  Utilization: ${util}"
        echo -e "  Temperature: ${temp}"
        echo -e "  Compute Cap: ${compute}"
        echo ""
    done
    
    # 显示当前使用的 GPU
    echo -e "${YELLOW}📍 Current GPU Selection: GPU ${GPU_ID} (via CUDA_VISIBLE_DEVICES)${NC}"
    echo ""
    
    # 如果跳过 GPU 测试
    if [ "$SKIP_GPU_TEST" = "true" ]; then
        echo -e "${YELLOW}⚠️  Skipping FAISS GPU compatibility test (--skip-gpu-test or --force-gpu)${NC}"
        if [ "$FORCE_GPU" = "true" ]; then
            echo -e "${YELLOW}💡 Forcing GPU mode${NC}"
        else
            echo -e "${YELLOW}💡 GPU will be enabled by default${NC}"
        fi
        FAISS_GPU_COMPATIBLE="skipped"
    else
        # 检查 FAISS GPU 兼容性
        echo -e "${YELLOW}🔍 Testing FAISS GPU compatibility...${NC}"
        
        # 使用子进程测试，避免主进程崩溃
        FAISS_TEST_RESULT=$(timeout 10 python3 << 'EOFPYTHON' 2>&1
import sys
import signal

# 设置超时处理
def timeout_handler(signum, frame):
    print("TIMEOUT")
    sys.exit(124)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(5)

try:
    import faiss
    import numpy as np
    
    print(f"FAISS version: {faiss.__version__}")
    
    # 检查是否有 GPU 支持
    if not hasattr(faiss, 'StandardGpuResources'):
        print("NO_GPU_SUPPORT")
        sys.exit(0)
    
    # 测试 GPU 兼容性 - 这可能会导致崩溃
    res = faiss.StandardGpuResources()
    test_index = faiss.IndexFlatL2(64)
    test_data = np.random.random((10, 64)).astype('float32')
    test_index.add(test_data)
    
    # 尝试转移到 GPU 并搜索
    gpu_index = faiss.index_cpu_to_gpu(res, 0, test_index)
    test_query = np.random.random((1, 64)).astype('float32')
    gpu_index.search(test_query, 1)
    
    print("GPU_COMPATIBLE")
    sys.exit(0)
    
except Exception as e:
    print(f"EXCEPTION: {e}")
    sys.exit(1)
EOFPYTHON
)
    
    FAISS_TEST_EXIT_CODE=$?
    
    # 检查测试结果
    if echo "$FAISS_TEST_RESULT" | grep -q "GPU_COMPATIBLE"; then
        echo -e "${GREEN}✅ FAISS GPU compatibility test PASSED${NC}"
        FAISS_GPU_COMPATIBLE="true"
    elif echo "$FAISS_TEST_RESULT" | grep -q "NO_GPU_SUPPORT"; then
        echo -e "${YELLOW}⚠️  FAISS-GPU not installed, will use CPU mode${NC}"
        USE_GPU="false"
        FAISS_GPU_COMPATIBLE="false"
    elif [ $FAISS_TEST_EXIT_CODE -eq 124 ]; then
        echo -e "${YELLOW}⚠️  FAISS GPU test timed out${NC}"
        if [ "$FORCE_GPU" = "true" ]; then
            echo -e "${YELLOW}💡 --force-gpu enabled, will attempt to use GPU anyway${NC}"
            FAISS_GPU_COMPATIBLE="unknown"
        else
            echo -e "${YELLOW}💡 Forcing CPU mode to prevent crashes${NC}"
            echo -e "${YELLOW}   Use --force-gpu to override this behavior${NC}"
            USE_GPU="false"
            FAISS_GPU_COMPATIBLE="false"
        fi
    else
        echo -e "${YELLOW}⚠️  FAISS GPU compatibility test FAILED (exit code: $FAISS_TEST_EXIT_CODE)${NC}"
        echo -e "${YELLOW}⚠️  Your GPU may not be supported by this FAISS version${NC}"
        if [ "$FORCE_GPU" = "true" ]; then
            echo -e "${YELLOW}💡 --force-gpu enabled, will attempt to use GPU anyway${NC}"
            echo -e "${RED}⚠️  WARNING: Server may crash if GPU is truly incompatible!${NC}"
            FAISS_GPU_COMPATIBLE="unknown"
        else
            echo -e "${YELLOW}💡 Forcing CPU mode to prevent crashes${NC}"
            echo -e "${YELLOW}   Use --force-gpu to override this behavior${NC}"
            USE_GPU="false"
            FAISS_GPU_COMPATIBLE="false"
        fi
    fi
    fi  # 结束 SKIP_GPU_TEST 的 if-else
else
    echo -e "${YELLOW}⚠️  No NVIDIA GPU detected, will run in CPU mode${NC}"
    USE_GPU="false"
fi

# ==================== GPU 配置总结 ====================
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              GPU Configuration Summary                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"

if [ "$USE_GPU" = "true" ] || [ "$USE_GPU" = "1" ]; then
    echo -e "${GREEN}🚀 FAISS will run in GPU mode${NC}"
    echo -e "${GREEN}   Using GPU: ${GPU_ID}${NC}"
    if [ "$FAISS_GPU_COMPATIBLE" = "true" ]; then
        echo -e "${GREEN}   GPU Compatibility: ✅ Verified${NC}"
    elif [ "$FAISS_GPU_COMPATIBLE" = "skipped" ]; then
        echo -e "${YELLOW}   GPU Compatibility: ⚠️  Not tested (skipped)${NC}"
    else
        echo -e "${YELLOW}   GPU Compatibility: ⚠️  Unknown${NC}"
    fi
else
    echo -e "${YELLOW}💻 FAISS will run in CPU mode${NC}"
    echo -e "${YELLOW}   Performance: Slower than GPU mode${NC}"
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${YELLOW}   💡 To enable GPU mode:${NC}"
        echo -e "${YELLOW}      - Use --force-gpu to skip compatibility test${NC}"
        echo -e "${YELLOW}      - Ensure FAISS-GPU is properly installed${NC}"
    fi
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

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
    echo -e "  RAG_USE_GPU=false $0  # 强制使用 CPU 模式"
    echo ""
    echo -e "${BLUE}环境变量:${NC}"
    echo -e "  RAG_DATA_DIR         - 数据目录路径"
    echo -e "  RAG_HOST             - 服务器主机地址"
    echo -e "  RAG_PORT             - 服务器端口"
    echo -e "  RAG_USE_GPU          - 是否使用 GPU 加载向量库 (true/false, 默认: true)"
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
echo -e "${BLUE}║              Starting RAG Server                          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")" || exit 1

echo -e "${BLUE}📋 Server Configuration:${NC}"
echo -e "   Host:            ${HOST}"
echo -e "   Port:            ${PORT}"
echo -e "   Data Directory:  ${DATA_DIR}"
echo -e "   Working Dir:     $(pwd)"
echo ""

echo -e "${BLUE}🤖 Model Configuration:${NC}"
if [ -d "$EMBEDDING_MODEL" ]; then
    echo -e "   Embedding Model: ${GREEN}✓${NC} ${EMBEDDING_MODEL}"
else
    echo -e "   Embedding Model: ${YELLOW}⚠${NC} Using default (not found at ${EMBEDDING_MODEL})"
fi

if [ -d "$RERANKER_MODEL" ]; then
    echo -e "   Reranker Model:  ${GREEN}✓${NC} ${RERANKER_MODEL}"
else
    echo -e "   Reranker Model:  ${YELLOW}⚠${NC} Using default (not found at ${RERANKER_MODEL})"
fi
echo ""

echo -e "${BLUE}🎮 GPU Configuration:${NC}"
if [ "$USE_GPU" = "false" ] || [ "$USE_GPU" = "0" ]; then
    echo -e "   Mode:            ${YELLOW}💻 CPU${NC}"
    echo -e "   Performance:     ${YELLOW}⚠️  Slower than GPU mode${NC}"
else
    echo -e "   Mode:            ${GREEN}🚀 GPU Accelerated${NC}"
    echo -e "   Device:          GPU ${GPU_ID} (CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES})"
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --id=${GPU_ID} --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null)
        if [ -n "$GPU_INFO" ]; then
            echo -e "   GPU Info:        ${GPU_INFO}"
        fi
    fi
fi
echo ""

# 构建启动命令
CMD="python3 rag_server.py --host ${HOST} --port ${PORT} --data-dir ${DATA_DIR}"

if [ -d "$EMBEDDING_MODEL" ]; then
    CMD="${CMD} --embedding-model ${EMBEDDING_MODEL}"
fi

if [ -d "$RERANKER_MODEL" ]; then
    CMD="${CMD} --reranker-model ${RERANKER_MODEL}"
fi

# GPU 配置：如果 USE_GPU 为 false，添加 --no-gpu 标志
if [ "$USE_GPU" = "false" ] || [ "$USE_GPU" = "0" ]; then
    CMD="${CMD} --no-gpu"
fi

echo -e "${YELLOW}📝 Launch Command:${NC}"
echo -e "   ${CMD}"
echo ""
echo -e "${GREEN}🚀 Starting server...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
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

