# MCP Tools for LocalSearchBench

基于 MCP (Model Context Protocol) 的 RAG 搜索工具，参考 RL-Factory 项目实现。

## 功能特性

- **RAG 搜索**: 查询本地商户信息（餐厅、商店等）
- **网络搜索**: 支持 Google、Bing、DuckDuckGo
- **标准 MCP 协议**: 兼容所有支持 MCP 的 AI 应用（Claude Desktop、Cursor 等）

## 快速开始

### 1. 安装依赖

```bash
pip install -r mcp_tools/requirements.txt
```

### 2. 启动 RAG 服务器

确保 RAG 服务器在运行：

```bash
cd server
bash start_rag_server.sh
```

RAG 服务器将在 `http://127.0.0.1:5003` 运行。

### 3. 测试 MCP 工具

```bash
# 直接运行测试
python3 mcp_tools/rag_search.py
```

### 4. 配置到 AI 应用

#### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "localsearch": {
      "command": "python3",
      "args": [
        "/Users/hehang03/code/localsearchbench.github.io/mcp_tools/rag_search.py"
      ]
    }
  }
}
```

#### Cursor IDE

将 `mcp_config.json` 添加到项目配置中。

## 可用工具

### query_rag

查询本地商户信息。

**参数**:
- `query` (str): 查询文本，例如 "附近好吃的火锅店"
- `city` (str, 可选): 城市名称，默认 "上海"
- `topk` (int, 可选): 返回结果数量，默认 5
- `retrieval_k` (int, 可选): 检索候选数量，默认 50

**示例**:
```python
query_rag("朝阳区附近有什么好吃的日料", city="北京", topk=3)
```

### web_search

网络搜索工具。

**参数**:
- `query` (str): 搜索查询
- `search_type` (str, 可选): 搜索引擎类型，默认 "google"
- `max_results` (int, 可选): 最大结果数，默认 5

**示例**:
```python
web_search("最新的 AI 技术趋势", search_type="google", max_results=5)
```

## 架构说明

```
mcp_tools/
├── rag_search.py          # MCP 工具实现（基于 fastmcp）
├── requirements.txt       # Python 依赖
├── mcp_config.json        # MCP 配置文件
└── README.md              # 本文档
```

## 与 RAG 服务器通信

MCP 工具通过 HTTP 与 RAG 服务器通信：

- **RAG 搜索端点**: `POST http://127.0.0.1:5003/search`
- **网络搜索端点**: `POST http://127.0.0.1:5003/web_search`

## 参考

本实现参考了 [RL-Factory](https://github.com/bytedance/RL-Factory) 项目的 MCP 工具设计：

- `RL-Factory/envs/tools/search.py` - MCP 工具实现
- `RL-Factory/envs/configs/mcp_tools.pydata` - 配置格式
- `RL-Factory/envs/utils/mcp_manager.py` - MCP 管理器

## 故障排查

### 连接失败

确保 RAG 服务器正在运行：
```bash
curl http://127.0.0.1:5003/health
```

### 依赖问题

升级 MCP 库：
```bash
pip install --upgrade mcp fastmcp
```

## License

Apache 2.0 License

