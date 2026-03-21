# NumCraft GitHub 部署指南

## ⚠️ 重要安全提示

**切勿在对话中分享您的GitHub令牌！** 如果您已经分享了令牌，请立即撤销：
1. 访问 GitHub Settings > Developer settings > Personal access tokens
2. 找到暴露的令牌并点击 "Delete" 删除
3. 创建新的令牌用于后续操作

---

## 方式一：使用 GitHub CLI（推荐）

### 1. 安装 GitHub CLI

```bash
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows (使用 winget)
winget install --id GitHub.cli
```

### 2. 认证

```bash
gh auth login
```

按照提示完成认证。

### 3. 创建仓库并推送

```bash
# 在项目根目录执行
cd /workspace/projects

# 创建 .gitignore（已创建）
# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: NumCraft multi-agent G-code generation system"

# 创建 GitHub 仓库
gh repo create numcraft --public --description "Multi-Agent Collaborative System for Intelligent G-Code Generation" --source=. --push

# 推送代码
git push -u origin main
```

---

## 方式二：手动创建仓库

### 步骤 1: 在 GitHub 上创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - Repository name: `numcraft`
   - Description: `Multi-Agent Collaborative System for Intelligent G-Code Generation`
   - 选择 Public
   - **不要**勾选 "Add a README file"（我们已经有了）
   - **不要**勾选 "Add .gitignore"（我们已经有了）
   - License: MIT
3. 点击 "Create repository"

### 步骤 2: 推送本地代码

```bash
cd /workspace/projects

# 初始化 Git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: NumCraft multi-agent G-code generation system

Features:
- Multi-agent collaborative architecture (5 specialized agents)
- Intelligent feature recognition from natural language
- Automated tool selection and parameter optimization
- Standard G-code generation (FANUC compliant)
- Comprehensive safety validation
- Support for holes, slots, pockets, and contours

Tech stack:
- LangGraph 1.0 for agent orchestration
- LangChain for tool integration
- PostgreSQL for memory persistence"

# 添加远程仓库（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/numcraft.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

---

## 方式三：使用 Personal Access Token

### 步骤 1: 创建新的访问令牌

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 设置名称: "NumCraft Deployment"
4. 选择权限: `repo` (完整仓库访问权限)
5. 点击 "Generate token"
6. **立即复制令牌**（只显示一次）

### 步骤 2: 推送代码

```bash
cd /workspace/projects

# 初始化
git init
git add .
git commit -m "Initial commit"

# 使用令牌推送（替换 YOUR_TOKEN 和 YOUR_USERNAME）
git remote add origin https://YOUR_TOKEN@github.com/YOUR_USERNAME/numcraft.git
git branch -M main
git push -u origin main
```

---

## 推送后的配置

### 1. 设置仓库描述和主题

在仓库设置中添加：
- Website: （您的项目网站）
- Topics: `cnc`, `g-code`, `multi-agent`, `langgraph`, `machining`, `automation`, `manufacturing`, `artificial-intelligence`

### 2. 启用 GitHub Pages（可选）

如果需要展示文档：
1. Settings > Pages
2. Source: Deploy from a branch
3. Branch: main, /docs folder
4. Save

### 3. 添加徽章

在 README.md 顶部添加：

```markdown
[![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/numcraft?style=social)](https://github.com/YOUR_USERNAME/numcraft/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/YOUR_USERNAME/numcraft?style=social)](https://github.com/YOUR_USERNAME/numcraft/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/YOUR_USERNAME/numcraft)](https://github.com/YOUR_USERNAME/numcraft/issues)
```

---

## 项目文件清单

确保以下文件已创建：

```
✅ README.md - 项目主文档
✅ LICENSE - MIT 许可证
✅ .gitignore - Git 忽略文件
✅ requirements.txt - Python 依赖
✅ docs/ARCHITECTURE.md - 架构文档
✅ docs/PERFORMANCE_VERIFICATION.md - 性能验证报告
✅ examples/basic_usage.py - 使用示例
✅ src/agents/agent.py - 主 Agent
✅ src/tools/*.py - 工具集
✅ src/graphs/*.py - 流程图
✅ config/agent_llm_config.json - 配置文件
```

---

## 下一步

推送完成后：

1. **完善文档**: 添加更多示例和教程
2. **添加测试**: 完善 test suite
3. **创建 Release**: 打 tag 发布版本
4. **推广项目**: 在相关社区分享

---

## 常见问题

### Q: 推送失败怎么办？

A: 检查：
- 令牌权限是否正确
- 仓库名称是否已存在
- 网络连接是否正常

### Q: 如何更新代码？

A: 
```bash
git add .
git commit -m "Update description"
git push
```

### Q: 如何添加协作者？

A: Settings > Manage access > Invite a collaborator

---

## 安全建议

1. **永远不要**在代码中硬编码密钥或令牌
2. 使用环境变量存储敏感信息
3. 定期轮换访问令牌
4. 为不同项目使用不同的令牌
5. 启用双因素认证（2FA）

---

<div align="center">

**祝您部署顺利！**

</div>
