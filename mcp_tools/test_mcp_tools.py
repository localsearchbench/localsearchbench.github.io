#!/usr/bin/env python3
"""
测试 MCP RAG 搜索工具
"""

import subprocess
import json
import sys


def test_mcp_tool():
    """测试 MCP 工具是否正常工作"""
    
    print("=" * 60)
    print("测试 MCP RAG 搜索工具")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        {
            "name": "基础 RAG 搜索",
            "tool": "query_rag",
            "params": {
                "query": "朝阳区附近好吃的火锅店",
                "city": "北京",
                "topk": 3
            }
        },
        {
            "name": "简单查询",
            "tool": "query_rag",
            "params": {
                "query": "咖啡店",
                "topk": 5
            }
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test['name']}")
        print("-" * 60)
        print(f"工具: {test['tool']}")
        print(f"参数: {json.dumps(test['params'], ensure_ascii=False, indent=2)}")
        print("-" * 60)
        
        try:
            # 构建 MCP 请求
            mcp_request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": test['tool'],
                    "arguments": test['params']
                }
            }
            
            # 调用 MCP 服务
            process = subprocess.Popen(
                ["python3", "mcp_tools/rag_search.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(
                input=json.dumps(mcp_request) + "\n",
                timeout=30
            )
            
            print("输出:")
            print(stdout)
            
            if stderr:
                print("错误:")
                print(stderr)
                
            print("✅ 测试完成")
            
        except subprocess.TimeoutExpired:
            print("❌ 测试超时")
            process.kill()
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)


def test_direct_import():
    """直接导入测试"""
    print("\n" + "=" * 60)
    print("直接导入测试")
    print("=" * 60)
    
    try:
        sys.path.insert(0, 'mcp_tools')
        from rag_search import query_rag
        
        print("\n测试: query_rag 函数")
        result = query_rag("好吃的火锅", city="北京", topk=3)
        print(result)
        print("✅ 直接导入测试成功")
        
    except Exception as e:
        print(f"❌ 直接导入测试失败: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试 MCP 工具")
    parser.add_argument("--direct", action="store_true", help="直接导入测试")
    args = parser.parse_args()
    
    if args.direct:
        test_direct_import()
    else:
        test_mcp_tool()

