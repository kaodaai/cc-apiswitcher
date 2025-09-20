# CC配置切换器 v1.0

🎯 **专业的Claude CLI配置管理工具，支持项目快速启动**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/GUI-wxPython-orange.svg" alt="GUI">
  <img src="https://img.shields.io/badge/Version-1.0-green.svg" alt="Version">
</p>

<p align="center">
  <strong>作者: kaodaai</strong>
</p>

## ✨ 功能特色

### 🔧 配置管理
- **配置CRUD** - 完整的配置增删改查功能
- **智能编辑** - 选中配置即可就地编辑，支持备注字段
- **安全删除** - 带确认提示的安全删除机制
- **一键切换** - 快速切换Claude CLI活跃配置
- **环境变量** - 直接设置系统环境变量

### 🧪 API测试验证
- **单配置测试** - 验证指定配置的API连通性
- **批量测试** - 一键测试所有配置，支持并发
- **实时状态** - 动态显示测试进度和结果
- **结果持久化** - 测试结果自动保存，颜色编码显示

### 🚀 项目快速启动
- **智能发现** - 自动扫描Claude Code项目历史
- **最近优先** - 按最后访问时间排序显示项目
- **一键启动** - 支持 `claude` 和 `claude -c` 两种启动模式
- **路径跳转** - 自动切换到项目目录执行命令

### 🎨 用户界面
- **单窗口设计** - 所有功能集中在一个界面
- **多列展示** - 配置信息清晰展示，支持鼠标悬停查看备注
- **实时配置显示** - 顶部显示当前Claude配置和系统环境变量
- **状态反馈** - 丰富的操作状态提示和错误处理

## 🖼️ 界面预览

```
┌────────────────── CC配置切换器 v1.0 ──────────────────┐
│ 当前Claude配置: https://api.anthropic.com | sonnet-4   │
│ 系统环境变量: https://api.anthropic.com               │
│                                                      │
│ ┌──── 配置列表 ────────────────────────────────────┐ │
│ │ 配置名称 │ 模型     │ 状态 │ 时间 │ 测试结果    │ │
│ │ ──────────────────────────────────────────────── │ │
│ │ prod     │ sonnet-4 │ 通过 │15:30 │ 正常响应    │ │
│ │ test     │ haiku    │ 失败 │15:25 │ 认证错误    │ │
│ │ dev      │ opus     │未测试│      │             │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ ┌──── 配置编辑 ────────────────────────────────────┐ │
│ │ 配置名称: [prod-config              ]           │ │
│ │ 基础URL:  [https://api.anthropic.com ]           │ │
│ │ 认证令牌: [************************]           │ │
│ │ 默认模型: [claude-sonnet-4-20250514▼]           │ │
│ │ 备    注: [生产环境配置             ]           │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ [添加][更新][删除]  [测试][批量测试]  [切换][环境变量] │
│                                                      │
│ ┌──── 项目快速启动 ─────────────────────────────────┐ │
│ │最近项目:[cc-switcher (D:\Code\cc-switcher)▼]    │ │
│ │        [刷新] [启动Claude] [启动Claude -c]       │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ 状态: 就绪                              by: kaodaai │
└──────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 下载使用

1. **下载可执行文件**
   ```
   下载 CCSwicher.exe (约21MB)
   双击运行即可，无需安装Python环境
   ```

2. **或从源码运行**
   ```bash
   git clone https://github.com/kaodaai/cc-switcher.git
   cd cc-switcher
   pip install wxpython requests
   python cc_switcher.py
   ```

### 基本使用

1. **管理配置**
   - 点击「添加」创建新配置
   - 选择配置后点击「更新」修改
   - 配置名称支持鼠标悬停显示备注

2. **测试验证**
   - 选择配置后点击「测试」验证API
   - 点击「批量测试」验证所有配置
   - 测试结果会显示在列表中并持久保存

3. **切换配置**
   - 选择配置后点击「切换配置」设为Claude CLI活跃配置
   - 点击「环境变量」直接设置系统环境变量

4. **项目启动**
   - 程序自动扫描Claude Code项目历史
   - 从下拉列表选择项目
   - 点击「启动Claude」或「启动Claude -c」快速启动

## 📋 系统要求

### 运行环境
- **操作系统**: Windows 10/11
- **Python**: 3.11+ (源码运行)
- **依赖包**: wxpython, requests (源码运行)

### 可执行文件
- **文件大小**: ~21MB
- **运行依赖**: 无需Python环境
- **启动方式**: 双击即可运行

## 🔧 开发构建

### 安装依赖
```bash
pip install wxpython>=4.2.0 requests>=2.31.0 pyinstaller>=6.14.2
```

### 项目结构
```
cc-switcher/
├── cc_switcher.py              # 主程序
├── build.py                    # 构建脚本
├── README.md                   # 项目文档
├── pyproject.toml              # 项目配置
└── dist/CCSwicher.exe          # 构建的可执行文件
```

### 构建可执行文件
```bash
# 构建
python build.py

# 清理旧构建
python build.py clean
```

## 📊 技术架构

### 核心组件
```
SimpleConfigManager         # 配置管理核心
├── 配置CRUD操作            # 增删改查
├── API测试功能             # 单个和批量测试
├── 状态持久化              # 测试结果保存
├── 环境变量管理            # 系统集成
└── Claude项目发现          # 项目历史扫描

ConfigManagementFrame       # 主界面
├── 配置列表显示            # 多列信息展示
├── 配置编辑区域            # 表单编辑
├── 项目快速启动            # 项目管理
├── 操作按钮组              # 功能入口
└── 状态反馈栏              # 操作提示
```

### 数据结构
```json
{
  "configs": [
    {
      "name": "配置名称",
      "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
      "ANTHROPIC_AUTH_TOKEN": "sk-ant-...",
      "default_model": "claude-sonnet-4-20250514",
      "note": "配置备注",
      "test_status": "通过",
      "test_time": "15:30:25",
      "test_message": "Q:测试 A:正常响应"
    }
  ],
  "active_config": "配置名称",
  "version": "1.0"
}
```

## 🎯 使用场景

### 开发者
- **多环境管理** - 开发/测试/生产环境配置快速切换
- **API验证** - 配置有效性批量验证
- **项目切换** - Claude Code项目间快速跳转
- **团队协作** - 统一的配置管理方式

### 个人用户
- **多账号管理** - 管理不同的Claude账号配置
- **配置备份** - 安全的本地配置存储
- **快速启动** - 便捷的项目开发环境启动

## 🛡️ 安全特性

### 数据保护
- **本地存储** - 所有配置数据存储在本地
- **令牌脱敏** - 界面显示时自动隐藏敏感信息
- **权限检查** - 完善的文件访问权限验证
- **安全删除** - 删除操作需要用户确认

### 操作安全
- **状态保护** - 添加模式下防止误操作
- **输入验证** - 完整的表单字段验证
- **错误处理** - 友好的错误提示和异常处理
- **权限提示** - 清晰的权限不足提示信息

## 📈 更新日志

### v1.0 (当前版本)
- ✅ 完整的配置管理功能
- ✅ API测试和批量测试
- ✅ Claude Code项目自动发现
- ✅ 项目快速启动功能
- ✅ 智能状态显示和错误处理
- ✅ 优化的用户界面设计
- ✅ 完善的权限处理机制

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 问题报告
如遇到问题，请提供以下信息：
- 操作系统版本
- Python版本（如果从源码运行）
- 具体操作步骤
- 错误信息截图

### 功能建议
欢迎提出改进建议和新功能需求。

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [Claude CLI 官方文档](https://docs.claude.ai/)
- [wxPython 文档](https://docs.wxpython.org/)
- [问题反馈](https://github.com/kaodaai/cc-switcher/issues)

---

**CC配置切换器 v1.0** - 让Claude CLI配置管理变得简单高效！ 🚀

**作者: kaodaai**