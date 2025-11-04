#!/bin/bash

# RAG Server 测试脚本
# 用于验证服务器配置和功能

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器配置
SERVER_URL="${RAG_SERVER_URL:-http://localhost:8000}"
TIMEOUT=5

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     LocalSearchBench RAG Server Test Script               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🎯 Testing server: ${SERVER_URL}${NC}"
echo ""

# 测试计数器
PASSED=0
FAILED=0

# 测试函数
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_code="${5:-200}"
    
    echo -n "Testing ${name}... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "${SERVER_URL}${endpoint}" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X POST --max-time $TIMEOUT \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${SERVER_URL}${endpoint}" 2>&1)
    fi
    
    # 提取状态码（最后一行）
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    # 检查是否为数字
    if ! [[ "$http_code" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}❌ FAILED${NC}"
        echo -e "  ${RED}Error: Cannot connect to server${NC}"
        echo -e "  ${YELLOW}Response: ${http_code}${NC}"
        ((FAILED++))
        return 1
    fi
    
    if [ "$http_code" -eq "$expected_code" ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo -e "  ${RED}Expected: ${expected_code}, Got: ${http_code}${NC}"
        echo -e "  ${YELLOW}Response: ${body:0:200}${NC}"
        ((FAILED++))
        return 1
    fi
}

# ==================== 开始测试 ====================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Basic Endpoints${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 1. 健康检查
test_endpoint "Health Check" "GET" "/health"

# 2. 根路径
test_endpoint "Root Endpoint" "GET" "/"

# 3. 城市列表
test_endpoint "Cities List" "GET" "/cities"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Search API${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 4. 基本搜索
test_endpoint "Basic Search" "POST" "/search" '{
  "query": "推荐一家火锅店",
  "city": "shanghai",
  "top_k": 5,
  "retriever": "faiss",
  "reranker": "qwen3"
}'

# 5. 不同城市搜索
test_endpoint "Beijing Search" "POST" "/search" '{
  "query": "咖啡店",
  "city": "beijing",
  "top_k": 3,
  "retriever": "faiss",
  "reranker": "none"
}'

# 6. 无效城市（应该返回错误）
test_endpoint "Invalid City (Should Fail)" "POST" "/search" '{
  "query": "测试",
  "city": "invalid_city",
  "top_k": 5,
  "retriever": "faiss",
  "reranker": "none"
}' 422

# 7. 空查询（应该返回错误）
test_endpoint "Empty Query (Should Fail)" "POST" "/search" '{
  "query": "",
  "city": "shanghai",
  "top_k": 5,
  "retriever": "faiss",
  "reranker": "none"
}' 422

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Performance Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 8. 性能测试（测量响应时间）
echo -n "Search Performance Test... "
start_time=$(date +%s.%N)
curl -s -X POST --max-time 10 \
    -H "Content-Type: application/json" \
    -d '{
      "query": "好吃的餐厅",
      "city": "shanghai",
      "top_k": 10,
      "retriever": "faiss",
      "reranker": "qwen3"
    }' \
    "${SERVER_URL}/search" > /dev/null
exit_code=$?
end_time=$(date +%s.%N)

if [ $exit_code -eq 0 ]; then
    elapsed=$(echo "$end_time - $start_time" | bc)
    echo -e "${GREEN}✅ PASSED${NC}"
    echo -e "  ${GREEN}Response time: ${elapsed}s${NC}"
    
    # 判断性能
    threshold=3.0
    if (( $(echo "$elapsed < $threshold" | bc -l) )); then
        echo -e "  ${GREEN}Performance: Excellent (<${threshold}s)${NC}"
    else
        echo -e "  ${YELLOW}Performance: Acceptable (>${threshold}s)${NC}"
    fi
    ((PASSED++))
else
    echo -e "${RED}❌ FAILED${NC}"
    echo -e "  ${RED}Request timed out or failed${NC}"
    ((FAILED++))
fi

# ==================== 测试总结 ====================

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

TOTAL=$((PASSED + FAILED))
echo -e "Total Tests: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED}${NC}"
    echo ""
    echo -e "${RED}❌ Some tests failed. Please check the server logs.${NC}"
    exit 1
else
    echo -e "${RED}Failed: ${FAILED}${NC}"
    echo ""
    echo -e "${GREEN}✅ All tests passed! Server is working correctly.${NC}"
    exit 0
fi

