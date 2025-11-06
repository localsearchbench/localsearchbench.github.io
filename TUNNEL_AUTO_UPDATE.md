# Cloudflare 临时隧道自动更新

本文档介绍如何使用自动监控脚本来检测和更新 Cloudflare 临时隧道。

## 功能特性

- ✅ 自动检测隧道是否运行
- ✅ 定期检查隧道是否可访问（健康检查）
- ✅ 隧道挂掉时自动重启
- ✅ 自动更新配置文件中的隧道 URL
- ✅ 详细的日志记录
- ✅ 连续失败阈值机制（避免频繁重启）

## 使用方法

### 方式一：使用 Shell 脚本（推荐 macOS/Linux）

#### 1. 赋予执行权限

```bash
chmod +x auto_update_tunnel.sh
```

#### 2. 启动监控

```bash
# 持续监控模式（默认）
./auto_update_tunnel.sh monitor

# 或者直接运行
./auto_update_tunnel.sh
```

#### 3. 其他命令

```bash
# 启动隧道
./auto_update_tunnel.sh start

# 停止隧道
./auto_update_tunnel.sh stop

# 重启隧道
./auto_update_tunnel.sh restart

# 检查状态
./auto_update_tunnel.sh status
```

### 方式二：使用 Python 脚本（跨平台）

#### 1. 安装依赖

```bash
pip install requests
```

#### 2. 启动监控

```bash
# 持续监控模式（默认）
python auto_update_tunnel.py monitor

# 或者直接运行
python auto_update_tunnel.py
```

#### 3. 其他命令

```bash
# 启动隧道
python auto_update_tunnel.py start

# 停止隧道
python auto_update_tunnel.py stop

# 重启隧道
python auto_update_tunnel.py restart

# 检查状态
python auto_update_tunnel.py status
```

## 工作原理

### 1. 监控流程

```
开始监控
    ↓
检查隧道进程是否运行
    ↓ 否 → 重启隧道
    ↓ 是
获取隧道 URL
    ↓
检查 URL 是否可访问（/health 端点）
    ↓ 否 → 记录失败次数
    ↓ 是 → 重置失败次数
    ↓
失败次数 ≥ 3？
    ↓ 是 → 重启隧道
    ↓ 否
等待 30 秒
    ↓
循环
```

### 2. 隧道重启流程

```
停止现有隧道进程
    ↓
清空日志文件
    ↓
启动新的隧道
    ↓
等待并获取新的 URL
    ↓
更新配置文件
    ↓
完成
```

### 3. 配置文件更新

脚本会自动更新 `static/js/config.js` 中的 `RAG_SERVER_URL`：

```javascript
// 更新前
RAG_SERVER_URL: 'https://old-url.trycloudflare.com',

// 更新后
RAG_SERVER_URL: 'https://new-url.trycloudflare.com',
```

## 配置参数

### Shell 脚本配置

编辑 `auto_update_tunnel.sh` 顶部的配置：

```bash
CONFIG_FILE="static/js/config.js"      # 配置文件路径
LOG_FILE="cloudflared.log"             # Cloudflare 日志文件
TUNNEL_LOG="tunnel_updates.log"        # 监控日志文件
CHECK_INTERVAL=30                      # 检查间隔（秒）
```

### Python 脚本配置

编辑 `auto_update_tunnel.py` 顶部的配置：

```python
CONFIG_FILE = "static/js/config.js"    # 配置文件路径
LOG_FILE = "cloudflared.log"           # Cloudflare 日志文件
TUNNEL_LOG = "tunnel_updates.log"      # 监控日志文件
CHECK_INTERVAL = 30                    # 检查间隔（秒）
MAX_FAILURES = 3                       # 最大连续失败次数
```

## 日志文件

### 1. `cloudflared.log`
Cloudflare 隧道的原始日志，包含隧道 URL 等信息。

### 2. `tunnel_updates.log`
监控脚本的日志，记录所有检查和更新操作：

```
[2025-11-06 10:30:00] 🔍 开始监控 Cloudflare 隧道
[2025-11-06 10:30:00] 检查间隔: 30秒
[2025-11-06 10:30:30] ✅ 隧道正常运行: https://xxx.trycloudflare.com
[2025-11-06 10:35:00] ⚠️  隧道无法访问 (失败次数: 1/3)
[2025-11-06 10:35:30] ⚠️  隧道无法访问 (失败次数: 2/3)
[2025-11-06 10:36:00] ❌ 隧道连续失败 3 次，正在重启...
[2025-11-06 10:36:10] 🚀 启动新的 Cloudflare 隧道...
[2025-11-06 10:36:15] ✅ 隧道已启动: https://yyy.trycloudflare.com
[2025-11-06 10:36:15] ✅ 配置文件已更新: https://yyy.trycloudflare.com
```

## 后台运行

### 使用 nohup（Shell 脚本）

```bash
nohup ./auto_update_tunnel.sh monitor > monitor.log 2>&1 &
```

### 使用 screen

```bash
# 创建新会话
screen -S tunnel-monitor

# 运行监控脚本
./auto_update_tunnel.sh monitor

# 按 Ctrl+A 然后按 D 分离会话
# 重新连接: screen -r tunnel-monitor
```

### 使用 tmux

```bash
# 创建新会话
tmux new -s tunnel-monitor

# 运行监控脚本
./auto_update_tunnel.sh monitor

# 按 Ctrl+B 然后按 D 分离会话
# 重新连接: tmux attach -t tunnel-monitor
```

### 使用 systemd（Linux）

创建服务文件 `/etc/systemd/system/tunnel-monitor.service`：

```ini
[Unit]
Description=Cloudflare Tunnel Monitor
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/localsearchbench.github.io
ExecStart=/path/to/localsearchbench.github.io/auto_update_tunnel.sh monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable tunnel-monitor
sudo systemctl start tunnel-monitor
sudo systemctl status tunnel-monitor
```

## 停止监控

### 前台运行时

按 `Ctrl+C` 停止

### 后台运行时

```bash
# 查找进程
ps aux | grep auto_update_tunnel

# 停止进程
kill <PID>

# 或者使用 pkill
pkill -f auto_update_tunnel
```

## 故障排除

### 1. 隧道无法启动

**问题**: 脚本显示"隧道启动超时"

**解决方案**:
- 检查 `cloudflared` 是否已安装: `which cloudflared`
- 检查端口 8000 是否被占用: `lsof -i :8000`
- 手动测试隧道: `cloudflared tunnel --url http://localhost:8000`

### 2. 配置文件未更新

**问题**: 隧道 URL 已改变但配置文件没有更新

**解决方案**:
- 检查配置文件路径是否正确
- 检查文件权限: `ls -l static/js/config.js`
- 查看备份文件: `static/js/config.js.backup`

### 3. 频繁重启

**问题**: 隧道频繁重启

**解决方案**:
- 增加 `CHECK_INTERVAL` 值（如改为 60 秒）
- 增加 `MAX_FAILURES` 值（如改为 5）
- 检查网络连接是否稳定
- 检查 RAG 服务器是否正常运行

### 4. Python 脚本依赖问题

**问题**: `ModuleNotFoundError: No module named 'requests'`

**解决方案**:
```bash
pip install requests
```

## 最佳实践

1. **使用 tmux 或 screen**: 在后台持续运行监控脚本
2. **定期查看日志**: 检查 `tunnel_updates.log` 了解隧道状态
3. **调整检查间隔**: 根据需要调整 `CHECK_INTERVAL`
4. **备份配置文件**: 脚本会自动备份，但建议定期手动备份
5. **监控资源使用**: 确保监控脚本不会消耗过多资源

## 与现有服务集成

如果您已经在运行 RAG 服务器，可以这样启动：

```bash
# 终端 1: 启动 RAG 服务器
cd server
python rag_server.py

# 终端 2: 启动隧道监控
cd ..
./auto_update_tunnel.sh monitor
```

或者使用 tmux 一次性启动：

```bash
# 创建新会话并启动 RAG 服务器
tmux new -s rag-server -d "cd server && python rag_server.py"

# 创建新会话并启动隧道监控
tmux new -s tunnel-monitor -d "./auto_update_tunnel.sh monitor"

# 查看所有会话
tmux ls
```

## 注意事项

1. **临时隧道限制**: Cloudflare 临时隧道可能会在一段时间后自动关闭，监控脚本会自动重启
2. **配置文件格式**: 确保 `config.js` 中的 URL 格式正确
3. **健康检查端点**: 确保 RAG 服务器有 `/health` 端点
4. **文件权限**: 确保脚本有读写配置文件的权限
5. **进程管理**: 避免同时运行多个监控实例

## 更新记录

- 2025-11-06: 初始版本，支持自动检测和更新隧道

