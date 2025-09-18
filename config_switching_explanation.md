# Claude Config Switcher 配置切换说明

## 🎯 当前切换配置的工作原理

### ✅ **切换的是 Claude Code 配置文件**

当前的配置切换机制是将配置写入 **Claude Code 的配置文件**，具体位置：

```
C:\Users\用户名\.claude\settings.json
```

### 📋 切换过程

1. **配置管理器中的"切换配置"按钮**：
   - 从 `cc_switcher_configs.json` 中读取选中的配置
   - 将配置写入 `~/.claude/settings.json`
   - 更新 `active_config` 记录

2. **Claude Code 的配置文件格式**：
   ```json
   {
     "ANTHROPIC_BASE_URL": "https://api.anthropic.com",
     "ANTHROPIC_AUTH_TOKEN": "sk-ant-api03-...",
     "default_model": "claude-3-haiku-20240307"
   }
   ```

### 🚫 **不是系统环境变量**

- **不会修改** Windows 系统环境变量
- **不会修改** 用户环境变量
- **只修改** Claude Code 的配置文件

### 🔄 配置文件优先级

Claude Code 启动时会按以下顺序读取配置：

1. **`~/.claude/settings.json`** (当前应用修改的文件)
2. 系统环境变量（如果配置文件不存在）
3. 默认配置

### 📝 使用方法

1. **在应用中切换配置**：
   - 打开配置管理器
   - 选择一个配置
   - 点击"切换配置"按钮

2. **验证切换成功**：
   - Claude Code 会使用新的配置
   - 可以通过 API 测试验证

3. **查看当前配置**：
   - 打开 `C:\Users\用户名\.claude\settings.json`
   - 或在应用中查看活跃的配置标记

### 🎉 优势

- **即时生效**：无需重启 Claude Code
- **安全可靠**：不会影响系统其他应用
- **配置持久**：下次启动 Claude Code 时仍有效
- **灵活切换**：可以随时在不同配置间切换

---

总结：这个应用是专门为 Claude Code 设计的配置管理工具，通过修改 Claude Code 的配置文件来实现配置切换，而不是修改系统环境变量。