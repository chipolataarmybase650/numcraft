# 贡献指南

感谢您对 NumCraft 项目的关注！我们欢迎来自学术界的各种贡献。

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请通过 [GitHub Issues](https://github.com/hanshiyingbing/numcraft/issues) 提交。

提交问题时，请包含：
- 问题的详细描述
- 复现步骤（如果是 bug）
- 期望的行为
- 实际的行为
- 环境信息（Python 版本、操作系统等）

### 提交代码

1. **Fork 本仓库**

2. **创建功能分支**
```bash
git checkout -b feature/your-feature-name
```

3. **进行开发**
   - 遵循 PEP 8 代码规范
   - 编写清晰的注释
   - 添加必要的测试

4. **运行测试**
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/

# 代码格式化
black src/
isort src/
```

5. **提交更改**
```bash
git commit -m "feat: 添加XXX功能"
```

提交信息格式：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

6. **推送到 Fork**
```bash
git push origin feature/your-feature-name
```

7. **创建 Pull Request**
   - 描述您的更改
   - 关联相关的 Issue
   - 等待代码审查

## 开发环境设置

### 系统要求

- Python 3.12+
- PostgreSQL 12+（可选，用于持久化）
- Git

### 安装步骤

```bash
# 克隆您的 Fork
git clone https://github.com/YOUR_USERNAME/numcraft.git
cd numcraft

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 配置环境变量
export COZE_WORKLOAD_IDENTITY_API_KEY="your-api-key"
export COZE_INTEGRATION_MODEL_BASE_URL="your-base-url"
```

### 项目结构

```
numcraft/
├── src/
│   ├── agents/        # 智能体实现
│   ├── tools/         # 工具定义
│   ├── graphs/        # 工作流定义
│   └── storage/       # 持久化层
├── tests/             # 测试套件
├── docs/              # 文档
├── examples/          # 使用示例
└── config/            # 配置文件
```

## 代码规范

### Python 代码

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用类型注解
- 函数和类添加文档字符串
- 单行不超过 100 个字符

示例：
```python
def analyze_features(description: str, material: str) -> dict:
    """
    分析零件特征。
    
    Args:
        description: 零件描述文本
        material: 材料信息
        
    Returns:
        包含特征列表的字典
    """
    # 实现...
    pass
```

### 文档

- 使用中文编写用户文档
- API 文档使用英文
- 保持简洁明了

### 测试

- 为新功能编写测试
- 确保所有测试通过
- 测试覆盖率不低于 80%

## 行为准则

- 尊重所有贡献者
- 保持专业和建设性的讨论
- 接受建设性批评
- 关注对社区最有利的事情

## 许可证

通过贡献代码，您同意您的贡献将按照 MIT 许可证授权。

## 联系方式

- 问题反馈: [GitHub Issues](https://github.com/hanshiyingbing/numcraft/issues)
- 讨论交流: [GitHub Discussions](https://github.com/hanshiyingbing/numcraft/discussions)

---

感谢您的贡献！
