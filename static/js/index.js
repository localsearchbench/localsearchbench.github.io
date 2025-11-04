window.HELP_IMPROVE_VIDEOJS = false;

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

// Example queries data
const exampleQueries = [
    "I want to find a highly-rated hotpot restaurant near Wudaokou that's open late and has parking available.",
    "I need a hotel near Beijing West Railway Station with good reviews and breakfast included for under 500 RMB.",
    "Looking for a movie theater showing the latest Marvel film in IMAX near Sanlitun.",
    "I need to buy a birthday cake with fresh fruit decoration near Zhongguancun, preferably from a popular bakery.",
    "Looking for a reliable dental clinic near Guomao with English-speaking doctors and good patient reviews.",
    "Planning to visit the Great Wall this weekend, need recommendations for the best section and transportation options."
];

function loadExample(index) {
    console.log('loadExample called with index:', index);
    const query = exampleQueries[index];
    console.log('Query:', query);
    
    // Find the currently active tab/panel
    const activeTab = document.querySelector('.tabs li.is-active');
    console.log('Active tab:', activeTab);
    let queryInputId = 'rag-query'; // default to RAG
    
    if (activeTab) {
        const tabText = activeTab.textContent.trim();
        console.log('Tab text:', tabText);
        if (tabText.includes('Web Search')) {
            queryInputId = 'web-query';
        } else if (tabText.includes('Agentic Search')) {
            queryInputId = 'agentic-query';
        } else if (tabText.includes('RAG Search')) {
            queryInputId = 'rag-query';
        }
    }
    
    console.log('Query input ID:', queryInputId);
    const queryInput = document.getElementById(queryInputId);
    console.log('Query input element:', queryInput);
    
    if (queryInput) {
        queryInput.value = query;
        // Focus on the input
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
        console.error('Query input not found for ID:', queryInputId);
    }
}

// RAG Search Function
async function runRAG() {
    const query = document.getElementById('rag-query').value;
    const topK = parseInt(document.getElementById('rag-topk').value);
    const retriever = document.getElementById('rag-retriever').value;
    const reranker = document.getElementById('rag-reranker').value;
    
    if (!query.trim()) {
        alert('Please enter a query first!');
        return;
    }
    
    // Show loading state
    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>Running...</span>';
    button.disabled = true;
    
    try {
        // Call actual RAG API endpoint
        const response = await callRAGAPI(query, topK, retriever, reranker);
        
        // Display results
        displayRAGResults(response);
        
    } catch (error) {
        console.error('Error running RAG search:', error);
        
        // Check if it's a network error
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            const config = window.CONFIG || { RAG_SERVER_URL: 'http://localhost:8000' };
            const errorMsg = `
🚧 RAG 服务器未连接

当前配置的服务器: ${config.RAG_SERVER_URL}

快速开始指南:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣ 本地测试（推荐）
   cd server && ./deploy.sh --dev

2️⃣ 使用 Gradio 版本
   ./run_gradio.sh
   
3️⃣ 使用在线演示
   访问 Hugging Face Space (见项目 README)

详细文档: 
📖 QUICK_START.md - 5分钟快速开始
📖 DEPLOYMENT.md - 完整部署指南
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

提示: 这是一个需要后端支持的交互式演示。
您可以查看页面其他部分了解 LocalSearchBench！
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
async function callRAGAPI(query, topK, retriever, reranker) {
    const config = window.CONFIG || { RAG_SERVER_URL: 'http://localhost:8000', API_ENDPOINTS: { RAG_SEARCH: '/api/v1/rag/search' } };
    const url = `${config.RAG_SERVER_URL}${config.API_ENDPOINTS.RAG_SEARCH}`;
    
    const requestBody = {
        query: query,
        top_k: topK,
        retriever_model: retriever,
        reranker_model: reranker,
        use_reranker: true,
        generate_answer: true
    };
    
    console.log('Calling RAG API:', url);
    console.log('Request body:', requestBody);
    
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed (${response.status}): ${errorText}`);
    }
    
    const data = await response.json();
    console.log('RAG API response:', data);
    
    // Transform API response to match display format
    return {
        retrieved_docs: data.retrieved_documents.map(doc => ({
            title: doc.title || doc.merchant_name || 'Untitled',
            score: doc.score || doc.similarity_score || 0,
            content: doc.content || doc.description || '',
            type: doc.type || 'merchant'
        })),
        generated_answer: data.generated_answer || '暂无生成的答案',
        metrics: {
            correctness: data.metrics?.correctness || 0,
            completeness: data.metrics?.completeness || 0,
            faithfulness: data.metrics?.faithfulness || 0,
            retrieval_time: data.timing?.retrieval_time || '0s',
            generation_time: data.timing?.generation_time || '0s'
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
    const metricsDiv = document.getElementById('metrics');
    
    // Display retrieved documents
    retrievedDocsDiv.innerHTML = response.retrieved_docs.map((doc, index) => `
        <div class="box" style="margin-bottom: 1rem; border-left: 3px solid #3273dc;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <p class="has-text-weight-semibold">${index + 1}. ${doc.title}</p>
                    <p class="is-size-7" style="margin-top: 0.5rem;">${doc.content}</p>
                </div>
                <span class="tag is-primary" style="margin-left: 1rem;">Score: ${doc.score.toFixed(2)}</span>
            </div>
        </div>
    `).join('');
    
    // Display generated answer
    generatedAnswerDiv.innerHTML = `
        <div class="box" style="background-color: #f5f5f5;">
            <div class="content">
                ${response.generated_answer.replace(/\n/g, '<br>')}
            </div>
        </div>
    `;
    
    // Display metrics
    metricsDiv.innerHTML = `
        <div class="columns">
            <div class="column">
                <div class="box has-text-centered">
                    <p class="heading">Correctness</p>
                    <p class="title is-4" style="color: #48c774;">${(response.metrics.correctness * 100).toFixed(1)}%</p>
                </div>
            </div>
            <div class="column">
                <div class="box has-text-centered">
                    <p class="heading">Completeness</p>
                    <p class="title is-4" style="color: #3273dc;">${(response.metrics.completeness * 100).toFixed(1)}%</p>
                </div>
            </div>
            <div class="column">
                <div class="box has-text-centered">
                    <p class="heading">Faithfulness</p>
                    <p class="title is-4" style="color: #ffdd57;">${(response.metrics.faithfulness * 100).toFixed(1)}%</p>
                </div>
            </div>
            <div class="column">
                <div class="box has-text-centered">
                    <p class="heading">Total Time</p>
                    <p class="title is-4">${(parseFloat(response.metrics.retrieval_time) + parseFloat(response.metrics.generation_time)).toFixed(2)}s</p>
                </div>
            </div>
        </div>
    `;
    
    // Show results area
    resultsArea.style.display = 'block';
    
    // Scroll to results
    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Agentic Search Function
async function runAgenticSearch() {
    const query = document.getElementById('agentic-query').value;
    const model = document.getElementById('agentic-model').value;
    
    if (!query.trim()) {
        alert('Please enter a query first!');
        return;
    }
    
    // Show loading state
    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    button.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>Running...</span>';
    button.disabled = true;
    
    try {
        // Simulate API call (replace with actual API endpoint)
        const response = await simulateAgenticSearch(query, model);
        
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
    const metricsDiv = document.getElementById('agentic-metrics');
    
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
    
    // Display metrics
    metricsDiv.innerHTML = `
        <div class="columns">
            <div class="column">
                <div class="box has-text-centered">
                    <p class="heading">Correctness</p>
                    <p class="title is-4" style="color: #48c774;">${(response.metrics.correctness * 100).toFixed(1)}%</p>
                </div>
            </div>
            <div class="column">
                <div class="box has-text-centered">
                    <p class="heading">Completeness</p>
                    <p class="title is-4" style="color: #3273dc;">${(response.metrics.completeness * 100).toFixed(1)}%</p>
                </div>
            </div>
            <div class="column">
                <div class="box has-text-centered">
                    <p class="heading">Faithfulness</p>
                    <p class="title is-4" style="color: #ffdd57;">${(response.metrics.faithfulness * 100).toFixed(1)}%</p>
                </div>
            </div>
            <div class="column">
                <div class="box has-text-centered">
                    <p class="heading">Steps</p>
                    <p class="title is-4">${response.metrics.steps_count}</p>
                </div>
            </div>
            <div class="column">
                <div class="box has-text-centered">
                    <p class="heading">Total Time</p>
                    <p class="title is-4">${response.metrics.total_time}</p>
                </div>
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

})
