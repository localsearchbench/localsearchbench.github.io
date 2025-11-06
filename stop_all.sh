#!/bin/bash

# 停止所有服务

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}停止本地隧道服务...${NC}"
echo ""

# 停止 tmux 会话
echo "1. 停止隧道监控..."
tmux kill-session -t tunnel-monitor 2>/dev/null && echo -e "${GREEN}✅ 隧道监控已停止${NC}" || echo -e "${YELLOW}⚠️  隧道监控未运行${NC}"

# 停止 cloudflared 进程
echo "2. 停止 Cloudflare 隧道..."
pkill -f "cloudflared tunnel" && echo -e "${GREEN}✅ Cloudflare 隧道已停止${NC}" || echo -e "${YELLOW}⚠️  Cloudflare 隧道未运行${NC}"

echo ""
echo -e "${GREEN}本地服务已停止${NC}"
echo -e "${YELLOW}注意：内网 RAG 服务器仍在运行（需要在服务器上手动停止）${NC}"

