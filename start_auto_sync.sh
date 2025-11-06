#!/bin/bash

# 启动隧道监控和自动同步到 GitHub Pages
# 这个脚本会同时运行：
# 1. 隧道监控和自动重启 (auto_update_tunnel.sh)
# 2. 配置文件自动提交到 GitHub (auto_commit_config.sh)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TUNNEL_SCRIPT="$SCRIPT_DIR/auto_update_tunnel.sh"
COMMIT_SCRIPT="$SCRIPT_DIR/auto_commit_config.sh"

PID_FILE_TUNNEL="$SCRIPT_DIR/.tunnel_monitor.pid"
PID_FILE_COMMIT="$SCRIPT_DIR/.commit_monitor.pid"

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# 检查脚本是否存在
check_scripts() {
    if [ ! -f "$TUNNEL_SCRIPT" ]; then
        log "${RED}❌ 找不到隧道监控脚本: $TUNNEL_SCRIPT${NC}"
        exit 1
    fi
    
    if [ ! -f "$COMMIT_SCRIPT" ]; then
        log "${RED}❌ 找不到自动提交脚本: $COMMIT_SCRIPT${NC}"
        exit 1
    fi
    
    # 确保脚本有执行权限
    chmod +x "$TUNNEL_SCRIPT" "$COMMIT_SCRIPT"
}

# 启动所有服务
start_services() {
    log "${GREEN}=========================================${NC}"
    log "${GREEN}🚀 启动 LocalSearchBench 自动同步服务${NC}"
    log "${GREEN}=========================================${NC}"
    
    # 启动隧道监控
    log "${YELLOW}📡 启动隧道监控服务...${NC}"
    nohup "$TUNNEL_SCRIPT" monitor > tunnel_monitor.log 2>&1 &
    echo $! > "$PID_FILE_TUNNEL"
    log "${GREEN}✅ 隧道监控已启动 (PID: $(cat $PID_FILE_TUNNEL))${NC}"
    
    # 等待一下，让隧道先启动
    sleep 5
    
    # 启动自动提交
    log "${YELLOW}📝 启动自动提交服务...${NC}"
    nohup "$COMMIT_SCRIPT" monitor > commit_monitor.log 2>&1 &
    echo $! > "$PID_FILE_COMMIT"
    log "${GREEN}✅ 自动提交已启动 (PID: $(cat $PID_FILE_COMMIT))${NC}"
    
    log "${GREEN}=========================================${NC}"
    log "${GREEN}✅ 所有服务已启动！${NC}"
    log "${GREEN}=========================================${NC}"
    log ""
    log "${BLUE}📊 服务状态：${NC}"
    log "  • 隧道监控: 运行中 (日志: tunnel_monitor.log)"
    log "  • 自动提交: 运行中 (日志: commit_monitor.log)"
    log ""
    log "${YELLOW}💡 提示：${NC}"
    log "  • 查看隧道日志: tail -f tunnel_monitor.log"
    log "  • 查看提交日志: tail -f commit_monitor.log"
    log "  • 停止所有服务: $0 stop"
    log "  • 查看服务状态: $0 status"
}

# 停止所有服务
stop_services() {
    log "${YELLOW}=========================================${NC}"
    log "${YELLOW}🛑 停止所有服务...${NC}"
    log "${YELLOW}=========================================${NC}"
    
    local stopped=0
    
    # 停止隧道监控
    if [ -f "$PID_FILE_TUNNEL" ]; then
        local pid=$(cat "$PID_FILE_TUNNEL")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log "${GREEN}✅ 已停止隧道监控 (PID: $pid)${NC}"
            stopped=1
        fi
        rm -f "$PID_FILE_TUNNEL"
    fi
    
    # 停止自动提交
    if [ -f "$PID_FILE_COMMIT" ]; then
        local pid=$(cat "$PID_FILE_COMMIT")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log "${GREEN}✅ 已停止自动提交 (PID: $pid)${NC}"
            stopped=1
        fi
        rm -f "$PID_FILE_COMMIT"
    fi
    
    # 停止 cloudflared 进程
    if pgrep -f "cloudflared tunnel" > /dev/null; then
        pkill -f "cloudflared tunnel"
        log "${GREEN}✅ 已停止 Cloudflare 隧道${NC}"
        stopped=1
    fi
    
    if [ $stopped -eq 0 ]; then
        log "${YELLOW}⚠️  没有运行中的服务${NC}"
    else
        log "${GREEN}✅ 所有服务已停止${NC}"
    fi
}

# 检查服务状态
check_status() {
    log "${BLUE}=========================================${NC}"
    log "${BLUE}📊 服务状态${NC}"
    log "${BLUE}=========================================${NC}"
    
    local all_running=true
    
    # 检查隧道监控
    if [ -f "$PID_FILE_TUNNEL" ]; then
        local pid=$(cat "$PID_FILE_TUNNEL")
        if kill -0 "$pid" 2>/dev/null; then
            log "${GREEN}✅ 隧道监控: 运行中 (PID: $pid)${NC}"
        else
            log "${RED}❌ 隧道监控: 已停止${NC}"
            all_running=false
        fi
    else
        log "${RED}❌ 隧道监控: 未启动${NC}"
        all_running=false
    fi
    
    # 检查自动提交
    if [ -f "$PID_FILE_COMMIT" ]; then
        local pid=$(cat "$PID_FILE_COMMIT")
        if kill -0 "$pid" 2>/dev/null; then
            log "${GREEN}✅ 自动提交: 运行中 (PID: $pid)${NC}"
        else
            log "${RED}❌ 自动提交: 已停止${NC}"
            all_running=false
        fi
    else
        log "${RED}❌ 自动提交: 未启动${NC}"
        all_running=false
    fi
    
    # 检查 cloudflared
    if pgrep -f "cloudflared tunnel" > /dev/null; then
        log "${GREEN}✅ Cloudflare 隧道: 运行中${NC}"
        
        # 显示当前隧道 URL
        if [ -f "cloudflared.log" ]; then
            local url=$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' cloudflared.log | tail -1)
            if [ -n "$url" ]; then
                log "${BLUE}🌐 当前隧道: $url${NC}"
            fi
        fi
    else
        log "${RED}❌ Cloudflare 隧道: 未运行${NC}"
        all_running=false
    fi
    
    log "${BLUE}=========================================${NC}"
    
    if $all_running; then
        log "${GREEN}✅ 所有服务正常运行${NC}"
        return 0
    else
        log "${YELLOW}⚠️  部分服务未运行${NC}"
        return 1
    fi
}

# 重启所有服务
restart_services() {
    log "${YELLOW}🔄 重启所有服务...${NC}"
    stop_services
    sleep 2
    start_services
}

# 查看日志
view_logs() {
    local log_type="${1:-all}"
    
    case "$log_type" in
        tunnel)
            tail -f tunnel_monitor.log
            ;;
        commit)
            tail -f commit_monitor.log
            ;;
        all)
            tail -f tunnel_monitor.log commit_monitor.log
            ;;
        *)
            log "${RED}❌ 未知的日志类型: $log_type${NC}"
            log "可用选项: tunnel, commit, all"
            exit 1
            ;;
    esac
}

# 主函数
main() {
    check_scripts
    
    case "${1:-start}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs "${2:-all}"
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|logs [tunnel|commit|all]}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动所有服务（默认）"
            echo "  stop    - 停止所有服务"
            echo "  restart - 重启所有服务"
            echo "  status  - 查看服务状态"
            echo "  logs    - 查看日志 (tunnel/commit/all)"
            echo ""
            echo "示例:"
            echo "  $0 start          # 启动所有服务"
            echo "  $0 status         # 查看状态"
            echo "  $0 logs tunnel    # 查看隧道日志"
            echo "  $0 logs all       # 查看所有日志"
            exit 1
            ;;
    esac
}

main "$@"

