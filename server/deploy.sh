#!/bin/bash

# LocalSearchBench RAG Server 一键部署脚本
# 使用方式: ./deploy.sh [--docker | --systemd | --dev]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 GPU
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        print_info "检测到 NVIDIA GPU:"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
        return 0
    else
        print_warn "未检测到 NVIDIA GPU，将使用 CPU 模式"
        return 1
    fi
}

# Docker 部署
deploy_docker() {
    print_info "开始 Docker 部署..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装"
        exit 1
    fi
    
    # 检查环境变量文件
    if [ ! -f ".env" ]; then
        print_warn ".env 文件不存在，从示例创建..."
        cp config.env.example .env
        print_warn "请编辑 .env 文件配置 API Keys"
        exit 1
    fi
    
    # 构建和启动
    print_info "构建 Docker 镜像..."
    docker-compose build
    
    print_info "启动服务..."
    docker-compose up -d
    
    print_info "等待服务启动..."
    sleep 5
    
    # 检查健康状态
    if docker-compose ps | grep -q "Up"; then
        print_info "✅ 服务启动成功！"
        print_info "API 文档: http://localhost:8000/docs"
        print_info "查看日志: docker-compose logs -f"
    else
        print_error "服务启动失败，查看日志:"
        docker-compose logs
        exit 1
    fi
}

# Systemd 部署
deploy_systemd() {
    print_info "开始 Systemd 部署..."
    
    # 检查权限
    if [ "$EUID" -ne 0 ]; then
        print_error "需要 root 权限来配置 systemd 服务"
        print_info "请使用: sudo ./deploy.sh --systemd"
        exit 1
    fi
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 安装目录
    INSTALL_DIR="/opt/localsearch-rag"
    
    print_info "创建安装目录: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    
    # 复制文件
    print_info "复制文件..."
    cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
    
    # 创建虚拟环境
    print_info "创建 Python 虚拟环境..."
    cd "$INSTALL_DIR"
    python3 -m venv venv
    
    # 安装依赖
    print_info "安装依赖..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 检查并安装 GPU 支持
    if check_gpu; then
        print_info "安装 GPU 版本的 FAISS..."
        pip install faiss-gpu
    else
        print_info "安装 CPU 版本的 FAISS..."
        pip install faiss-cpu
    fi
    
    # 创建环境变量文件
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        cp "$INSTALL_DIR/config.env.example" "$INSTALL_DIR/.env"
        print_warn "请编辑 $INSTALL_DIR/.env 配置 API Keys"
    fi
    
    # 创建 systemd 服务
    print_info "创建 systemd 服务..."
    cat > /etc/systemd/system/localsearch-rag.service <<EOF
[Unit]
Description=LocalSearch RAG Server
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python rag_server.py --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 启动服务
    print_info "启动服务..."
    systemctl daemon-reload
    systemctl enable localsearch-rag
    systemctl start localsearch-rag
    
    # 检查状态
    sleep 3
    if systemctl is-active --quiet localsearch-rag; then
        print_info "✅ 服务启动成功！"
        print_info "状态: systemctl status localsearch-rag"
        print_info "日志: journalctl -u localsearch-rag -f"
        print_info "API 文档: http://localhost:8000/docs"
    else
        print_error "服务启动失败，查看日志:"
        journalctl -u localsearch-rag -n 50
        exit 1
    fi
}

# 开发模式
deploy_dev() {
    print_info "开始开发模式部署..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    print_info "激活虚拟环境..."
    source venv/bin/activate
    
    # 安装依赖
    print_info "安装依赖..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 检查 GPU
    if check_gpu; then
        pip install faiss-gpu
    else
        pip install faiss-cpu
    fi
    
    # 创建环境变量文件
    if [ ! -f ".env" ]; then
        cp config.env.example .env
        print_warn "已创建 .env 文件，请配置 API Keys"
    fi
    
    # 启动开发服务器
    print_info "启动开发服务器..."
    print_info "使用 --reload 模式，代码修改会自动重启"
    python rag_server.py --host 0.0.0.0 --port 8000 --reload
}

# 显示帮助
show_help() {
    cat <<EOF
LocalSearchBench RAG Server 部署脚本

使用方式:
    ./deploy.sh [选项]

选项:
    --docker        使用 Docker 部署（推荐用于生产环境）
    --systemd       使用 Systemd 部署（需要 root 权限）
    --dev           开发模式（自动重载）
    --help          显示此帮助信息

示例:
    # 开发模式
    ./deploy.sh --dev

    # Docker 部署
    ./deploy.sh --docker

    # Systemd 部署
    sudo ./deploy.sh --systemd

更多信息请查看 DEPLOYMENT.md
EOF
}

# 主逻辑
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════╗"
    echo "║   LocalSearchBench RAG Server 部署工具        ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    
    check_gpu
    echo ""
    
    case "${1:-}" in
        --docker)
            deploy_docker
            ;;
        --systemd)
            deploy_systemd
            ;;
        --dev)
            deploy_dev
            ;;
        --help)
            show_help
            ;;
        *)
            print_warn "未指定部署方式"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

