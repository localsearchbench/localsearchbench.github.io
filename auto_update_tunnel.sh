#!/bin/bash

# 自动检测和更新 Cloudflare 临时隧道
# 当隧道挂掉时自动重启并更新配置文件

CONFIG_FILE="static/js/config.js"
LOG_FILE="cloudflared.log"
TUNNEL_LOG="tunnel_updates.log"
CHECK_INTERVAL=30  # 每30秒检查一次

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$TUNNEL_LOG"
}

# 从日志文件中提取最新的隧道 URL
get_tunnel_url() {
    if [ -f "$LOG_FILE" ]; then
        # 查找最后一个 trycloudflare.com URL
        grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' "$LOG_FILE" | tail -1
    fi
}

# 更新配置文件中的隧道 URL
update_config() {
    local new_url="$1"
    if [ -z "$new_url" ]; then
        log "错误: 没有找到新的隧道 URL"
        return 1
    fi
    
    # 备份配置文件
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"
    
    # 使用 sed 更新 RAG_SERVER_URL
    sed -i.tmp "s|RAG_SERVER_URL: 'https://[a-zA-Z0-9-]*\.trycloudflare\.com'|RAG_SERVER_URL: '$new_url'|g" "$CONFIG_FILE"
    rm -f "${CONFIG_FILE}.tmp"
    
    log "✅ 配置文件已更新: $new_url"
    echo -e "${GREEN}配置文件已更新为: $new_url${NC}"
}

# 检查隧道是否正在运行
check_tunnel_running() {
    pgrep -f "cloudflared tunnel" > /dev/null
    return $?
}

# 检查隧道 URL 是否可访问
check_tunnel_accessible() {
    local url="$1"
    if [ -z "$url" ]; then
        return 1
    fi
    
    # 尝试访问健康检查端点
    local health_url="${url}/health"
    local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$health_url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# 启动新的隧道
start_tunnel() {
    log "🚀 启动新的 Cloudflare 隧道..."
    echo -e "${YELLOW}启动新的 Cloudflare 隧道...${NC}"
    
    # 清空旧的日志文件
    > "$LOG_FILE"
    
    # 启动隧道（后台运行）
    nohup cloudflared tunnel --url http://localhost:8000 > "$LOG_FILE" 2>&1 &
    
    # 等待隧道启动并获取 URL
    local max_wait=30
    local waited=0
    local tunnel_url=""
    
    while [ $waited -lt $max_wait ]; do
        sleep 2
        waited=$((waited + 2))
        tunnel_url=$(get_tunnel_url)
        
        if [ -n "$tunnel_url" ]; then
            log "✅ 隧道已启动: $tunnel_url"
            echo -e "${GREEN}隧道已启动: $tunnel_url${NC}"
            
            # 等待隧道完全就绪
            sleep 3
            
            # 更新配置文件
            update_config "$tunnel_url"
            return 0
        fi
    done
    
    log "❌ 隧道启动超时"
    echo -e "${RED}隧道启动超时${NC}"
    return 1
}

# 停止现有隧道
stop_tunnel() {
    log "⏹️  停止现有隧道..."
    pkill -f "cloudflared tunnel"
    sleep 2
}

# 主监控循环
monitor_tunnel() {
    log "========================================="
    log "🔍 开始监控 Cloudflare 隧道"
    log "检查间隔: ${CHECK_INTERVAL}秒"
    log "========================================="
    
    echo -e "${GREEN}开始监控 Cloudflare 隧道...${NC}"
    echo "按 Ctrl+C 停止监控"
    echo ""
    
    local consecutive_failures=0
    local max_failures=3  # 连续失败3次后重启
    
    while true; do
        # 检查隧道进程是否运行
        if ! check_tunnel_running; then
            log "⚠️  隧道进程未运行"
            echo -e "${RED}隧道进程未运行，正在重启...${NC}"
            stop_tunnel
            start_tunnel
            consecutive_failures=0
            sleep 10
            continue
        fi
        
        # 获取当前隧道 URL
        current_url=$(get_tunnel_url)
        
        if [ -z "$current_url" ]; then
            log "⚠️  无法获取隧道 URL"
            consecutive_failures=$((consecutive_failures + 1))
        else
            # 检查隧道是否可访问
            if check_tunnel_accessible "$current_url"; then
                if [ $consecutive_failures -gt 0 ]; then
                    log "✅ 隧道恢复正常: $current_url"
                    echo -e "${GREEN}✅ 隧道正常运行: $current_url${NC}"
                fi
                consecutive_failures=0
            else
                consecutive_failures=$((consecutive_failures + 1))
                log "⚠️  隧道无法访问 (失败次数: $consecutive_failures/$max_failures): $current_url"
                echo -e "${YELLOW}⚠️  隧道无法访问 (失败次数: $consecutive_failures/$max_failures)${NC}"
            fi
        fi
        
        # 如果连续失败达到阈值，重启隧道
        if [ $consecutive_failures -ge $max_failures ]; then
            log "❌ 隧道连续失败 $consecutive_failures 次，正在重启..."
            echo -e "${RED}隧道已挂掉，正在重启...${NC}"
            stop_tunnel
            start_tunnel
            consecutive_failures=0
            sleep 10
        fi
        
        # 等待下一次检查
        sleep $CHECK_INTERVAL
    done
}

# 信号处理
cleanup() {
    log "========================================="
    log "🛑 收到停止信号，退出监控"
    log "========================================="
    echo -e "\n${YELLOW}停止监控...${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 主函数
main() {
    case "${1:-monitor}" in
        start)
            start_tunnel
            ;;
        stop)
            stop_tunnel
            ;;
        restart)
            stop_tunnel
            start_tunnel
            ;;
        status)
            if check_tunnel_running; then
                current_url=$(get_tunnel_url)
                echo -e "${GREEN}✅ 隧道正在运行${NC}"
                echo "URL: $current_url"
                if check_tunnel_accessible "$current_url"; then
                    echo -e "${GREEN}✅ 隧道可访问${NC}"
                else
                    echo -e "${RED}❌ 隧道不可访问${NC}"
                fi
            else
                echo -e "${RED}❌ 隧道未运行${NC}"
            fi
            ;;
        monitor)
            monitor_tunnel
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|monitor}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动隧道"
            echo "  stop    - 停止隧道"
            echo "  restart - 重启隧道"
            echo "  status  - 检查隧道状态"
            echo "  monitor - 持续监控隧道（默认）"
            exit 1
            ;;
    esac
}

main "$@"

