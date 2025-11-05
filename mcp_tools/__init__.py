"""
MCP Tools for LocalSearchBench
基于 MCP (Model Context Protocol) 的 RAG 搜索工具包
参考 RL-Factory 项目实现
"""

__version__ = "1.0.0"
__author__ = "LocalSearchBench Team"

from .rag_search import query_rag, web_search

__all__ = ["query_rag", "web_search"]

