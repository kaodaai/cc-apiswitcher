# test_claude_official_api.py
import requests
import json
import os

# 从环境变量读取 API Key（更安全）
ANTHROPIC_API_KEY = 'sk-LXa94gifODRSsTGowQfbmTLRn7gznZVPb2H9NZQ6ObTT36s9'
url = "https://jp.duckcoding.com/v1/messages"

headers = {
    "x-api-key": ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

def test_claude_api_basic():
    """测试最基本的 Claude API 调用"""
    data = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "Hello, who are you?"}]
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    # 关键断言
    assert response.status_code == 200, f"API 请求失败: {response.text}"
    
    response_data = response.json()
    assert "content" in response_data
    assert len(response_data["content"]) > 0
    assert "text" in response_data["content"][0]
    
    print("✓ Claude API 基本测试通过")
    print(f"Claude 回复: {response_data['content'][0]['text'][:50]}...")

if __name__ == '__main__':
    if not ANTHROPIC_API_KEY:
        print("请设置 ANTHROPIC_API_KEY 环境变量")
    else:
        test_claude_api_basic()