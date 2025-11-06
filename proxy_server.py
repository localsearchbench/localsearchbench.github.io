#!/usr/bin/env python3
"""
CORS 代理服务器
用于转发前端请求到内网 RAG 服务器
"""

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import requests
import sys

app = Flask(__name__)
CORS(app)  # 允许所有跨域请求

# 内网 RAG 服务器地址
# 修改这里为您的实际内网地址
RAG_SERVER = "http://内网IP:8000"  # 例如: http://192.168.1.100:8000

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    try:
        response = requests.get(f"{RAG_SERVER}/health", timeout=5)
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"无法连接到 RAG 服务器: {str(e)}"
        }), 503

def enhance_rerank_text(data):
    """增强重排序文本格式，添加中文标签"""
    if isinstance(data, dict):
        # 处理检索结果中的文档
        if 'retrieved_docs' in data:
            for doc in data.get('retrieved_docs', []):
                if 'metadata' in doc:
                    metadata = doc['metadata']
                    # 构建增强的重排序文本
                    parts = []
                    if metadata.get('name'):
                        parts.append(f"店名：{metadata['name']}")
                    if metadata.get('category'):
                        parts.append(f"类型：{metadata['category']}")
                    if metadata.get('subcategory'):
                        parts.append(f"子类型：{metadata['subcategory']}")
                    if metadata.get('address'):
                        parts.append(f"地址：{metadata['address']}")
                    
                    if parts:
                        # 更新 rerank_text 字段
                        metadata['rerank_text'] = ' - '.join(parts)
    return data

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    """代理所有 API 请求"""
    try:
        # 构建目标 URL
        url = f"{RAG_SERVER}/api/{path}"
        
        # 转发请求
        if request.method == 'GET':
            response = requests.get(
                url,
                params=request.args,
                headers={k: v for k, v in request.headers if k.lower() != 'host'},
                timeout=120
            )
        elif request.method == 'POST':
            response = requests.post(
                url,
                json=request.get_json(),
                params=request.args,
                headers={k: v for k, v in request.headers if k.lower() != 'host'},
                timeout=120
            )
        else:
            return jsonify({"error": "Method not allowed"}), 405
        
        # 如果是 RAG 搜索请求，增强返回数据
        if response.status_code == 200 and 'rag/search' in path:
            try:
                data = response.json()
                data = enhance_rerank_text(data)
                return jsonify(data)
            except:
                pass  # 如果解析失败，直接返回原始响应
        
        # 返回响应
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in response.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        return Response(
            response.content,
            status=response.status_code,
            headers=headers
        )
        
    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "message": "请求超时"
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            "status": "error",
            "message": f"无法连接到 RAG 服务器 {RAG_SERVER}"
        }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    if len(sys.argv) > 1:
        RAG_SERVER = sys.argv[1]
    
    print("=" * 60)
    print("🚀 CORS 代理服务器启动")
    print("=" * 60)
    print(f"📡 目标 RAG 服务器: {RAG_SERVER}")
    print(f"🌐 本地代理地址: http://localhost:8001")
    print(f"📝 用法: python3 proxy_server.py [RAG服务器地址]")
    print("=" * 60)
    print()
    
    app.run(host='0.0.0.0', port=8001, debug=False)
