#!/bin/bash
# 测试远程RAG服务器连接

SERVER_IP="10.164.243.10"
SERVER_PORT="8000"
SERVER_URL="http://${SERVER_IP}:${SERVER_PORT}"
export RAG_SERVER_URL="${SERVER_URL}"

echo "======================================"
echo "测试远程RAG服务器连接"
echo "服务器: ${SERVER_URL}"
echo "======================================"
echo ""

# 1. 测试网络连通性
echo "1️⃣  测试网络连通性..."
if ping -c 2 ${SERVER_IP} > /dev/null 2>&1; then
    echo "✅ 网络连通"
else
    echo "❌ 无法ping通服务器"
    exit 1
fi
echo ""

# 2. 测试健康检查
echo "2️⃣  测试健康检查接口..."
if curl -s --connect-timeout 5 ${SERVER_URL}/health > /dev/null 2>&1; then
    echo "✅ 健康检查成功"
    curl -s ${SERVER_URL}/health | python3 -m json.tool 2>/dev/null || curl -s ${SERVER_URL}/health
else
    echo "❌ 健康检查失败 - 服务器可能未启动或端口未开放"
    exit 1
fi
echo ""

# 3. 测试RAG搜索
echo "3️⃣  测试RAG搜索接口..."
response=$(curl -s --connect-timeout 10 -X POST ${SERVER_URL}/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "找一家火锅店",
    "city": "beijing",
    "top_k": 2
  }')

if [ $? -eq 0 ] && [ ! -z "$response" ]; then
    echo "✅ RAG搜索成功"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo "❌ RAG搜索失败"
fi
echo ""

# 4. 显示配置
echo "======================================"
echo "✅ 连接配置"
echo "======================================"
echo "在你的代码中使用："
echo ""
echo "export RAG_SERVER_URL=\"${SERVER_URL}\""
echo ""
echo "或在 Python 中："
echo "RAG_SERVER_URL = \"${SERVER_URL}\""
echo ""

