#!/bin/bash

# 一键启动 RAG 服务器和隧道监控
# 使用 tmux 在后台运行两个服务

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}启动 LocalSearchBench 完整服务${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 tmux 是否安装
if ! command -v tmux &> /dev/null; then
    echo -e "${YELLOW}⚠️  tmux 未安装，正在安装...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install tmux
    else
        sudo apt-get install -y tmux
    fi
fi

# 检查 cloudflared 是否安装
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}❌ cloudflared 未安装${NC}"
    echo "请先安装 cloudflared:"
    echo "  macOS: brew install cloudflared"
    echo "  Linux: 参考 https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
    exit 1
fi

# 停止现有会话（如果存在）
tmux kill-session -t rag-server 2>/dev/null || true
tmux kill-session -t tunnel-monitor 2>/dev/null || true

echo -e "${YELLOW}1. 启动 RAG 服务器...${NC}"
tmux new-session -d -s rag-server "cd server && python rag_server.py"
sleep 2

echo -e "${YELLOW}2. 启动隧道监控...${NC}"
tmux new-session -d -s tunnel-monitor "./auto_update_tunnel.sh monitor"
sleep 2

echo ""
echo -e "${GREEN}✅ 服务启动成功！${NC}"
echo ""
echo "运行中的服务："
echo "  - RAG 服务器 (tmux session: rag-server)"
echo "  - 隧道监控 (tmux session: tunnel-monitor)"
echo ""
echo "查看服务状态："
echo -e "  ${YELLOW}tmux ls${NC}                          # 查看所有会话"
echo -e "  ${YELLOW}tmux attach -t rag-server${NC}       # 连接到 RAG 服务器"
echo -e "  ${YELLOW}tmux attach -t tunnel-monitor${NC}   # 连接到隧道监控"
echo ""
echo "停止服务："
echo -e "  ${YELLOW}./stop_all.sh${NC}                   # 停止所有服务"
echo ""
echo "查看日志："
echo -e "  ${YELLOW}tail -f server/logs/rag_server.log${NC}  # RAG 服务器日志"
echo -e "  ${YELLOW}tail -f tunnel_updates.log${NC}           # 隧道监控日志"
echo -e "  ${YELLOW}tail -f cloudflared.log${NC}              # Cloudflare 隧道日志"
echo ""
echo -e "${GREEN}========================================${NC}"

