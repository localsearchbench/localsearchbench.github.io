# 🌐 Mac 代理服务器配置指南

## 📋 概述

本指南帮助您配置 Mac 作为代理服务器，让远程服务器通过 Mac 访问外网。

## 🖥️ Mac 端配置（已完成 ✅）

### 1. 代理服务器状态

- **监听地址**: `0.0.0.0:8410`
- **Mac IP**: `172.31.3.48`
- **代理 URL**: `http://172.31.3.48:8410`
- **防火墙**: 已关闭 ✅

### 2. 检查代理服务器

```bash
# 查看是否在运行
lsof -i :8410

# 查看日志
tail -f ~/proxy_server.log
```

### 3. 重启代理服务器（如需要）

```bash
# 停止（如果在运行）
pkill -f "python.*proxy"

# 启动
python3 - << 'SCRIPT'
import http.server
import socketserver
import urllib.request
from http import HTTPStatus

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request()
    
    def do_POST(self):
        self.proxy_request()
    
    def do_HEAD(self):
        self.proxy_request()
    
    def proxy_request(self):
        try:
            print(f"✅ [{self.command}] 代理请求成功: {self.path}")
            req = urllib.request.Request(self.path, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                self.send_response(HTTPStatus.OK)
                for key, value in response.headers.items():
                    self.send_header(key, value)
                self.end_headers()
                if self.command != 'HEAD':
                    self.wfile.write(response.read())
        except Exception as e:
            print(f"❌ 代理请求失败: {e}")
            self.send_error(HTTPStatus.BAD_GATEWAY, str(e))

PORT = 8410
with socketserver.TCPServer(("0.0.0.0", PORT), ProxyHTTPRequestHandler) as httpd:
    print(f"🚀 代理服务器启动在 0.0.0.0:{PORT}")
    httpd.serve_forever()
SCRIPT
```

## 🖧 服务器端配置

### 方法 1: 使用自动配置脚本（推荐）

```bash
# 1. 将脚本复制到服务器
scp server/setup_proxy.sh hadoop-ai-search@set-zw04-mlp-codelab-pc398:~/

# 2. 在服务器上运行
ssh hadoop-ai-search@set-zw04-mlp-codelab-pc398
cd ~
chmod +x setup_proxy.sh
./setup_proxy.sh
```

### 方法 2: 手动配置

```bash
# 1. 测试连接
nc -zv 172.31.3.48 8410

# 2. 测试代理
curl -x http://172.31.3.48:8410 -I http://www.baidu.com

# 3. 设置环境变量（临时）
export http_proxy=http://172.31.3.48:8410
export https_proxy=http://172.31.3.48:8410

# 4. 测试是否生效
curl -I http://www.baidu.com

# 5. 永久配置（添加到 ~/.bashrc 或 ~/.zshrc）
cat >> ~/.bashrc << 'BASHRC'
# Mac Proxy Configuration
export http_proxy=http://172.31.3.48:8410
export https_proxy=http://172.31.3.48:8410
export HTTP_PROXY=http://172.31.3.48:8410
export HTTPS_PROXY=http://172.31.3.48:8410
export no_proxy=localhost,127.0.0.1,::1
export NO_PROXY=localhost,127.0.0.1,::1
# End Mac Proxy
BASHRC

# 6. 使配置生效
source ~/.bashrc
```

## 🧪 测试验证

### 在服务器上测试

```bash
# 测试 1: 检查环境变量
echo $http_proxy
# 应该显示: http://172.31.3.48:8410

# 测试 2: 访问百度
curl -I http://www.baidu.com
# 应该返回 HTTP/1.0 200 OK

# 测试 3: 访问 Google（如果可以）
curl -I http://www.google.com

# 测试 4: 下载测试
curl -o /dev/null -w "下载速度: %{speed_download} bytes/sec\n" http://www.baidu.com
```

## �� 常见问题

### 1. 连接超时

```bash
# 检查 Mac 防火墙是否关闭
# 在 Mac 上: 系统偏好设置 → 安全性与隐私 → 防火墙

# 检查网络连通性
ping 172.31.3.48
```

### 2. 代理不生效

```bash
# 检查环境变量
env | grep -i proxy

# 重新加载配置
source ~/.bashrc
```

### 3. 临时禁用代理

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
```

### 4. 永久禁用代理

```bash
# 编辑配置文件
vim ~/.bashrc
# 删除或注释掉代理配置部分
source ~/.bashrc
```

## 📊 代理服务器监控

### 在 Mac 上查看日志

```bash
tail -f ~/proxy_server.log
```

### 查看连接状态

```bash
# Mac 上
netstat -an | grep 8410

# 服务器上
netstat -an | grep 172.31.3.48:8410
```

## 🔒 安全建议

1. **仅在受信任的网络中使用**
2. **定期检查连接日志**
3. **使用完毕后关闭代理服务器**
4. **考虑使用 SSH 隧道加密流量**

## 🚇 SSH 隧道方案（可选）

如果需要更安全的连接，可以使用 SSH 反向隧道：

```bash
# 在 Mac 上运行
ssh -R 8410:localhost:8410 -N hadoop-ai-search@set-zw04-mlp-codelab-pc398

# 然后在服务器上使用 localhost
export http_proxy=http://localhost:8410
export https_proxy=http://localhost:8410
```

## 📞 支持

如有问题，请检查：
1. Mac 代理服务器日志
2. 网络连接状态
3. 防火墙设置
4. 环境变量配置

---

**最后更新**: 2025-11-04
