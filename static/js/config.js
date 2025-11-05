/**
 * LocalSearchBench Configuration
 * 
 * 配置说明：
 * 1. 如果你在本地运行 RAG 服务器，使用 'http://localhost:8000'
 * 2. 如果你部署了远程服务器，使用完整的 URL，例如 'https://rag.your-domain.com'
 * 3. 确保 RAG 服务器已配置 CORS 允许来自 GitHub Pages 的请求
 */

const CONFIG = {
    // RAG Server Configuration
    RAG_SERVER_URL: 'http://10.131.27.205:8000',
    
    // API Endpoints
    API_ENDPOINTS: {
        RAG_SEARCH: '/api/rag/search',
        WEB_SEARCH: '/api/web/search',
        AGENTIC_SEARCH: '/api/agentic/search',
        HEALTH_CHECK: '/health'
    },
    
    // Default Parameters
    DEFAULTS: {
        TOP_K: 20,
        RETRIEVER_MODEL: 'Qwen3-Embedding-8B',
        RERANKER_MODEL: 'Qwen3-Reranker-8B',
        LLM_MODEL: 'gpt-4',
        USE_RERANKER: true,
        GENERATE_ANSWER: true
    },
    
    // Timeout settings (milliseconds)
    TIMEOUT: {
        RAG_SEARCH: 60000,      // 60 seconds
        WEB_SEARCH: 10000,      // 10 seconds
        AGENTIC_SEARCH: 120000  // 120 seconds
    }
};

// Export for use in other scripts
window.CONFIG = CONFIG;

