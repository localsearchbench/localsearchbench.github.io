#!/usr/bin/env python3
"""
MCP RAG 搜索工具使用示例
演示如何在 Python 中直接调用 MCP 工具
"""

import sys
import os

# 添加路径以便导入
sys.path.insert(0, os.path.dirname(__file__))

from rag_search import query_rag, web_search


def demo_rag_search():
    """演示 RAG 搜索功能"""
    print("\n" + "=" * 60)
    print("演示 1: RAG 商户搜索")
    print("=" * 60)
    
    # 示例 1: 基础搜索
    print("\n【示例 1】查找火锅店")
    print("-" * 60)
    result = query_rag(
        query="朝阳区附近有什么好吃的火锅店",
        city="北京",
        topk=3
    )
    print(result)
    
    # 示例 2: 上海咖啡店
    print("\n【示例 2】查找咖啡店")
    print("-" * 60)
    result = query_rag(
        query="静安区有哪些安静适合办公的咖啡店",
        city="上海",
        topk=5
    )
    print(result)


def demo_web_search():
    """演示网络搜索功能"""
    print("\n" + "=" * 60)
    print("演示 2: 网络搜索")
    print("=" * 60)
    
    print("\n【示例】搜索最新 AI 技术")
    print("-" * 60)
    result = web_search(
        query="2024 年最新的 AI 技术趋势",
        search_type="google",
        max_results=3
    )
    print(result)


def main():
    """主函数"""
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║       MCP RAG 搜索工具 - 使用示例演示                 ║")
    print("║       参考 RL-Factory 的 MCP 工具实现                 ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    # 检查服务器连接
    print("\n📡 检查服务器连接...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:5003/health", timeout=2)
        if response.status_code == 200:
            print("✅ RAG 服务器运行正常")
        else:
            print("⚠️  RAG 服务器响应异常")
    except Exception as e:
        print(f"❌ 无法连接到 RAG 服务器: {e}")
        print("请先启动 RAG 服务器:")
        print("  cd server && bash start_rag_server.sh")
        return
    
    # 运行演示
    try:
        demo_rag_search()
        # demo_web_search()  # 如果 RAG 服务器支持 web_search
        
        print("\n" + "=" * 60)
        print("✅ 所有演示完成")
        print("=" * 60)
        
        print("\n💡 提示:")
        print("  - 将 MCP 工具配置到 Claude Desktop 或 Cursor")
        print("  - 配置文件: mcp_tools/mcp_config.json")
        print("  - 查看 README: mcp_tools/README.md")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



