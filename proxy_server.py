#!/usr/bin/env python3
"""
简单的 HTTP 代理服务器
将请求从 Mac (11.45.22.196:8000) 转发到内网服务器 (10.164.243.10:8000)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import json

TARGET_SERVER = 'http://10.164.243.10:8000'

class ProxyHandler(BaseHTTPRequestHandler):
    
    def _send_cors_headers(self):
        """发送 CORS 头部"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        """处理 OPTIONS 预检请求"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """转发 GET 请求"""
        target_url = TARGET_SERVER + self.path
        try:
            print(f"GET {target_url}")
            response = urllib.request.urlopen(target_url, timeout=30)
            
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
            self.end_headers()
            
            self.wfile.write(response.read())
        except Exception as e:
            print(f"Error: {e}")
            self.send_error(500, str(e))
    
    def do_POST(self):
        """转发 POST 请求"""
        target_url = TARGET_SERVER + self.path
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            print(f"POST {target_url}")
            print(f"Data: {post_data[:200]}...")  # 打印前200字符
            
            # 创建请求
            req = urllib.request.Request(
                target_url,
                data=post_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # 发送请求
            response = urllib.request.urlopen(req, timeout=30)
            
            # 返回响应
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            self.wfile.write(response.read())
        except Exception as e:
            print(f"Error: {e}")
            self.send_error(500, str(e))

def run_server(port=8000):
    """运行代理服务器"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, ProxyHandler)
    print(f'🚀 Proxy server running on http://0.0.0.0:{port}')
    print(f'📡 Forwarding to {TARGET_SERVER}')
    print(f'🌐 External access: http://11.45.22.196:{port}')
    print('Press Ctrl+C to stop')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n👋 Server stopped')

if __name__ == '__main__':
    run_server()

