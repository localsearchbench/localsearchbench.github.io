"""
RAG Server - 部署在有 GPU 的服务器上
支持 Web Search、RAG Search 和 Agentic Search

运行方式：
    python rag_server.py --port 8000 --host 0.0.0.0

环境变量配置：
    export OPENAI_API_KEY="your-key"
    export DASHSCOPE_API_KEY="your-key"  # 如果使用 Qwen 模型
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uvicorn
import argparse
import os
import time
from datetime import datetime

# 如果使用 GPU 加载模型
try:
    import torch
    from sentence_transformers import SentenceTransformer
    # from transformers import AutoTokenizer, AutoModel
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🚀 Using device: {DEVICE}")
except ImportError:
    DEVICE = "cpu"
    print("⚠️ PyTorch not found, using CPU mode")

app = FastAPI(
    title="LocalSearchBench RAG API",
    description="RAG Search API with GPU support",
    version="1.0.0"
)

# 配置 CORS - 允许 Gradio 客户端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================

class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    retriever: str = "qwen3-embedding-8b"
    reranker: str = "qwen3-reranker-8b"

class WebSearchRequest(BaseModel):
    query: str
    top_k: int = 10

class AgenticSearchRequest(BaseModel):
    query: str
    model: str = "gpt-4.1"
    max_iterations: int = 5

class SearchResult(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    metrics: Dict[str, float]
    reasoning_steps: Optional[List[str]] = None
    processing_time: float

# ==================== 模型加载（GPU）====================

class RAGModels:
    """在服务器启动时加载模型到 GPU"""
    
    def __init__(self):
        self.embedding_model = None
        self.reranker_model = None
        self.llm = None
        
    def load_embedding_model(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """加载 Embedding 模型到 GPU"""
        if self.embedding_model is None:
            print(f"📥 Loading embedding model: {model_name}")
            # 这里使用 sentence-transformers 作为示例
            # 你可以替换为 Qwen3-Embedding-8B 或其他模型
            try:
                self.embedding_model = SentenceTransformer(model_name, device=DEVICE)
                print(f"✅ Embedding model loaded on {DEVICE}")
            except Exception as e:
                print(f"❌ Failed to load embedding model: {e}")
                self.embedding_model = None
        return self.embedding_model
    
    def load_reranker_model(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """加载 Reranker 模型到 GPU"""
        if self.reranker_model is None:
            print(f"📥 Loading reranker model: {model_name}")
            try:
                from sentence_transformers import CrossEncoder
                self.reranker_model = CrossEncoder(model_name, device=DEVICE)
                print(f"✅ Reranker model loaded on {DEVICE}")
            except Exception as e:
                print(f"❌ Failed to load reranker model: {e}")
                self.reranker_model = None
        return self.reranker_model
    
    def encode_query(self, query: str):
        """使用 GPU 进行查询编码"""
        if self.embedding_model is None:
            self.load_embedding_model()
        
        if self.embedding_model:
            with torch.no_grad():
                embedding = self.embedding_model.encode(query, convert_to_tensor=True)
            return embedding.cpu().numpy()
        else:
            # Fallback: 使用简单的方法
            return None

# 全局模型实例
models = RAGModels()

# ==================== RAG 实现 ====================

def perform_rag_search(query: str, top_k: int, retriever: str, reranker: str) -> Dict:
    """
    真实的 RAG 搜索实现
    
    替换这个函数为你的实际实现，例如：
    - 使用 Qwen3-Embedding-8B 进行检索
    - 使用 Qwen3-Reranker-8B 进行重排序
    - 调用 LLM 生成答案
    """
    start_time = time.time()
    
    # 1. 使用 GPU 进行向量检索
    query_embedding = models.encode_query(query)
    
    # 2. 从向量数据库检索（这里需要你的实现）
    # 例如：使用 FAISS, Milvus, Qdrant 等
    retrieved_docs = [
        {
            "merchant_name": "海底捞火锅(陆家嘴店)",
            "address": "上海市浦东新区陆家嘴世纪大道100号",
            "rating": 4.8,
            "price": "人均150元",
            "description": "知名火锅品牌，服务好，食材新鲜",
            "score": 0.92
        },
        {
            "merchant_name": "小辉哥火锅(南京西路店)", 
            "address": "上海市静安区南京西路1618号",
            "rating": 4.6,
            "price": "人均120元",
            "description": "潮汕牛肉火锅，肉质鲜美",
            "score": 0.88
        }
    ]
    
    # 3. 使用 GPU 进行重排序
    if models.reranker_model:
        pairs = [[query, doc["description"]] for doc in retrieved_docs]
        rerank_scores = models.reranker_model.predict(pairs)
        for doc, score in zip(retrieved_docs, rerank_scores):
            doc["rerank_score"] = float(score)
        retrieved_docs = sorted(retrieved_docs, key=lambda x: x["rerank_score"], reverse=True)
    
    # 4. 生成答案（调用 LLM）
    answer = f"根据您的查询「{query}」，为您推荐以下{len(retrieved_docs)}家商户..."
    
    # 5. 计算评估指标
    metrics = {
        "precision": 0.85,
        "recall": 0.78,
        "ndcg": 0.82,
        "latency_ms": (time.time() - start_time) * 1000
    }
    
    return {
        "answer": answer,
        "sources": retrieved_docs[:top_k],
        "metrics": metrics,
        "processing_time": time.time() - start_time
    }

def perform_web_search(query: str, top_k: int) -> Dict:
    """传统 Web 搜索"""
    start_time = time.time()
    
    # 实现你的 Web 搜索逻辑
    # 例如：ElasticSearch, BM25 等
    
    results = [
        {
            "merchant_name": f"商户 {i+1}",
            "address": f"上海市某区某街道{i+1}号",
            "rating": 4.5 - i * 0.1,
            "price": f"人均{100 + i*20}元"
        }
        for i in range(top_k)
    ]
    
    return {
        "answer": f"找到 {len(results)} 条结果",
        "sources": results,
        "metrics": {"latency_ms": (time.time() - start_time) * 1000},
        "processing_time": time.time() - start_time
    }

def perform_agentic_search(query: str, model: str, max_iterations: int) -> Dict:
    """智能体搜索"""
    start_time = time.time()
    
    # 实现你的 Agent 逻辑
    # 例如：使用 LangChain, AutoGPT 等
    
    reasoning_steps = [
        "🤔 分析查询意图...",
        "🔍 第1步：搜索相关商户...",
        "📊 第2步：过滤和排序结果...",
        "💡 第3步：生成推荐..."
    ]
    
    results = [
        {
            "merchant_name": "推荐商户 1",
            "address": "上海市浦东新区",
            "rating": 4.8,
            "reason": "高评分且符合您的需求"
        }
    ]
    
    return {
        "answer": "基于多步推理，为您推荐...",
        "sources": results,
        "metrics": {
            "correctness": 0.85,
            "completeness": 0.90,
            "faithfulness": 0.88,
            "latency_ms": (time.time() - start_time) * 1000
        },
        "reasoning_steps": reasoning_steps,
        "processing_time": time.time() - start_time
    }

# ==================== API 端点 ====================

@app.get("/")
def root():
    return {
        "service": "LocalSearchBench RAG API",
        "version": "1.0.0",
        "device": DEVICE,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "device": DEVICE,
        "gpu_available": torch.cuda.is_available() if 'torch' in globals() else False,
        "models_loaded": {
            "embedding": models.embedding_model is not None,
            "reranker": models.reranker_model is not None
        }
    }

@app.post("/api/rag/search", response_model=SearchResult)
async def rag_search(request: RAGSearchRequest):
    """RAG 搜索端点"""
    try:
        result = perform_rag_search(
            query=request.query,
            top_k=request.top_k,
            retriever=request.retriever,
            reranker=request.reranker
        )
        return SearchResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/web/search", response_model=SearchResult)
async def web_search(request: WebSearchRequest):
    """Web 搜索端点"""
    try:
        result = perform_web_search(
            query=request.query,
            top_k=request.top_k
        )
        return SearchResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agentic/search", response_model=SearchResult)
async def agentic_search(request: AgenticSearchRequest):
    """Agentic 搜索端点"""
    try:
        result = perform_agentic_search(
            query=request.query,
            model=request.model,
            max_iterations=request.max_iterations
        )
        return SearchResult(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """服务启动时预加载模型"""
    print("🚀 Starting LocalSearchBench RAG Server...")
    print(f"📍 Device: {DEVICE}")
    
    # 预加载模型到 GPU
    if DEVICE == "cuda":
        print("📥 Pre-loading models to GPU...")
        models.load_embedding_model()
        models.load_reranker_model()
        print("✅ Models loaded successfully")
    else:
        print("⚠️ Running in CPU mode")

@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭时清理资源"""
    print("👋 Shutting down LocalSearchBench RAG Server...")
    # 清理 GPU 显存
    if DEVICE == "cuda" and 'torch' in globals():
        torch.cuda.empty_cache()

# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="LocalSearchBench RAG Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║     LocalSearchBench RAG Server                           ║
║     Device: {DEVICE:48s} ║
║     Host: {args.host:50s} ║
║     Port: {args.port:50d} ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "rag_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info"
    )

if __name__ == "__main__":
    main()

