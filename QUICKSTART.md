# WebMDAI 5分钟快速上手

> 零基础用户的入门指南，用最少的命令完成最常用的任务。

## 场景 1: 我有一个网页链接，想翻译它

```bash
# 方式1: 使用向导（推荐新手）
webmdai workflow wizard
# 按提示输入链接和选择选项即可

# 方式2: 手动创建（了解流程）
# 1. 创建任务文件，写入链接
echo "https://example.com/article" > TASK.md

# 2. 初始化翻译工作流
webmdai workflow init translate-novel -o workflow.yaml

# 3. 运行
webmdai workflow run
```

## 场景 2: 我有多个链接需要批量翻译

```bash
# 1. 创建任务文件，包含所有链接
cat > TASK.md << 'EOF'
# 我的翻译任务

## 参考链接
- [第一章](https://example.com/chapter1)
- [第二章](https://example.com/chapter2)
- [第三章](https://example.com/chapter3)
EOF

# 2. 初始化并运行
webmdai workflow init translate-novel -o workflow.yaml
webmdai workflow run
```

## 场景 3: 我已经有一个项目目录

```bash
# 进入项目目录
cd myproject

# 创建任务文件（如果没有）
echo "https://example.com/article" > TASK.md

# 初始化工作流
webmdai workflow init translate-novel -o workflow.yaml

# 编辑 TASK.md 添加更多链接
# 运行
webmdai workflow run
```

## 场景 4: 我只想爬取网页，不需要翻译

```bash
# 交互式爬取（适合少量链接）
webmdai fetch interactive

# 批量爬取（适合大量链接）
webmdai fetch from-task TASK.md
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `webmdai workflow wizard` | 交互式向导，推荐新手 |
| `webmdai workflow run` | 运行当前目录的 workflow.yaml |
| `webmdai workflow run path/to/workflow.yaml` | 运行指定路径的工作流 |
| `webmdai workflow templates` | 查看可用模板 |
| `webmdai workflow init <模板名>` | 从模板创建工作流 |
| `webmdai fetch from-task` | 从 TASK.md 爬取链接 |

## 任务文件格式 (TASK.md)

```markdown
# 任务名称

## 参考链接
- [链接描述](https://example.com)
- [另一个链接](https://example2.com)

## 说明
这里可以写任何备注...
```

## 首次使用必看

### 1. 配置LLM模型（只需一次）

```bash
# 添加OpenAI兼容的API
webmdai model add --name mymodel \
    --endpoint https://api.openai.com/v1 \
    --model gpt-4 \
    --key your-api-key

# 设为默认
webmdai model set-default mymodel
```

### 2. 验证安装

```bash
# 查看帮助
webmdai --help

# 查看工作流帮助
webmdai workflow --help
```

### 3. 快速测试

```bash
# 创建测试目录
mkdir test_project && cd test_project

# 创建任务文件
echo "https://example.com" > TASK.md

# 使用向导创建配置
webmdai workflow wizard
# 按提示选择选项

# 运行
webmdai workflow run
```

## 常见问题

### Q: 运行后文件在哪里？
A: 工作流会在工作目录下创建 `output/` 文件夹，所有输出都在里面。

### Q: 如何修改翻译提示词？
A: 编辑 `workflow.yaml` 文件，找到 `llm` 阶段的 `prompt_template` 或 `prompt_file`。

### Q: 如何添加更多链接？
A: 编辑 `TASK.md` 文件，按格式添加链接后重新运行 `webmdai workflow run`。

### Q: 如何只爬取不翻译？
A: 编辑 `workflow.yaml`，将 `llm` 阶段的 `enabled` 设为 `false`。

### Q: 工作流文件找不到？
A: 使用向导模式或运行 `webmdai workflow init translate-novel` 创建。

## 下一步

- 阅读 [完整文档](README.md) 了解所有功能
- 查看 [工作流模板](workflow.example.yaml) 学习高级用法
- 运行 `webmdai workflow templates` 查看所有可用模板
