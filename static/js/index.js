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
    "Looking for a movie theater showing the latest Marvel film in IMAX near Sanlitun."
];

function loadExample(index) {
    const query = exampleQueries[index];
    const queryInput = document.getElementById('rag-query');
    if (queryInput) {
        queryInput.value = query;
        queryInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// RAG Search Function
async function runRAG() {
    const query = document.getElementById('rag-query').value;
    const topK = document.getElementById('rag-topk').value;
    const retriever = document.getElementById('rag-retriever').value;
    const generator = document.getElementById('rag-generator').value;
    
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
        const response = await simulateRAGSearch(query, topK, retriever, generator);
        
        // Display results
        displayRAGResults(response);
        
    } catch (error) {
        console.error('Error running RAG search:', error);
        alert('An error occurred while running the search. Please try again.');
    } finally {
        // Restore button state
        button.innerHTML = originalHTML;
        button.disabled = false;
    }
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

})
