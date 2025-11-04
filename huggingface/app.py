"""
Gradio 客户端 - 调用远程 RAG 服务器
这个文件可以部署到任何支持 Python 的平台（Hugging Face Spaces, Railway, Render 等）
然后在 GitHub Pages 中通过 iframe 嵌入

部署方式：
1. 部署到 Hugging Face Spaces（推荐，免费）
2. 部署到 Railway/Render（支持更多自定义）
3. 本地运行：python playground_app_client.py
"""

import gradio as gr
import requests
from typing import Dict, List
import os

# ==================== 配置 ====================

# RAG 服务器地址（部署在你的 GPU 服务器上）
RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://your-gpu-server.com:8000")

# 如果你的 GPU 服务器需要认证
API_KEY = os.getenv("RAG_API_KEY", "")

# ==================== API 调用函数 ====================

def call_rag_server(endpoint: str, data: Dict) -> Dict:
    """调用远程 RAG 服务器"""
    try:
        headers = {}
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        
        response = requests.post(
            f"{RAG_SERVER_URL}/api/{endpoint}",
            json=data,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "answer": f"❌ 连接服务器失败: {str(e)}",
            "sources": [],
            "metrics": {},
            "processing_time": 0
        }

def format_search_results(result: Dict) -> tuple:
    """格式化搜索结果"""
    answer = result.get("answer", "")
    sources = result.get("sources", [])
    metrics = result.get("metrics", {})
    reasoning_steps = result.get("reasoning_steps", [])
    processing_time = result.get("processing_time", 0)
    
    # 格式化 sources
    sources_html = "<div class='sources-container'>"
    for idx, source in enumerate(sources, 1):
        sources_html += f"""
        <div class='source-card'>
            <h4>🏪 {source.get('merchant_name', 'N/A')}</h4>
            <p>📍 {source.get('address', 'N/A')}</p>
            <p>⭐ 评分: {source.get('rating', 'N/A')}</p>
            <p>💰 {source.get('price', 'N/A')}</p>
            {f"<p>📝 {source.get('description', '')}</p>" if source.get('description') else ""}
            {f"<p>🎯 相关度: {source.get('score', source.get('rerank_score', 'N/A')):.3f}</p>" if isinstance(source.get('score') or source.get('rerank_score'), (int, float)) else ""}
        </div>
        """
    sources_html += "</div>"
    
    # 格式化 metrics
    metrics_html = "<div class='metrics-container'>"
    for key, value in metrics.items():
        if isinstance(value, float):
            if 'latency' in key.lower() or 'time' in key.lower():
                metrics_html += f"<div class='metric'>⏱️ {key}: {value:.2f} ms</div>"
            else:
                metrics_html += f"<div class='metric'>📊 {key}: {value:.3f}</div>"
        else:
            metrics_html += f"<div class='metric'>📊 {key}: {value}</div>"
    metrics_html += f"<div class='metric'>⚡ 总耗时: {processing_time:.3f}s</div>"
    metrics_html += "</div>"
    
    # 格式化 reasoning steps
    reasoning_html = ""
    if reasoning_steps:
        reasoning_html = "<div class='reasoning-container'><h3>🧠 推理过程</h3>"
        for step in reasoning_steps:
            reasoning_html += f"<div class='reasoning-step'>{step}</div>"
        reasoning_html += "</div>"
    
    return answer, sources_html, metrics_html, reasoning_html

# ==================== RAG Search ====================

def rag_search_fn(query: str, top_k: int, retriever: str, reranker: str):
    """调用 RAG 搜索"""
    if not query.strip():
        return "请输入查询内容", "", "", ""
    
    result = call_rag_server("rag/search", {
        "query": query,
        "top_k": top_k,
        "retriever": retriever,
        "reranker": reranker
    })
    
    return format_search_results(result)

# ==================== Web Search ====================

def web_search_fn(query: str, top_k: int):
    """调用 Web 搜索"""
    if not query.strip():
        return "请输入查询内容", "", "", ""
    
    result = call_rag_server("web/search", {
        "query": query,
        "top_k": top_k
    })
    
    answer, sources_html, metrics_html, _ = format_search_results(result)
    return answer, sources_html, metrics_html

# ==================== Agentic Search ====================

def agentic_search_fn(query: str, model: str):
    """调用 Agentic 搜索"""
    if not query.strip():
        return "请输入查询内容", "", "", ""
    
    result = call_rag_server("agentic/search", {
        "query": query,
        "model": model,
        "max_iterations": 5
    })
    
    return format_search_results(result)

# ==================== Gradio UI ====================

# 自定义 CSS
custom_css = """
.sources-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}

.source-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
    background: #f9f9f9;
    transition: transform 0.2s, box-shadow 0.2s;
}

.source-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.source-card h4 {
    margin: 0 0 0.5rem 0;
    color: #2c3e50;
}

.source-card p {
    margin: 0.25rem 0;
    font-size: 0.9rem;
    color: #555;
}

.metrics-container {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    margin-top: 1rem;
    padding: 1rem;
    background: #f0f7ff;
    border-radius: 8px;
}

.metric {
    padding: 0.5rem 1rem;
    background: white;
    border-radius: 6px;
    font-weight: 500;
}

.reasoning-container {
    margin-top: 1rem;
    padding: 1rem;
    background: #fff9e6;
    border-radius: 8px;
}

.reasoning-step {
    padding: 0.5rem;
    margin: 0.5rem 0;
    background: white;
    border-left: 3px solid #ffa500;
    border-radius: 4px;
}

.server-status {
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 8px;
    text-align: center;
}

.server-status.online {
    background: #d4edda;
    color: #155724;
}

.server-status.offline {
    background: #f8d7da;
    color: #721c24;
}
"""

# 创建 Gradio 界面
with gr.Blocks(title="LocalSearchBench Playground", css=custom_css, theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("""
    # 🔍 LocalSearchBench Interactive Playground
    
    **连接到远程 GPU 服务器** - 体验三种本地搜索方式
    """)
    
    # 服务器状态检查
    def check_server_status():
        try:
            response = requests.get(f"{RAG_SERVER_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                device = data.get("device", "unknown")
                gpu = "🟢 GPU" if data.get("gpu_available") else "🔵 CPU"
                return f"""
                <div class='server-status online'>
                    ✅ 服务器在线 | 设备: {gpu} ({device}) | 服务器: {RAG_SERVER_URL}
                </div>
                """
        except:
            pass
        return f"""
        <div class='server-status offline'>
            ⚠️ 无法连接到服务器: {RAG_SERVER_URL}
        </div>
        """
    
    server_status = gr.HTML(value=check_server_status())
    
    gr.Markdown("点击下面的按钮刷新服务器状态")
    refresh_btn = gr.Button("🔄 刷新服务器状态", size="sm")
    refresh_btn.click(fn=check_server_status, outputs=server_status)
    
    # 三个标签页
    with gr.Tabs():
        
        # ========== RAG Search Tab ==========
        with gr.Tab("🤖 RAG Search"):
            gr.Markdown("""
            ### 检索增强生成（RAG）
            使用语义检索 + 重排序 + LLM 生成，提供最准确的答案
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    rag_query = gr.Textbox(
                        label="输入查询",
                        placeholder="例如：浦东新区附近有什么好吃的火锅店？",
                        lines=2
                    )
                    
                    with gr.Row():
                        rag_top_k = gr.Slider(1, 20, value=5, step=1, label="返回结果数量")
                    
                    with gr.Row():
                        rag_retriever = gr.Dropdown(
                            choices=["qwen3-embedding-8b", "bge-large-zh", "text-embedding-3-small"],
                            value="qwen3-embedding-8b",
                            label="检索模型"
                        )
                        rag_reranker = gr.Dropdown(
                            choices=["qwen3-reranker-8b", "bge-reranker-large", "cohere-rerank"],
                            value="qwen3-reranker-8b",
                            label="重排序模型"
                        )
                    
                    rag_search_btn = gr.Button("🚀 搜索", variant="primary")
                    
                    # 示例查询
                    gr.Examples(
                        examples=[
                            ["浦东新区附近有什么好吃的火锅店？"],
                            ["静安区评分高的日料推荐"],
                            ["人均100元左右的网红咖啡店"]
                        ],
                        inputs=rag_query
                    )
            
            rag_answer = gr.Textbox(label="📝 生成答案", lines=3)
            rag_sources = gr.HTML(label="📚 检索来源")
            rag_metrics = gr.HTML(label="📊 评估指标")
            rag_reasoning = gr.HTML(label="🧠 推理过程")
            
            rag_search_btn.click(
                fn=rag_search_fn,
                inputs=[rag_query, rag_top_k, rag_retriever, rag_reranker],
                outputs=[rag_answer, rag_sources, rag_metrics, rag_reasoning]
            )
        
        # ========== Web Search Tab ==========
        with gr.Tab("🌐 Web Search"):
            gr.Markdown("""
            ### 传统关键词搜索
            基于 BM25 或 ElasticSearch 的经典搜索方式
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    web_query = gr.Textbox(
                        label="输入查询",
                        placeholder="例如：火锅店 浦东",
                        lines=2
                    )
                    
                    web_top_k = gr.Slider(1, 50, value=10, step=1, label="返回结果数量")
                    web_search_btn = gr.Button("🔍 搜索", variant="primary")
                    
                    gr.Examples(
                        examples=[
                            ["火锅店 浦东"],
                            ["日料 静安区"],
                            ["咖啡店 网红"]
                        ],
                        inputs=web_query
                    )
            
            web_answer = gr.Textbox(label="📝 搜索摘要", lines=2)
            web_sources = gr.HTML(label="📚 搜索结果")
            web_metrics = gr.HTML(label="📊 性能指标")
            
            web_search_btn.click(
                fn=web_search_fn,
                inputs=[web_query, web_top_k],
                outputs=[web_answer, web_sources, web_metrics]
            )
        
        # ========== Agentic Search Tab ==========
        with gr.Tab("🤖 Agentic Search"):
            gr.Markdown("""
            ### 智能体多步推理搜索
            使用 LLM Agent 进行多步推理和工具调用，解决复杂查询
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    agent_query = gr.Textbox(
                        label="输入查询",
                        placeholder="例如：找一家适合商务宴请的餐厅，要求环境好、停车方便、人均300-500元",
                        lines=3
                    )
                    
                    agent_model = gr.Dropdown(
                        choices=[
                            "gpt-4.1",
                            "gpt-4o-mini",
                            "claude-3.5-sonnet",
                            "gemini-2.5-pro",
                            "qwen-plus-latest",
                            "deepseek-v3.1"
                        ],
                        value="gpt-4.1",
                        label="LLM 模型"
                    )
                    
                    agent_search_btn = gr.Button("🧠 开始推理", variant="primary")
                    
                    gr.Examples(
                        examples=[
                            ["找一家适合商务宴请的餐厅，要求环境好、停车方便、人均300-500元"],
                            ["推荐适合情侣约会的浪漫餐厅，要靠窗位置"],
                            ["寻找评分4.5以上、有包厢、能容纳15人的聚餐场所"]
                        ],
                        inputs=agent_query
                    )
            
            agent_answer = gr.Textbox(label="📝 推理结果", lines=4)
            agent_reasoning = gr.HTML(label="🧠 推理步骤")
            agent_sources = gr.HTML(label="📚 参考来源")
            agent_metrics = gr.HTML(label="📊 评估指标")
            
            agent_search_btn.click(
                fn=agentic_search_fn,
                inputs=[agent_query, agent_model],
                outputs=[agent_answer, agent_sources, agent_metrics, agent_reasoning]
            )
    
    gr.Markdown("""
    ---
    
    ### 📖 使用说明
    
    1. **RAG Search**: 最适合需要精确答案的查询
    2. **Web Search**: 适合快速浏览多个结果
    3. **Agentic Search**: 适合复杂的、需要多步推理的查询
    
    ### 🔧 技术架构
    
    - **前端**: Gradio（可部署到 Hugging Face Spaces）
    - **后端**: FastAPI + GPU 服务器（运行模型推理）
    - **嵌入**: 通过 iframe 嵌入到 GitHub Pages
    
    ### 📊 关于服务器
    
    后端服务器地址: `{RAG_SERVER_URL}`
    
    如需修改服务器地址，请设置环境变量: `RAG_SERVER_URL=http://your-server.com:8000`
    """)

# ==================== 启动 ====================

if __name__ == "__main__":
    # 启动配置
    demo.queue(max_size=20)  # 支持并发
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # 如果需要公开链接，设为 True
        show_error=True
    )

