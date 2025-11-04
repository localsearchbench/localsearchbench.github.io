# LocalSearchBench 部署指南

本指南介绍如何部署 LocalSearchBench 的完整系统。

## 架构概览

```
用户浏览器
    ↓
GitHub Pages (前端静态网站)
    ↓ (API 调用)
远程 GPU 服务器 (RAG 后端)
```

## 部署步骤

### 1. 部署前端（GitHub Pages）

前端是一个静态网站，自动部署到 GitHub Pages。

**步骤：**

1. Fork 或 clone 本仓库
2. 启用 GitHub Pages（Settings → Pages → Source: main branch）
3. 访问 `https://your-username.github.io/localsearchbench.github.io`

**配置后端地址：**

编辑 `static/js/config.js`：

```javascript
const API_CONFIG = {
    baseURL: 'http://your-gpu-server.com:8000'  // 修改为您的后端地址
};
```

### 2. 部署后端（RAG 服务器）

后端需要部署到有 GPU 的服务器上。

#### 方法 1: 使用启动脚本（推荐）

```bash
# 1. SSH 登录到 GPU 服务器
ssh user@gpu-server.com

# 2. 克隆代码
git clone https://github.com/your-username/localsearchbench.github.io.git
cd localsearchbench.github.io/server

# 3. 准备数据目录（包含模型和向量索引）
# 确保有以下文件：
# - Qwen3-Embedding-8B/
# - Qwen3-Reranker-8B/
# - faiss_merchant_index_vllm_*.faiss

# 4. 启动服务
./start_rag_server.sh --data-dir /path/to/your/data --host 0.0.0.0 --port 8000
```

详细说明见 [server/README.md](server/README.md)

#### 方法 2: 使用 Docker

```bash
# 1. 准备 docker-compose.yml
cd server

# 2. 编辑 docker-compose.yml，设置数据目录
nano docker-compose.yml

# 3. 启动容器
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

#### 方法 3: 使用 Systemd（生产环境）

创建 systemd 服务文件：

```bash
sudo nano /etc/systemd/system/localsearch-rag.service
```

内容：

```ini
[Unit]
Description=LocalSearchBench RAG Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/localsearch-rag/server
Environment="PATH=/opt/localsearch-rag/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/opt/localsearch-rag/server/start_rag_server.sh --data-dir /data/rag --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable localsearch-rag
sudo systemctl start localsearch-rag
sudo systemctl status localsearch-rag
```

### 3. 配置网络和防火墙

#### 开放端口

```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

#### 配置 Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 配置 HTTPS（可选，使用 Certbot）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 验证部署

### 测试后端

```bash
# 健康检查
curl http://your-server:8000/health

# 城市列表
curl http://your-server:8000/cities

# 搜索测试
curl -X POST http://your-server:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "火锅店", "city": "shanghai", "top_k": 5}'
```

### 测试前端

1. 访问 GitHub Pages 网址
2. 在搜索框输入查询
3. 选择城市
4. 查看搜索结果

## 常见问题

### 跨域问题（CORS）

如果前端调用后端时出现 CORS 错误，确保后端已配置 CORS：

`rag_server.py` 中已包含 CORS 配置：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### GPU 内存不足

```bash
# 使用 CPU 模式
./start_rag_server.sh --cpu --data-dir /path/to/data

# 或减少 GPU 内存使用率（编辑 start_rag_server.sh）
```

### 服务自动重启

使用 systemd 服务可以确保服务崩溃后自动重启。

## 性能优化

### 1. 使用多 GPU

```bash
export CUDA_VISIBLE_DEVICES=0,1,2,3
./start_rag_server.sh --data-dir /path/to/data
```

### 2. 调整批处理大小

编辑 `rag_server.py` 中的批处理参数以优化性能。

### 3. 使用 Nginx 负载均衡

运行多个后端实例，用 Nginx 做负载均衡。

## 监控和日志

### 查看实时日志

```bash
# Systemd 服务
sudo journalctl -u localsearch-rag -f

# Docker
docker-compose logs -f
```

### GPU 监控

```bash
# 实时监控 GPU
watch -n 1 nvidia-smi
```

## 数据备份

定期备份重要文件：

```bash
# 备份向量索引
rsync -av /data/rag/ /backup/rag/

# 备份配置文件
cp server/.env server/.env.backup
```

## 更新和维护

### 更新代码

```bash
cd localsearchbench.github.io
git pull
sudo systemctl restart localsearch-rag
```

### 更新模型

1. 下载新模型到数据目录
2. 重启服务

## 相关文档

- [RAG 服务器详细说明](server/README.md)
- [模型规格说明](MODEL_SPEC.md)
- [服务集成指南](SERVER_INTEGRATION.md)

## 获取帮助

如有问题，请：
1. 查看日志输出
2. 检查 GPU 状态
3. 验证数据文件完整性
4. 提交 GitHub Issue
