#!/usr/bin/env python3
"""
LocalSearchBench Playground - Gradio Interface
A web interface for testing Web Search, RAG Search, and Agentic Search methods.
"""

import gradio as gr
import json
from typing import List, Dict, Tuple, Optional

# Mock data for demonstration - replace with actual implementation
def mock_web_search(query: str, top_k: int = 10) -> Tuple[str, str]:
    """Perform traditional keyword-based search."""
    results_html = f"""
    <div style="padding: 1rem; background: #f5f5f5; border-radius: 8px;">
        <h4>Search Results for: "{query}"</h4>
        <p><em>Top {top_k} results</em></p>
        <ol>
            <li><strong>Haidilao Hotpot (Wudaokou)</strong> - ⭐ 4.5/5 - Open until 2 AM</li>
            <li><strong>Xiabu Xiabu</strong> - ⭐ 4.2/5 - Parking available</li>
            <li><strong>Dezhuang Hotpot</strong> - ⭐ 4.6/5 - Near subway station</li>
        </ol>
    </div>
    """
    metrics = "📊 Results: 3 found | ⏱️ Latency: 0.12s"
    return results_html, metrics


def mock_rag_search(query: str, top_k: int = 20, retriever: str = "Qwen3-Embedding-8B", 
                   reranker: str = "Qwen3-Reranker-8B") -> Tuple[str, str, str]:
    """Perform RAG-based search with retrieval and reranking."""
    retrieved_docs = f"""
    <div style="padding: 1rem; background: #e8f4f8; border-radius: 8px;">
        <h4>Retrieved Documents (Top {top_k})</h4>
        <p><em>Using {retriever} for retrieval and {reranker} for reranking</em></p>
        <div style="margin-top: 0.5rem;">
            <div style="background: white; padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid #3273dc;">
                <strong>Doc 1:</strong> Haidilao Hotpot (Wudaokou Branch) - Famous chain restaurant known for excellent service...
            </div>
            <div style="background: white; padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid #3273dc;">
                <strong>Doc 2:</strong> Located near Line 13 Wudaokou Station, offers late-night dining...
            </div>
            <div style="background: white; padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid #3273dc;">
                <strong>Doc 3:</strong> Parking available in basement, reservations recommended on weekends...
            </div>
        </div>
    </div>
    """
    
    answer = """
    <div style="padding: 1rem; background: #e8f5e9; border-radius: 8px;">
        <h4>Generated Answer</h4>
        <p>Based on your requirements, I recommend <strong>Haidilao Hotpot (Wudaokou Branch)</strong>. It's a highly-rated restaurant 
        (4.5/5 stars) located near Wudaokou subway station. The restaurant is open until 2 AM, making it perfect for late-night dining. 
        They also offer parking in the basement. The service is exceptional, and they're known for complimentary snacks and entertainment 
        while you wait.</p>
    </div>
    """
    
    metrics = """
    📊 Precision@10: 0.85 | Recall@10: 0.72 | NDCG@10: 0.79
    ⏱️ Retrieval: 0.23s | Reranking: 0.15s | Generation: 1.2s | Total: 1.58s
    """
    
    return retrieved_docs, answer, metrics


def mock_agentic_search(query: str, model: str = "deepseek-v3.1") -> Tuple[str, str, str]:
    """Perform agentic search with LLM-powered reasoning."""
    process = f"""
    <div style="padding: 1rem; background: #fff3e0; border-radius: 8px;">
        <h4>Search Process (Using {model})</h4>
        <div style="margin-top: 0.5rem;">
            <div style="background: white; padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid #ff9800;">
                <strong>Step 1:</strong> 🤔 Analyzing query components: location=Wudaokou, cuisine=hotpot, requirements=[late hours, parking]
            </div>
            <div style="background: white; padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid #ff9800;">
                <strong>Step 2:</strong> 🔍 Searching database for hotpot restaurants in Wudaokou area...
            </div>
            <div style="background: white; padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid #ff9800;">
                <strong>Step 3:</strong> 🏪 Filtering results: checking operating hours and parking availability...
            </div>
            <div style="background: white; padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid #ff9800;">
                <strong>Step 4:</strong> ⭐ Ranking by user ratings and relevance scores...
            </div>
            <div style="background: white; padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid #ff9800;">
                <strong>Step 5:</strong> 📝 Generating comprehensive recommendation...
            </div>
        </div>
    </div>
    """
    
    answer = """
    <div style="padding: 1rem; background: #f3e5f5; border-radius: 8px;">
        <h4>Final Answer</h4>
        <p><strong>Top Recommendation: Haidilao Hotpot (Wudaokou Branch)</strong></p>
        <ul>
            <li>📍 Location: 5 minutes walk from Wudaokou Station (Line 13)</li>
            <li>⭐ Rating: 4.5/5 (2,348 reviews)</li>
            <li>🕐 Hours: 10:00 AM - 2:00 AM</li>
            <li>🅿️ Parking: Available (Underground, ¥10/hour)</li>
            <li>💰 Average cost: ¥80-120 per person</li>
            <li>📞 Phone: 010-8888-8888</li>
        </ul>
        <p><em>Alternative options: Xiabu Xiabu (budget-friendly) and Dezhuang Hotpot (authentic Sichuan flavor)</em></p>
    </div>
    """
    
    metrics = """
    📊 Accuracy: 0.92 | Relevance: 0.88 | Completeness: 0.85
    ⏱️ Planning: 0.8s | Tool Calls: 3 (2.1s) | Reasoning: 1.5s | Total: 4.4s
    🤖 Agent Steps: 5 | Tools Used: search_db, filter_results, rank_by_rating
    """
    
    return process, answer, metrics


# Build the Gradio interface
def create_interface():
    with gr.Blocks(title="LocalSearchBench Playground", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🔍 LocalSearchBench Playground
            
            Test different search methods for local life services. Compare **Web Search**, **RAG Search**, and **Agentic Search** approaches.
            """
        )
        
        with gr.Tabs() as tabs:
            # RAG Search Tab
            with gr.Tab("RAG Search", id="rag"):
                gr.Markdown("**RAG Search** combines retrieval and generation for accurate, context-aware responses.")
                
                with gr.Row():
                    rag_query = gr.Textbox(
                        label="Query",
                        placeholder="e.g., I want to find a highly-rated hotpot restaurant near Wudaokou that's open late and has parking...",
                        lines=3
                    )
                
                with gr.Row():
                    rag_topk = gr.Number(label="Top-K Results", value=20, interactive=False)
                    rag_retriever = gr.Textbox(label="Retrieval Model", value="Qwen3-Embedding-8B", interactive=False)
                    rag_reranker = gr.Textbox(label="Reranker Model", value="Qwen3-Reranker-8B", interactive=False)
                
                rag_button = gr.Button("🚀 Run RAG Search", variant="primary", size="lg")
                
                with gr.Column(visible=False) as rag_results:
                    gr.Markdown("### 📚 Retrieved Documents")
                    rag_docs_output = gr.HTML()
                    
                    gr.Markdown("### 💡 Generated Answer")
                    rag_answer_output = gr.HTML()
                    
                    gr.Markdown("### 📊 Evaluation Metrics")
                    rag_metrics_output = gr.Textbox(interactive=False, show_label=False)
                
                def run_rag(query, topk, retriever, reranker):
                    docs, answer, metrics = mock_rag_search(query, int(topk), retriever, reranker)
                    return {
                        rag_results: gr.Column(visible=True),
                        rag_docs_output: docs,
                        rag_answer_output: answer,
                        rag_metrics_output: metrics
                    }
                
                rag_button.click(
                    fn=run_rag,
                    inputs=[rag_query, rag_topk, rag_retriever, rag_reranker],
                    outputs=[rag_results, rag_docs_output, rag_answer_output, rag_metrics_output]
                )
            
            # Web Search Tab
            with gr.Tab("Web Search", id="web"):
                gr.Markdown("**Web Search** performs traditional keyword-based search across local merchants and products.")
                
                web_query = gr.Textbox(
                    label="Query",
                    placeholder="e.g., hotpot restaurant in Wudaokou",
                    lines=3
                )
                web_topk = gr.Slider(label="Top-K Results", minimum=1, maximum=50, value=10, step=1)
                web_button = gr.Button("🌐 Run Web Search", variant="primary", size="lg")
                
                with gr.Column(visible=False) as web_results:
                    gr.Markdown("### 🔍 Search Results")
                    web_output = gr.HTML()
                    web_metrics_output = gr.Textbox(interactive=False, show_label=False)
                
                def run_web(query, topk):
                    results, metrics = mock_web_search(query, topk)
                    return {
                        web_results: gr.Column(visible=True),
                        web_output: results,
                        web_metrics_output: metrics
                    }
                
                web_button.click(
                    fn=run_web,
                    inputs=[web_query, web_topk],
                    outputs=[web_results, web_output, web_metrics_output]
                )
            
            # Agentic Search Tab
            with gr.Tab("Agentic Search", id="agentic"):
                gr.Markdown("**Agentic Search** uses LLM-powered agents to perform multi-step reasoning and tool use.")
                
                agentic_query = gr.Textbox(
                    label="Query",
                    placeholder="Enter your search query...",
                    lines=3
                )
                
                agentic_model = gr.Dropdown(
                    label="LLM Model",
                    choices=[
                        ("🟢 GPT-4.1", "gpt-4.1"),
                        ("🔵 Gemini-2.5-Pro", "gemini-2.5-pro"),
                        ("🔮 Qwen-Plus-Latest", "qwen-plus-latest"),
                        ("🟢 LongCat-Large-32K", "longcat-large-32k"),
                        ("Hunyuan-T1", "hunyuan-t1"),
                        ("🔮 Qwen3-235B-A22B", "qwen3-235b-a22b"),
                        ("🔮 Qwen3-32B", "qwen3-32b"),
                        ("🔮 Qwen3-14B", "qwen3-14b"),
                        ("🔵 GLM-4.5", "glm-4.5"),
                        ("🔷 Deepseek-V3.1", "deepseek-v3.1"),
                    ],
                    value="deepseek-v3.1"
                )
                
                agentic_button = gr.Button("🤖 Run Agentic Search", variant="primary", size="lg")
                
                with gr.Column(visible=False) as agentic_results:
                    gr.Markdown("### 🔄 Search Process")
                    agentic_process_output = gr.HTML()
                    
                    gr.Markdown("### ✨ Final Answer")
                    agentic_answer_output = gr.HTML()
                    
                    gr.Markdown("### 📊 Evaluation Metrics")
                    agentic_metrics_output = gr.Textbox(interactive=False, show_label=False)
                
                def run_agentic(query, model):
                    process, answer, metrics = mock_agentic_search(query, model)
                    return {
                        agentic_results: gr.Column(visible=True),
                        agentic_process_output: process,
                        agentic_answer_output: answer,
                        agentic_metrics_output: metrics
                    }
                
                agentic_button.click(
                    fn=run_agentic,
                    inputs=[agentic_query, agentic_model],
                    outputs=[agentic_results, agentic_process_output, agentic_answer_output, agentic_metrics_output]
                )
        
        # Example queries
        gr.Markdown("### 💡 Example Queries")
        with gr.Row():
            example1 = gr.Button("🍲 Restaurant Search", size="sm")
            example2 = gr.Button("🏨 Hotel Booking", size="sm")
            example3 = gr.Button("💇 Salon Services", size="sm")
        
        example_query_1 = "Find a highly-rated hotpot restaurant near Wudaokou that's open late and has parking"
        example_query_2 = "I need a hotel near Beijing Airport, budget around 500 RMB, with good breakfast"
        example_query_3 = "Looking for a hair salon in Sanlitun area that specializes in women's haircuts, preferably with English-speaking staff"
        
        # Load examples into all query boxes
        example1.click(lambda: example_query_1, outputs=[rag_query, web_query, agentic_query])
        example2.click(lambda: example_query_2, outputs=[rag_query, web_query, agentic_query])
        example3.click(lambda: example_query_3, outputs=[rag_query, web_query, agentic_query])
        
        gr.Markdown(
            """
            ---
            
            ### About This Playground
            
            This interface allows you to compare three different search approaches:
            
            - **Web Search**: Traditional keyword matching and ranking
            - **RAG Search**: Retrieval-Augmented Generation with embedding models
            - **Agentic Search**: LLM-powered multi-step reasoning with tool use
            
            For the full benchmark results and paper, visit [LocalSearchBench](https://localsearchbench.github.io)
            """
        )
    
    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

