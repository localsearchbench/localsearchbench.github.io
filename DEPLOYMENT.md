# 🚀 LocalSearchBench 部署指南

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     用户浏览器                                │
│                                                               │
│  访问: https://your-username.github.io/localsearchbench     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ 加载静态页面
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Pages (静态托管)                      │
│                                                               │
│  • index.html (展示页面)                                      │
│  • 嵌入 iframe: Gradio 界面                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ iframe 加载
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          Hugging Face Spaces (免费托管 Gradio)                │
│                                                               │
│  • playground_app_client.py                                   │
│  • Gradio 交互界面                                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTP API 调用
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              你的 GPU 服务器 (运行 RAG 后端)                  │
│                                                               │
│  • rag_server.py (FastAPI)                                    │
│  • Qwen3-Embedding-8B (GPU 加速)                             │
│  • Qwen3-Reranker-8B (GPU 加速)                              │
│  • 向量数据库 (FAISS/Qdrant/Milvus)                          │
└─────────────────────────────────────────────────────────────┘
```

## 📋 部署步骤

### 第一步：部署 GPU 服务器后端

#### 1.1 在你的 GPU 服务器上安装依赖

```bash
# SSH 登录到你的 GPU 服务器
ssh user@your-gpu-server.com

# 创建工作目录
mkdir -p /opt/localsearch-rag
cd /opt/localsearch-rag

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r server/requirements.txt

# 如果有 GPU，安装 GPU 版本的包
pip install faiss-gpu  # 而不是 faiss-cpu
```

#### 1.2 配置环境变量

```bash
# 复制配置文件
cp server/config.env.example server/.env

# 编辑配置
nano server/.env
```

修改 `.env` 文件：

```bash
# API Keys
OPENAI_API_KEY=sk-xxx
DASHSCOPE_API_KEY=sk-xxx  # Qwen 模型

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# GPU
CUDA_VISIBLE_DEVICES=0

# Models
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
RERANKER_MODEL=Qwen/Qwen3-Reranker-8B
```

#### 1.3 测试运行

```bash
cd server
python rag_server.py --host 0.0.0.0 --port 8000
```

访问 `http://your-gpu-server.com:8000/docs` 查看 API 文档。

#### 1.4 使用 Systemd 设置开机自启（推荐）

创建服务文件 `/etc/systemd/system/localsearch-rag.service`:

```ini
[Unit]
Description=LocalSearch RAG Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/localsearch-rag/server
Environment="PATH=/opt/localsearch-rag/venv/bin"
EnvironmentFile=/opt/localsearch-rag/server/.env
ExecStart=/opt/localsearch-rag/venv/bin/python rag_server.py --host 0.0.0.0 --port 8000
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

#### 1.5 配置防火墙和 Nginx（可选但推荐）

**配置防火墙：**

```bash
# 开放端口
sudo ufw allow 8000/tcp
```

**使用 Nginx 反向代理（推荐，提供 HTTPS）：**

```nginx
# /etc/nginx/sites-available/localsearch-rag
server {
    listen 80;
    server_name rag.your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name rag.your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/rag.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rag.your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/localsearch-rag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 使用 Let's Encrypt 获取免费 SSL 证书
sudo certbot --nginx -d rag.your-domain.com
```

现在你的 RAG API 可以通过 `https://rag.your-domain.com` 访问！

### 第二步：部署 Gradio 前端到 Hugging Face Spaces

#### 2.1 创建 Hugging Face Space

1. 访问 https://huggingface.co/spaces
2. 点击 "Create new Space"
3. 填写信息：
   - **Name**: `localsearch-playground`
   - **SDK**: Gradio
   - **Hardware**: CPU Basic (免费)
4. 点击 "Create Space"

#### 2.2 准备文件

创建以下文件结构：

```
localsearch-playground/
├── app.py                    # 重命名 playground_app_client.py
├── requirements.txt          # Python 依赖
└── README.md                 # Space 说明
```

**app.py** (就是 `playground_app_client.py` 的内容):

```python
# 修改服务器地址
RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "https://rag.your-domain.com")
```

**requirements.txt**:

```
gradio>=4.0.0
requests>=2.31.0
```

**README.md**:

```markdown
---
title: LocalSearchBench Playground
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
---

# LocalSearchBench Interactive Playground

交互式本地搜索评测平台
```

#### 2.3 上传文件

**方式 1: Web 界面上传**

直接在 Hugging Face Space 页面上传文件。

**方式 2: Git 推送**

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/localsearch-playground
cd localsearch-playground

# 复制文件
cp ../playground_app_client.py app.py
cp ../requirements-gradio.txt requirements.txt

# 提交
git add .
git commit -m "Initial commit"
git push
```

#### 2.4 配置环境变量

在 Hugging Face Space 设置中添加环境变量：

- `RAG_SERVER_URL`: `https://rag.your-domain.com`
- `RAG_API_KEY`: `your-api-key` (如果需要)

#### 2.5 等待部署

Space 会自动部署，通常需要 1-2 分钟。部署完成后，你会得到一个 URL：

```
https://huggingface.co/spaces/YOUR_USERNAME/localsearch-playground
```

### 第三步：在 GitHub Pages 中嵌入 Gradio

#### 3.1 修改 index.html

在你的 `index.html` 的 Playground 部分，添加 iframe：

```html
<!-- Playground Section -->
<section id="playground" class="section">
    <div class="container">
        <h2 class="section-title">🎮 Interactive Playground</h2>
        <p class="section-description">
            体验三种本地搜索方式：RAG Search、Web Search 和 Agentic Search
        </p>
        
        <!-- Gradio iframe -->
        <div class="gradio-container" style="margin-top: 2rem;">
            <iframe 
                src="https://YOUR_USERNAME-localsearch-playground.hf.space"
                frameborder="0" 
                width="100%" 
                height="1500px"
                style="border: 2px solid #e8e8e8; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);"
                allow="clipboard-write"
            ></iframe>
        </div>
        
        <!-- 备用链接 -->
        <div style="text-align: center; margin-top: 1rem;">
            <a href="https://YOUR_USERNAME-localsearch-playground.hf.space" 
               target="_blank" 
               style="color: #667eea; text-decoration: none;">
                🔗 在新窗口中打开 Playground
            </a>
        </div>
    </div>
</section>
```

#### 3.2 添加响应式 CSS（可选）

在 `static/css/index.css` 中添加：

```css
.gradio-container {
    position: relative;
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
}

.gradio-container iframe {
    width: 100%;
    min-height: 1500px;
}

/* 移动端适配 */
@media (max-width: 768px) {
    .gradio-container iframe {
        height: 1200px;
    }
}
```

#### 3.3 推送到 GitHub

```bash
git add index.html static/css/index.css
git commit -m "Add Gradio playground"
git push origin master
```

GitHub Pages 会自动部署，几分钟后访问：

```
https://YOUR_USERNAME.github.io/localsearchbench.github.io
```

## 🎉 完整流程示例

假设你的配置：

- **GPU 服务器**: `rag.mycompany.com`
- **HF Space**: `myname-localsearch-playground`
- **GitHub Pages**: `myname.github.io/localsearchbench`

用户访问流程：

1. 用户访问 `https://myname.github.io/localsearchbench`
2. 页面加载，显示项目介绍、数据集、Leaderboard 等
3. 滚动到 Playground 部分，iframe 加载 `https://myname-localsearch-playground.hf.space`
4. 用户在 Gradio 界面输入查询，点击搜索
5. Gradio 发送请求到 `https://rag.mycompany.com/api/rag/search`
6. GPU 服务器处理请求，返回结果
7. Gradio 显示结果

## 🔒 安全建议

### 1. API 认证

在 `rag_server.py` 中添加认证：

```python
from fastapi import Header, HTTPException

API_KEY = os.getenv("API_KEY", "your-secret-key")

async def verify_api_key(authorization: str = Header(None)):
    if not authorization or authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@app.post("/api/rag/search", dependencies=[Depends(verify_api_key)])
async def rag_search(request: RAGSearchRequest):
    # ...
```

### 2. 速率限制

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/rag/search")
@limiter.limit("10/minute")  # 每分钟最多 10 次请求
async def rag_search(request: Request, ...):
    # ...
```

### 3. CORS 配置

在生产环境中，限制允许的域名：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myname.github.io",
        "https://myname-localsearch-playground.hf.space"
    ],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)
```

## 💰 成本分析

| 组件 | 平台 | 成本 |
|------|------|------|
| 静态网站 | GitHub Pages | **免费** |
| Gradio 前端 | HF Spaces (CPU Basic) | **免费** |
| RAG 后端 | 自有 GPU 服务器 | 已有设备 |
| SSL 证书 | Let's Encrypt | **免费** |
| 域名 | 域名注册商 | ~$10/年 |

**总成本**: 基本免费（除了域名）

## 📊 性能优化

### 1. 模型优化

```python
# 使用量化模型减少显存
from transformers import AutoModel, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

model = AutoModel.from_pretrained(
    "Qwen/Qwen3-Embedding-8B",
    quantization_config=quantization_config
)
```

### 2. 缓存

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str):
    # 缓存常见查询的 embedding
    return models.encode_query(text)
```

### 3. 批处理

```python
# 批量处理多个查询
def batch_encode(queries: List[str]):
    return models.embedding_model.encode(queries, batch_size=32)
```

## 🐛 故障排除

### 问题 1: iframe 不显示

**原因**: CORS 或 X-Frame-Options 限制

**解决**:

在 Gradio app 中启动时添加：

```python
demo.launch(
    allowed_paths=["*"],
    share=False
)
```

### 问题 2: API 调用超时

**原因**: GPU 服务器响应慢或网络问题

**解决**:

1. 增加超时时间：
```python
response = requests.post(..., timeout=60)  # 60 秒
```

2. 检查 GPU 服务器日志：
```bash
sudo journalctl -u localsearch-rag -f
```

### 问题 3: GPU 显存不足

**解决**:

1. 使用模型量化
2. 减少 batch size
3. 使用更小的模型
4. 使用模型流式加载：

```python
model = AutoModel.from_pretrained(
    "model-name",
    device_map="auto",  # 自动分配到多个 GPU
    torch_dtype=torch.float16  # 使用半精度
)
```

## 📚 更多资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Gradio 文档](https://gradio.app/docs)
- [HF Spaces 文档](https://huggingface.co/docs/hub/spaces)
- [GitHub Pages 文档](https://docs.github.com/pages)

## 🎯 下一步

部署完成后，你可以：

1. ✅ 替换 mock 数据为真实的 RAG 实现
2. ✅ 添加更多的检索和排序模型
3. ✅ 集成真实的向量数据库
4. ✅ 添加用户分析和日志
5. ✅ 优化界面和用户体验

祝部署顺利！🚀

