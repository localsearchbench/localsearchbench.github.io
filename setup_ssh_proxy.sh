#!/bin/bash

# SSH 隧道代理设置脚本
# 将内网 RAG 服务器映射到本地端口

echo "🔧 SSH 隧道代理设置"
echo "===================="
echo ""
echo "使用方法："
echo "1. 如果 RAG 服务器有公网 SSH 访问："
echo "   ssh -L 8001:localhost:8000 user@your-server-ip"
echo ""
echo "2. 如果通过跳板机访问："
echo "   ssh -L 8001:internal-rag-ip:8000 user@jump-server"
echo ""
echo "3. 后台运行："
echo "   ssh -f -N -L 8001:localhost:8000 user@your-server-ip"
echo ""
echo "设置完成后，RAG 服务将在 http://localhost:8001 可用"
echo "然后可以用 cloudflared 或 ngrok 暴露 localhost:8001"
