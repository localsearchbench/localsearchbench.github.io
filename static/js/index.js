window.HELP_IMPROVE_VIDEOJS = false;

/**
 * 设置按钮加载状态，根据高峰期显示不同提示
 */
function setButtonLoadingState(button) {
    const originalHTML = button.innerHTML;
    
    // Check if it's peak hours (10:30-21:00 Beijing time)
    const now = new Date();
    const beijingTime = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Shanghai"}));
    const hour = beijingTime.getHours();
    const minute = beijingTime.getMinutes();
    const currentTime = hour * 100 + minute;
    const isPeakHour = currentTime >= 1030 && currentTime <= 2100;
    
    if (isPeakHour) {
        button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>当前在高峰期，请耐心等待...</span>';
    } else {
        button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>Processing...</span>';
    }
    button.disabled = true;
    
    return originalHTML;
}

/**
 * 切换折叠/展开状态
 */
function toggleFold(foldId, button) {
    const foldDiv = document.getElementById(foldId);
    const icon = button.querySelector('i');
    const textSpan = button.querySelector('span:last-child');
    
    if (foldDiv.style.display === 'none') {
        // 展开
        foldDiv.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        textSpan.textContent = '收起';
    } else {
        // 收起
        foldDiv.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        const hiddenCount = foldDiv.children.length;
        textSpan.textContent = `显示更多 (${hiddenCount} 个)`;
    }
}

/**
 * 根据选择的城市更新位置输入框的 placeholder
 */
function updateLocationPlaceholder(cityValue) {
    const locationInput = document.getElementById('rag-location');
    if (!locationInput) return;
    
    // 城市对应的地点示例
    const cityLocationExamples = {
        'shanghai': '外滩, 陆家嘴, 徐家汇, 静安寺, 黄浦区',
        'beijing': '五道口, 三里屯, 国贸, 王府井, 海淀区',
        'guangzhou': '广州塔, 天河区, 珠江新城, 北京路, 上下九',
        'shenzhen': '深圳湾公园, 南山区, 福田区, 罗湖区, 宝安区',
        'hangzhou': '钱江世纪城, 西湖区, 滨江区, 拱墅区, 江干区',
        'suzhou': '东方之门,姑苏区, 工业园区, 吴中区, 相城区',
        'chengdu': '春熙路, 宽窄巷子, 锦里, 太古里, 锦江区',
        'chongqing': '解放碑, 观音桥, 南坪, 沙坪坝',
        'wuhan': '武昌站, 汉口站, 光谷, 江汉路'
    };
    
    const examples = cityLocationExamples[cityValue] || '外滩, 五道口, 天河区';
    locationInput.placeholder = `e.g., ${examples}`;
}

    // More Works Dropdown Functionality
function toggleMoreWorks() {
    const dropdown = document.getElementById('moreWorksDropdown');
    const button = document.querySelector('.more-works-btn');
    
    if (dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
        button.classList.remove('active');
    } else {
        dropdown.classList.add('show');
        button.classList.add('active');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const container = document.querySelector('.more-works-container');
    const dropdown = document.getElementById('moreWorksDropdown');
    const button = document.querySelector('.more-works-btn');
    
    if (container && !container.contains(event.target)) {
        dropdown.classList.remove('show');
        button.classList.remove('active');
    }
});

// 页面加载完成后，为城市选择器添加事件监听
document.addEventListener('DOMContentLoaded', function() {
    // 为所有城市选择器添加事件监听
    const citySelectors = ['rag-city', 'web-city', 'agentic-city'];
    
    citySelectors.forEach(selectorId => {
        const citySelect = document.getElementById(selectorId);
        if (citySelect) {
            // 初始化时设置 placeholder
            updateLocationPlaceholder(citySelect.value);
            
            // 监听城市选择变化
            citySelect.addEventListener('change', function() {
                updateLocationPlaceholder(this.value);
            });
        }
    });
});

// Close dropdown on escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const dropdown = document.getElementById('moreWorksDropdown');
        const button = document.querySelector('.more-works-btn');
        dropdown.classList.remove('show');
        button.classList.remove('active');
    }
});

// Copy BibTeX to clipboard
function copyBibTeX() {
    const bibtexElement = document.getElementById('bibtex-code');
    const button = document.querySelector('.copy-bibtex-btn');
    const copyText = button.querySelector('.copy-text');
    
    if (bibtexElement) {
        navigator.clipboard.writeText(bibtexElement.textContent).then(function() {
            // Success feedback
            button.classList.add('copied');
            copyText.textContent = 'Cop';
            
            setTimeout(function() {
                button.classList.remove('copied');
                copyText.textContent = 'Copy';
            }, 2000);
        }).catch(function(err) {
            console.error('Failed to copy: ', err);
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = bibtexElement.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            button.classList.add('copied');
            copyText.textContent = 'Cop';
            setTimeout(function() {
                button.classList.remove('copied');
                copyText.textContent = 'Copy';
            }, 2000);
        });
    }
}

// Scroll to top functionality
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Show/hide scroll to top button
window.addEventListener('scroll', function() {
    const scrollButton = document.querySelector('.scroll-to-top');
    if (window.pageYOffset > 300) {
        scrollButton.classList.add('visible');
    } else {
        scrollButton.classList.remove('visible');
    }
});

// Toggle RAG results collapse/expand
function toggleRAGResults() {
    const content = document.getElementById('rag-results-content');
    const button = document.getElementById('rag-toggle-btn');
    const icon = button.querySelector('i');
    const text = button.querySelector('span:last-child');
    
    console.log('toggleRAGResults called, content:', content, 'button:', button);
    
    // 检查当前状态：如果没有设置 display 或者是 block，说明是展开状态
    const isExpanded = content.style.display !== 'none';
    
    if (isExpanded) {
        // 当前是展开状态，点击后收起
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';  // 收起后显示向下箭头（表示可以展开）
        text.textContent = 'Expand';
        console.log('Collapsed RAG results');
    } else {
        // 当前是收起状态，点击后展开
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';    // 展开后显示向上箭头（表示可以收起）
        text.textContent = 'Collapse';
        console.log('Expanded RAG results');
    }
}

// Toggle Web Search results collapse/expand
function toggleWebResults() {
    const content = document.getElementById('web-results-content');
    const button = document.getElementById('web-toggle-btn');
    const icon = button.querySelector('i');
    const text = button.querySelector('span:last-child');
    
    console.log('toggleWebResults called, content:', content, 'button:', button);
    
    // 检查当前状态：如果没有设置 display 或者是 block，说明是展开状态
    const isExpanded = content.style.display !== 'none';
    
    if (isExpanded) {
        // 当前是展开状态，点击后收起
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';  // 收起后显示向下箭头（表示可以展开）
        text.textContent = 'Expand';
        console.log('Collapsed Web results');
    } else {
        // 当前是收起状态，点击后展开
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';    // 展开后显示向上箭头（表示可以收起）
        text.textContent = 'Collapse';
        console.log('Expanded Web results');
    }
}

// Toggle Agentic Search results collapse/expand
function toggleAgenticResults() {
    const content = document.getElementById('agentic-results-content');
    const button = document.getElementById('agentic-toggle-btn');
    const icon = button.querySelector('i');
    const text = button.querySelector('span:last-child');
    
    console.log('toggleAgenticResults called, content:', content, 'button:', button);
    
    // 检查当前状态：如果没有设置 display 或者是 block，说明是展开状态
    const isExpanded = content.style.display !== 'none';
    
    if (isExpanded) {
        // 当前是展开状态，点击后收起
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';  // 收起后显示向下箭头（表示可以展开）
        text.textContent = 'Expand';
        console.log('Collapsed Agentic results');
    } else {
        // 当前是收起状态，点击后展开
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';    // 展开后显示向上箭头（表示可以收起）
        text.textContent = 'Collapse';
        console.log('Expanded Agentic results');
    }
}

// Video carousel autoplay when in view
function setupVideoCarouselAutoplay() {
    const carouselVideos = document.querySelectorAll('.results-carousel video');
    
    if (carouselVideos.length === 0) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const video = entry.target;
            if (entry.isIntersecting) {
                // Video is in view, play it
                video.play().catch(e => {
                    // Autoplay failed, probably due to browser policy
                    console.log('Autoplay prevented:', e);
                });
            } else {
                // Video is out of view, pause it
                video.pause();
            }
        });
    }, {
        threshold: 0.5 // Trigger when 50% of the video is visible
    });
    
    carouselVideos.forEach(video => {
        observer.observe(video);
    });
}

// Playground Functions
function switchTool(toolName) {
    // Update tab active states
    const tabs = document.querySelectorAll('.tabs li');
    tabs.forEach(tab => {
        if (tab.getAttribute('data-tab') === toolName) {
            tab.classList.add('is-active');
        } else {
            tab.classList.remove('is-active');
        }
    });
    
    // Update panel visibility
    const panels = document.querySelectorAll('.tool-panel');
    panels.forEach(panel => {
        if (panel.id === `${toolName}-panel`) {
            panel.classList.add('active');
        } else {
            panel.classList.remove('active');
        }
    });
}

// City name mapping: English -> Chinese
const CITY_NAME_MAP = {
    'shanghai': '上海',
    'beijing': '北京',
    'guangzhou': '广州',
    'shenzhen': '深圳',
    'hangzhou': '杭州',
    'suzhou': '苏州',
    'chengdu': '成都',
    'chongqing': '重庆',
    'wuhan': '武汉'
};

// Helper function to convert English city name to Chinese
function getCityNameChinese(englishName) {
    return CITY_NAME_MAP[englishName] || englishName;
}

// Example queries data - [city, location, query]
const exampleQueries = [
    { city: "shanghai", location: "外滩", query: "餐厅" },
    { city: "beijing", location: "五道口", query: "火锅店" },
    { city: "shenzhen", location: "南山区", query: "电影院" },
    { city: "guangzhou", location: "天河区", query: "生日蛋糕" },
    { city: "chengdu", location: "春熙路", query: "咖啡店" },
    { city: "wuhan", location: "武昌站", query: "酒店" }
];

function loadExample(index) {
    console.log('loadExample called with index:', index);
    const example = exampleQueries[index];
    console.log('Example:', example);
    
    // Find the currently active tab/panel
    const activeTab = document.querySelector('.tabs li.is-active');
    console.log('Active tab:', activeTab);
    let prefix = 'rag'; // default to RAG
    
    if (activeTab) {
        const tabText = activeTab.textContent.trim();
        console.log('Tab text:', tabText);
        if (tabText.includes('Web Search')) {
            prefix = 'web';
        } else if (tabText.includes('Agentic Search')) {
            prefix = 'agentic';
        } else if (tabText.includes('LocalRAG Search')) {
            prefix = 'rag';
        }
    }
    
    // Set city, location, and query
    const citySelect = document.getElementById(`${prefix}-city`);
    const locationInput = document.getElementById(`${prefix}-location`);
    const queryInput = document.getElementById(`${prefix}-query`);
    
    console.log('Setting values for prefix:', prefix);
    
    if (citySelect && locationInput && queryInput) {
        citySelect.value = example.city;
        locationInput.value = example.location;
        queryInput.value = example.query;
        
        // 更新位置输入框的 placeholder
        updateLocationPlaceholder(example.city);
        
        // Focus on the query input
        queryInput.focus();
        // Scroll to the input
        queryInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Add a highlight effect
        queryInput.style.transition = 'box-shadow 0.3s ease';
        queryInput.style.boxShadow = '0 0 0 0.2em rgba(50, 115, 220, 0.25)';
        setTimeout(() => {
            queryInput.style.boxShadow = '';
        }, 1000);
    } else {
        console.error('Input elements not found for prefix:', prefix);
    }
}

// RAG Search Function
async function runRAG() {
    const city = document.getElementById('rag-city').value;
    const location = document.getElementById('rag-location').value;
    const queryContent = document.getElementById('rag-query').value;
    const topK = parseInt(document.getElementById('rag-topk').value);
    const retriever = document.getElementById('rag-retriever').value;
    const reranker = document.getElementById('rag-reranker').value;
    
    // 检查必填字段
    if (!city) {
        alert('请选择城市！');
        return;
    }
    
    if (!queryContent.trim()) {
        alert('请输入查询内容！');
        return;
    }
    
    // 组合完整查询: city + location + query
    let fullQuery = '';
    if (location.trim()) {
        fullQuery = `${location.trim()} ${queryContent.trim()}`;
    } else {
        fullQuery = queryContent.trim();
    }
    
    console.log('City:', city);
    console.log('Location:', location);
    console.log('Query Content:', queryContent);
    console.log('Full Query:', fullQuery);
    
    // Show loading state with peak hour message
    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    
    // Check if it's peak hours (10:30-21:00 Beijing time)
    const now = new Date();
    const beijingTime = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Shanghai"}));
    const hour = beijingTime.getHours();
    const minute = beijingTime.getMinutes();
    const currentTime = hour * 100 + minute;
    const isPeakHour = currentTime >= 1030 && currentTime <= 2100;
    
    if (isPeakHour) {
        button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>当前在高峰期，请耐心等待...</span>';
    } else {
        button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>Running...</span>';
    }
    button.disabled = true;
    
    try {
        // Call actual RAG API endpoint with full query
        const response = await callRAGAPI(fullQuery, city, topK, retriever, reranker);
        
        // Display results
        displayRAGResults(response);
        
    } catch (error) {
        console.error('Error running RAG search:', error);
        
        // Check if it's a network error
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            const errorMsg = `
🚧 LocalRAG 服务器未连接
LocalRAG Server Not Connected

支持时间: 工作日10:30-21:00
Support Hours: Weekdays 10:30-21:00

提示: 这是一个需要后端支持的交互式演示。
您可以查看页面其他部分了解 LocalSearchBench！
Tip: This is an interactive demo that requires backend support.
You can explore other parts of the page to learn about LocalSearchBench!
            `.trim();
            alert(errorMsg);
        } else {
            alert('运行搜索时发生错误: ' + error.message);
        }
    } finally {
        // Restore button state
        button.innerHTML = originalHTML;
        button.disabled = false;
    }
}

// Call RAG API
async function callRAGAPI(query, city, topK, retriever, reranker) {
    const config = window.CONFIG || { RAG_SERVER_URL: 'http://localhost:8000', API_ENDPOINTS: { RAG_SEARCH: '/api/v1/rag/search' } };
    const url = `${config.RAG_SERVER_URL}${config.API_ENDPOINTS.RAG_SEARCH}`;
    
    // Convert English city name to Chinese
    const chineseCity = getCityNameChinese(city);
    
    const requestBody = {
        query: query,
        city: chineseCity,  // Use Chinese city name
        top_k: topK,
        retriever_model: retriever,
        reranker_model: reranker,
        use_reranker: true,
        generate_answer: true
    };
    
    console.log('Calling RAG API:', url);
    console.log('City (English):', city, '-> (Chinese):', chineseCity);
    console.log('Request body:', requestBody);
    
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        },
        cache: 'no-cache',
        body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed (${response.status}): ${errorText}`);
    }
    
    const data = await response.json();
    console.log('RAG API response:', data);
    
    // 调试：打印第一个 source 的字段
    if (data.sources && data.sources.length > 0) {
        console.log('First source fields:', Object.keys(data.sources[0]));
        console.log('First source name:', data.sources[0].name);
        console.log('First source data:', data.sources[0]);
    }
    
    // Transform API response to match display format
    // 后端返回: answer, sources, metrics, processing_time
    return {
        retrieved_docs: (data.sources || []).map(doc => {
            // 保留所有原始字段
            const title = doc.name || doc.title || 'Untitled';
            const score = doc.rerank_score || doc.vector_score || doc.score || doc.similarity_score || 0;
            
            console.log(`Mapping doc: name="${doc.name}", title="${title}"`);
            
            // 返回所有字段
            return {
                ...doc,  // 保留所有原始字段
                title: title,  // 添加 title 字段方便显示
                score: score   // 统一的 score 字段
            };
        }),
        generated_answer: data.answer || '暂无生成的答案',
        metrics: {
            correctness: data.metrics?.correctness || 0,
            completeness: data.metrics?.completeness || 0,
            faithfulness: data.metrics?.faithfulness || 0,
            retrieval_time: data.metrics?.latency_ms ? `${(data.metrics.latency_ms / 1000).toFixed(2)}s` : '0s',
            generation_time: data.processing_time ? `${data.processing_time.toFixed(2)}s` : '0s'
        }
    };
}

// Simulate RAG search (replace with actual API call)
async function simulateRAGSearch(query, topK, retriever, generator) {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Mock response data
    return {
        retrieved_docs: [
            {
                title: "海底捞火锅 (五道口店)",
                score: 0.92,
                content: "位于五道口地铁站附近，营业时间10:00-02:00，提供免费停车位。人均消费约120元，评分4.8/5.0。",
                type: "merchant"
            },
            {
                title: "呷哺呷哺 (五道口店)",
                score: 0.87,
                content: "五道口华联购物中心3楼，营业时间11:00-22:00，有地下停车场。人均70元，评分4.5/5.0。",
                type: "merchant"
            },
            {
                title: "小龙坎火锅 (清华店)",
                score: 0.84,
                content: "清华东路，营业时间10:30-23:30，免费停车2小时。人均150元，评分4.7/5.0。",
                type: "merchant"
            },
            {
                title: "大龙燚火锅",
                score: 0.81,
                content: "五道口购物中心，营业到凌晨1点，地下停车场。人均130元，评分4.6/5.0。",
                type: "merchant"
            },
            {
                title: "蜀大侠火锅",
                score: 0.78,
                content: "五道口地铁A口步行5分钟，营业时间11:00-01:00，停车位充足。人均140元，评分4.7/5.0。",
                type: "merchant"
            }
        ],
        generated_answer: `根据您的需求，我为您推荐以下几家火锅餐厅：

**首选推荐：海底捞火锅 (五道口店)**
- 位置：五道口地铁站附近，交通便利
- 营业时间：10:00-02:00（营业到凌晨，符合您"开到很晚"的要求）
- 停车：提供免费停车位
- 评分：4.8/5.0（高评分）
- 人均：约120元

**备选推荐：**
1. **小龙坎火锅 (清华店)** - 评分4.7，免费停车2小时，人均150元
2. **蜀大侠火锅** - 营业到凌晨1点，停车位充足，评分4.7，人均140元
3. **大龙燚火锅** - 营业到凌晨1点，地下停车场，评分4.6，人均130元

这些餐厅都满足您提出的三个关键条件：位于五道口附近、评分较高、营业时间晚且有停车位。`,
        metrics: {
            correctness: 0.95,
            completeness: 0.88,
            faithfulness: 0.92,
            retrieval_time: "0.32s",
            generation_time: "1.45s"
        }
    };
}

function displayRAGResults(response) {
    const resultsArea = document.getElementById('rag-results');
    const retrievedDocsDiv = document.getElementById('retrieved-docs');
    const generatedAnswerDiv = document.getElementById('generated-answer');
    
    // Display retrieved documents with all fields
    retrievedDocsDiv.innerHTML = response.retrieved_docs.map((doc, index) => {
        // 定义字段显示的顺序和分组
        const mainFields = ['name', 'category', 'subcategory', 'description'];
        const locationFields = ['address', 'city', 'district', 'business_area', 'landmark', 'latitude', 'longitude'];
        const businessFields = ['business_hours', 'price_range', 'avg_price', 'rating', 'review_count', 'phone', 'mobile', 'email'];
        const serviceFields = ['delivery_available', 'delivery_range', 'delivery_fee', 'min_order_amount'];
        const extraFields = ['tags', 'facilities', 'promotions', 'products', 'group_deals'];
        const scoreFields = ['vector_score', 'rerank_score'];
        
        // 格式化字段值
        const formatValue = (key, value) => {
            if (value === null || value === undefined || value === '') return '<span class="has-text-grey-light">N/A</span>';
            if (typeof value === 'boolean') return value ? '✓' : '✗';
            if (typeof value === 'number') return value.toFixed(4);
            if (Array.isArray(value)) {
                if (value.length === 0) return '<span class="has-text-grey-light">N/A</span>';
                // 检查数组中是否包含对象
                if (value.some(item => typeof item === 'object' && item !== null)) {
                    // 对于对象数组，使用卡片式展示，支持折叠
                    const shouldFold = (key === 'products' || key === 'group_deals') && value.length > 5;
                    const visibleItems = shouldFold ? value.slice(0, 5) : value;
                    const hiddenItems = shouldFold ? value.slice(5) : [];
                    const foldId = `fold_${key}_${Math.random().toString(36).substr(2, 9)}`;
                    
                    let html = '<div style="margin-top: 0.5rem;">';
                    
                    // 显示前5个项目
                    html += visibleItems.map((item, idx) => {
                        const entries = Object.entries(item);
                        return `
                            <div style="background: #f9f9f9; padding: 0.75rem; margin-bottom: 0.5rem; border-radius: 6px; border-left: 3px solid #3273dc;">
                                <div style="font-weight: 600; color: #363636; margin-bottom: 0.5rem; font-size: 0.9rem;">
                                    ${key === 'products' ? '📦 产品' : '🎁 团购'} ${idx + 1}
                                </div>
                                ${entries.map(([k, v]) => `
                                    <div style="display: flex; margin-bottom: 0.25rem; font-size: 0.875rem;">
                                        <span style="color: #7a7a7a; min-width: 100px;">${k}:</span>
                                        <span style="color: #363636; flex: 1;">${v}</span>
                                    </div>
                                `).join('')}
                            </div>
                        `;
                    }).join('');
                    
                    // 如果需要折叠，添加展开/收起功能
                    if (shouldFold) {
                        html += `
                            <div id="${foldId}" style="display: none;">
                                ${hiddenItems.map((item, idx) => {
                                    const entries = Object.entries(item);
                                    return `
                                        <div style="background: #f9f9f9; padding: 0.75rem; margin-bottom: 0.5rem; border-radius: 6px; border-left: 3px solid #3273dc;">
                                            <div style="font-weight: 600; color: #363636; margin-bottom: 0.5rem; font-size: 0.9rem;">
                                                ${key === 'products' ? '📦 产品' : '🎁 团购'} ${idx + 6}
                                            </div>
                                            ${entries.map(([k, v]) => `
                                                <div style="display: flex; margin-bottom: 0.25rem; font-size: 0.875rem;">
                                                    <span style="color: #7a7a7a; min-width: 100px;">${k}:</span>
                                                    <span style="color: #363636; flex: 1;">${v}</span>
                                                </div>
                                            `).join('')}
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                            <div style="text-align: center; margin-top: 0.5rem;">
                                <button class="button is-small is-light" onclick="toggleFold('${foldId}', this)" style="font-size: 0.8rem;">
                                    <span class="icon is-small"><i class="fas fa-chevron-down"></i></span>
                                    <span>显示更多 (${hiddenItems.length} 个)</span>
                                </button>
                            </div>
                        `;
                    }
                    
                    html += '</div>';
                    return html;
                }
                // 对于简单类型数组，使用join
                return value.join(', ');
            }
            if (typeof value === 'string' && value.length > 100) return value.substring(0, 100) + '...';
            return value;
        };
        
        // 生成字段组HTML
        const renderFieldGroup = (title, fields) => {
            const fieldsHtml = fields.map(key => {
                if (doc.hasOwnProperty(key)) {
                    return `
                        <div style="display: flex; margin-bottom: 0.3rem;">
                            <span class="has-text-weight-semibold" style="min-width: 150px; color: #363636;">${key}:</span>
                            <span style="flex: 1;">${formatValue(key, doc[key])}</span>
                        </div>
                    `;
                }
                return '';
            }).filter(h => h).join('');
            
            return fieldsHtml ? `
                <div style="margin-bottom: 1rem;">
                    <p class="has-text-weight-bold is-size-6" style="color: #3273dc; margin-bottom: 0.5rem;">${title}</p>
                    ${fieldsHtml}
                </div>
            ` : '';
        };
        
        return `
            <div class="box" style="margin-bottom: 1.5rem; border-left: 4px solid #3273dc; position: relative;">
                <div style="position: absolute; top: 10px; right: 10px;">
                    <span class="tag is-primary is-medium">Score: ${doc.score.toFixed(4)}</span>
                </div>
                
                <p class="title is-5" style="margin-bottom: 1rem; padding-right: 120px;">
                    ${index + 1}. ${doc.name || 'Untitled'}
                </p>
                
                ${renderFieldGroup('📋 基本信息', mainFields)}
                ${renderFieldGroup('📍 位置信息', locationFields)}
                ${renderFieldGroup('💼 营业信息', businessFields)}
                ${renderFieldGroup('🚚 配送服务', serviceFields)}
                ${renderFieldGroup('🏷️ 标签与设施', extraFields)}
                
                <details style="margin-top: 1rem;">
                    <summary class="has-text-grey" style="cursor: pointer; user-select: none;">
                        查看完整JSON数据
                    </summary>
                    <pre style="background: #f5f5f5; padding: 1rem; margin-top: 0.5rem; border-radius: 4px; font-size: 0.85rem; overflow-x: auto;">${JSON.stringify(doc, null, 2)}</pre>
                </details>
            </div>
        `;
    }).join('');
    
    // Display generated answer (without box around the summary text)
    generatedAnswerDiv.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
            <p class="is-size-5 has-text-weight-medium" style="color: #363636;">
                ${response.generated_answer}
            </p>
        </div>
    `;
    
    // Show results area
    resultsArea.style.display = 'block';
    
    // Scroll to results
    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Web Search Function
async function runWebSearch() {
    const city = document.getElementById('web-city').value;
    const location = document.getElementById('web-location').value;
    const queryContent = document.getElementById('web-query').value;
    const topK = parseInt(document.getElementById('web-topk').value);
    
    // 检查必填字段
    if (!city) {
        alert('请选择城市！');
        return;
    }
    
    if (!queryContent.trim()) {
        alert('请输入查询内容！');
        return;
    }
    
    // 组合完整查询: city + location + query
    let fullQuery = '';
    if (location.trim()) {
        fullQuery = `${location.trim()} ${queryContent.trim()}`;
    } else {
        fullQuery = queryContent.trim();
    }
    
    console.log('Web Search - City:', city);
    console.log('Web Search - Location:', location);
    console.log('Web Search - Query Content:', queryContent);
    console.log('Web Search - Full Query:', fullQuery);
    
    // Show loading state with peak hour message
    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    
    // Check if it's peak hours (10:30-21:00 Beijing time)
    const now = new Date();
    const beijingTime = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Shanghai"}));
    const hour = beijingTime.getHours();
    const minute = beijingTime.getMinutes();
    const currentTime = hour * 100 + minute;
    const isPeakHour = currentTime >= 1030 && currentTime <= 2100;
    
    if (isPeakHour) {
        button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>当前在高峰期，请耐心等待...</span>';
    } else {
        button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>Running...</span>';
    }
    button.disabled = true;
    
    try {
        // TODO: Call actual Web Search API endpoint
        alert('Web Search 功能开发中...\n\nCity: ' + city + '\nLocation: ' + location + '\nQuery: ' + queryContent);
    } catch (error) {
        console.error('Error running web search:', error);
        alert('运行搜索时发生错误: ' + error.message);
    } finally {
        // Restore button state
        button.innerHTML = originalHTML;
        button.disabled = false;
    }
}

// Agentic Search Function
async function runAgenticSearch() {
    const city = document.getElementById('agentic-city').value;
    const location = document.getElementById('agentic-location').value;
    const queryContent = document.getElementById('agentic-query').value;
    const model = document.getElementById('agentic-model').value;
    
    // 检查必填字段
    if (!city) {
        alert('请选择城市！');
        return;
    }
    
    if (!queryContent.trim()) {
        alert('请输入查询内容！');
        return;
    }
    
    // 组合完整查询: city + location + query
    let fullQuery = '';
    if (location.trim()) {
        fullQuery = `${location.trim()} ${queryContent.trim()}`;
    } else {
        fullQuery = queryContent.trim();
    }
    
    console.log('Agentic Search - City:', city);
    console.log('Agentic Search - Location:', location);
    console.log('Agentic Search - Query Content:', queryContent);
    console.log('Agentic Search - Full Query:', fullQuery);
    
    // Show loading state with peak hour message
    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    
    // Check if it's peak hours (10:30-21:00 Beijing time)
    const now = new Date();
    const beijingTime = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Shanghai"}));
    const hour = beijingTime.getHours();
    const minute = beijingTime.getMinutes();
    const currentTime = hour * 100 + minute;
    const isPeakHour = currentTime >= 1030 && currentTime <= 2100;
    
    if (isPeakHour) {
        button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>当前在高峰期，请耐心等待...</span>';
    } else {
        button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>Running...</span>';
    }
    button.disabled = true;
    
    try {
        // Simulate API call (replace with actual API endpoint)
        const response = await simulateAgenticSearch(fullQuery, model);
        
        // Display results
        displayAgenticResults(response);
        
    } catch (error) {
        console.error('Error running agentic search:', error);
        alert('An error occurred while running the search. Please try again.');
    } finally {
        // Restore button state
        button.innerHTML = originalHTML;
        button.disabled = false;
    }
}

// Simulate Agentic search (replace with actual API call)
async function simulateAgenticSearch(query, model) {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Mock response data
    return {
        search_steps: [
            {
                step: 1,
                action: "Query Analysis",
                description: "Analyzing user query and extracting key requirements...",
                result: "Extracted: location=五道口, type=火锅, requirements=[高评分, 营业晚, 停车位]"
            },
            {
                step: 2,
                action: "Merchant Search",
                description: "Searching for hotpot restaurants in Wudaokou area...",
                result: "Found 15 matching merchants"
            },
            {
                step: 3,
                action: "Filter by Operating Hours",
                description: "Filtering restaurants that operate late (after 22:00)...",
                result: "5 restaurants match the late-night requirement"
            },
            {
                step: 4,
                action: "Check Parking Availability",
                description: "Verifying parking facilities for filtered restaurants...",
                result: "3 restaurants have parking available"
            },
            {
                step: 5,
                action: "Rank by Rating",
                description: "Sorting results by customer ratings...",
                result: "Top 3 restaurants identified"
            }
        ],
        final_answer: `基于多步推理和工具调用，我为您推荐以下火锅餐厅：

**最佳推荐：海底捞火锅 (五道口店)**
- 📍 位置：五道口地铁站A口步行3分钟
- ⏰ 营业时间：10:00-02:00 ✅ 营业到凌晨
- 🅿️ 停车：免费停车位60个
- ⭐ 评分：4.8/5.0（共12,453条评价）
- 💰 人均：120元
- 🔥 特色：24小时服务、免费小食、排队管理系统

**备选方案：**

1. **小龙坎火锅 (清华店)**
   - 📍 清华东路，距离五道口1.2公里
   - ⏰ 10:30-23:30
   - 🅿️ 免费停车2小时
   - ⭐ 4.7/5.0
   - 💰 150元

2. **蜀大侠火锅**
   - 📍 五道口购物中心3楼
   - ⏰ 11:00-01:00 ✅ 营业到凌晨
   - 🅿️ 地下停车场（与商场共享）
   - ⭐ 4.7/5.0
   - 💰 140元

**推理过程：**
通过5步搜索过程，从15家候选餐厅中筛选出符合"高评分+营业晚+有停车"的3家餐厅。海底捞因其最高评分(4.8)、最晚营业时间(02:00)和充足停车位(60个)被评为首选。`,
        metrics: {
            correctness: 0.92,
            completeness: 0.94,
            faithfulness: 0.89,
            total_time: "2.87s",
            steps_count: 5
        },
        model_used: model
    };
}

function displayAgenticResults(response) {
    const resultsArea = document.getElementById('agentic-results');
    const processDiv = document.getElementById('search-process');
    const answerDiv = document.getElementById('agentic-answer');
    
    // Display search process
    processDiv.innerHTML = response.search_steps.map((step, index) => `
        <div class="box" style="margin-bottom: 1rem; border-left: 4px solid ${index === response.search_steps.length - 1 ? '#48c774' : '#3273dc'};">
            <div style="display: flex; align-items: start;">
                <div style="flex-shrink: 0; width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-right: 1rem;">
                    ${step.step}
                </div>
                <div style="flex: 1;">
                    <p class="has-text-weight-semibold" style="color: #363636;">${step.action}</p>
                    <p class="is-size-7" style="margin-top: 0.25rem; color: #7a7a7a;">${step.description}</p>
                    <p class="is-size-7" style="margin-top: 0.5rem; padding: 0.5rem; background-color: #f5f5f5; border-radius: 4px; font-family: monospace;">${step.result}</p>
                </div>
            </div>
        </div>
    `).join('');
    
    // Display final answer
    answerDiv.innerHTML = `
        <div class="box" style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); border: 2px solid #667eea;">
            <div class="content">
                ${response.final_answer.replace(/\n/g, '<br>')}
            </div>
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e0e0e0;">
                <span class="tag is-info">Model: ${response.model_used}</span>
            </div>
        </div>
    `;
    
    // Show results area
    resultsArea.style.display = 'block';
    
    // Scroll to results
    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Leaderboard Table Sorting
function initLeaderboardSorting() {
    const table = document.getElementById('leaderboard-table');
    if (!table) return;
    
    const headers = table.querySelectorAll('thead th.sortable');
    let currentSort = { column: null, direction: null };
    
    headers.forEach(header => {
        header.addEventListener('click', function() {
            const column = parseInt(this.getAttribute('data-column'));
            
            // Determine sort direction
            let direction = 'desc'; // Default to descending (higher values first)
            if (currentSort.column === column) {
                direction = currentSort.direction === 'desc' ? 'asc' : 'desc';
            }
            
            // Update current sort state
            currentSort = { column, direction };
            
            // Update header styles
            headers.forEach(h => {
                h.classList.remove('asc', 'desc');
            });
            this.classList.add(direction);
            
            // Sort the table
            sortTable(table, column, direction);
        });
    });
}

function sortTable(table, column, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Separate average row from data rows
    const averageRow = rows.find(row => row.classList.contains('average-row'));
    const dataRows = rows.filter(row => 
        row.hasAttribute('data-values') && !row.classList.contains('average-row')
    );
    
    // Sort data rows
    dataRows.sort((a, b) => {
        const aValues = JSON.parse(a.getAttribute('data-values') || '[]');
        const bValues = JSON.parse(b.getAttribute('data-values') || '[]');
        
        const aValue = aValues[column] || 0;
        const bValue = bValues[column] || 0;
        
        if (direction === 'asc') {
            return aValue - bValue;
        } else {
            return bValue - aValue;
        }
    });
    
    // Clear tbody
    tbody.innerHTML = '';
    
    // Re-append sorted data rows
    dataRows.forEach(row => tbody.appendChild(row));
    
    // Always keep average row at the end
    if (averageRow) {
        tbody.appendChild(averageRow);
    }
    
    // Add animation
    dataRows.forEach((row, index) => {
        setTimeout(() => {
            row.style.animation = 'fadeIn 0.3s ease-in';
        }, index * 20);
    });
}

$(document).ready(function() {
    // Check for click events on the navbar burger icon

    var options = {
	slidesToScroll: 1,
	slidesToShow: 1,
	loop: true,
	infinite: true,
	autoplay: true,
	autoplaySpeed: 5000,
    }

	// Initialize all div with carousel class
    var carousels = bulmaCarousel.attach('.carousel', options);
	
    bulmaSlider.attach();
    
    // Setup video autoplay for carousel
    setupVideoCarouselAutoplay();
    
    // Initialize leaderboard sorting
    initLeaderboardSorting();
    
    // Listen for config loaded event
    window.addEventListener('configLoaded', function(event) {
        console.log('✅ 配置已加载，RAG 服务器 URL:', event.detail.RAG_SERVER_URL);
        updateServerStatus();
        // Check server connection after config is loaded
        setTimeout(checkServerConnection, 500);
    });
    
    // Listen for tunnel URL change event
    window.addEventListener('tunnelUrlChanged', function(event) {
        const { oldUrl, newUrl } = event.detail;
        console.log('🔄 检测到隧道 URL 变化');
        
        // Show notification to user
        showTunnelChangeNotification(oldUrl, newUrl);
        
        // Update server status
        updateServerStatus();
        
        // Re-check server connection
        setTimeout(checkServerConnection, 1000);
    });
    
    // Listen for config updated event (from polling)
    window.addEventListener('configUpdated', function(event) {
        console.log('🔄 配置已更新:', event.detail.RAG_SERVER_URL);
        updateServerStatus();
    });
    
    // Also update status on page load
    setTimeout(updateServerStatus, 1000);
    // Check server connection on page load
    setTimeout(checkServerConnection, 2000);

})

// Update server status display
function updateServerStatus() {
    const config = window.CONFIG;
    if (!config) return;
    
    const serverUrlElement = document.getElementById('server-url-display');
    if (serverUrlElement) {
        serverUrlElement.textContent = config.RAG_SERVER_URL;
    }
}

// Show tunnel URL change notification
function showTunnelChangeNotification(oldUrl, newUrl) {
    // Check if notification already exists
    let notification = document.getElementById('tunnel-change-notification');
    if (notification) {
        notification.remove();
    }
    
    // Create notification
    notification = document.createElement('div');
    notification.id = 'tunnel-change-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        z-index: 10001;
        max-width: 400px;
        animation: slideInRight 0.5s ease-out;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: start; gap: 1rem;">
            <div style="font-size: 2rem;">🔄</div>
            <div style="flex: 1;">
                <div style="font-weight: 600; margin-bottom: 0.5rem;">隧道 URL 已更新</div>
                <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">
                    临时隧道已重启，新的访问地址：
                </div>
                <div style="font-size: 0.85rem; font-family: monospace; background: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px; word-break: break-all; margin-bottom: 0.5rem;">
                    ${newUrl}
                </div>
                <div style="font-size: 0.8rem; opacity: 0.7;">
                    页面将自动使用新地址，无需刷新。
                </div>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" style="background: transparent; border: none; color: white; font-size: 1.5rem; cursor: pointer; padding: 0; line-height: 1;">×</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
        if (notification && notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.5s ease-out';
            setTimeout(() => notification.remove(), 500);
        }
    }, 10000);
}

// Check server connection and show modal if disconnected
async function checkServerConnection() {
    const config = window.CONFIG || { RAG_SERVER_URL: 'http://localhost:8000', API_ENDPOINTS: { HEALTH_CHECK: '/health' } };
    const healthUrl = `${config.RAG_SERVER_URL}${config.API_ENDPOINTS.HEALTH_CHECK}`;
    
    try {
        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(healthUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            },
            cache: 'no-cache',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ RAG 服务器连接正常:', data);
            return true;
        } else {
            throw new Error(`服务器响应错误: ${response.status}`);
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.warn('⚠️  RAG 服务器连接超时');
        } else {
            console.warn('⚠️  RAG 服务器连接失败:', error.message);
        }
        return false;
    }
}

// Custom Select with Model Logos
document.addEventListener('DOMContentLoaded', function() {
    const customSelect = document.getElementById('agentic-model-select');
    if (!customSelect) return;
    
    const trigger = customSelect.querySelector('.custom-select-trigger');
    const options = customSelect.querySelectorAll('.custom-select-option');
    const hiddenSelect = document.getElementById('agentic-model');
    
    // Model logo mapping
    const modelLogos = {
        'gpt-4.1': 'static/images/logo/icon-chatgpt (1).png',
        'gemini-2.5-pro': 'static/images/logo/google.png',
        'qwen-plus-latest': 'static/images/logo/qwen.png',
        'longcat-large-32k': 'static/images/logo/longcat.png',
        'hunyuan-t1': 'static/images/logo/ai_hunyuan.png',
        'qwen3-235b-a22b': 'static/images/logo/qwen.png',
        'qwen3-32b': 'static/images/logo/qwen.png',
        'qwen3-14b': 'static/images/logo/qwen.png',
        'glm-4.5': 'static/images/logo/logo_chatglm.png',
        'deepseek-v3.1': 'static/images/logo/deepseek.png'
    };
    
    // Model name mapping
    const modelNames = {
        'gpt-4.1': 'GPT-4.1',
        'gemini-2.5-pro': 'Gemini-2.5-Pro',
        'qwen-plus-latest': 'Qwen-Plus-Latest',
        'longcat-large-32k': 'LongCat-Large-32K',
        'hunyuan-t1': 'Hunyuan-T1',
        'qwen3-235b-a22b': 'Qwen3-235B-A22B',
        'qwen3-32b': 'Qwen3-32B',
        'qwen3-14b': 'Qwen3-14B',
        'glm-4.5': 'GLM-4.5',
        'deepseek-v3.1': 'Deepseek-V3.1'
    };
    
    // Initialize selected option
    const selectedOption = customSelect.querySelector('.custom-select-option[data-selected="true"]');
    if (selectedOption) {
        const value = selectedOption.getAttribute('data-value');
        updateTrigger(value);
        selectedOption.classList.add('selected');
    } else if (hiddenSelect.value) {
        // Fallback: use hidden select value
        const value = hiddenSelect.value;
        updateTrigger(value);
        const option = customSelect.querySelector(`.custom-select-option[data-value="${value}"]`);
        if (option) {
            option.classList.add('selected');
        }
    }
    
    // Toggle dropdown
    trigger.addEventListener('click', function(e) {
        e.stopPropagation();
        customSelect.classList.toggle('active');
    });
    
    // Handle option selection
    options.forEach(option => {
        option.addEventListener('click', function(e) {
            e.stopPropagation();
            const value = this.getAttribute('data-value');
            
            // Update hidden select
            hiddenSelect.value = value;
            
            // Update trigger
            updateTrigger(value);
            
            // Update selected state
            options.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            
            // Close dropdown
            customSelect.classList.remove('active');
        });
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!customSelect.contains(e.target)) {
            customSelect.classList.remove('active');
        }
    });
    
    // Update trigger display
    function updateTrigger(value) {
        const logoImg = trigger.querySelector('.model-logo-select');
        const nameSpan = trigger.querySelector('span');
        
        if (logoImg && modelLogos[value]) {
            logoImg.src = modelLogos[value];
            logoImg.alt = modelNames[value] || value;
        }
        
        if (nameSpan && modelNames[value]) {
            nameSpan.textContent = modelNames[value];
        }
    }
    
    // Sync with hidden select changes (if changed programmatically)
    hiddenSelect.addEventListener('change', function() {
        const value = this.value;
        updateTrigger(value);
        
        // Update selected state
        options.forEach(opt => {
            opt.classList.remove('selected');
            if (opt.getAttribute('data-value') === value) {
                opt.classList.add('selected');
            }
        });
    });
});

