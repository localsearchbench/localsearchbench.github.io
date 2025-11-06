#!/bin/bash
# 启动 MCP RAG 搜索工具
# 参考 RL-Factory 的启动方式

set -e

echo "=========================================="
echo "MCP RAG 搜索工具启动脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 环境
echo -e "\n${YELLOW}[1/4]${NC} 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python 版本: $(python3 --version)"

# 检查依赖
echo -e "\n${YELLOW}[2/4]${NC} 检查依赖..."
if ! python3 -c "import mcp" 2>/dev/null; then
    echo -e "${YELLOW}警告: 未安装 mcp 库，正在安装...${NC}"
    pip install -r mcp_tools/requirements.txt
fi
echo -e "${GREEN}✓${NC} 依赖检查完成"

# 检查 RAG 服务器
echo -e "\n${YELLOW}[3/4]${NC} 检查 RAG 服务器连接..."
RAG_URL="http://127.0.0.1:5003/health"
if curl -s "$RAG_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} RAG 服务器运行正常"
else
    echo -e "${RED}警告: RAG 服务器未运行 ($RAG_URL)${NC}"
    echo "请先启动 RAG 服务器："
    echo "  cd server && bash start_rag_server.sh"
fi

# 启动 MCP 工具
echo -e "\n${YELLOW}[4/4]${NC} 启动 MCP 工具..."
echo -e "${GREEN}✓${NC} MCP 工具已准备就绪"
echo ""
echo "可用工具："
echo "  - query_rag: 本地商户 RAG 搜索"
echo "  - web_search: 网络搜索"
echo ""
echo "配置文件: mcp_tools/mcp_config.json"
echo ""
echo "=========================================="

# 运行 MCP 服务
python3 mcp_tools/rag_search.py


