#!/usr/bin/env python3
"""
Claude Code Switcher API测试示例

如果您想要测试API功能，请按以下步骤操作：

1. 获取有效的Anthropic API Key:
   - 访问 https://console.anthropic.com/
   - 创建账户并获取API Key

2. 在cc_switcher中添加配置:
   - 配置名称: 例如 "My Claude Config"
   - ANTHROPIC_BASE_URL: https://api.anthropic.com
   - ANTHROPIC_AUTH_TOKEN: 您的实际API Key (sk-ant-api03-...)
   - default_model: claude-3-haiku-20240307 或其他支持的模型

3. 使用API测试功能:
   - 点击"API 测试"按钮
   - 选择您的配置
   - 输入测试问题如："你好，请介绍一下自己"
   - 查看API响应结果

重要提示：
- 请确保您的API Key有效且有足够的配额
- 测试会消耗您的API使用额度
- 如果遇到403错误，通常表示API Key无效或无权限
"""

if __name__ == "__main__":
    from cc_switcher import ClaudeConfigSwitcher

    print("启动Claude Config Switcher...")
    print("请在GUI中配置有效的API信息后进行测试")

    app = ClaudeConfigSwitcher()
    app.run()