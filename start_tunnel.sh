#!/bin/bash

# Cloudflare 隧道启动脚本
# 自动启动隧道并更新配置文件

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 配置
TARGET_URL="${1:-http://localhost:8001}"
CONFIG_FILE="tunnel_config.json"
LOG_FILE="tunnel.log"

echo "============================================================"
echo "🚀 启动 Cloudflare 隧道"
echo "============================================================"
echo "📡 目标地址: $TARGET_URL"
echo "📝 日志文件: $LOG_FILE"
echo "============================================================"

# 检查 cloudflared 是否安装
if ! command -v cloudflared &> /dev/null; then
    echo "❌ 错误: cloudflared 未安装"
    echo "   请访问: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
    exit 1
fi

# 检查目标服务是否可用
if ! curl -s --max-time 3 "$TARGET_URL/health" > /dev/null 2>&1; then
    echo "⚠️  警告: 目标服务 $TARGET_URL 可能不可用"
    echo "   继续启动隧道..."
fi

# 启动隧道并捕获 URL
echo ""
echo "🔄 正在启动隧道..."
echo ""

# 使用临时文件捕获输出
TEMP_OUTPUT=$(mktemp)
trap "rm -f $TEMP_OUTPUT" EXIT

# 启动隧道（后台运行）
cloudflared tunnel --url "$TARGET_URL" > "$TEMP_OUTPUT" 2>&1 &
TUNNEL_PID=$!

# 等待隧道启动并提取 URL
echo "⏳ 等待隧道启动..."
TUNNEL_URL=""
MAX_WAIT=15
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    sleep 1
    WAITED=$((WAITED + 1))
    
    # 尝试从输出中提取 URL (兼容 macOS grep)
    TUNNEL_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$TEMP_OUTPUT" 2>/dev/null | head -1 || echo "")
    
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
    
    # 检查进程是否还在运行
    if ! ps -p "$TUNNEL_PID" > /dev/null 2>&1; then
        echo "❌ 错误: 隧道进程意外退出"
        echo "   请检查 $TEMP_OUTPUT 文件内容:"
        cat "$TEMP_OUTPUT" 2>/dev/null || true
        exit 1
    fi
done

if [ -z "$TUNNEL_URL" ]; then
    echo "❌ 错误: 无法从隧道输出中提取 URL (等待了 ${WAITED} 秒)"
    echo "   请检查 $TEMP_OUTPUT 文件内容:"
    cat "$TEMP_OUTPUT" 2>/dev/null | tail -20 || true
    kill $TUNNEL_PID 2>/dev/null || true
    exit 1
fi

echo "✅ 隧道已启动!"
echo "🌐 隧道 URL: $TUNNEL_URL"
echo "📋 进程 ID: $TUNNEL_PID"
echo ""

# 更新配置文件
echo "📝 更新配置文件..."
cat > "$CONFIG_FILE" <<EOF
{
  "rag_server_url": "$TUNNEL_URL",
  "tunnel_type": "temporary",
  "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "target": "$TARGET_URL",
  "pid": $TUNNEL_PID
}
EOF

# 更新 config.js 中的默认值
if [ -f "static/js/config.js" ]; then
    # 备份原文件
    cp "static/js/config.js" "static/js/config.js.backup.$(date +%Y%m%d_%H%M%S)"
    
    # 更新 URL
    sed -i.bak "s|RAG_SERVER_URL: 'https://[^']*'|RAG_SERVER_URL: '$TUNNEL_URL'|" "static/js/config.js"
    rm -f "static/js/config.js.bak"
    
    echo "✅ 已更新 static/js/config.js"
fi

# 保存 PID 和 URL 到文件
echo "$TUNNEL_PID" > .tunnel_pid
echo "$TUNNEL_URL" > .tunnel_url

echo ""
echo "============================================================"
echo "✅ 配置更新完成!"
echo "============================================================"
echo "🌐 新的 RAG 服务器 URL: $TUNNEL_URL"
echo "📋 隧道进程 ID: $TUNNEL_PID"
echo ""
echo "💡 提示:"
echo "   - 隧道正在后台运行"
echo "   - 停止隧道: kill $TUNNEL_PID 或运行 ./stop_tunnel.sh"
echo "   - 查看日志: tail -f $LOG_FILE"
echo "============================================================"

# 将输出重定向到日志文件
mv "$TEMP_OUTPUT" "$LOG_FILE"

# 保持脚本运行（可选）
# 如果需要在前台运行，取消下面的注释
# wait $TUNNEL_PID

