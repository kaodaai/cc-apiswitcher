#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cc_switcher

def test_app():
    print("=== 测试 CC 配置切换器 ===")

    # 创建应用实例
    app = cc_switcher.ClaudeConfigSwitcher()

    print("应用初始化成功")
    print(f"配置数量: {len(app.configs_data['configs'])}")

    # 显示所有配置
    print("\n=== 当前配置列表 ===")
    for i, config in enumerate(app.configs_data['configs']):
        print(f"{i+1}. {config['name']}")
        print(f"   URL: {config['ANTHROPIC_BASE_URL']}")
        print(f"   Model: {config['default_model']}")

    # 检查当前环境变量
    print("\n=== 当前环境变量 ===")
    env_vars = app.get_environment_variables()
    print(f"ANTHROPIC_BASE_URL: {env_vars['ANTHROPIC_BASE_URL']}")
    print(f"ANTHROPIC_AUTH_TOKEN: {env_vars['ANTHROPIC_AUTH_TOKEN'][:20]}...")

    print(f"\n管理员权限: {app.is_admin()}")
    print("环境变量切换功能已添加到主界面")

    print("\n=== 使用说明 ===")
    print("1. 在左侧配置列表中选择一个配置")
    print("2. 点击'切换配置'按钮切换配置文件")
    print("3. 点击'切换环境变量'按钮直接切换系统环境变量")
    print("4. 点击'配置管理'按钮进行高级配置管理")

    return app

if __name__ == "__main__":
    test_app()