#!/bin/bash

# 停止 Cloudflare 隧道

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE=".tunnel_pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🛑 正在停止隧道 (PID: $PID)..."
        kill "$PID" 2>/dev/null || true
        sleep 2
        
        # 如果还在运行，强制杀死
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️  强制停止隧道..."
            kill -9 "$PID" 2>/dev/null || true
        fi
        
        echo "✅ 隧道已停止"
    else
        echo "ℹ️  隧道进程 (PID: $PID) 已不存在"
    fi
    rm -f "$PID_FILE"
else
    echo "ℹ️  未找到隧道 PID 文件"
    # 尝试通过进程名查找
    PIDS=$(pgrep -f "cloudflared tunnel" || true)
    if [ -n "$PIDS" ]; then
        echo "🛑 发现运行中的隧道进程，正在停止..."
        echo "$PIDS" | xargs kill 2>/dev/null || true
        echo "✅ 已停止所有隧道进程"
    else
        echo "ℹ️  未发现运行中的隧道进程"
    fi
fi















