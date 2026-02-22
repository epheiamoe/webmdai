# WebMDAI 项目结构说明

## 目录结构

```
webmdai/                          # 项目根目录
├── webmdai/                      # Python包目录（主要代码）
│   ├── __init__.py
│   ├── __main__.py               # 支持 python -m webmdai 运行
│   ├── cli.py                    # 命令行入口
│   ├── config.py                 # 配置管理
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── fetch_result.py       # 爬取结果模型
│   │   ├── llm_task.py          # LLM任务模型
│   │   └── workflow.py          # 工作流模型
│   ├── modules/                  # 功能模块
│   │   ├── __init__.py
│   │   ├── content_cleaner.py   # 内容清理模块（新增）
│   │   ├── fetcher.py           # 网页爬取
│   │   ├── llm_handler.py       # LLM处理
│   │   ├── processor.py         # 文本处理
│   │   ├── git_handler.py       # Git管理
│   │   └── workflow_engine.py   # 工作流引擎
│   ├── utils/                    # 工具函数
│   │   ├── __init__.py
│   │   ├── file_utils.py        # 文件操作
│   │   └── validators.py        # 输入验证
│   └── tests/                    # 单元测试
│       ├── __init__.py
│       ├── test_config.py
│       ├── test_fetcher.py
│       ├── test_file_utils.py
│       ├── test_task_markdown.py
│       └── test_validators.py
├── docs/                         # 文档目录
│   └── WORKFLOW.md              # 工作流详细文档
├── .gitignore                    # Git忽略配置
├── config.example.json          # 配置文件示例
├── LICENSE                       # 许可证
├── MANIFEST.in                   # 打包配置
├── PROJECT_STRUCTURE.md         # 本文件
├── pytest.ini                  # 测试配置
├── README.md                     # 项目说明
├── requirements.txt             # 依赖列表
├── setup.py                     # 安装配置
├── TASK.md.example              # 任务文件示例
├── workflow.example.yaml        # 工作流配置示例
└── workflow.summarize.yaml      # 摘要工作流示例
```

## 关于两层 `webmdai` 目录的说明

你可能会注意到项目中有两层名为 `webmdai` 的目录：

```
webmdai/                    # 第一层：项目根目录
└── webmdai/               # 第二层：Python包目录
    ├── __init__.py
    ├── cli.py
    └── ...
```

**这是标准的Python项目结构：**

1. **第一层 `webmdai/`** - 项目根目录
   
   - 包含项目级别的文件（README, setup.py等）
   - 包含 `.git/` 版本控制
   - 这是你在GitHub上看到的目录

2. **第二层 `webmdai/webmdai/`** - Python包目录
   
   - 包含实际的Python代码
   - 是一个有效的Python包（有 `__init__.py`）
   - 安装后可以通过 `import webmdai` 导入

**为什么这样设计？**

- 分离项目元数据和源代码
- 支持 `pip install -e .` 开发模式安装
- 避免命名冲突
- 符合Python社区惯例

## 工作流相关目录（运行时生成）

运行工作流时会生成以下目录（已添加到 .gitignore）：

```
.
├── TASK/                       # fetch阶段输出
│   ├── TASK_1_xxx.md
│   ├── TASK_2_xxx.md
│   └── ...
├── prompts/                    # 自定义提示词目录（用户创建）
│   └── translate_novel.txt
├── rules/                      # 清理规则目录（用户创建）
│   └── kakuyomu.yaml
├── names/                      # 人名替换规则（用户创建）
│   └── characters.json
└── ZhChapters_Collected/       # merge阶段输出
    └── ...
```

## 快速开始

### 1. 安装

```bash
cd webmdai                    # 进入项目根目录（第一层）
pip install -e .
```

### 2. 配置

```bash
# 复制示例配置
cp config.example.json ~/.webmdai/config.json
# 编辑配置，添加模型API密钥
```

### 3. 运行

```bash
# 直接运行
webmdai fetch from-task

# 或使用Python模块方式
cd webmdai
python -m webmdai fetch from-task
```

# 
