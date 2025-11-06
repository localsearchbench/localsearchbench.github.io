#!/bin/bash

# 检查所有服务状态

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}LocalSearchBench 服务状态${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 RAG 服务器
echo "1. RAG 服务器:"
if tmux has-session -t rag-server 2>/dev/null; then
    echo -e "   ${GREEN}✅ 运行中 (tmux session: rag-server)${NC}"
    
    # 检查端口
    if lsof -i :8000 &>/dev/null; then
        echo -e "   ${GREEN}✅ 端口 8000 监听中${NC}"
    else
        echo -e "   ${YELLOW}⚠️  端口 8000 未监听${NC}"
    fi
else
    echo -e "   ${RED}❌ 未运行${NC}"
fi
echo ""

# 检查隧道监控
echo "2. 隧道监控:"
if tmux has-session -t tunnel-monitor 2>/dev/null; then
    echo -e "   ${GREEN}✅ 运行中 (tmux session: tunnel-monitor)${NC}"
else
    echo -e "   ${RED}❌ 未运行${NC}"
fi
echo ""

# 检查 Cloudflare 隧道
echo "3. Cloudflare 隧道:"
if pgrep -f "cloudflared tunnel" > /dev/null; then
    echo -e "   ${GREEN}✅ 运行中${NC}"
    
    # 获取隧道 URL
    if [ -f "cloudflared.log" ]; then
        tunnel_url=$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' cloudflared.log | tail -1)
        if [ -n "$tunnel_url" ]; then
            echo -e "   ${GREEN}URL: $tunnel_url${NC}"
            
            # 检查隧道是否可访问
            if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$tunnel_url/health" | grep -q "200"; then
                echo -e "   ${GREEN}✅ 隧道可访问${NC}"
            else
                echo -e "   ${YELLOW}⚠️  隧道不可访问${NC}"
            fi
        fi
    fi
else
    echo -e "   ${RED}❌ 未运行${NC}"
fi
echo ""

# 显示最近的日志
echo "4. 最近的日志 (最后 5 行):"
echo ""
if [ -f "tunnel_updates.log" ]; then
    echo -e "${YELLOW}隧道监控日志:${NC}"
    tail -5 tunnel_updates.log | sed 's/^/   /'
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo ""
echo "查看完整日志："
echo -e "  ${YELLOW}tail -f tunnel_updates.log${NC}           # 隧道监控日志"
echo -e "  ${YELLOW}tail -f cloudflared.log${NC}              # Cloudflare 隧道日志"
echo -e "  ${YELLOW}tail -f server/logs/rag_server.log${NC}  # RAG 服务器日志"
echo ""
echo "连接到服务："
echo -e "  ${YELLOW}tmux attach -t rag-server${NC}       # 连接到 RAG 服务器"
echo -e "  ${YELLOW}tmux attach -t tunnel-monitor${NC}   # 连接到隧道监控"
echo -e "  ${YELLOW}(按 Ctrl+B 然后按 D 分离会话)${NC}"
echo ""

