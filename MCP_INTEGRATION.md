# MCP 工具集成指南

## 概述

本项目已集成 MCP (Model Context Protocol) 工具，支持将 RAG 搜索功能作为标准 MCP 工具暴露给 AI 应用使用。

参考项目：[RL-Factory](https://github.com/bytedance/RL-Factory) 的 MCP 工具实现

## 项目结构

```
localsearchbench.github.io/
├── mcp_tools/                    # MCP 工具目录
│   ├── __init__.py              # Python 包初始化
│   ├── rag_search.py            # MCP RAG 搜索工具实现
│   ├── requirements.txt         # 依赖列表
│   ├── mcp_config.json          # MCP 配置文件
│   ├── README.md                # 详细文档
│   ├── demo.py                  # 使用示例
│   ├── test_mcp_tools.py        # 测试脚本
│   └── start_mcp_tools.sh       # 启动脚本
│
├── server/                       # RAG 服务器
│   ├── rag_server.py            # RAG 服务器实现
│   └── start_rag_server.sh      # 启动脚本
│
└── MCP_INTEGRATION.md           # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
# 安装 MCP 工具依赖
pip install -r mcp_tools/requirements.txt

# 安装 RAG 服务器依赖
pip install -r server/requirements.txt
```

### 2. 启动 RAG 服务器

```bash
cd server
bash start_rag_server.sh
```

RAG 服务器将在 `http://127.0.0.1:5003` 运行。

### 3. 测试 MCP 工具

```bash
# 运行演示
python3 mcp_tools/demo.py

# 或者运行测试
python3 mcp_tools/test_mcp_tools.py --direct
```

## 配置 AI 应用

### Claude Desktop

1. 找到配置文件：
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. 添加配置：

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

3. 重启 Claude Desktop

4. 在对话中使用：
   - "帮我找朝阳区附近好吃的火锅店"
   - "上海静安区有哪些适合办公的咖啡店"

### Cursor IDE

1. 在项目中打开 `mcp_tools/mcp_config.json`

2. Cursor 会自动识别 MCP 配置

3. 在 AI 对话中使用工具

### 其他 MCP 兼容应用

任何支持 MCP 协议的应用都可以使用本工具。参考 `mcp_tools/mcp_config.json` 进行配置。

## 可用工具

### query_rag

查询本地商户信息的 RAG 搜索工具。

**功能**：
- 基于语义搜索找到相关商户
- 支持多城市查询
- 返回商户名称、地址、评分、价格等信息
- 包含 AI 生成的搜索摘要

**参数**：
- `query` (必需): 查询文本，例如 "好吃的火锅店"
- `city` (可选): 城市名称，默认 "上海"
- `topk` (可选): 返回结果数量，默认 5
- `retrieval_k` (可选): 检索候选数量，默认 50

**示例**：
```python
query_rag(
    query="朝阳区附近有什么好吃的火锅店",
    city="北京",
    topk=3
)
```

**返回格式**：
```
查询: 朝阳区附近有什么好吃的火锅店
城市: 北京
找到 3 个相关商户

摘要:
[AI 生成的搜索摘要]

商户 1:
- 名称: 海底捞火锅
- 地址: 朝阳区xxx
- 评分: 4.5
- 价格: 100
- 类型: 火锅
- 相似度: 0.8542

...
```

### web_search

网络搜索工具（如果 RAG 服务器支持）。

**参数**：
- `query` (必需): 搜索查询
- `search_type` (可选): 搜索引擎类型，默认 "google"
- `max_results` (可选): 最大结果数，默认 5

## 技术细节

### MCP 协议

MCP (Model Context Protocol) 是一个开放标准，允许 AI 应用安全地调用外部工具和数据源。

**核心特性**：
- 标准化的工具定义
- 参数验证
- 错误处理
- 跨平台兼容

### 实现参考

本实现参考了 RL-Factory 项目的以下组件：

1. **MCP 工具实现** (`RL-Factory/envs/tools/search.py`):
   - 使用 `fastmcp` 库定义工具
   - 通过 HTTP 与后端服务通信
   - 完善的错误处理

2. **配置格式** (`RL-Factory/envs/configs/mcp_tools.pydata`):
   - 标准 MCP 服务器配置
   - 命令行参数定义
   - 环境变量支持

3. **管理器模式** (`RL-Factory/envs/utils/mcp_manager.py`):
   - 单例模式管理 MCP 客户端
   - 异步事件循环
   - 连接重试机制

### 架构图

```
┌─────────────────┐
│  AI 应用        │
│  (Claude/Cursor)│
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────┐
│  MCP Tool       │
│  rag_search.py  │
└────────┬────────┘
         │ HTTP
         │
┌────────▼────────┐
│  RAG Server     │
│  rag_server.py  │
└────────┬────────┘
         │
┌────────▼────────┐
│  Vector Store   │
│  FAISS Index    │
└─────────────────┘
```

## 开发指南

### 添加新工具

1. 在 `mcp_tools/rag_search.py` 中定义新工具：

```python
@mcp.tool()
def your_new_tool(param1: str, param2: int = 10):
    """工具描述
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        
    Returns:
        str: 返回值说明
    """
    # 实现逻辑
    pass
```

2. 更新 `__init__.py` 导出新工具

3. 添加测试用例

4. 更新文档

### 调试技巧

1. **查看 MCP 通信日志**：
   ```bash
   # 启动时查看详细输出
   python3 mcp_tools/rag_search.py
   ```

2. **测试 RAG 服务器连接**：
   ```bash
   curl http://127.0.0.1:5003/health
   ```

3. **直接调用工具**：
   ```bash
   python3 mcp_tools/demo.py
   ```

## 故障排查

### 问题：MCP 工具无法连接到 RAG 服务器

**解决方案**：
1. 确认 RAG 服务器正在运行
2. 检查端口 5003 是否被占用
3. 查看服务器日志

### 问题：Claude Desktop 无法识别工具

**解决方案**：
1. 检查配置文件路径是否正确
2. 确认 Python 路径正确
3. 重启 Claude Desktop
4. 查看 Claude 的日志文件

### 问题：工具调用超时

**解决方案**：
1. 增加超时时间（在 `rag_search.py` 中修改 `timeout` 参数）
2. 检查网络连接
3. 优化 RAG 服务器性能

## 性能优化

1. **连接池**：MCP Manager 自动管理连接
2. **缓存**：考虑添加查询结果缓存
3. **批量查询**：支持一次查询多个商户
4. **异步处理**：使用 async/await 提高并发性能

## 安全考虑

1. **本地运行**：工具默认连接本地服务器
2. **无代理访问**：绕过系统代理，确保本地连接
3. **超时保护**：防止长时间阻塞
4. **错误隔离**：工具错误不影响 AI 应用主流程

## 参考资料

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [RL-Factory 项目](https://github.com/bytedance/RL-Factory)
- [FastMCP 文档](https://github.com/jlowin/fastmcp)
- [Claude Desktop MCP 配置](https://docs.anthropic.com/claude/docs/model-context-protocol)

## 贡献

欢迎提交 Issue 和 Pull Request！

## License

Apache 2.0 License

