#!/bin/bash

# LocalSearchBench Gradio Playground Launcher
echo "🚀 Starting LocalSearchBench Gradio Playground..."

# Check if gradio is installed
if ! python -c "import gradio" 2>/dev/null; then
    echo "📦 Gradio not found. Installing..."
    pip install -r requirements-gradio.txt
fi

# Run the playground
echo "🌐 Launching playground at http://localhost:7860"
python playground_app.py

