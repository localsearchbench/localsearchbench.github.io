#!/bin/bash

# 一键启动隧道服务，连接到内网 RAG 服务器
# 使用 tmux 在后台运行隧道监控
#
# 用法:
#   ./start_with_monitor.sh                    # 使用默认地址 (localhost:8000)
#   ./start_with_monitor.sh http://10.0.0.5:8000  # 指定内网服务器地址

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取内网服务器地址（从参数或环境变量）
RAG_SERVER_URL="${1:-${RAG_SERVER_URL:-http://localhost:8000}}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}启动 LocalSearchBench 隧道服务${NC}"
echo -e "${GREEN}(连接到内网 RAG 服务器)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}内网服务器地址: $RAG_SERVER_URL${NC}"
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
tmux kill-session -t tunnel-monitor 2>/dev/null || true

echo -e "${YELLOW}启动 Cloudflare 隧道监控...${NC}"
echo -e "${YELLOW}(自动连接到内网 RAG 服务器并更新前端配置)${NC}"
tmux new-session -d -s tunnel-monitor "RAG_SERVER_URL='$RAG_SERVER_URL' ./auto_update_tunnel.sh monitor"
sleep 3

echo ""
echo -e "${GREEN}✅ 隧道服务启动成功！${NC}"
echo ""
echo "运行中的服务："
echo "  - Cloudflare 隧道监控 (tmux session: tunnel-monitor)"
echo "  - 连接到: $RAG_SERVER_URL"
echo ""
echo "查看服务状态："
echo -e "  ${YELLOW}tmux ls${NC}                          # 查看所有会话"
echo -e "  ${YELLOW}tmux attach -t tunnel-monitor${NC}   # 连接到隧道监控"
echo ""
echo "停止服务："
echo -e "  ${YELLOW}./stop_all.sh${NC}                   # 停止所有服务"
echo ""
echo "查看日志："
echo -e "  ${YELLOW}tail -f tunnel_updates.log${NC}           # 隧道监控日志"
echo -e "  ${YELLOW}tail -f cloudflared.log${NC}              # Cloudflare 隧道日志"
echo ""
echo -e "${YELLOW}📝 工作原理：${NC}"
echo "  1. Cloudflare 隧道连接到内网 RAG 服务器 ($RAG_SERVER_URL)"
echo "  2. 获得一个公网可访问的临时 URL (https://xxx.trycloudflare.com)"
echo "  3. 自动更新前端配置文件 (static/js/config.js)"
echo "  4. 前端页面通过隧道 URL 访问内网 RAG 服务器"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "  - 如需更改内网服务器地址，运行:"
echo -e "    ${GREEN}./start_with_monitor.sh http://新地址:端口${NC}"
echo "  - 或设置环境变量:"
echo -e "    ${GREEN}export RAG_SERVER_URL=http://新地址:端口${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"

