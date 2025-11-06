#!/usr/bin/env python3
"""
自动检测和更新 Cloudflare 临时隧道
当隧道挂掉时自动重启并更新配置文件
"""

import os
import re
import time
import signal
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# 配置
CONFIG_FILE = "static/js/config.js"
LOG_FILE = "cloudflared.log"
TUNNEL_LOG = "tunnel_updates.log"
CHECK_INTERVAL = 30  # 每30秒检查一次
MAX_FAILURES = 3  # 连续失败3次后重启

class TunnelMonitor:
    def __init__(self):
        self.config_file = Path(CONFIG_FILE)
        self.log_file = Path(LOG_FILE)
        self.tunnel_log = Path(TUNNEL_LOG)
        self.consecutive_failures = 0
        self.running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.tunnel_log, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def get_tunnel_url(self):
        """从日志文件中提取最新的隧道 URL"""
        if not self.log_file.exists():
            return None
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 查找所有 trycloudflare.com URL
                urls = re.findall(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                if urls:
                    return urls[-1]  # 返回最后一个
        except Exception as e:
            self.log(f"❌ 读取日志文件失败: {e}")
        
        return None
    
    def update_config(self, new_url):
        """更新配置文件中的隧道 URL"""
        if not new_url:
            self.log("❌ 错误: 没有找到新的隧道 URL")
            return False
        
        try:
            # 备份配置文件
            backup_file = self.config_file.with_suffix('.js.backup')
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(backup_file, "w", encoding="utf-8") as f:
                    f.write(content)
            
            # 更新 RAG_SERVER_URL
            with open(self.config_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 替换 URL
            pattern = r"RAG_SERVER_URL: 'https://[a-zA-Z0-9-]+\.trycloudflare\.com'"
            replacement = f"RAG_SERVER_URL: '{new_url}'"
            new_content = re.sub(pattern, replacement, content)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            self.log(f"✅ 配置文件已更新: {new_url}")
            return True
        
        except Exception as e:
            self.log(f"❌ 更新配置文件失败: {e}")
            return False
    
    def check_tunnel_running(self):
        """检查隧道进程是否正在运行"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "cloudflared tunnel"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def check_tunnel_accessible(self, url):
        """检查隧道 URL 是否可访问"""
        if not url:
            return False
        
        try:
            health_url = f"{url}/health"
            response = requests.get(health_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def start_tunnel(self):
        """启动新的隧道"""
        self.log("🚀 启动新的 Cloudflare 隧道...")
        
        try:
            # 清空旧的日志文件
            with open(self.log_file, "w") as f:
                f.write("")
            
            # 启动隧道（后台运行）
            subprocess.Popen(
                ["cloudflared", "tunnel", "--url", "http://localhost:8000"],
                stdout=open(self.log_file, "w"),
                stderr=subprocess.STDOUT
            )
            
            # 等待隧道启动并获取 URL
            max_wait = 30
            waited = 0
            
            while waited < max_wait:
                time.sleep(2)
                waited += 2
                tunnel_url = self.get_tunnel_url()
                
                if tunnel_url:
                    self.log(f"✅ 隧道已启动: {tunnel_url}")
                    
                    # 等待隧道完全就绪
                    time.sleep(3)
                    
                    # 更新配置文件
                    self.update_config(tunnel_url)
                    return True
            
            self.log("❌ 隧道启动超时")
            return False
        
        except Exception as e:
            self.log(f"❌ 启动隧道失败: {e}")
            return False
    
    def stop_tunnel(self):
        """停止现有隧道"""
        self.log("⏹️  停止现有隧道...")
        try:
            subprocess.run(["pkill", "-f", "cloudflared tunnel"])
            time.sleep(2)
        except Exception as e:
            self.log(f"⚠️  停止隧道时出错: {e}")
    
    def monitor(self):
        """主监控循环"""
        self.log("=" * 50)
        self.log("🔍 开始监控 Cloudflare 隧道")
        self.log(f"检查间隔: {CHECK_INTERVAL}秒")
        self.log("=" * 50)
        
        print("\n按 Ctrl+C 停止监控\n")
        
        while self.running:
            try:
                # 检查隧道进程是否运行
                if not self.check_tunnel_running():
                    self.log("⚠️  隧道进程未运行，正在重启...")
                    self.stop_tunnel()
                    self.start_tunnel()
                    self.consecutive_failures = 0
                    time.sleep(10)
                    continue
                
                # 获取当前隧道 URL
                current_url = self.get_tunnel_url()
                
                if not current_url:
                    self.log("⚠️  无法获取隧道 URL")
                    self.consecutive_failures += 1
                else:
                    # 检查隧道是否可访问
                    if self.check_tunnel_accessible(current_url):
                        if self.consecutive_failures > 0:
                            self.log(f"✅ 隧道恢复正常: {current_url}")
                        self.consecutive_failures = 0
                    else:
                        self.consecutive_failures += 1
                        self.log(f"⚠️  隧道无法访问 (失败次数: {self.consecutive_failures}/{MAX_FAILURES}): {current_url}")
                
                # 如果连续失败达到阈值，重启隧道
                if self.consecutive_failures >= MAX_FAILURES:
                    self.log(f"❌ 隧道连续失败 {self.consecutive_failures} 次，正在重启...")
                    self.stop_tunnel()
                    self.start_tunnel()
                    self.consecutive_failures = 0
                    time.sleep(10)
                
                # 等待下一次检查
                time.sleep(CHECK_INTERVAL)
            
            except Exception as e:
                self.log(f"❌ 监控循环出错: {e}")
                time.sleep(CHECK_INTERVAL)
    
    def status(self):
        """检查隧道状态"""
        if self.check_tunnel_running():
            current_url = self.get_tunnel_url()
            print(f"✅ 隧道正在运行")
            print(f"URL: {current_url}")
            
            if self.check_tunnel_accessible(current_url):
                print("✅ 隧道可访问")
            else:
                print("❌ 隧道不可访问")
        else:
            print("❌ 隧道未运行")
    
    def cleanup(self, signum=None, frame=None):
        """清理并退出"""
        self.log("=" * 50)
        self.log("🛑 收到停止信号，退出监控")
        self.log("=" * 50)
        print("\n停止监控...")
        self.running = False
        exit(0)


def main():
    import sys
    
    monitor = TunnelMonitor()
    
    command = sys.argv[1] if len(sys.argv) > 1 else "monitor"
    
    if command == "start":
        monitor.start_tunnel()
    elif command == "stop":
        monitor.stop_tunnel()
    elif command == "restart":
        monitor.stop_tunnel()
        monitor.start_tunnel()
    elif command == "status":
        monitor.status()
    elif command == "monitor":
        monitor.monitor()
    else:
        print("用法: python auto_update_tunnel.py {start|stop|restart|status|monitor}")
        print()
        print("命令说明:")
        print("  start   - 启动隧道")
        print("  stop    - 停止隧道")
        print("  restart - 重启隧道")
        print("  status  - 检查隧道状态")
        print("  monitor - 持续监控隧道（默认）")
        sys.exit(1)


if __name__ == "__main__":
    main()

