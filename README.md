# webmdai

一个~~功能强大~~的Python命令行工具，提供网页内容爬取、文本处理和LLM处理三大功能模块。

> 这是一个纯AI开发的小工具，请您不要抱有太多期待。毕竟它还把我翻译的内容给删了。。详见`archive/AGENTS.md`
> 
> 欢迎提交PR和Issue，包括AI写的。
> 
> 谢谢您。

## 功能特性

- **网页爬取 (fetch)**: 支持多种服务商爬取网页内容并保存为Markdown格式
- **文本处理 (deal)**: 批量处理Markdown文件，支持正则表达式和普通文本替换/删除
- **LLM处理 (llm)**: 调用兼容OpenAI格式的API进行智能处理
- **模型管理 (model)**: 管理多个LLM模型配置
- **工作流 (workflow)**: 自动化多阶段处理管道
- **路径工具 (path)**: 路径调试和项目管理

## 安装

### 从源码安装

```bash
git clone https://github.com/epheiamoe/webmdai.git
cd webmdai
pip install -e .
```

### 依赖项

- Python 3.8+
- requests
- beautifulsoup4
- click
- gitpython
- colorama

## 路径处理规则（重要！）

> 🚀 **零基础用户？请先阅读 [零基础5分钟上手](doc_example/零基础5分钟上手.md)**

### 核心规则：所有文件放在同一个目录

webmdai中的所有相对路径都相对于**你运行命令时的当前目录**。为了避免路径问题，建议：

```
my_project/              ← 项目目录（你在这里运行命令）
├── workflow.yaml        ← 工作流配置
├── TASK.md             ← 任务文件
├── prompts/            ← 提示词目录
│   └── translate.txt
└── （输出文件自动生成）
```

### 路径基准目录

| 命令/场景                                         | 基准目录              | 说明     |
| --------------------------------------------- | ----------------- | ------ |
| `webmdai workflow run workflow.yaml`          | workflow.yaml所在目录 | 自动推断   |
| `webmdai workflow run workflow.yaml -d /path` | 指定目录              | 覆盖默认   |
| `webmdai path info`                           | 当前目录              | 相对路径基准 |

### 工作流中的相对路径

在工作流配置中，所有相对路径都相对于**workflow.yaml文件所在目录**：

```yaml
stages:
  - name: 爬取
    type: fetch
    params:
      taskfile: "TASK.md"           # 相对于workflow.yaml所在目录

  - name: 翻译
    type: llm
    params:
      prompt_file: "prompts/translate.txt"  # 相对于workflow.yaml所在目录

  - name: 替换
    type: replace
    params:
      replacements_file: "names.json"      # 相对于workflow.yaml所在目录
```

### 路径调试工具

遇到路径问题？使用 `webmdai path` 命令：

```bash
# 查看路径解析信息
webmdai path info workflow.yaml

# 检查工作流中所有路径
webmdai path check workflow.yaml

# 查看项目目录结构
webmdai path tree
```

### 常见问题

**Q：文件应该放在哪里？**
A：全部放在同一个目录下！进入项目目录，所有文件都创建在这里。

**Q：提示词文件找不到？**
A：确保提示词文件在workflow.yaml同目录或子目录，使用 `webmdai path check` 检查。

**Q：路径太复杂怎么办？**
A：使用绝对路径最可靠，如 `prompt_file: "/full/path/to/prompts/translate.txt"`

## 快速开始

> 🚀 **零基础用户？先看 [5分钟快速上手](QUICKSTART.md)**

### 1. 配置LLM模型

```bash
# 添加OpenAI模型
webmdai model add --name gpt5.2 --endpoint https://api.openai.com/v1 --model gpt-5.2 --key your-api-key

# 添加自定义端点
webmdai model add --name local --endpoint http://localhost:8000/v1 --model llama3 --key dummy-key

# 设置默认模型
webmdai model set-default gpt5.2

# 列出所有模型
webmdai model list
```

### 2. 爬取网页

```bash
# 交互模式
webmdai fetch interactive

# 批量模式
webmdai fetch batch -w "https://example.com,https://example2.com" -n mytask -st

# 从任务文件爬取（默认 TASK.md）
webmdai fetch from-task
webmdai fetch from-task mytask.md -n mytask -st
```

### 3. 文本处理

```bash
# 交互模式
webmdai deal interactive

# 批量替换
webmdai deal batch --text -f "old_text" -r "new_text" -d ./docs

# 正则替换
webmdai deal batch --re -f "\\d+" -r "[NUMBER]" -d ./docs
```

### 4. LLM处理

```bash
# 交互模式
webmdai llm interactive

# 批量翻译
webmdai llm batch -d ./articles --all -t translate -m gpt4

# 批量摘要
webmdai llm batch -d ./articles --separate -t summarize -m gpt4
```

### 5. 工作流（自动化管道）

```bash
# 交互式向导（推荐新手）
webmdai workflow wizard

# 查看可用模板
webmdai workflow templates

# 初始化工作流（从模板创建）
webmdai workflow init translate-novel -o workflow.yaml

# 运行工作流（自动推断工作目录）
webmdai workflow run
webmdai workflow run myproject/workflow.yaml  # 指定路径

# 设置变量运行
webmdai workflow run -v novel_name="我的小说" -v target_lang="简体中文"
```

**工作流**可以将多个步骤（爬取→**清理**→翻译→替换→合并）串联成一个自动化管道，用 YAML 配置，无需编写脚本。

**完整的轻小说翻译工作流示例：**

```yaml
name: 轻小说翻译
description: 爬取、清理、翻译、人名替换、合并

stages:
  - name: 爬取章节
    type: fetch
    params:
      source: taskfile
      taskfile: TASK.md
      reader: jina
      delay: 1.0

  - name: 清理内容                    # 关键！减少Token消耗
    type: clean
    params:
      file_pattern: "*.md"
      preset: "kakuyomu"             # 使用预设规则
      output_suffix: "_cleaned"

  - name: 翻译内容
    type: llm
    params:
      file_pattern: "*_cleaned_*.md"  # 使用清理后的文件
      prompt_file: "prompts/translate.txt"  # 自定义提示词
      output_suffix: "_zh"

  - name: 人名替换
    type: replace
    params:
      file_pattern: "*_zh_*.md"
      replacements_file: "names/characters.json"

  - name: 合并章节
    type: merge
    params:
      file_pattern: "*_zh_*.md"
      output: "全书合并版.md"
```

## 详细使用说明

### Fetch 模块 - 网页爬取

#### 交互模式

```bash
webmdai fetch interactive
```

按提示输入网址（每行一个），输入 `/start` 结束，然后输入任务名称。

#### 批量模式

```bash
webmdai fetch batch -w url1,url2,url3 -n 任务名 [选项]
```

**选项：**

- `-r, --reader`: 指定爬取服务商（默认: jina）
- `-w, --websites`: 网址列表（逗号分隔）
- `-n, --name`: 任务名称
- `-s, --separate`: 每个网页保存为单独文件
- `-t, --together`: 所有网页合并为一个文件
- `-st`: 同时生成单独文件和合并文件（默认）

#### 从任务文件爬取

从Markdown文件中读取链接列表并爬取，适合管理批量爬取任务。

```bash
# 使用默认的 TASK.md 文件
webmdai fetch from-task

# 指定其他文件
webmdai fetch from-task mytask.md

# 覆盖任务名称
webmdai fetch from-task TASK.md -n myproject -st
```

**任务文件格式（TASK.md）：**

```markdown
# 任务名称（会用作输出目录名）

## 需要爬取的链接

- [Example](https://example.com)
- [GitHub](https://github.com)
- [文档](https://docs.python.org)

## 参考资料

更多描述文字...[链接文字](https://another-link.com)
```

**支持的链接格式：**

- 行内链接: `[文字](https://example.com)`
- 尖括号包裹: `<https://example.com>`

**选项：**

- `TASKFILE`: 任务文件路径（默认: TASK.md）
- `-n, --name`: 覆盖任务名称
- `-r, --reader`: 指定爬取服务商
- `-s, --separate`, `-t, --together`, `-st`: 输出模式

**支持的Reader：**

- `jina`: Jina Reader（免费，无需API密钥，但建议配置API Key以提高速率限制）
- `firecrawl`: Firecrawl（需要API密钥）
- `direct`: 直接爬取（使用requests+BeautifulSoup）

**配置 Fetch 选项：**

在 `~/.webmdai/config.json` 中可以配置以下选项：

```json
{
  "fetch": {
    "default_reader": "jina",
    "timeout": 30,
    "retry_times": 3,
    "delay": 1.0,
    "jina_api_key": null
  }
}
```

- `delay`: 爬取间隔（秒），默认为1秒，避免请求过快被封
- `jina_api_key`: Jina AI API密钥，可选，用于提高速率限制

获取 API Key: https://jina.ai/reader

如果遇到 400 错误或者速率限制，建议配置 Jina API Key。

### Deal 模块 - 文本处理

#### 交互模式

```bash
webmdai deal interactive
```

#### 批量模式

```bash
webmdai deal batch [选项]
```

**选项：**

- `-d, --directory`: 工作目录（默认: 当前目录）
- `--text`: 普通文本模式
- `--re`: 正则表达式模式
- `-f, --find`: 查找内容
- `-r, --replace`: 替换内容（可选，留空表示删除）
- `--preview`: 预览修改但不实际执行
- `--no-git`: 禁用Git自动管理

**Git自动管理：**

- 自动检查/初始化Git仓库
- 操作前自动提交备份
- 提交信息格式：`webmdai: [操作类型] 查找词 -> 替换词`

### LLM 模块 - LLM处理

#### 预设任务

- `explain`: 解释技术文档或代码
- `translate`: 翻译为中文
- `summarize`: 生成内容摘要
- `abstract`: 提取关键要点

#### 交互模式

```bash
webmdai llm interactive
```

#### 批量模式

```bash
webmdai llm batch [选项]
```

**选项：**

- `-d, --directory`: 工作目录
- `-m, --model`: 指定使用的模型（别名或完整名称）
- `-t, --task`: 任务类型（explain/translate/summarize/abstract）
- `--separate`: 分批处理模式
- `--all`: 合并处理模式
- `-p, --prompt`: 自定义提示词（覆盖预设任务）
- `-o, --output`: 输出目录

### Model 模块 - 模型管理

```bash
# 列出所有模型
webmdai model list

# 添加模型
webmdai model add --name <别名> --endpoint <API地址> --model <模型名称> --key <API密钥>

# 删除模型
webmdai model remove <别名>

# 设置默认模型
webmdai model set-default <别名>
```

**配置文件位置：** `~/.webmdai/config.json`

**环境变量支持：** 在配置中可以使用 `$ENV_VAR` 格式引用环境变量

```json
{
  "models": {
    "gpt4": {
      "endpoint": "https://api.openai.com/v1",
      "model": "gpt-4",
      "key": "$OPENAI_API_KEY"
    }
  }
}
```

### Workflow 模块 - 工作流自动化

工作流可以将多个处理步骤串联成一个自动化管道，适合批量处理、翻译、摘要等场景。

#### 快速开始

**新手推荐 - 使用向导：**

```bash
# 交互式向导，引导你完成配置
webmdai workflow wizard
```

**手动配置：**

```bash
# 1. 查看可用模板
webmdai workflow templates

# 2. 初始化工作流配置
webmdai workflow init translate-novel -o workflow.yaml

# 3. 编辑 workflow.yaml 自定义配置

# 4. 运行工作流
webmdai workflow run
```

#### 命令说明

**`webmdai workflow wizard`** - 交互式向导

适合新手的引导式配置，会询问你的需求并自动创建配置文件。

**`webmdai workflow run [WORKFLOW_FILE]`** - 运行工作流

```bash
# 运行当前目录的 workflow.yaml
webmdai workflow run

# 运行指定路径的工作流（自动推断工作目录为该文件所在目录）
webmdai workflow run ./myproject/workflow.yaml

# 指定工作目录（覆盖自动推断）
webmdai workflow run workflow.yaml -d ./output

# 运行时设置变量
webmdai workflow run -v novel_name="我的小说"
```

**工作目录自动推断规则：**

- 如果不指定 `-d` 参数，工作目录自动设置为 workflow.yaml 所在目录
- 这简化了项目管理，无需重复指定路径

#### 工作流配置格式

```yaml
name: 工作流名称
description: 工作流描述
version: "1.0"

# 全局变量
variables:
  novel_name: "我的小说"

# 工作流阶段
stages:
  - name: 阶段名称
    type: 阶段类型  # fetch/llm/replace/merge/script/command
    enabled: true   # 是否启用
    on_error: stop  # 错误处理: stop/skip/ignore
    params:
      # 阶段参数...
```

#### 支持的阶段类型

| 类型        | 说明    | 主要参数                                                     |
| --------- | ----- | -------------------------------------------------------- |
| `fetch`   | 爬取网页  | `source`, `taskfile`, `reader`, `delay`                  |
| `clean`   | 内容清理  | `file_pattern`, `preset`/`rules_file`, `remove_patterns` |
| `llm`     | LLM处理 | `model`, `prompt_file`/`prompt_template`, `file_pattern` |
| `replace` | 文本替换  | `file_pattern`, `replacements`, `backup`                 |
| `merge`   | 合并文件  | `file_pattern`, `sort_by`, `output`                      |
| `script`  | 运行脚本  | `script`, `interpreter`, `args`                          |
| `command` | 执行命令  | `command`, `timeout`                                     |

#### 为什么需要 `clean` 阶段？

爬取的原始网页通常包含大量无关内容（导航、广告、UI元素等），直接发送给LLM会导致：

- **Token浪费**：无关内容占用大量token
- **上下文干扰**：广告文字可能被误认为正文
- **API成本增加**：token越多费用越高

`clean` 阶段使用规则（正则表达式或预设规则）自动清理内容，通常可以减少 **30%-70%** 的token消耗。

#### 完整示例：轻小说翻译

```yaml
name: 轻小说翻译
description: 爬取、翻译、人名替换、合并

stages:
  - name: 爬取章节
    type: fetch
    params:
      source: taskfile
      taskfile: TASK.md
      reader: jina
      delay: 1.0

  - name: 翻译
    type: llm
    params:
      model: default
      prompt_template: translate
      file_pattern: "*.md"
      output_suffix: "_zh"

  - name: 人名替换
    type: replace
    params:
      file_pattern: "*_zh_*.md"
      replacements:
        "罗特": "洛特"
        "阿莉莎": "阿丽莎"

  - name: 合并
    type: merge
    params:
      file_pattern: "*_zh_*.md"
      sort_by: numeric
      output: "全书合并版.md"
      add_chapter_headers: true
```

#### 高级用法

**变量替换：** 在参数中使用 `${变量名}` 引用变量

```yaml
variables:
  novel_name: "我的小说"

stages:
  - name: 合并
    type: merge
    params:
      output: "${novel_name}_合并版.md"
```

**运行时设置变量：**

```bash
webmdai workflow run -v novel_name="另一部小说"
```

**条件执行：**

```yaml
stages:
  - name: 可选步骤
    type: llm
    enabled: false  # 默认禁用
```

**错误处理：**

```yaml
stages:
  - name: 可能失败的步骤
    type: llm
    on_error: skip  # 失败时跳过，继续执行后续阶段
```

## 交互式命令

在交互模式下支持以下斜杠命令：

- `/start`: 结束URL列表输入
- `/exit`: 退出程序
- `/help`: 显示帮助信息

## 输出规范

### Fetch 输出

创建以任务名命名的文件夹：

- `separate` 模式：`任务名_序号_网页标题.md`
- `together` 模式：`任务名_合并.md`
- `both` 模式：同时生成上述两种文件

每个文件包含YAML frontmatter元数据：

```yaml
---
fetch_time: 2024-01-01T00:00:00
source_url: https://example.com
title: 页面标题
---
```

### LLM 输出

- `separate` 模式：`原文件名_任务名.md`
- `all` 模式：`合并_任务名.md`

## 扩展开发

### 添加新的Reader

```python
from webmdai.modules.fetcher import BaseReader, register_reader

class MyReader(BaseReader):
    name = "myreader"

    def fetch(self, url: str) -> FetchResult:
        # 实现爬取逻辑
        pass

# 注册Reader
register_reader("myreader", MyReader)
```

### 添加新的LLM客户端

```python
from webmdai.modules.llm_handler import BaseLLMClient, register_llm_client

class MyLLMClient(BaseLLMClient):
    def chat_completion(self, messages, **kwargs) -> str:
        # 实现API调用
        pass

# 注册客户端
register_llm_client("myclient", MyLLMClient)
```

## 测试

```bash
# 运行所有测试
python -m pytest webmdai/tests/

# 运行特定测试
python -m pytest webmdai/tests/test_config.py

# 生成覆盖率报告
python -m pytest --cov=webmdai webmdai/tests/
```

## 项目结构

```
webmdai/
├── cli.py              # 命令行入口
├── config.py           # 配置管理
├── models/             # 数据模型
│   ├── fetch_result.py
│   └── llm_task.py
├── modules/
│   ├── fetcher.py      # 爬取模块
│   ├── processor.py    # 文本处理模块
│   ├── llm_handler.py  # LLM处理模块
│   └── git_handler.py  # Git自动管理
├── utils/
│   ├── file_utils.py   # 文件操作工具
│   └── validators.py   # 输入验证
└── tests/              # 单元测试
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
