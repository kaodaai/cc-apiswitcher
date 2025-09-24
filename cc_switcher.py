#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CC-APISwitch v1.1
专业的Claude API配置切换管理工具，支持项目快速启动
"""

import wx
import os
import json
import shutil
import winreg
import requests
import threading
import time
import glob
from pathlib import Path
from datetime import datetime


class SimpleConfigManager:
    """API配置管理器"""

    def __init__(self):
        self.claude_dir = Path.home() / ".claude"
        self.settings_file = self.claude_dir / "settings.json"

        # 优先使用新的配置文件名，如果不存在则尝试旧文件名
        self.configs_file = self.claude_dir / "cc_apiswitch_configs.json"
        old_configs_file = self.claude_dir / "cc_switcher_configs.json"

        # 如果新文件不存在但旧文件存在，则迁移配置
        if not self.configs_file.exists() and old_configs_file.exists():
            import shutil
            try:
                shutil.copy2(old_configs_file, self.configs_file)
                print(f"已迁移配置文件: {old_configs_file} -> {self.configs_file}")
            except Exception as e:
                print(f"迁移配置文件失败: {e}")
                # 如果迁移失败，继续使用旧文件
                self.configs_file = old_configs_file

        self.configs_data = self.load_configs_data()

    def load_configs_data(self):
        """从JSON文件加载配置"""
        default_data = {"configs": [], "active_config": None, "version": "1.0"}

        if not self.configs_file.exists():
            return default_data

        try:
            with open(self.configs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key in default_data:
                    if key not in data:
                        data[key] = default_data[key]
                return data
        except (json.JSONDecodeError, IOError):
            return default_data

    def save_configs_data(self):
        """保存配置到JSON文件"""
        try:
            self.claude_dir.mkdir(exist_ok=True)
            with open(self.configs_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs_data, f, indent=2, ensure_ascii=False)
        except (IOError, OSError):
            pass

    def get_all_configs(self):
        """获取所有配置"""
        return self.configs_data["configs"]

    def add_config(self, name, base_url, auth_token, model, note=""):
        """添加新配置"""
        for config in self.configs_data["configs"]:
            if config["name"] == name:
                return False, "名称已存在"

        new_config = {
            "name": name,
            "ANTHROPIC_BASE_URL": base_url,
            "ANTHROPIC_AUTH_TOKEN": auth_token,
            "default_model": model,
            "note": note,
            "test_status": "未测试",
            "test_time": "",
            "test_message": ""
        }

        self.configs_data["configs"].append(new_config)
        self.save_configs_data()
        return True, "配置添加成功"

    def update_config(self, index, name, base_url, auth_token, model, note=""):
        """更新配置"""
        if index < 0 or index >= len(self.configs_data["configs"]):
            return False, "无效的配置索引"

        # 检查名称冲突
        for i, config in enumerate(self.configs_data["configs"]):
            if i != index and config["name"] == name:
                return False, "名称已存在"

        config = self.configs_data["configs"][index]
        config.update({
            "name": name,
            "ANTHROPIC_BASE_URL": base_url,
            "ANTHROPIC_AUTH_TOKEN": auth_token,
            "default_model": model,
            "note": note
        })

        self.save_configs_data()
        return True, "配置更新成功"

    def delete_config(self, index):
        """删除配置"""
        if index < 0 or index >= len(self.configs_data["configs"]):
            return False, "无效的配置索引"

        config_name = self.configs_data["configs"][index]["name"]
        del self.configs_data["configs"][index]

        if self.configs_data["active_config"] == config_name:
            self.configs_data["active_config"] = None

        self.save_configs_data()
        return True, "配置删除成功"

    def switch_config(self, index):
        """切换配置"""
        if index < 0 or index >= len(self.configs_data["configs"]):
            return False, "无效的配置索引"

        config = self.configs_data["configs"][index]

        try:
            settings_content = {
                "ANTHROPIC_BASE_URL": config["ANTHROPIC_BASE_URL"],
                "ANTHROPIC_AUTH_TOKEN": config["ANTHROPIC_AUTH_TOKEN"],
                "default_model": config["default_model"]
            }

            self.claude_dir.mkdir(exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_content, f, indent=2)

            self.configs_data["active_config"] = config["name"]
            self.save_configs_data()

            return True, f"已切换到配置 {config['name']}"
        except Exception as e:
            return False, f"切换失败: {str(e)}"

    def set_environment_variables(self, index, scope="user"):
        """设置环境变量"""
        if index < 0 or index >= len(self.configs_data["configs"]):
            return False, "无效的配置索引"

        config = self.configs_data["configs"][index]

        try:
            base_url = config["ANTHROPIC_BASE_URL"]
            auth_token = config["ANTHROPIC_AUTH_TOKEN"]
            model = config.get("default_model", "claude-sonnet-4-20250514")

            # 设置当前进程环境变量
            os.environ["ANTHROPIC_BASE_URL"] = base_url
            os.environ["ANTHROPIC_AUTH_TOKEN"] = auth_token
            os.environ["ANTHROPIC_MODEL"] = model

            # 根据scope选择注册表位置
            if scope == "system":
                # 系统环境变量需要管理员权限
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment", 0, winreg.KEY_ALL_ACCESS)
                    scope_name = "系统"
                except PermissionError:
                    return False, "设置系统环境变量需要管理员权限，请以管理员身份运行程序"
            else:
                # 用户环境变量
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
                scope_name = "用户"

            # 设置注册表环境变量
            winreg.SetValueEx(key, "ANTHROPIC_BASE_URL", 0, winreg.REG_SZ, base_url)
            winreg.SetValueEx(key, "ANTHROPIC_AUTH_TOKEN", 0, winreg.REG_SZ, auth_token)
            winreg.SetValueEx(key, "ANTHROPIC_MODEL", 0, winreg.REG_SZ, model)
            winreg.CloseKey(key)

            # 通知系统环境变量已更改
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x1A
            SMTO_ABORTIFHUNG = 0x0002
            result = ctypes.c_long()
            ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 5000, ctypes.byref(result))

            return True, f"{scope_name}环境变量已设置为: {config['name']}"
        except Exception as e:
            return False, f"设置失败: {str(e)}"

    def test_config(self, index, question="1+2=?"):
        """测试单个配置"""
        if index < 0 or index >= len(self.configs_data["configs"]):
            return False, "无效的配置索引", {}

        config = self.configs_data["configs"][index]

        try:
            headers = {
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key": config["ANTHROPIC_AUTH_TOKEN"],
                "user-agent": "claude-cli/1.0.115 (external, cli)"
            }

            data = {
                "model": config["default_model"],
                "max_tokens": 100,
                "messages": [{"role": "user", "content": question}]
            }

            url = f"{config['ANTHROPIC_BASE_URL'].rstrip('/')}/v1/messages"
            response = requests.post(url, json=data, headers=headers, timeout=10)

            current_time = time.strftime("%H:%M:%S")

            if response.status_code == 200:
                response_data = response.json()
                answer = response_data.get("content", [{}])[0].get("text", "")

                config.update({
                    "test_status": "通过",
                    "test_time": current_time,
                    "test_message": f"Q:{question} A:{answer[:30]}..."
                })
                self.save_configs_data()
                return True, "测试成功", {"answer": answer}

            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    pass

                config.update({
                    "test_status": "失败",
                    "test_time": current_time,
                    "test_message": error_msg
                })
                self.save_configs_data()
                return False, error_msg, {}

        except requests.exceptions.Timeout:
            config.update({
                "test_status": "超时",
                "test_time": time.strftime("%H:%M:%S"),
                "test_message": "请求超时"
            })
            self.save_configs_data()
            return False, "请求超时", {}

        except Exception as e:
            config.update({
                "test_status": "错误",
                "test_time": time.strftime("%H:%M:%S"),
                "test_message": str(e)
            })
            self.save_configs_data()
            return False, f"测试失败: {str(e)}", {}

    def get_current_claude_config(self):
        """获取当前claude配置"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}

    def get_system_env_config(self):
        """获取系统环境变量配置"""
        env_config = {}
        try:
            env_config['ANTHROPIC_BASE_URL'] = os.environ.get('ANTHROPIC_BASE_URL', '')
            env_config['ANTHROPIC_AUTH_TOKEN'] = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
            env_config['ANTHROPIC_MODEL'] = os.environ.get('ANTHROPIC_MODEL', '')
        except:
            pass
        return env_config

    def get_available_models(self):
        """获取可用模型列表"""
        return [
            # Claude 4系列模型
            "claude-4-sonnet",
            "claude-sonnet-4-20250514",

            # Claude 3.7系列模型
            "claude-3-7-sonnet",
            "claude-3-7-sonnet-20250219",

            # Claude 3.5系列模型
            "claude-3-5-sonnet",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku",
            "claude-3-5-haiku-20241022",

            # Claude 3系列模型
            "claude-3-opus",
            "claude-3-opus-20240229",

            # 简化名称模型
            "claude-sonnet",
            "claude-haiku",
            "claude-opus"
        ]

    def get_claude_code_projects(self):
        """获取Claude Code最近的项目列表"""
        projects = []

        try:
            claude_projects_dir = Path.home() / ".claude" / "projects"

            if not claude_projects_dir.exists():
                return projects

            # 检查读取权限
            if not os.access(claude_projects_dir, os.R_OK):
                print("没有权限访问Claude项目目录")
                return projects

            # 遍历所有项目目录
            for project_dir in claude_projects_dir.iterdir():
                if not project_dir.is_dir() or project_dir.name.startswith('.'):
                    continue

                try:
                    # 获取项目名称（解码目录名）
                    project_name = project_dir.name.replace("D--", "D:\\").replace("-", "\\")

                    # 查找最新的会话文件来获取最后访问时间
                    jsonl_files = list(project_dir.glob("*.jsonl"))
                    if not jsonl_files:
                        continue

                    latest_time = None
                    project_path = None

                    # 遍历jsonl文件找到最新的和项目路径
                    for jsonl_file in jsonl_files:
                        try:
                            # 检查文件权限
                            if not os.access(jsonl_file, os.R_OK):
                                continue

                            with open(jsonl_file, 'r', encoding='utf-8') as f:
                                first_line = f.readline().strip()
                                if first_line:
                                    data = json.loads(first_line)
                                    # 跳过summary行，找用户消息
                                    if data.get('type') == 'summary':
                                        second_line = f.readline().strip()
                                        if second_line:
                                            data = json.loads(second_line)

                                    if 'cwd' in data and 'timestamp' in data:
                                        file_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                                        if latest_time is None or file_time > latest_time:
                                            latest_time = file_time
                                            project_path = data['cwd']
                        except (json.JSONDecodeError, IOError, KeyError, PermissionError) as e:
                            continue

                    if project_path and latest_time:
                        # 检查项目路径是否仍然存在且有访问权限
                        try:
                            project_path_obj = Path(project_path)
                            if project_path_obj.exists() and os.access(project_path_obj, os.R_OK):
                                projects.append({
                                    'name': project_path_obj.name,
                                    'path': project_path,
                                    'last_access': latest_time
                                })
                        except (OSError, PermissionError):
                            continue

                except (OSError, PermissionError) as e:
                    continue

            # 按最后访问时间排序（最新的在前）
            projects.sort(key=lambda x: x['last_access'], reverse=True)

        except (PermissionError, OSError) as e:
            print(f"访问Claude目录时权限不足: {e}")
        except Exception as e:
            print(f"获取项目列表时出错: {e}")

        return projects


class ConfigManagementFrame(wx.Frame):
    """API配置管理主窗口"""

    def __init__(self):
        super().__init__(None, title="CC-APISwitch v1.1", size=(900, 700))  # 调整窗口高度
        self.config_manager = SimpleConfigManager()
        self.selected_index = -1
        self.testing_indices = set()  # 正在测试的配置索引

        self.create_ui()
        self.refresh_list()
        self.Center()

    def create_ui(self):
        """创建界面"""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 当前配置显示
        self.current_config_label = wx.StaticText(panel, label="")
        config_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.current_config_label.SetFont(config_font)
        self.current_config_label.SetForegroundColour(wx.Colour(0, 100, 200))
        main_sizer.Add(self.current_config_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        # 系统环境变量配置显示
        self.env_config_label = wx.StaticText(panel, label="")
        env_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.env_config_label.SetFont(env_font)
        self.env_config_label.SetForegroundColour(wx.Colour(0, 100, 200))
        main_sizer.Add(self.env_config_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        # 配置列表 - 多列显示，支持拖动排序
        self.config_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.config_list.AppendColumn('配置名称', width=150)
        self.config_list.AppendColumn('模型', width=200)
        self.config_list.AppendColumn('状态', width=80)
        self.config_list.AppendColumn('测试时间', width=80)
        self.config_list.AppendColumn('测试结果', width=300)
        main_sizer.Add(self.config_list, 3, wx.ALL | wx.EXPAND, 10)

        # 配置编辑区域
        edit_box = wx.StaticBox(panel, label="API配置编辑")
        edit_sizer = wx.StaticBoxSizer(edit_box, wx.VERTICAL)

        # 表单网格
        form_sizer = wx.FlexGridSizer(5, 2, 5, 10)
        form_sizer.AddGrowableCol(1)

        # 名称
        form_sizer.Add(wx.StaticText(panel, label="配置名称:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.name_text = wx.TextCtrl(panel)
        form_sizer.Add(self.name_text, 1, wx.EXPAND)

        # URL
        form_sizer.Add(wx.StaticText(panel, label="基础URL:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.url_text = wx.TextCtrl(panel, value="https://api.anthropic.com")
        form_sizer.Add(self.url_text, 1, wx.EXPAND)

        # Token
        form_sizer.Add(wx.StaticText(panel, label="认证令牌:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.token_text = wx.TextCtrl(panel)
        form_sizer.Add(self.token_text, 1, wx.EXPAND)

        # Model
        form_sizer.Add(wx.StaticText(panel, label="默认模型:"), 0, wx.ALIGN_CENTER_VERTICAL)
        models = self.config_manager.get_available_models()
        self.model_choice = wx.Choice(panel, choices=models)
        # 设置默认选择为 claude-sonnet-4-20250514
        default_model_index = models.index("claude-sonnet-4-20250514") if "claude-sonnet-4-20250514" in models else 0
        self.model_choice.SetSelection(default_model_index)
        form_sizer.Add(self.model_choice, 1, wx.EXPAND)

        # 备注
        form_sizer.Add(wx.StaticText(panel, label="备注:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.note_text = wx.TextCtrl(panel)
        form_sizer.Add(self.note_text, 1, wx.EXPAND)

        edit_sizer.Add(form_sizer, 0, wx.ALL | wx.EXPAND, 10)
        main_sizer.Add(edit_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # 操作按钮区域
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.add_btn = wx.Button(panel, label="添加")
        self.update_btn = wx.Button(panel, label="更新")
        self.delete_btn = wx.Button(panel, label="删除")
        self.test_btn = wx.Button(panel, label="测试")
        self.batch_test_btn = wx.Button(panel, label="批量测试")
        self.switch_btn = wx.Button(panel, label="切换配置")
        self.env_btn = wx.Button(panel, label="用户环境变量")
        self.system_env_btn = wx.Button(panel, label="系统环境变量")
        self.clear_btn = wx.Button(panel, label="清除")
        self.move_up_btn = wx.Button(panel, label="上移")
        self.move_down_btn = wx.Button(panel, label="下移")

        btn_sizer.Add(self.add_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.update_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.delete_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.clear_btn, 0, wx.ALL, 2)
        btn_sizer.AddSpacer(10)
        btn_sizer.Add(self.move_up_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.move_down_btn, 0, wx.ALL, 2)
        btn_sizer.AddSpacer(10)
        btn_sizer.Add(self.test_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.batch_test_btn, 0, wx.ALL, 2)
        btn_sizer.AddSpacer(10)
        btn_sizer.Add(self.switch_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.env_btn, 0, wx.ALL, 2)
        btn_sizer.Add(self.system_env_btn, 0, wx.ALL, 2)

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 5)

        # 项目管理区域
        project_box = wx.StaticBox(panel, label="项目快速启动")
        project_sizer = wx.StaticBoxSizer(project_box, wx.HORIZONTAL)

        # 项目选择下拉框
        project_sizer.Add(wx.StaticText(panel, label="最近项目:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.project_choice = wx.Choice(panel, size=(400, -1))
        project_sizer.Add(self.project_choice, 1, wx.EXPAND | wx.ALL, 5)

        # 项目操作按钮
        self.refresh_project_btn = wx.Button(panel, label="刷新")
        self.open_claude_btn = wx.Button(panel, label="启动Claude")
        self.open_claude_c_btn = wx.Button(panel, label="启动Claude -c")

        project_sizer.Add(self.refresh_project_btn, 0, wx.ALL, 5)
        project_sizer.Add(self.open_claude_btn, 0, wx.ALL, 5)
        project_sizer.Add(self.open_claude_c_btn, 0, wx.ALL, 5)

        main_sizer.Add(project_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # 底部状态栏和版权信息区域（同一行）
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 左侧状态信息
        self.status_text = wx.StaticText(panel, label="就绪")
        bottom_sizer.Add(self.status_text, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)

        # 右侧版权信息
        bottom_sizer.AddStretchSpacer()
        copyright_text = wx.StaticText(panel, label="by: kaodaai")
        copyright_font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        copyright_text.SetFont(copyright_font)
        copyright_text.SetForegroundColour(wx.Colour(128, 128, 128))  # 灰色
        bottom_sizer.Add(copyright_text, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        main_sizer.Add(bottom_sizer, 0, wx.EXPAND | wx.BOTTOM, 5)

        panel.SetSizer(main_sizer)

        # 事件绑定
        self.config_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select)
        self.config_list.Bind(wx.EVT_MOTION, self.on_list_motion)
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add)
        self.update_btn.Bind(wx.EVT_BUTTON, self.on_update)
        self.delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear)  # 绑定清除按钮事件
        self.move_up_btn.Bind(wx.EVT_BUTTON, self.on_move_up)
        self.move_down_btn.Bind(wx.EVT_BUTTON, self.on_move_down)
        self.test_btn.Bind(wx.EVT_BUTTON, self.on_test)
        self.batch_test_btn.Bind(wx.EVT_BUTTON, self.on_batch_test)
        self.switch_btn.Bind(wx.EVT_BUTTON, self.on_switch)
        self.env_btn.Bind(wx.EVT_BUTTON, self.on_env_switch)
        self.system_env_btn.Bind(wx.EVT_BUTTON, self.on_system_env_switch)

        # 项目管理事件绑定
        self.refresh_project_btn.Bind(wx.EVT_BUTTON, self.on_refresh_projects)
        self.open_claude_btn.Bind(wx.EVT_BUTTON, self.on_open_claude)
        self.open_claude_c_btn.Bind(wx.EVT_BUTTON, self.on_open_claude_c)

        self.update_config_display()
        self.refresh_projects()  # 初始化项目列表

    def update_config_display(self):
        """更新配置显示信息"""
        # 获取当前claude配置
        claude_config = self.config_manager.get_current_claude_config()
        if claude_config:
            base_url = claude_config.get('ANTHROPIC_BASE_URL', '未设置')
            model = claude_config.get('default_model', '未设置')
            claude_text = f"当前Claude配置: {base_url} | {model}"
        else:
            claude_text = "当前Claude配置: 未配置"

        self.current_config_label.SetLabel(claude_text)

        # 获取系统环境变量配置
        env_config = self.config_manager.get_system_env_config()
        env_url = env_config.get('ANTHROPIC_BASE_URL', '未设置')
        env_model = env_config.get('ANTHROPIC_MODEL', '未设置')
        env_text = f"系统环境变量: {env_url} | {env_model}"
        self.env_config_label.SetLabel(env_text)

    def on_list_motion(self, event):
        """处理列表鼠标移动事件，显示备注工具提示"""
        pos = event.GetPosition()
        item, flags = self.config_list.HitTest(pos)

        if item != wx.NOT_FOUND:
            configs = self.config_manager.get_all_configs()
            if item < len(configs):
                config = configs[item]
                note = config.get("note", "")
                if note:
                    self.config_list.SetToolTip(f"{config['name']}: {note}")
                else:
                    self.config_list.SetToolTip(f"{config['name']}: 无备注")
        else:
            self.config_list.SetToolTip("")

        event.Skip()

    def refresh_list(self):
        """刷新配置列表"""
        self.config_list.DeleteAllItems()
        configs = self.config_manager.get_all_configs()

        for i, config in enumerate(configs):
            index = self.config_list.InsertItem(i, config["name"])

            # 模型显示
            model = config.get("default_model", "")
            self.config_list.SetItem(index, 1, model)

            # 测试状态
            status = config.get("test_status", "未测试")
            if i in self.testing_indices:
                status = "测试中..."

            self.config_list.SetItem(index, 2, status)

            # 测试时间
            test_time = config.get("test_time", "")
            self.config_list.SetItem(index, 3, test_time)

            # 测试结果
            test_message = config.get("test_message", "")
            self.config_list.SetItem(index, 4, test_message)

            # 设置颜色
            if config["name"] == self.config_manager.configs_data.get("active_config"):
                self.config_list.SetItemTextColour(index, wx.Colour(0, 150, 0))  # 绿色-活跃
            elif status == "通过":
                self.config_list.SetItemTextColour(index, wx.Colour(0, 100, 200))  # 蓝色-通过
            elif status in ["失败", "错误", "超时"]:
                self.config_list.SetItemTextColour(index, wx.Colour(200, 0, 0))  # 红色-失败

    def clear_form(self):
        """清空表单"""
        self.name_text.SetValue("")
        self.url_text.SetValue("https://api.anthropic.com")
        self.token_text.SetValue("")
        self.model_choice.SetSelection(0)
        self.note_text.SetValue("")

    def load_form(self, config):
        """加载配置到表单"""
        self.name_text.SetValue(config["name"])
        self.url_text.SetValue(config.get("ANTHROPIC_BASE_URL", ""))
        self.token_text.SetValue(config.get("ANTHROPIC_AUTH_TOKEN", ""))
        self.note_text.SetValue(config.get("note", ""))

        model = config.get("default_model", "")
        models = self.config_manager.get_available_models()
        if model in models:
            self.model_choice.SetSelection(models.index(model))

    def on_select(self, event):
        """选择配置"""
        self.selected_index = event.GetIndex()
        if self.selected_index >= 0:
            configs = self.config_manager.get_all_configs()
            if self.selected_index < len(configs):
                self.load_form(configs[self.selected_index])
                self.status_text.SetLabel(f"已选择配置: {configs[self.selected_index]['name']}")

    def on_add(self, event):
        """添加配置 - 直接保存配置内容"""
        # 直接保存配置，不需要进入添加模式
        name = self.name_text.GetValue().strip()
        url = self.url_text.GetValue().strip()
        token = self.token_text.GetValue().strip()
        model = self.model_choice.GetStringSelection()
        note = self.note_text.GetValue().strip()

        if not all([name, url, token, model]):
            wx.MessageBox("请填写所有必填字段", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        # 检查是否已存在同名配置
        configs = self.config_manager.get_all_configs()
        for config in configs:
            if config["name"] == name:
                wx.MessageBox(f"配置名称 '{name}' 已存在，请使用其他名称", "提示", wx.OK | wx.ICON_INFORMATION)
                return

        success, message = self.config_manager.add_config(name, url, token, model, note)
        if success:
            self.status_text.SetLabel(message)
            self.refresh_list()
            self.clear_form()
        else:
            wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)

    def on_clear(self, event):
        """清除表单内容"""
        self.clear_form()
        self.selected_index = -1
        self.status_text.SetLabel("已清除表单内容")

    def on_update(self, event):
        """更新配置"""
        if self.selected_index < 0:
            wx.MessageBox("请先选择一个配置", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        name = self.name_text.GetValue().strip()
        url = self.url_text.GetValue().strip()
        token = self.token_text.GetValue().strip()
        model = self.model_choice.GetStringSelection()
        note = self.note_text.GetValue().strip()

        if not all([name, url, token, model]):
            wx.MessageBox("请填写所有必填字段", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        success, message = self.config_manager.update_config(
            self.selected_index, name, url, token, model, note)
        if success:
            self.status_text.SetLabel(message)
            self.refresh_list()
        else:
            wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)

    def on_delete(self, event):
        """删除配置"""
        if self.selected_index < 0:
            wx.MessageBox("请先选择一个配置", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        configs = self.config_manager.get_all_configs()
        config_name = configs[self.selected_index]["name"]

        if wx.MessageBox(f"确定删除配置 '{config_name}' 吗？",
                        "确认删除", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            success, message = self.config_manager.delete_config(self.selected_index)
            if success:
                self.status_text.SetLabel(message)
                self.refresh_list()
                self.clear_form()
                self.selected_index = -1
            else:
                wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)

    def on_test(self, event):
        """测试单个配置"""
        if self.selected_index < 0:
            wx.MessageBox("请先选择一个配置", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        if self.selected_index in self.testing_indices:
            wx.MessageBox("该配置正在测试中，请稍候", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        self.testing_indices.add(self.selected_index)
        self.test_btn.SetLabel("测试中...")
        self.test_btn.Enable(False)
        self.refresh_list()

        def test_thread():
            success, message, data = self.config_manager.test_config(self.selected_index)
            wx.CallAfter(self.test_complete, self.selected_index, success, message)

        threading.Thread(target=test_thread, daemon=True).start()

    def on_batch_test(self, event):
        """批量测试所有配置"""
        configs = self.config_manager.get_all_configs()
        if not configs:
            wx.MessageBox("没有配置可测试", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        # 检查是否有配置正在测试
        if self.testing_indices:
            wx.MessageBox("有配置正在测试中，请稍候", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        self.batch_test_btn.SetLabel("批量测试中...")
        self.batch_test_btn.Enable(False)
        self.status_text.SetLabel("开始批量测试...")

        # 添加所有配置到测试队列
        for i in range(len(configs)):
            self.testing_indices.add(i)

        self.refresh_list()

        def batch_test_thread():
            for i in range(len(configs)):
                if i not in self.testing_indices:  # 防止重复测试
                    continue

                wx.CallAfter(self.status_text.SetLabel, f"正在测试配置 {i+1}/{len(configs)}: {configs[i]['name']}")
                success, message, data = self.config_manager.test_config(i)
                wx.CallAfter(self.test_complete, i, success, message, is_batch=True)
                time.sleep(1)  # 避免请求过快

            wx.CallAfter(self.batch_test_complete)

        threading.Thread(target=batch_test_thread, daemon=True).start()

    def test_complete(self, index, success, message, is_batch=False):
        """测试完成回调"""
        if index in self.testing_indices:
            self.testing_indices.remove(index)

        if not is_batch:
            self.test_btn.SetLabel("测试")
            self.test_btn.Enable(True)
            if success:
                self.status_text.SetLabel(f"测试成功: {message}")
            else:
                self.status_text.SetLabel(f"测试失败: {message}")

        self.refresh_list()

    def batch_test_complete(self):
        """批量测试完成"""
        self.batch_test_btn.SetLabel("批量测试")
        self.batch_test_btn.Enable(True)
        self.status_text.SetLabel("批量测试完成")

    def on_switch(self, event):
        """切换配置"""
        if self.selected_index < 0:
            wx.MessageBox("请先选择一个配置", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        success, message = self.config_manager.switch_config(self.selected_index)
        if success:
            self.status_text.SetLabel(message)
            self.refresh_list()
            self.update_config_display()  # 更新配置显示
        else:
            wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)

    def on_env_switch(self, event):
        """用户环境变量切换"""
        if self.selected_index < 0:
            wx.MessageBox("请先选择一个配置", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        success, message = self.config_manager.set_environment_variables(self.selected_index, "user")
        if success:
            self.status_text.SetLabel(message)
            self.update_config_display()  # 更新配置显示
        else:
            wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)

    def on_system_env_switch(self, event):
        """系统环境变量切换"""
        if self.selected_index < 0:
            wx.MessageBox("请先选择一个配置", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        success, message = self.config_manager.set_environment_variables(self.selected_index, "system")
        if success:
            self.status_text.SetLabel(message)
            self.update_config_display()  # 更新配置显示
        else:
            wx.MessageBox(message, "错误", wx.OK | wx.ICON_ERROR)

    def refresh_projects(self):
        """刷新项目列表"""
        self.project_choice.Clear()
        self.project_choice.Append("正在加载项目...")
        self.project_choice.SetSelection(0)
        self.status_text.SetLabel("正在加载项目列表...")
        
        # 使用后台线程加载项目，避免阻塞UI
        def load_projects():
            projects = self.config_manager.get_claude_code_projects()
            wx.CallAfter(self.update_projects_ui, projects)
            
        threading.Thread(target=load_projects, daemon=True).start()

    def update_projects_ui(self, projects):
        """在UI线程中更新项目列表"""
        self.project_choice.Clear()
        
        # 存储项目数据
        self.projects_data = projects

        if projects:
            for project in projects:
                # 显示项目名称和路径
                display_text = f"{project['name']} ({project['path']})"
                self.project_choice.Append(display_text)
            self.project_choice.SetSelection(0)
            self.status_text.SetLabel(f"已加载 {len(projects)} 个最近项目")
        else:
            # 检查是否是权限问题
            claude_dir = Path.home() / ".claude"
            if not claude_dir.exists():
                self.project_choice.Append("Claude目录不存在")
                self.status_text.SetLabel("未找到Claude配置目录，请先使用Claude Code")
            elif not os.access(claude_dir, os.R_OK):
                self.project_choice.Append("无权限访问Claude目录")
                self.status_text.SetLabel("权限不足：无法访问Claude配置目录")
            else:
                self.project_choice.Append("未找到Claude Code项目")
                self.status_text.SetLabel("未找到Claude Code项目历史记录")

    def on_refresh_projects(self, event):
        """刷新项目按钮事件"""
        self.refresh_projects()

    def get_selected_project_path(self):
        """获取选中项目的路径"""
        selection = self.project_choice.GetSelection()
        if selection >= 0 and hasattr(self, 'projects_data') and selection < len(self.projects_data):
            return self.projects_data[selection]['path']
        return None

    def launch_claude_with_mode(self, use_c_flag=False):
        """通用的Claude启动函数

        Args:
            use_c_flag (bool): 是否使用 -c 参数启动Claude
        """
        project_path = self.get_selected_project_path()
        if not project_path:
            wx.MessageBox("请先选择一个项目", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        # 使用独立线程启动，不阻塞主程序
        def launch_claude():
            try:
                import subprocess
                import tempfile
                import os

                # 获取当前选中的配置和模型
                if self.selected_index >= 0:
                    configs = self.config_manager.get_all_configs()
                    if self.selected_index < len(configs):
                        config = configs[self.selected_index]
                        model = config.get("default_model", "claude-sonnet-4-20250514")
                    else:
                        model = "claude-sonnet-4-20250514"
                else:
                    model = "claude-sonnet-4-20250514"

                # 根据参数决定启动方式
                claude_command = "claude -c" if use_c_flag else "claude"
                window_title = "Claude-c" if use_c_flag else "Claude"
                mode_text = "Claude -c" if use_c_flag else "Claude"

                # 创建临时批处理文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False, encoding='gbk') as bat_file:
                    bat_content = f'''@echo off
cd /d "{project_path}"
echo 启动{mode_text}，将使用环境变量中的模型: {model}
start "{window_title}" powershell -NoExit -Command "{claude_command}"
'''
                    bat_file.write(bat_content)
                    bat_path = bat_file.name

                # 执行批处理文件
                command = f'cmd /c "{bat_path}"'
                subprocess.Popen(command, shell=True)

                # 在主线程中更新状态
                status_message = f"已在 {project_path} 启动{mode_text} (新窗口)"
                wx.CallAfter(self.status_text.SetLabel, status_message)
                print(f"{mode_text} launched in new window at {project_path}")

            except Exception as e:
                error_message = f"启动{mode_text}失败: {str(e)}"
                wx.CallAfter(lambda: wx.MessageBox(error_message, "错误", wx.OK | wx.ICON_ERROR))

        # 启动线程
        threading.Thread(target=launch_claude, daemon=True).start()

    def on_open_claude(self, event):
        """启动Claude命令"""
        self.launch_claude_with_mode(use_c_flag=False)

    def on_open_claude_c(self, event):
        """启动Claude -c命令"""
        self.launch_claude_with_mode(use_c_flag=True)

    def on_move_up(self, event):
        """上移配置"""
        if self.selected_index < 0:
            wx.MessageBox("请先选择一个配置", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        configs = self.config_manager.get_all_configs()
        if self.selected_index > 0:
            # 交换配置
            configs[self.selected_index], configs[self.selected_index - 1] = configs[self.selected_index - 1], configs[self.selected_index]

            # 更新配置数据
            self.config_manager.configs_data["configs"] = configs
            self.config_manager.save_configs_data()

            # 刷新列表
            self.refresh_list()

            # 更新选中状态
            self.selected_index -= 1
            self.config_list.Select(self.selected_index, True)

            # 状态提示
            self.status_text.SetLabel(f"已上移配置: {configs[self.selected_index]['name']}")

    def on_move_down(self, event):
        """下移配置"""
        if self.selected_index < 0:
            wx.MessageBox("请先选择一个配置", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        configs = self.config_manager.get_all_configs()
        if self.selected_index < len(configs) - 1:
            # 交换配置
            configs[self.selected_index], configs[self.selected_index + 1] = configs[self.selected_index + 1], configs[self.selected_index]

            # 更新配置数据
            self.config_manager.configs_data["configs"] = configs
            self.config_manager.save_configs_data()

            # 刷新列表
            self.refresh_list()

            # 更新选中状态
            self.selected_index += 1
            self.config_list.Select(self.selected_index, True)

            # 状态提示
            self.status_text.SetLabel(f"已下移配置: {configs[self.selected_index]['name']}")


class SimpleApp(wx.App):
    """应用程序"""

    def OnInit(self):
        frame = ConfigManagementFrame()
        frame.Show()
        return True


if __name__ == "__main__":
    app = SimpleApp()
    app.MainLoop()