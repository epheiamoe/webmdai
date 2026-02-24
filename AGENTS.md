# AGENTS.md - AI Agent 开发指南

> 本文件为 AI Agent 提供项目维护和开发指导

---

## 项目概览

### 仓库用途
WebMDAI - 一个纯 AI 开发的 Python 命令行工具，提供网页内容爬取、文本处理和 LLM 处理功能。

### 技术栈
- **语言**: Python 3.8+
- **核心依赖**: requests, beautifulsoup4, click, pyyaml, python-dotenv
- **测试**: pytest
- **CLI框架**: Click

### 目标用户
- 需要批量处理网页内容的开发者
- 轻小说翻译爱好者
- 需要自动化文本处理流程的用户

---

## 构建与部署

### 安装
```bash
# 源码安装
pip install -e .

# 开发模式安装
pip install -e ".[dev]"
```

### 开发
```bash
# 运行测试
python -m pytest webmdai/tests/ -v

# 带覆盖率测试
python -m pytest --cov=webmdai webmdai/tests/
```

### 构建
```bash
# 构建发布包
python setup.py sdist bdist_wheel
```

---

## 代码规范

### 风格指南
- 使用 Python 标准风格（PEP 8）
- 行长度限制：100 字符
- 使用 Black 格式化：`black webmdai/`
- 使用 Flake8 检查：`flake8 webmdai/`

### 命名约定
- **模块**: 小写字母 + 下划线 (snake_case)
- **类**: 首字母大写 (PascalCase)
- **函数/变量**: 小写字母 + 下划线 (snake_case)
- **常量**: 全大写 + 下划线 (UPPER_SNAKE_CASE)

### 文件组织
```
webmdai/
├── cli.py              # 命令行入口
├── config.py           # 配置管理
├── models/             # 数据模型
│   ├── fetch_result.py
│   ├── llm_task.py
│   └── workflow.py
├── modules/            # 功能模块
│   ├── fetcher.py      # 爬取模块
│   ├── processor.py    # 文本处理
│   ├── llm_handler.py  # LLM处理
│   ├── content_cleaner.py  # 内容清理
│   ├── git_handler.py  # Git管理
│   └── workflow_engine.py  # 工作流引擎
├── utils/              # 工具函数
│   ├── file_utils.py
│   └── validators.py
└── tests/              # 单元测试
```

---

## 架构说明

### 目录结构
- **cli.py**: Click 框架实现的命令行入口
- **config.py**: 单例模式的配置管理
- **models/**: 数据模型定义
- **modules/**: 核心功能模块
- **utils/**: 通用工具函数

### 模块边界
- `fetcher`: 网页内容爬取，支持多种 Reader
- `processor`: 文本批量处理
- `llm_handler`: LLM API 调用封装
- `content_cleaner`: 网页内容清理
- `workflow_engine`: 工作流执行引擎

### 关键抽象
- `BaseReader`: 爬虫抽象基类
- `BaseLLMClient`: LLM 客户端抽象基类
- `StageConfig`: 工作流阶段配置
- `WorkflowContext`: 工作流执行上下文

---

## 测试策略

### 测试框架
- **框架**: pytest
- **覆盖率**: pytest-cov
- **测试文件位置**: `webmdai/tests/`

### 测试文件命名
- `test_<模块名>.py`

### 运行方式
```bash
# 运行所有测试
python -m pytest webmdai/tests/ -v

# 运行特定模块测试
python -m pytest webmdai/tests/test_config.py -v

# 生成覆盖率报告
python -m pytest --cov=webmdai webmdai/tests/ --cov-report=html
```

---

## 权限边界

### 允许的操作 ✅
- 修改现有代码文件和测试
- 添加新的测试用例
- 更新文档（README.md, CHANGELOG.md, doc_example/）
- 创建新的工具模块
- 提交代码到版本控制

### 禁止的操作 ❌
- 自动安装依赖（需用户确认）
- 强制 git push 到远程仓库
- 删除重要文件或历史记录
- 修改 LICENSE 或 AGENTS.md 核心规则
- 在未测试的情况下修改核心功能

### 需要用户确认的操作 ⚠️
- 修改项目依赖版本
- 重构核心模块架构
- 修改测试框架配置
- 发布新版本

---

## 常用命令

### 开发相关
```bash
# 安装
pip install -e .

# 测试
python -m pytest webmdai/tests/ -v

# 代码检查
flake8 webmdai/
black --check webmdai/
```

### 运行命令
```bash
# 查看帮助
webmdai --help

# 爬取网页
webmdai fetch from-task TASK.md

# 处理文本
webmdai deal batch --text -f "old" -r "new" -d ./docs

# LLM处理
webmdai llm batch -d ./articles --all -t translate

# 运行工作流
webmdai workflow run workflow.yaml

# 路径调试
webmdai path check workflow.yaml
webmdai path tree
```

---

## 版本管理

### 版本号规则
遵循 Semantic Versioning (SemVer)
- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的新功能
- PATCH: 向后兼容的 bug 修复

### 提交信息规范
```
<类型>: <简短描述>

[可选的详细描述]
```

类型包括: feat, fix, docs, test, refactor, chore

### 发布流程
1. 更新 CHANGELOG.md
2. 提交版本更新
3. 创建 Git tag: `git tag v0.x.x`
4. 用户确认后 push

---

## 注意事项

1. **路径问题**: 所有相对路径相对于工作流文件所在目录
2. **配置位置**: 用户配置在 `~/.webmdai/config.json`
3. **环境变量**: 支持在配置中使用 `$ENV_VAR` 引用环境变量
4. **测试优先**: 修改代码前先确保测试通过
