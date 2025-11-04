# LocalSearchBench - Gradio Playground Integration

这个文档说明如何将现有的 Web/RAG/Agentic Search 部分改成 Gradio 界面。

## 📋 目录

- [快速开始](#快速开始)
- [功能特性](#功能特性)
- [集成方式](#集成方式)
- [部署选项](#部署选项)
- [自定义开发](#自定义开发)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements-gradio.txt
```

或者直接安装 Gradio：

```bash
pip install gradio
```

### 2. 启动 Gradio 界面

**方式一：使用启动脚本**
```bash
./run_gradio.sh
```

**方式二：直接运行 Python**
```bash
python playground_app.py
```

启动后，访问 `http://localhost:7860` 即可看到 Gradio 界面。

### 3. 查看效果

Gradio 界面提供了三个标签页：
- **RAG Search**: 检索增强生成搜索
- **Web Search**: 传统网页搜索
- **Agentic Search**: 智能体多步推理搜索

## ✨ 功能特性

### RAG Search
- 📚 使用 Qwen3-Embedding-8B 进行语义检索
- 🔄 使用 Qwen3-Reranker-8B 重排序
- 💡 生成自然语言答案
- 📊 显示评估指标（Precision、Recall、NDCG）

### Web Search
- 🌐 传统关键词搜索
- 🎚️ 可调节 Top-K 结果数量
- ⚡ 快速响应

### Agentic Search
- 🤖 支持多个 LLM 模型：
  - GPT-4.1
  - Gemini-2.5-Pro
  - Qwen-Plus-Latest
  - LongCat-Large-32K
  - Deepseek-V3.1
  - 等等...
- 🔄 显示推理过程
- 🛠️ 展示工具调用步骤
- 📊 完整的评估指标

### 示例查询
- 🍲 餐厅搜索
- 🏨 酒店预订
- 💇 美发服务

## 🔗 集成方式

### 方式一：iframe 嵌入（推荐，最简单）

在你的 `index.html` 中替换 Playground 部分：

```html
<!-- 在 Playground Section 中添加 -->
<div class="gradio-wrapper" style="margin-top: 2rem;">
  <iframe 
    src="http://localhost:7860" 
    frameborder="0" 
    width="100%" 
    height="1400px"
    style="border: 2px solid #e8e8e8; border-radius: 12px;"
  ></iframe>
</div>
```

### 方式二：Gradio Web Component

1. 在 `<head>` 中添加 Gradio 脚本：
```html
<script type="module" src="https://gradio.s3-us-west-2.amazonaws.com/4.0.0/gradio.js"></script>
```

2. 在 Playground 部分使用 Web Component：
```html
<gradio-app src="http://localhost:7860"></gradio-app>
```

### 方式三：使用示例文件

我已经创建了一个示例文件 `index_with_gradio.html`，你可以：

1. 备份原始 `index.html`
2. 查看 `index_with_gradio.html` 了解集成方式
3. 将相关代码复制到你的 `index.html` 中

## 🌐 部署选项

### 本地开发

```bash
python playground_app.py
```

访问 `http://localhost:7860`

### 生成公开分享链接

修改 `playground_app.py` 最后一行：

```python
demo.launch(share=True)  # 会生成一个公开的 gradio.app 链接
```

### 部署到 Hugging Face Spaces（免费托管）

1. 访问 [Hugging Face Spaces](https://huggingface.co/spaces)
2. 创建新 Space，选择 Gradio 类型
3. 上传文件：
   - `playground_app.py` → 重命名为 `app.py`
   - `requirements-gradio.txt` → 重命名为 `requirements.txt`
4. Space 会自动部署

部署后，在你的网页中使用：

```html
<iframe 
  src="https://huggingface.co/spaces/YOUR_USERNAME/localsearchbench-playground" 
  width="100%" 
  height="1400px"
></iframe>
```

### Docker 部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY playground_app.py requirements-gradio.txt ./
RUN pip install -r requirements-gradio.txt
EXPOSE 7860
CMD ["python", "playground_app.py"]
```

构建和运行：

```bash
docker build -t localsearch-gradio .
docker run -p 7860:7860 localsearch-gradio
```

## 🛠️ 自定义开发

### 替换 Mock 数据为真实后端

在 `playground_app.py` 中，替换 `mock_*` 函数：

```python
def mock_rag_search(query, top_k, retriever, reranker):
    # 替换为你的真实实现
    from your_backend import rag_search
    
    results = rag_search(
        query=query,
        top_k=top_k,
        retriever=retriever,
        reranker=reranker
    )
    
    return format_results(results)
```

### 添加 API 集成

如果你有后端 API：

```python
import requests

def call_rag_api(query, top_k, retriever, reranker):
    response = requests.post(
        "https://your-api.com/rag/search",
        json={
            "query": query,
            "top_k": top_k,
            "retriever": retriever,
            "reranker": reranker
        }
    )
    return response.json()
```

### 自定义主题

```python
# 使用内置主题
demo = gr.Blocks(theme=gr.themes.Soft())  # Soft, Base, Glass, Monochrome

# 或自定义 CSS
with gr.Blocks(css="""
    .gradio-container {
        max-width: 1400px !important;
        font-family: 'Segoe UI', sans-serif;
    }
    .gr-button-primary {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%) !important;
    }
""") as demo:
    # ...界面代码...
```

### 添加认证

```python
demo.launch(
    auth=("admin", "password123"),  # 简单认证
    # 或使用函数
    # auth=lambda u, p: u == "admin" and p == "secret"
)
```

### 启用队列（支持多用户）

```python
demo.queue(max_size=20)  # 最多20个并发请求
demo.launch()
```

## 📊 对比：原 HTML vs Gradio

| 特性 | 原 HTML/JS 实现 | Gradio 实现 |
|------|----------------|-------------|
| 开发速度 | 需要写 HTML/CSS/JS | 几行 Python 代码 |
| 维护成本 | 高（三种语言） | 低（纯 Python） |
| 响应式设计 | 需手动实现 | 自动适配移动端 |
| 部署难度 | 需要配置服务器 | 一键部署到 HF Spaces |
| API 集成 | 需要 AJAX/Fetch | 直接 Python 调用 |
| 样式自定义 | 完全自由 | 主题+CSS 自定义 |
| 多用户支持 | 需要额外处理 | 内置队列系统 |
| 分享链接 | 需要部署 | `share=True` 即可 |

## 🎯 推荐使用场景

**使用原 HTML 界面：**
- 需要完全自定义的设计
- 与现有网站深度集成
- 纯前端展示，无后端逻辑

**使用 Gradio 界面：**
- 快速原型开发
- 需要频繁迭代
- 有 Python 后端
- 需要快速部署和分享
- 多人协作测试

## 💡 最佳实践

1. **开发阶段**：使用 Gradio 快速迭代
2. **展示阶段**：可以保留两个版本
   - Gradio 版本用于内部测试和快速演示
   - HTML 版本用于网站展示
3. **生产部署**：
   - 将 Gradio 部署到 HF Spaces（免费）
   - 在主网站用 iframe 嵌入
   - 这样可以分离前端展示和后端逻辑

## 🔧 故障排除

### 端口被占用
```python
demo.launch(server_port=7861)  # 使用其他端口
```

### CORS 问题
```python
demo.launch(
    server_name="0.0.0.0",
    allowed_paths=["*"]
)
```

### iframe 不显示
检查浏览器控制台的错误信息，可能是：
- Gradio 服务未启动
- 端口不匹配
- CORS 策略限制

### 性能优化
```python
# 启用缓存
@gr.cache_examples
def process_query(query):
    # ...

# 异步处理
demo.queue()
```

## 📚 更多资源

- [Gradio 官方文档](https://gradio.app/docs)
- [Gradio GitHub](https://github.com/gradio-app/gradio)
- [Hugging Face Spaces 文档](https://huggingface.co/docs/hub/spaces)
- [示例 Spaces](https://huggingface.co/spaces)

## 📝 文件说明

项目中新增的文件：

- `playground_app.py` - Gradio 应用主程序
- `requirements-gradio.txt` - Python 依赖
- `run_gradio.sh` - 启动脚本
- `GRADIO_SETUP.md` - 详细设置文档
- `README_GRADIO.md` - 本文档
- `index_with_gradio.html` - 集成示例

## 🎉 总结

使用 Gradio 可以让你：
1. ✅ 用 Python 快速构建交互界面
2. ✅ 轻松集成机器学习模型和 API
3. ✅ 一键部署和分享
4. ✅ 自动适配移动端
5. ✅ 内置队列和并发处理

现在就试试吧！

```bash
./run_gradio.sh
```

然后访问 `http://localhost:7860` 🎊

