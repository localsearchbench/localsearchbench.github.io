/**
 * LocalSearchBench Configuration
 * 
 * 配置说明：
 * 1. RAG_SERVER_URL 会在页面加载时动态从 tunnel_config.json 获取
 * 2. 如果动态加载失败，会使用这里的默认值作为后备
 * 3. 确保 RAG 服务器已配置 CORS 允许来自 GitHub Pages 的请求
 */

const CONFIG = {
    // RAG Server Configuration
    // 这个 URL 会在运行时被动态配置覆盖
    RAG_SERVER_URL: 'https://terrorists-eyes-focused-reasonable.trycloudflare.com',
    
    // 动态配置文件路径（相对于网站根目录）
    DYNAMIC_CONFIG_URL: './tunnel_config.json',
    
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

/**
 * 动态加载 RAG 服务器配置
 * 从 tunnel_config.json 获取最新的隧道 URL
 */
async function loadDynamicConfig() {
    try {
        // 添加时间戳防止缓存
        const timestamp = new Date().getTime();
        const response = await fetch(`${CONFIG.DYNAMIC_CONFIG_URL}?t=${timestamp}`, {
            cache: 'no-cache',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
        });
        
        if (response.ok) {
            const dynamicConfig = await response.json();
            if (dynamicConfig.rag_server_url) {
                CONFIG.RAG_SERVER_URL = dynamicConfig.rag_server_url;
                console.log('✅ 动态配置加载成功:', CONFIG.RAG_SERVER_URL);
                console.log('📅 配置更新时间:', dynamicConfig.updated_at || '未知');
                return true;
            }
        }
    } catch (error) {
        console.warn('⚠️  动态配置加载失败，使用默认配置:', error.message);
    }
    return false;
}

// 在页面加载时自动加载动态配置
if (typeof window !== 'undefined') {
    // 立即加载动态配置
    loadDynamicConfig().then(() => {
        // 触发自定义事件，通知配置已更新
        window.dispatchEvent(new CustomEvent('configLoaded', { detail: CONFIG }));
    });
}

// Export for use in other scripts
window.CONFIG = CONFIG;
window.loadDynamicConfig = loadDynamicConfig;
