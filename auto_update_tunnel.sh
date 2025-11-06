#!/bin/bash

# 自动检测和更新 Cloudflare 临时隧道
# 当隧道挂掉时自动重启并更新配置文件
#
# ⚠️  重要提示：
# 临时隧道每次重启都会生成新的 URL！
# 如需固定 URL，请使用 Cloudflare 命名隧道（需要 Cloudflare 账号）

CONFIG_FILE="static/js/config.js"
DYNAMIC_CONFIG_FILE="tunnel_config.json"
LOG_FILE="cloudflared.log"
TUNNEL_LOG="tunnel_updates.log"
URL_HISTORY_FILE="tunnel_url_history.log"  # 记录历史 URL
CHECK_INTERVAL=100  # 每100秒检查一次
RESTART_COOLDOWN=300  # 重启冷却时间（秒），避免频繁重启

# Git 自动推送配置（可通过环境变量覆盖）
# 设置为 "true" 启用自动推送，"false" 禁用
AUTO_GIT_PUSH="${AUTO_GIT_PUSH:-true}"
GIT_BRANCH="${GIT_BRANCH:-main}"  # Git 分支名称

# 内网 RAG 服务器地址（可通过环境变量覆盖）
# 格式: http://内网IP:端口 或 http://域名:端口
RAG_SERVER_URL="${RAG_SERVER_URL:-http://localhost:8000}"

# 上次重启时间
LAST_RESTART_TIME=0

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

# 更新动态配置文件（JSON）
update_dynamic_config() {
    local new_url="$1"
    if [ -z "$new_url" ]; then
        log "错误: 没有找到新的隧道 URL"
        return 1
    fi
    
    # 获取当前时间（ISO 8601 格式）
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S+08:00")
    
    # 记录 URL 历史
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $new_url" >> "$URL_HISTORY_FILE"
    
    # 创建 JSON 配置文件
    cat > "$DYNAMIC_CONFIG_FILE" << EOF
{
  "rag_server_url": "$new_url",
  "updated_at": "$timestamp",
  "status": "active",
  "version": "1.0",
  "tunnel_type": "temporary",
  "note": "临时隧道 - URL 每次重启会变化"
}
EOF
    
    log "✅ 动态配置文件已更新: $new_url"
    echo -e "${GREEN}动态配置文件已更新为: $new_url${NC}"
    echo -e "${YELLOW}⚠️  注意：这是临时隧道，URL 在重启后会变化${NC}"
    
    # 发送桌面通知（如果可用）
    if command -v osascript &> /dev/null; then
        osascript -e "display notification \"新隧道 URL: $new_url\" with title \"LocalSearchBench 隧道已更新\""
    fi
}

# Git 提交并推送配置更新
git_commit_and_push() {
    local new_url="$1"
    
    # 检查是否启用自动推送
    if [ "$AUTO_GIT_PUSH" != "true" ]; then
        log "ℹ️  自动 Git 推送已禁用（AUTO_GIT_PUSH=$AUTO_GIT_PUSH）"
        echo -e "${YELLOW}ℹ️  自动 Git 推送已禁用，配置仅保存在本地${NC}"
        return 0
    fi
    
    # 检查是否在 git 仓库中
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        log "⚠️  不在 Git 仓库中，跳过提交"
        return 0
    fi
    
    # 检查是否有需要提交的更改
    if ! git diff --quiet "$DYNAMIC_CONFIG_FILE" "$CONFIG_FILE" 2>/dev/null; then
        log "📤 准备提交配置更新到 Git..."
        echo -e "${YELLOW}📤 正在提交配置到 Git...${NC}"
        
        # 添加文件到暂存区
        git add "$DYNAMIC_CONFIG_FILE" "$CONFIG_FILE" 2>/dev/null
        
        # 提取短 URL 用于提交信息
        local short_url=$(echo "$new_url" | sed 's|https://||' | sed 's|/.*||')
        local commit_msg="🔄 Auto-update tunnel URL to ${short_url}"
        
        if git commit -m "$commit_msg" &> /dev/null; then
            log "✅ Git 提交成功"
            echo -e "${GREEN}✅ 配置已提交到本地仓库${NC}"
            
            # 尝试推送到远程
            log "📤 推送到远程仓库 ($GIT_BRANCH)..."
            echo -e "${YELLOW}📤 推送到 GitHub...${NC}"
            
            if git push origin "$GIT_BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
                log "✅ 推送成功"
                echo -e "${GREEN}✅ 配置已推送到 GitHub${NC}"
                echo -e "${GREEN}   分支: $GIT_BRANCH${NC}"
                
                # 发送推送成功通知
                if command -v osascript &> /dev/null; then
                    osascript -e "display notification \"配置已推送到 GitHub ($GIT_BRANCH)\" with title \"隧道配置已更新\""
                fi
            else
                log "⚠️  推送失败，可能需要手动推送"
                echo -e "${YELLOW}⚠️  推送失败，请稍后手动推送或检查网络${NC}"
                echo -e "${YELLOW}   提示：运行 'git push origin $GIT_BRANCH' 手动推送${NC}"
            fi
        else
            log "⚠️  Git 提交失败"
            echo -e "${YELLOW}⚠️  Git 提交失败${NC}"
        fi
    else
        log "ℹ️  没有需要提交的更改"
    fi
}

# 更新配置文件中的隧道 URL（保留作为后备）
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
    
    log "✅ 静态配置文件已更新: $new_url"
    echo -e "${GREEN}静态配置文件已更新为: $new_url${NC}"
}

# 检查隧道是否正在运行
check_tunnel_running() {
    pgrep -f "cloudflared tunnel" > /dev/null
    return $?
}

# 检查 RAG 服务器是否在线（直接访问本地）
check_rag_server_local() {
    local health_url="${RAG_SERVER_URL}/health"
    local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 --max-time 5 "$health_url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# 检查隧道 URL 是否可访问（通过公网访问）
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
    log "   连接到: $RAG_SERVER_URL"
    echo -e "${YELLOW}启动新的 Cloudflare 隧道...${NC}"
    echo -e "${YELLOW}连接到内网服务器: $RAG_SERVER_URL${NC}"
    
    # 清空旧的日志文件
    > "$LOG_FILE"
    
    # 启动隧道（后台运行）
    nohup cloudflared tunnel --url "$RAG_SERVER_URL" > "$LOG_FILE" 2>&1 &
    
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
            
            # 更新动态配置文件（主要）
            update_dynamic_config "$tunnel_url"
            
            # 更新静态配置文件（作为后备）
            update_config "$tunnel_url"
            
            # 提交并推送配置更新
            git_commit_and_push "$tunnel_url"
            
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

# 检查是否应该重启（考虑冷却时间）
should_restart() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - LAST_RESTART_TIME))
    
    if [ $elapsed -lt $RESTART_COOLDOWN ]; then
        local remaining=$((RESTART_COOLDOWN - elapsed))
        log "⏰ 重启冷却中，还需等待 ${remaining} 秒"
        echo -e "${YELLOW}⏰ 为避免频繁重启，需等待 ${remaining} 秒${NC}"
        return 1
    fi
    return 0
}

# 主监控循环
monitor_tunnel() {
    log "========================================="
    log "🔍 开始监控 Cloudflare 临时隧道"
    log "检查间隔: ${CHECK_INTERVAL}秒"
    log "重启冷却: ${RESTART_COOLDOWN}秒"
    log "连接到: $RAG_SERVER_URL"
    log "自动推送: $AUTO_GIT_PUSH"
    if [ "$AUTO_GIT_PUSH" = "true" ]; then
        log "Git 分支: $GIT_BRANCH"
    fi
    log "========================================="
    
    echo -e "${GREEN}开始监控 Cloudflare 隧道...${NC}"
    echo -e "${YELLOW}⚠️  临时隧道每次重启都会生成新的 URL${NC}"
    if [ "$AUTO_GIT_PUSH" = "true" ]; then
        echo -e "${GREEN}✅ 自动 Git 推送已启用 (分支: $GIT_BRANCH)${NC}"
    else
        echo -e "${YELLOW}ℹ️  自动 Git 推送已禁用${NC}"
    fi
    echo "按 Ctrl+C 停止监控"
    echo ""
    
    local consecutive_failures=0
    local max_failures=3  # 连续失败3次后重启
    local check_count=0
    
    while true; do
        check_count=$((check_count + 1))
        
        # 检查隧道进程是否运行
        if ! check_tunnel_running; then
            log "⚠️  隧道进程未运行 (检查 #$check_count)"
            echo -e "${RED}隧道进程未运行，正在重启...${NC}"
            
            if should_restart; then
                stop_tunnel
                start_tunnel
                LAST_RESTART_TIME=$(date +%s)
                consecutive_failures=0
                sleep 10
            else
                sleep $CHECK_INTERVAL
            fi
            continue
        fi
        
        # 获取当前隧道 URL
        current_url=$(get_tunnel_url)
        
        if [ -z "$current_url" ]; then
            log "⚠️  无法获取隧道 URL (检查 #$check_count)"
            consecutive_failures=$((consecutive_failures + 1))
        else
            # 先检查本地 RAG 服务器是否在线
            if ! check_rag_server_local; then
                # RAG 服务器本地不可访问，可能正在重启
                if [ $((check_count % 10)) -eq 0 ]; then
                    log "⚠️  RAG 服务器本地不可访问，可能正在重启（隧道保持运行）"
                    echo -e "${YELLOW}⚠️  RAG 服务器暂时不可用（隧道正常，无需重启）${NC}"
                fi
                # 不算作隧道失败，RAG 服务器重启后会自动恢复
                consecutive_failures=0
                sleep $CHECK_INTERVAL
                continue
            fi
            
            # RAG 服务器在线，检查隧道是否可访问
            if check_tunnel_accessible "$current_url"; then
                if [ $consecutive_failures -gt 0 ]; then
                    log "✅ 隧道恢复正常: $current_url"
                    echo -e "${GREEN}✅ 隧道正常运行: $current_url${NC}"
                elif [ $((check_count % 20)) -eq 0 ]; then
                    # 每20次检查（约10分钟）输出一次状态
                    log "💚 隧道运行正常: $current_url (已检查 $check_count 次)"
                    echo -e "${GREEN}💚 隧道运行正常 (已检查 $check_count 次)${NC}"
                fi
                consecutive_failures=0
            else
                # RAG 服务器本地可访问但隧道不可访问 = 隧道有问题
                consecutive_failures=$((consecutive_failures + 1))
                log "⚠️  隧道无法访问但 RAG 服务器正常 (失败次数: $consecutive_failures/$max_failures): $current_url"
                echo -e "${YELLOW}⚠️  隧道无法访问（RAG 服务器正常）(失败次数: $consecutive_failures/$max_failures)${NC}"
            fi
        fi
        
        # 如果连续失败达到阈值且满足冷却时间，重启隧道
        if [ $consecutive_failures -ge $max_failures ]; then
            log "❌ 隧道连续失败 $consecutive_failures 次"
            echo -e "${RED}❌ 隧道连续失败 $consecutive_failures 次${NC}"
            
            if should_restart; then
                log "🔄 正在重启隧道（⚠️  将生成新的 URL）..."
                echo -e "${RED}🔄 正在重启隧道（URL 会改变）...${NC}"
                stop_tunnel
                start_tunnel
                LAST_RESTART_TIME=$(date +%s)
                consecutive_failures=0
                sleep 10
            fi
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
            echo ""
            echo "环境变量配置:"
            echo "  AUTO_GIT_PUSH  - 自动 Git 推送 (true/false, 默认: true)"
            echo "  GIT_BRANCH     - Git 分支名称 (默认: main)"
            echo "  RAG_SERVER_URL - RAG 服务器地址 (默认: http://localhost:8000)"
            echo ""
            echo "示例:"
            echo "  # 禁用自动推送"
            echo "  AUTO_GIT_PUSH=false $0 monitor"
            echo ""
            echo "  # 推送到其他分支"
            echo "  GIT_BRANCH=dev $0 monitor"
            exit 1
            ;;
    esac
}

main "$@"

