# LocalSearchBench Gradio Playground Setup

This document explains how to run the Gradio-based playground interface for LocalSearchBench.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-gradio.txt
```

Or install Gradio directly:

```bash
pip install gradio
```

### 2. Run the Playground

```bash
python playground_app.py
```

The interface will be available at `http://localhost:7860`

### 3. Share Publicly (Optional)

To create a public shareable link:

```python
# In playground_app.py, change:
demo.launch(share=True)  # This will generate a public gradio.app link
```

## Features

The Gradio playground provides three search methods:

### 🔍 RAG Search
- Combines retrieval and generation
- Uses embedding models (Qwen3-Embedding-8B) for semantic search
- Reranks results with Qwen3-Reranker-8B
- Generates natural language answers

### 🌐 Web Search
- Traditional keyword-based search
- Fast and simple
- Configurable top-k results

### 🤖 Agentic Search
- LLM-powered multi-step reasoning
- Supports multiple models (GPT-4.1, Gemini-2.5-Pro, Deepseek-V3.1, etc.)
- Shows reasoning process step-by-step
- Uses tool calling for complex queries

## Embedding in Your Website

You can embed the Gradio interface in your existing webpage:

### Option 1: Full Page Replacement

Replace the current playground section in `index.html` with an iframe:

```html
<section class="section" id="playground">
  <div class="container is-max-desktop">
    <h2 class="title is-3">Try It Yourself</h2>
    <iframe 
      src="http://localhost:7860" 
      frameborder="0" 
      width="100%" 
      height="1200px"
      style="border: 1px solid #ddd; border-radius: 8px;"
    ></iframe>
  </div>
</section>
```

### Option 2: Gradio Embedded Mode

Use Gradio's built-in embedding feature:

```html
<gradio-app src="http://localhost:7860"></gradio-app>
<script type="module" src="https://gradio.s3-us-west-2.amazonaws.com/4.0.0/gradio.js"></script>
```

### Option 3: Deploy Separately

Deploy the Gradio app on Hugging Face Spaces and embed it:

1. Create a new Space on [Hugging Face](https://huggingface.co/spaces)
2. Upload `playground_app.py` and `requirements-gradio.txt`
3. Embed using the Space URL:

```html
<iframe 
  src="https://huggingface.co/spaces/YOUR_USERNAME/localsearchbench-playground" 
  frameborder="0" 
  width="100%" 
  height="1200px"
></iframe>
```

## Customization

### Adding Real Backend

Replace the `mock_*` functions in `playground_app.py` with your actual search implementations:

```python
def mock_rag_search(query, top_k, retriever, reranker):
    # Replace with actual RAG implementation
    from your_rag_module import run_rag
    results = run_rag(query, top_k=top_k, retriever=retriever, reranker=reranker)
    return format_results(results)
```

### Styling

Gradio supports custom themes:

```python
demo = gr.Blocks(theme=gr.themes.Soft())  # or Base, Glass, Monochrome
```

Or create custom CSS:

```python
with gr.Blocks(css="""
    .gradio-container {
        max-width: 1200px !important;
    }
""") as demo:
    # ...
```

## Deployment Options

### Local Development
```bash
python playground_app.py
```

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn playground_app:demo -b 0.0.0.0:7860
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY playground_app.py requirements-gradio.txt ./
RUN pip install -r requirements-gradio.txt
EXPOSE 7860
CMD ["python", "playground_app.py"]
```

### Hugging Face Spaces
1. Create a new Space (Gradio type)
2. Upload files:
   - `playground_app.py` → rename to `app.py`
   - `requirements-gradio.txt` → rename to `requirements.txt`
3. Space will automatically deploy

## Troubleshooting

### Port Already in Use
```python
demo.launch(server_port=7861)  # Use different port
```

### CORS Issues
```python
demo.launch(
    server_name="0.0.0.0",
    allowed_paths=["*"],
    show_error=True
)
```

### Performance
- Use `queue()` for handling multiple concurrent users
- Enable caching for expensive operations
- Consider using Gradio's built-in analytics

```python
demo.queue(max_size=20)
demo.launch()
```

## Next Steps

1. Replace mock functions with real implementations
2. Add authentication if needed (`auth=("username", "password")`)
3. Deploy to production (HF Spaces, AWS, etc.)
4. Monitor usage with Gradio analytics
5. Collect user feedback through the interface

For more information, see [Gradio Documentation](https://gradio.app/docs).

