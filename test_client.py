#!/usr/bin/env python3
"""
测试WiFi密码查询MCP服务
"""

import requests

BASE_URL = "http://localhost:8000"

def test_list_tools():
    """测试列出工具"""
    print("=== 测试列出工具 ===")
    response = requests.post(f"{BASE_URL}/mcp/list-tools")
    print(f"状态码: {response.status_code}")
    tools = response.json().get("tools", [])
    print(f"可用工具: {[t['name'] for t in tools]}")
    print()

def test_get_wifi_password():
    """测试获取WiFi密码"""
    print("=== 测试获取WiFi密码 ===")
    payload = {
        "name": "get_wifi_password",
        "parameters": {
            "question": "请问WiFi密码是多少？"
        }
    }
    response = requests.post(f"{BASE_URL}/mcp/call-tool", json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

def test_get_menu():
    """测试获取菜单"""
    print("=== 测试获取菜单 ===")
    payload = {
        "name": "get_menu",
        "parameters": {
            "question": "今天菜单有什么？"
        }
    }
    response = requests.post(f"{BASE_URL}/mcp/call-tool", json=payload)
    print(f"状态码: {response.status_code}")
    data = response.json()
    if data.get("content"):
        print(f"菜单:\n{data['content'][0]['text']}")
    print()

def test_get_queue_status():
    """测试获取排队状态"""
    print("=== 测试获取排队状态 ===")
    payload = {
        "name": "get_queue_status",
        "parameters": {
            "question": "现在排了多少人？"
        }
    }
    response = requests.post(f"{BASE_URL}/mcp/call-tool", json=payload)
    print(f"状态码: {response.status_code}")
    data = response.json()
    if data.get("content"):
        print(f"结果: {data['content'][0]['text']}")
    print()

def test_unknown_tool():
    """测试未知工具"""
    print("=== 测试未知工具 ===")
    payload = {
        "name": "unknown_tool",
        "parameters": {}
    }
    response = requests.post(f"{BASE_URL}/mcp/call-tool", json=payload)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

if __name__ == "__main__":
    try:
        test_list_tools()
        test_get_wifi_password()
        test_get_menu()
        test_get_queue_status()
        test_unknown_tool()
        print("所有测试完成！")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器，请确保服务器已启动 (python server.py)")
