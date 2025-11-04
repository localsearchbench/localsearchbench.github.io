# 📚 文档导航指南

本项目包含精简的文档集合，每个文档都有明确的用途。

## 📖 核心文档（按使用顺序）

### 1. 新手入门

| 文档 | 用途 | 适合人群 |
|------|------|---------|
| **[README.md](README.md)** | 项目总览和介绍 | 所有人 |
| **[server/README_QUICKSTART.md](server/README_QUICKSTART.md)** | 三步启动 RAG 服务器 | 想快速启动的新手 ⭐ |
| **[README_GRADIO.md](README_GRADIO.md)** | Gradio 界面使用指南 | 想用 UI 体验的用户 |

### 2. 深入配置

| 文档 | 用途 | 适合人群 |
|------|------|---------|
| **[MODEL_SPEC.md](MODEL_SPEC.md)** | 模型规格和要求 | 需要了解模型配置的人 |
| **[SERVER_INTEGRATION.md](SERVER_INTEGRATION.md)** | 服务器详细配置 | 高级用户、系统管理员 |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | 部署选项和最佳实践 | 部署到生产环境的人 |

## 🛠️ 配置文件

| 文件 | 说明 |
|------|------|
| **[server/config.example.sh](server/config.example.sh)** | 环境变量配置模板 |
| **[server/start_rag_server.sh](server/start_rag_server.sh)** | 快速启动脚本 |
| **[server/deploy.sh](server/deploy.sh)** | 一键部署脚本（Docker/Systemd） |
| **[server/test_server.sh](server/test_server.sh)** | 服务器测试脚本 |

## 🚀 推荐阅读路径

### 路径 A: 我想快速体验 ✨

```
README.md 
  ↓
server/README_QUICKSTART.md (三步启动)
  ↓
开始使用！
```

### 路径 B: 我想了解技术细节 🔧

```
README.md
  ↓
MODEL_SPEC.md (了解模型)
  ↓
server/README_QUICKSTART.md (启动服务)
  ↓
SERVER_INTEGRATION.md (深入配置)
```

### 路径 C: 我想部署到生产环境 🚀

```
README.md
  ↓
MODEL_SPEC.md (模型要求)
  ↓
SERVER_INTEGRATION.md (服务器配置)
  ↓
DEPLOYMENT.md (部署方案)
  ↓
使用 server/deploy.sh 部署
```

### 路径 D: 我想用 Gradio UI 🎨

```
README.md
  ↓
README_GRADIO.md (Gradio 使用)
  ↓
运行 ./run_gradio.sh
```

## 📂 文档结构

```
localsearchbench.github.io/
│
├── README.md                      # 项目主页
├── DOCS_GUIDE.md                  # 本文档（导航指南）
├── MODEL_SPEC.md                  # 模型规格说明
├── SERVER_INTEGRATION.md          # 服务器集成详解
├── DEPLOYMENT.md                  # 部署指南
├── README_GRADIO.md               # Gradio 使用说明
│
└── server/
    ├── README_QUICKSTART.md       # ⭐ 快速启动（推荐从这里开始）
    ├── config.example.sh          # 配置模板
    ├── start_rag_server.sh        # 启动脚本
    ├── deploy.sh                  # 部署脚本
    ├── test_server.sh             # 测试脚本
    └── rag_server.py              # 主程序
```

## 🎯 快速查找

### 我想知道...

**...如何快速启动？**
→ [server/README_QUICKSTART.md](server/README_QUICKSTART.md)

**...使用什么模型？**
→ [MODEL_SPEC.md](MODEL_SPEC.md)

**...如何配置环境变量？**
→ [server/config.example.sh](server/config.example.sh)

**...有哪些启动方式？**
→ [SERVER_INTEGRATION.md](SERVER_INTEGRATION.md) 的"4 种启动方式"部分

**...如何部署到生产环境？**
→ [DEPLOYMENT.md](DEPLOYMENT.md) 或使用 [server/deploy.sh](server/deploy.sh)

**...如何使用 Gradio 界面？**
→ [README_GRADIO.md](README_GRADIO.md)

**...如何测试服务器？**
→ 运行 `server/test_server.sh`

## 💡 文档设计原则

本项目遵循以下文档设计原则：

1. **避免重复** - 每个主题只在一个地方详细说明
2. **清晰导航** - 文档间相互链接，易于跳转
3. **分层设计** - 快速开始 → 详细配置 → 高级部署
4. **实用优先** - 提供可执行的脚本和配置

## 🔄 文档维护

如需更新文档：

1. **模型变更** → 更新 MODEL_SPEC.md
2. **配置变更** → 更新 server/config.example.sh
3. **部署流程** → 更新 DEPLOYMENT.md
4. **快速开始** → 更新 server/README_QUICKSTART.md

---

**有问题？** 从 [README.md](README.md) 开始，或直接跳到 [server/README_QUICKSTART.md](server/README_QUICKSTART.md) 快速启动！

