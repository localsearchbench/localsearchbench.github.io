#!/bin/bash

# 自动提交和推送配置文件更新到 GitHub
# 当隧道 URL 更新时，自动将 tunnel_config.json 推送到 GitHub Pages

CONFIG_FILE="tunnel_config.json"
COMMIT_INTERVAL=60  # 每60秒检查一次是否有更新需要提交

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# 检查是否有未提交的更改
has_changes() {
    git diff --quiet "$CONFIG_FILE"
    return $?
}

# 提交并推送更改
commit_and_push() {
    local url=$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' "$CONFIG_FILE" | head -1)
    
    if [ -z "$url" ]; then
        log "${RED}❌ 无法从配置文件中提取 URL${NC}"
        return 1
    fi
    
    log "${YELLOW}📝 检测到配置更新，准备提交...${NC}"
    
    # 添加文件到暂存区
    git add "$CONFIG_FILE"
    
    # 提交更改
    local commit_msg="Auto-update tunnel URL: $url"
    git commit -m "$commit_msg" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        log "${GREEN}✅ 已提交: $commit_msg${NC}"
        
        # 推送到远程仓库
        log "${YELLOW}🚀 正在推送到 GitHub...${NC}"
        git push origin master > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            log "${GREEN}✅ 已成功推送到 GitHub Pages${NC}"
            log "${GREEN}🌐 网站将在 1-3 分钟内更新${NC}"
            return 0
        else
            log "${RED}❌ 推送失败，请检查网络连接和 Git 权限${NC}"
            return 1
        fi
    else
        log "${YELLOW}⚠️  没有新的更改需要提交${NC}"
        return 1
    fi
}

# 主监控循环
monitor_and_commit() {
    log "${GREEN}=========================================${NC}"
    log "${GREEN}🔍 开始监控配置文件更新${NC}"
    log "${GREEN}文件: $CONFIG_FILE${NC}"
    log "${GREEN}检查间隔: ${COMMIT_INTERVAL}秒${NC}"
    log "${GREEN}=========================================${NC}"
    
    local last_commit_time=0
    
    while true; do
        # 检查文件是否存在
        if [ ! -f "$CONFIG_FILE" ]; then
            log "${YELLOW}⚠️  配置文件不存在，等待创建...${NC}"
            sleep $COMMIT_INTERVAL
            continue
        fi
        
        # 检查是否有未提交的更改
        if has_changes; then
            local current_time=$(date +%s)
            local time_since_last_commit=$((current_time - last_commit_time))
            
            # 避免频繁提交，至少间隔 30 秒
            if [ $time_since_last_commit -ge 30 ]; then
                commit_and_push
                if [ $? -eq 0 ]; then
                    last_commit_time=$current_time
                fi
            else
                log "${YELLOW}⏳ 距离上次提交时间太短，等待中...${NC}"
            fi
        fi
        
        sleep $COMMIT_INTERVAL
    done
}

# 信号处理
cleanup() {
    log "${YELLOW}=========================================${NC}"
    log "${YELLOW}🛑 收到停止信号，退出监控${NC}"
    log "${YELLOW}=========================================${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 主函数
main() {
    case "${1:-monitor}" in
        commit)
            # 立即提交一次
            if has_changes; then
                commit_and_push
            else
                log "${GREEN}✅ 配置文件没有更改${NC}"
            fi
            ;;
        monitor)
            # 持续监控
            monitor_and_commit
            ;;
        *)
            echo "用法: $0 {commit|monitor}"
            echo ""
            echo "命令说明:"
            echo "  commit  - 立即提交当前更改"
            echo "  monitor - 持续监控并自动提交（默认）"
            exit 1
            ;;
    esac
}

main "$@"

