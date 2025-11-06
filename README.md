# LocalSearchBench

> A benchmark for local search and recommendation systems

## Quick Links

- 🌐 **Demo Website**: [localsearchbench.github.io](https://localsearchbench.github.io)
- 🚀 **RAG Server**: See [server/README.md](server/README.md) for backend deployment
- 📄 **Paper**: Coming soon

## 🚀 Quick Start

### Option 1: One-Command Start (Recommended)

Start RAG server and tunnel monitor with automatic URL updates:

```bash
./start_with_monitor.sh
```

This will:
- ✅ Start RAG server on port 8000
- ✅ Start Cloudflare tunnel with auto-monitoring
- ✅ Automatically update frontend config when tunnel URL changes
- ✅ Run everything in background (tmux sessions)

Check status:
```bash
./check_status.sh
```

Stop all services:
```bash
./stop_all.sh
```

### Option 2: Manual Start

If you want to run the backend RAG server manually:

```bash
cd server
./start_rag_server.sh --data-dir /path/to/your/data --host 0.0.0.0 --port 8000
```

See [server/README.md](server/README.md) for detailed instructions.

### Tunnel Auto-Update

The tunnel monitor automatically:
- Detects when Cloudflare tunnel goes down
- Restarts the tunnel with a new URL
- Updates `static/js/config.js` automatically
- Logs all changes to `tunnel_updates.log`

See [TUNNEL_AUTO_UPDATE.md](TUNNEL_AUTO_UPDATE.md) for details.

## 📁 Project Structure

```
localsearchbench.github.io/
├── index.html              # Main website
├── static/                 # Frontend assets
│   ├── css/
│   ├── js/
│   ├── images/
│   └── videos/
└── server/                 # RAG backend
    ├── README.md           # Server documentation
    ├── rag_server.py       # Main server code
    ├── start_rag_server.sh # Startup script
    ├── requirements.txt    # Python dependencies
    ├── Dockerfile          # Docker image
    └── docker-compose.yml  # Docker setup
```

## 🌟 Features

- **Multi-City Support**: Search across 9 major Chinese cities
- **GPU-Accelerated RAG**: VLLM-powered embedding and reranking
- **Interactive Demo**: Web-based interface for testing
- **Scalable Backend**: FastAPI + FAISS vector search
- **Docker Support**: Easy deployment with Docker Compose
- **MCP Integration**: Use as AI tool in Claude Desktop, Cursor, and more! 🆕

## 🛠️ Development

### Frontend (Website)
Edit `index.html` and files in `static/` for the demo website.

### Backend (RAG Server)
See [server/README.md](server/README.md) for:
- Installation and setup
- Configuration options
- API documentation
- Troubleshooting

### MCP Tools (AI Integration)
See [mcp_tools/QUICKSTART.md](mcp_tools/QUICKSTART.md) for:
- 5-minute quick start guide
- Claude Desktop configuration
- Usage examples
- Troubleshooting

Reference: Based on [RL-Factory](https://github.com/bytedance/RL-Factory) MCP implementation

## 📖 Citation

```bibtex
@article{localsearchbench2025,
  title={LocalSearchBench: A Benchmark for Local Search and Recommendation},
  author={Your Name},
  year={2025}
}
```

## 📄 License

This project is licensed under the MIT License.

## Website License
<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.
