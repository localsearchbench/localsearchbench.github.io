---
title: LocalSearchBench Playground
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: apache-2.0
---

# 🔍 LocalSearchBench Interactive Playground

交互式本地搜索评测平台 - 体验三种搜索方式的实际效果

## ✨ 功能特性

### 🤖 RAG Search (检索增强生成)
- 使用 **Qwen3-Embedding-8B** 进行语义检索
- 使用 **Qwen3-Reranker-8B** 进行结果重排序
- 基于检索内容生成自然语言答案
- 显示 Precision、Recall、NDCG 等评估指标

### 🌐 Web Search (传统搜索)
- 基于 BM25 或 ElasticSearch 的关键词搜索
- 快速响应，适合浏览多个结果
- 可调节返回结果数量

### 🧠 Agentic Search (智能体搜索)
- 支持多个先进的 LLM 模型
- 多步推理和工具调用
- 展示完整的推理过程
- 适合复杂查询场景

## 🎯 使用场景

### 餐厅搜索
```
示例：浦东新区附近有什么好吃的火锅店？
```

### 酒店预订
```
示例：找一家适合商务宴请的餐厅，要求环境好、停车方便、人均300-500元
```

### 美发服务
```
示例：静安区评分高的日料推荐
```

## 🏗️ 技术架构

```
用户 → GitHub Pages → iframe → Gradio (HF Spaces) → API → GPU Server
```

### 前端
- **Gradio**: 快速构建交互界面
- **部署**: Hugging Face Spaces（免费）

### 后端
- **FastAPI**: 高性能 API 框架
- **GPU 加速**: CUDA + PyTorch
- **向量检索**: FAISS/Qdrant/Milvus
- **LLM**: Qwen/GPT-4/Claude

## 🔧 配置

本 Space 需要连接到后端 RAG 服务器。

### 环境变量

在 Space Settings 中配置：

- `RAG_SERVER_URL`: RAG 后端服务器地址（例如: `https://rag.your-domain.com`）
- `RAG_API_KEY`: API 认证密钥（如果需要）

## 📚 更多信息

- [项目主页](https://your-username.github.io/localsearchbench)
- [GitHub 仓库](https://github.com/your-username/localsearchbench.github.io)
- [论文](https://arxiv.org/abs/xxx)
- [Hugging Face](https://huggingface.co/localsearchbench)

## 🙏 致谢

感谢以下开源项目：
- [Gradio](https://gradio.app/)
- [Hugging Face](https://huggingface.co/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Qwen](https://github.com/QwenLM/Qwen)

## 📄 许可证

Apache License 2.0

