# MCP 工具快速入门

## 5 分钟快速开始

### Step 1: 安装依赖（1 分钟）

```bash
cd /Users/hehang03/code/localsearchbench.github.io
pip install -r mcp_tools/requirements.txt
```

### Step 2: 启动 RAG 服务器（1 分钟）

```bash
cd server
bash start_rag_server.sh
```

等待看到：
```
✅ RAG server started successfully!
🌐 Server running at: http://127.0.0.1:5003
```

### Step 3: 测试工具（1 分钟）

打开新终端：

```bash
cd /Users/hehang03/code/localsearchbench.github.io
python3 mcp_tools/demo.py
```

你应该看到搜索结果输出。

### Step 4: 配置 Claude Desktop（2 分钟）

1. 打开配置文件：

```bash
# macOS
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. 添加以下内容：

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

### Step 5: 在 Claude 中使用

现在你可以在 Claude 中这样问：

```
帮我找朝阳区附近好吃的火锅店
```

Claude 会自动调用 `query_rag` 工具并返回结果！

---

## 常见场景示例

### 场景 1: 找餐厅

**你问**：
> 找一家静安区附近适合约会的高档餐厅

**Claude 会**：
1. 调用 `query_rag("适合约会的高档餐厅", city="上海")`
2. 分析返回的商户信息
3. 给出推荐和理由

### 场景 2: 比较商户

**你问**：
> 比较一下朝阳区的两家日料店：xx寿司 vs yy料理

**Claude 会**：
1. 分别查询两家店的信息
2. 对比评分、价格、位置
3. 给出详细对比

### 场景 3: 规划路线

**你问**：
> 我在国贸，想找附近的咖啡店工作2小时，然后去吃午饭

**Claude 会**：
1. 查询国贸附近的咖啡店
2. 查询午餐选择
3. 给出完整的时间规划

---

## 命令速查

```bash
# 启动 RAG 服务器
cd server && bash start_rag_server.sh

# 测试 MCP 工具
python3 mcp_tools/demo.py

# 运行单元测试
python3 mcp_tools/test_mcp_tools.py --direct

# 启动 MCP 服务（用于 Claude Desktop）
python3 mcp_tools/rag_search.py

# 检查服务器健康
curl http://127.0.0.1:5003/health
```

---

## 故障排查 FAQ

### Q: Claude Desktop 看不到工具？

**A**: 检查配置文件：
1. 路径是否正确（使用绝对路径）
2. JSON 格式是否正确
3. 是否重启了 Claude Desktop

### Q: 工具调用失败？

**A**: 
1. 确认 RAG 服务器正在运行
2. 测试本地连接：`curl http://127.0.0.1:5003/health`
3. 查看服务器日志

### Q: 搜索结果为空？

**A**: 
1. 检查查询的城市是否有数据
2. 尝试更通用的查询词
3. 调整 `topk` 和 `retrieval_k` 参数

---

## 下一步

- 📖 阅读完整文档：[MCP_INTEGRATION.md](../MCP_INTEGRATION.md)
- 🔧 查看工具详情：[README.md](README.md)
- 💡 了解 RL-Factory 参考实现：[GitHub](https://github.com/bytedance/RL-Factory)

---

## 需要帮助？

- 查看 Issues: https://github.com/localsearchbench/localsearchbench.github.io/issues
- 阅读 MCP 官方文档: https://modelcontextprotocol.io/

