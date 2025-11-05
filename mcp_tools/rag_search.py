#!/usr/bin/env python3
"""
MCP RAG Search Tool
基于 MCP (Model Context Protocol) 的 RAG 搜索工具
参考 RL-Factory 的 search.py 实现
"""

import requests
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("LocalSearchRAG")


@mcp.tool()
def query_rag(query: str, city: str = "上海", topk: int = 5, retrieval_k: int = 50):
    """MCP RAG Query Tool - 查询本地商户信息
    
    Args:
        query: 查询文本，描述你想找的商户类型或特征
        city: 城市名称，默认为"上海"
        topk: 返回的结果数量，默认为5
        retrieval_k: 检索时的候选数量，默认为50
        
    Returns:
        str: 格式化的查询结果，包含商户名称、地址、评分等信息
        
    Example:
        >>> query_rag("附近有什么好吃的火锅店", city="上海", topk=3)
    """
    try:
        # 构建请求数据
        request_data = {
            "queries": [query],
            "city": city,
            "top_k": topk,
            "retrieval_k": retrieval_k,
            "return_scores": True
        }
        
        # 设置请求头和代理
        headers = {
            "Content-Type": "application/json"
        }
        
        # 使用本地连接，绕过代理
        proxies = {
            "http": None,
            "https": None
        }
        
        # 调用 RAG 服务器
        response = requests.post(
            "http://127.0.0.1:5003/search",
            json=request_data,
            headers=headers,
            proxies=proxies,
            timeout=30
        )
        
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        if not result.get("results"):
            return "⚠️ 未找到相关商户信息"
        
        # 格式化输出结果
        formatted_results = []
        for idx, merchant in enumerate(result["results"], 1):
            merchant_info = f"""
商户 {idx}:
- 名称: {merchant.get('name', 'N/A')}
- 地址: {merchant.get('address', 'N/A')}
- 评分: {merchant.get('rating', 'N/A')}
- 价格: {merchant.get('avg_price', 'N/A')}
- 类型: {merchant.get('poi_type', 'N/A')}
- 相似度: {merchant.get('combined_score', 'N/A'):.4f}
"""
            formatted_results.append(merchant_info.strip())
        
        # 添加摘要信息
        summary = result.get("summary", "")
        output = f"查询: {query}\n城市: {city}\n找到 {len(result['results'])} 个相关商户\n"
        
        if summary:
            output += f"\n摘要:\n{summary}\n"
        
        output += "\n" + "\n\n".join(formatted_results)
        
        return output
        
    except requests.exceptions.Timeout:
        return "⚠️ RAG 服务请求超时，请检查服务是否正常运行"
    except requests.exceptions.ConnectionError:
        return "⚠️ 无法连接到 RAG 服务，请确保服务正在运行 (http://127.0.0.1:5003)"
    except requests.exceptions.RequestException as e:
        error_detail = e.response.text if hasattr(e, 'response') else 'No detail'
        return f"⚠️ RAG 服务请求失败: {str(e)}\n详情: {error_detail}"
    except Exception as e:
        return f"⚠️ RAG 查询失败: {str(e)}\n错误类型: {type(e).__name__}"


@mcp.tool()
def web_search(query: str, search_type: str = "google", max_results: int = 5):
    """MCP Web Search Tool - 网络搜索
    
    Args:
        query: 搜索查询文本
        search_type: 搜索类型，可选 "google", "bing", "duckduckgo"
        max_results: 最大返回结果数量，默认为5
        
    Returns:
        str: 格式化的搜索结果
    """
    try:
        request_data = {
            "query": query,
            "search_type": search_type,
            "max_results": max_results
        }
        
        headers = {"Content-Type": "application/json"}
        proxies = {"http": None, "https": None}
        
        response = requests.post(
            "http://127.0.0.1:5003/web_search",
            json=request_data,
            headers=headers,
            proxies=proxies,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        if not result.get("results"):
            return "⚠️ 未找到搜索结果"
        
        # 格式化输出
        formatted_results = []
        for idx, item in enumerate(result["results"], 1):
            result_info = f"""
结果 {idx}:
- 标题: {item.get('title', 'N/A')}
- 链接: {item.get('url', 'N/A')}
- 摘要: {item.get('snippet', 'N/A')}
"""
            formatted_results.append(result_info.strip())
        
        output = f"搜索查询: {query}\n搜索引擎: {search_type}\n找到 {len(result['results'])} 个结果\n\n"
        output += "\n\n".join(formatted_results)
        
        return output
        
    except Exception as e:
        return f"⚠️ 网络搜索失败: {str(e)}"


if __name__ == "__main__":
    print("\n🚀 启动 MCP RAG 搜索服务...")
    print("📍 RAG 服务地址: http://127.0.0.1:5003")
    print("🔧 可用工具:")
    print("  - query_rag: 本地商户 RAG 搜索")
    print("  - web_search: 网络搜索")
    print("\n等待连接...\n")
    mcp.run(transport='stdio')

