# 动态配置系统使用说明

## 🎯 概述

LocalSearchBench 现在支持**动态隧道 URL 配置**，无需每次隧道变化时都手动提交代码。系统会自动：
1. 监控 Cloudflare 隧道状态
2. 检测隧道失效并自动重启
3. 更新配置文件
4. 自动提交并推送到 GitHub Pages

## 📁 文件结构

```
localsearchbench.github.io/
├── tunnel_config.json          # 动态配置文件（前端读取）
├── static/js/config.js         # 静态配置文件（包含动态加载逻辑）
├── auto_update_tunnel.sh       # 隧道监控和自动重启
├── auto_commit_config.sh       # 自动提交配置到 GitHub
└── start_auto_sync.sh          # 一键启动所有服务
```

## 🚀 快速开始

### 方法 1：一键启动（推荐）

```bash
# 启动所有服务（隧道监控 + 自动提交）
./start_auto_sync.sh start

# 查看服务状态
./start_auto_sync.sh status

# 查看日志
./start_auto_sync.sh logs all

# 停止所有服务
./start_auto_sync.sh stop
```

### 方法 2：分别启动

```bash
# 1. 启动隧道监控（后台运行）
./auto_update_tunnel.sh monitor &

# 2. 启动自动提交（后台运行）
./auto_commit_config.sh monitor &
```

## 🔧 工作原理

### 1. 隧道监控 (`auto_update_tunnel.sh`)

- **功能**：每 30 秒检查一次隧道状态
- **自动重启**：连续失败 3 次后自动重启隧道
- **配置更新**：更新 `tunnel_config.json` 和 `static/js/config.js`

**日志文件**：
- `tunnel_updates.log` - 隧道状态日志
- `cloudflared.log` - Cloudflare 隧道原始日志

### 2. 自动提交 (`auto_commit_config.sh`)

- **功能**：每 60 秒检查配置文件是否有更新
- **自动推送**：检测到更新后自动提交并推送到 GitHub
- **防抖动**：至少间隔 30 秒才会提交，避免频繁推送

**日志文件**：
- `commit_monitor.log` - 提交和推送日志

### 3. 前端动态加载 (`static/js/config.js`)

```javascript
// 页面加载时自动从 tunnel_config.json 获取最新 URL
await loadDynamicConfig();

// 监听配置加载完成事件
window.addEventListener('configLoaded', (event) => {
    console.log('配置已加载:', event.detail.RAG_SERVER_URL);
});
```

**特点**：
- ✅ 自动防止浏览器缓存（添加时间戳参数）
- ✅ 失败时使用静态配置作为后备
- ✅ 触发自定义事件通知其他模块

## 📊 配置文件格式

### `tunnel_config.json`

```json
{
  "rag_server_url": "https://your-tunnel.trycloudflare.com",
  "updated_at": "2025-11-06T11:45:47+08:00",
  "status": "active",
  "version": "1.0"
}
```

## 🛠️ 常用命令

### 查看服务状态

```bash
./start_auto_sync.sh status
```

输出示例：
```
✅ 隧道监控: 运行中 (PID: 12345)
✅ 自动提交: 运行中 (PID: 12346)
✅ Cloudflare 隧道: 运行中
🌐 当前隧道: https://example.trycloudflare.com
```

### 查看实时日志

```bash
# 查看所有日志
./start_auto_sync.sh logs all

# 只看隧道日志
./start_auto_sync.sh logs tunnel

# 只看提交日志
./start_auto_sync.sh logs commit
```

### 手动触发操作

```bash
# 手动重启隧道
./auto_update_tunnel.sh restart

# 手动提交配置
./auto_commit_config.sh commit

# 检查隧道状态
./auto_update_tunnel.sh status
```

## 🔍 故障排查

### 问题 1：隧道频繁重启

**原因**：可能是网络不稳定或 RAG 服务器未运行

**解决**：
```bash
# 1. 检查 RAG 服务器是否运行
curl http://localhost:8000/health

# 2. 查看隧道日志
tail -f cloudflared.log

# 3. 调整检查间隔（编辑 auto_update_tunnel.sh）
CHECK_INTERVAL=60  # 改为 60 秒
```

### 问题 2：配置未自动推送

**原因**：可能是 Git 权限问题或网络问题

**解决**：
```bash
# 1. 检查 Git 状态
git status

# 2. 手动推送测试
git push origin master

# 3. 查看提交日志
tail -f commit_monitor.log
```

### 问题 3：前端显示旧的 URL

**原因**：浏览器缓存

**解决**：
1. 强制刷新浏览器：`Cmd + Shift + R` (Mac) 或 `Ctrl + Shift + R` (Windows)
2. 清除浏览器缓存
3. 使用隐私/无痕模式

## ⚙️ 高级配置

### 自定义内网服务器地址

```bash
# 设置环境变量
export RAG_SERVER_URL="http://192.168.1.100:8000"

# 启动隧道
./auto_update_tunnel.sh start
```

### 修改检查间隔

编辑 `auto_update_tunnel.sh`：
```bash
CHECK_INTERVAL=30  # 隧道检查间隔（秒）
```

编辑 `auto_commit_config.sh`：
```bash
COMMIT_INTERVAL=60  # 提交检查间隔（秒）
```

### 修改失败阈值

编辑 `auto_update_tunnel.sh`：
```bash
max_failures=3  # 连续失败多少次后重启
```

## 📝 开机自启动

### macOS (使用 launchd)

创建 `~/Library/LaunchAgents/com.localsearchbench.autosync.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.localsearchbench.autosync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/code/localsearchbench.github.io/start_auto_sync.sh</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/code/localsearchbench.github.io/autosync.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/code/localsearchbench.github.io/autosync.error.log</string>
</dict>
</plist>
```

加载服务：
```bash
launchctl load ~/Library/LaunchAgents/com.localsearchbench.autosync.plist
```

### Linux (使用 systemd)

创建 `/etc/systemd/system/localsearchbench-autosync.service`：

```ini
[Unit]
Description=LocalSearchBench Auto Sync Service
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/localsearchbench.github.io
ExecStart=/path/to/localsearchbench.github.io/start_auto_sync.sh start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable localsearchbench-autosync
sudo systemctl start localsearchbench-autosync
```

## 🎉 优势

### 之前的方式
❌ 隧道挂了需要手动重启  
❌ URL 变化需要手动修改代码  
❌ 需要手动 git commit 和 push  
❌ GitHub Pages 更新需要等待部署  

### 现在的方式
✅ 隧道自动监控和重启  
✅ URL 自动更新到配置文件  
✅ 自动提交和推送到 GitHub  
✅ 前端动态加载最新配置  
✅ 完全自动化，无需人工干预  

## 📞 支持

如有问题，请查看：
- 隧道日志：`tail -f tunnel_updates.log`
- 提交日志：`tail -f commit_monitor.log`
- Cloudflare 日志：`tail -f cloudflared.log`

或运行诊断命令：
```bash
./start_auto_sync.sh status
```

