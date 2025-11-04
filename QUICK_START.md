# 🚀 LocalSearchBench 快速开始指南

本指南帮助你在 5 分钟内启动 LocalSearchBench 的交互式 Playground。

## 📋 目录

1. [方案选择](#方案选择)
2. [本地开发模式](#本地开发模式)
3. [生产部署](#生产部署)
4. [连接 GitHub Pages](#连接-github-pages)

---

## 方案选择

根据你的需求选择合适的部署方案：

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **本地开发** | 测试、开发 | 快速启动、易调试 | 仅本地访问 |
| **Docker 部署** | 生产环境、云服务器 | 隔离性好、易迁移 | 需要 Docker |
| **Systemd 服务** | Linux 服务器 | 开机自启、稳定 | 仅限 Linux |
| **Hugging Face Space** | 免费演示、分享 | 免费 GPU、易分享 | 有资源限制 |

---

## 本地开发模式

### 前置条件

- Python 3.8+
- 8GB+ RAM（推荐 16GB）
- （可选）NVIDIA GPU + CUDA

### 步骤 1: 启动 RAG 后端服务器

```bash
cd server

# 一键部署（开发模式）
./deploy.sh --dev
```

这将会：
1. 创建 Python 虚拟环境
2. 安装所有依赖
3. 创建 `.env` 配置文件（如果不存在）
4. 启动开发服务器（自动重载）

### 步骤 2: 配置 API Keys

编辑 `server/.env` 文件：

```bash
# 至少配置其中一个 LLM API
OPENAI_API_KEY=your_openai_key_here
# 或
DASHSCOPE_API_KEY=your_qwen_key_here
```

保存后，服务器会自动重启。

### 步骤 3: 验证服务器运行

访问：http://localhost:8000/docs

你应该能看到 FastAPI 自动生成的 API 文档。

### 步骤 4: 启动前端页面

```bash
# 在项目根目录
python -m http.server 8080
```

访问：http://localhost:8080

### 步骤 5: 测试 RAG 搜索

1. 在 Playground 页面，选择 "RAG Search"
2. 输入查询：`浦东新区附近有什么好吃的火锅店？`
3. 点击 "Run RAG Search"

如果一切正常，你会看到：
- ✅ 检索到的文档列表
- ✅ AI 生成的回答
- ✅ 评估指标

### 常见问题

#### 问题 1: CORS 错误

如果看到跨域错误，确保 `server/rag_server.py` 中已配置 CORS：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境可以用 *
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 问题 2: 连接失败

检查：
1. RAG 服务器是否在运行（http://localhost:8000/health）
2. `static/js/config.js` 中的 URL 是否正确
3. 浏览器控制台的错误信息

#### 问题 3: 内存不足

如果 GPU 内存不足，可以：
1. 减少 `batch_size`
2. 使用 CPU 模式
3. 使用更小的模型

---

## 生产部署

### 方案 A: Docker 部署（推荐）

```bash
cd server

# 1. 配置环境变量
cp config.env.example .env
nano .env  # 编辑 API keys

# 2. 一键部署
./deploy.sh --docker

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

### 方案 B: Systemd 服务

```bash
cd server

# 1. 配置环境变量
cp config.env.example .env
nano .env

# 2. 部署（需要 root 权限）
sudo ./deploy.sh --systemd

# 3. 管理服务
sudo systemctl status localsearch-rag
sudo systemctl restart localsearch-rag
sudo journalctl -u localsearch-rag -f
```

### 配置反向代理（可选）

使用 Nginx 配置 HTTPS：

```nginx
server {
    listen 443 ssl http2;
    server_name rag.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type' always;
    }
}
```

---

## 连接 GitHub Pages

### 步骤 1: 部署后端到服务器

选择上面的任一生产部署方案，确保服务器可以通过公网访问。

### 步骤 2: 配置前端

编辑 `static/js/config.js`：

```javascript
const CONFIG = {
    // 修改为你的服务器地址
    RAG_SERVER_URL: 'https://rag.your-domain.com',
    
    // ... 其他配置保持不变
};
```

### 步骤 3: 提交并推送

```bash
git add static/js/config.js
git commit -m "Update RAG server URL"
git push origin master
```

### 步骤 4: 验证

访问你的 GitHub Pages：`https://your-username.github.io/localsearchbench.github.io`

在 Playground 中测试 RAG 搜索功能。

---

## 使用 Hugging Face Spaces（免费方案）

如果你没有 GPU 服务器，可以使用 Hugging Face Spaces 的免费 GPU：

### 步骤 1: 创建 Space

1. 访问 https://huggingface.co/spaces
2. 点击 "Create new Space"
3. 选择 SDK: **Gradio**
4. 选择硬件: **CPU basic** 或 **GPU T4 (free)**

### 步骤 2: 上传文件

将 `huggingface/` 目录下的文件上传到 Space：

```
huggingface/
├── app.py              # Gradio 应用
├── README.md           # Space 说明
└── requirements.txt    # 依赖
```

### 步骤 3: 配置环境变量

在 Space Settings 中添加：

```
OPENAI_API_KEY=your_key_here
DASHSCOPE_API_KEY=your_qwen_key_here
```

### 步骤 4: 等待构建

Hugging Face 会自动构建和部署。几分钟后你的 Playground 就可以访问了！

### 步骤 5: 嵌入到 GitHub Pages

在 `index.html` 中添加 iframe：

```html
<iframe
  src="https://your-username-space-name.hf.space"
  frameborder="0"
  width="100%"
  height="800"
></iframe>
```

---

## 🎯 下一步

- 📖 阅读 [API 文档](http://localhost:8000/docs)
- 🔧 查看 [配置选项](server/config.env.example)
- 📊 了解 [评估指标](EVALUATION.md)
- 🐛 遇到问题？查看 [故障排查指南](TROUBLESHOOTING.md)

---

## 💡 提示

### 性能优化

1. **使用 GPU**: 显著提升推理速度
2. **批量处理**: 设置合适的 `batch_size`
3. **模型缓存**: 首次加载较慢，后续会快很多
4. **索引预构建**: 提前构建 FAISS 索引

### 成本控制

1. **使用开源模型**: Qwen、LLaMA 等免费
2. **API 限流**: 设置 rate limiting
3. **结果缓存**: 相同查询返回缓存结果
4. **混合方案**: 检索用本地模型，生成用 API

### 安全建议

1. **API 认证**: 生产环境启用 API Key
2. **HTTPS**: 使用 SSL/TLS 加密
3. **Rate Limiting**: 防止滥用
4. **输入验证**: 防止注入攻击

---

## 📞 需要帮助？

- 💬 GitHub Issues: [提交问题](https://github.com/your-username/localsearchbench.github.io/issues)
- 📧 Email: your-email@example.com
- 🐦 Twitter: @your_handle

---

**祝你使用愉快！🎉**

