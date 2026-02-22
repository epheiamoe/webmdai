# WebMDAI 工作流系统详细文档

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [完整配置参考](#完整配置参考)
4. [阶段类型详解](#阶段类型详解)
5. [变量系统](#变量系统)
6. [实际案例](#实际案例)
7. [故障排查](#故障排查)

---

## 快速开始

### 1. 初始化工作流

```bash
# 查看可用模板
webmdai workflow templates

# 从模板创建工作流配置文件
webmdai workflow init translate-novel -o myworkflow.yaml

# 运行工作流
webmdai workflow run myworkflow.yaml
```

### 2. 最小工作流示例

```yaml
name: 简单爬取
description: 爬取网页并保存

stages:
  - name: 爬取
    type: fetch
    params:
      source: taskfile
      taskfile: TASK.md
```

---

## 核心概念

### 什么是工作流？

工作流是一系列**阶段（Stage）**组成的处理管道。每个阶段执行特定任务，前一阶段的输出作为后一阶段的输入。

```
输入 → [阶段1: 爬取] → [阶段2: 清理] → [阶段3: 翻译] → [阶段4: 合并] → 输出
```

### 工作流执行流程

1. **解析配置**：加载YAML配置文件
2. **变量替换**：替换 `${变量名}` 为实际值
3. **阶段执行**：按顺序执行每个启用的阶段
4. **错误处理**：根据 `on_error` 设置处理异常
5. **完成报告**：输出执行结果统计

---

## 完整配置参考

### 顶层配置

```yaml
name: "工作流名称"                    # 必填：工作流名称
description: "工作流描述"             # 可选：描述信息
version: "1.0"                       # 可选：版本号

# 全局变量
variables:
  novel_name: "我的小说"
  author: "作者名"

# 全局设置
settings:
  backup: true                       # 是否自动备份
  parallel: false                    # 是否并行执行（实验性）

# 阶段列表
stages: []
```

### 阶段配置

```yaml
stages:
  - name: "阶段名称"                  # 必填：阶段显示名称
    type: "fetch"                    # 必填：阶段类型
    enabled: true                    # 可选：是否启用（默认true）
    on_error: "stop"                 # 可选：错误处理策略
    condition: null                  # 可选：执行条件（未来支持）
    params: {}                       # 可选：阶段参数
```

### on_error 策略

| 值        | 说明              |
| -------- | --------------- |
| `stop`   | 立即停止整个工作流（默认）   |
| `skip`   | 跳过当前阶段，继续执行后续阶段 |
| `ignore` | 忽略错误，继续执行（不推荐）  |

---

## 阶段类型详解

### 1. fetch - 爬取网页

从任务文件或URL列表爬取网页内容。

**参数：**

```yaml
- name: 爬取章节
  type: fetch
  params:
    # 数据源设置
    source: "taskfile"               # 数据源：taskfile 或 urls
    taskfile: "TASK.md"              # 当source=taskfile时，指定任务文件
    urls: ""                         # 当source=urls时，逗号分隔的URL列表

    # 爬取设置
    reader: "jina"                   # 爬取服务：jina/firecrawl/direct
    delay: 1.0                       # 请求间隔（秒）
    timeout: 30                      # 超时时间（秒）
```

**输出变量：**

- `${TASK_DIR}` - 任务目录路径
- `${TASK_NAME}` - 任务名称

---

### 2. clean - 内容清理（新增）

清理原始HTML/Markdown内容，移除无关元素，减少Token消耗。

**参数：**

```yaml
- name: 清理内容
  type: clean
  params:
    file_pattern: "*.md"             # 要处理的文件匹配模式

    # 清理规则
    remove_selectors:                # CSS选择器移除（针对原始HTML）
      - "nav"
      - "footer"
      - ".advertisement"

    remove_patterns:                 # 正则表达式移除
      - "https?://[^\\s]+购[入买]"    # 移除购买链接
      - "### 目次.*?$(?=#|\\Z)"      # 移除目录部分
      - "!\\[Image.*?\\)"             # 移除图片

    # 内容提取
    extract_rules:                   # 内容提取规则
      start_markers:                 # 正文开始标记
        - "第\\d+話"
        - "プロローグ"
        - "第一章"
      end_markers:                   # 正文结束标记
        - "次のエピソード"
        - "书籍发售"
      min_content_length: 500        # 最小内容长度（过滤失败的）

    # LLM辅助清理（可选）
    use_llm_cleanup: false           # 是否使用LLM辅助识别正文
    llm_prompt: |                    # 自定义LLM提示词
      请从以下网页内容中提取小说正文，移除所有导航、广告、UI元素。
      只输出正文内容，不要添加任何解释。
```

**清理规则文件（推荐）：**

可以将清理规则保存为单独文件，便于复用：

```yaml
# kakuyomu.yaml - カクヨム网站清理规则
remove_patterns:
  - "^---.*?^---"                    # 移除YAML frontmatter
  - "Title:.*?Markdown Content:"     # 移除头部信息
  - "!\\[Image.*?\\)"                 # 移除图片
  - "https?://[^\\s]+(?:购[入买]|カクヨムネクスト)"  # 移除广告
  - "### 作者を応援しよう！.*?$(?=#|\\Z)"  # 移除应援提示
  - "### 目次.*?$(?=#|\\Z)"          # 移除目录
  - "### ネクスト限定エピソード.*?$"  # 移除限定章节

start_markers:
  - "プロローグ"
  - "第\\d+話"
  - "――"

end_markers:
  - "\\d+/\\d+（土）発売予定"
  - "### "
```

使用规则文件：

```yaml
- name: 清理
  type: clean
  params:
    file_pattern: "*.md"
    rules_file: "kakuyomu.yaml"
```

---

### 3. llm - LLM处理

调用LLM API进行翻译、摘要等处理。

**参数：**

```yaml
- name: 翻译
  type: llm
  params:
    file_pattern: "*_cleaned_*.md"   # 输入文件匹配模式
    output_suffix: "_zh"             # 输出文件后缀

    # 模型设置
    model: "default"                 # 模型别名（default使用配置的默认模型）

    # 提示词设置（三选一）
    prompt_template: "translate"     # 方式1：预设模板
    custom_prompt: "翻译以下内容"     # 方式2：自定义简单提示词
    prompt_file: "prompts/translate_novel.txt"  # 方式3：从文件加载完整提示词

    # 高级参数
    temperature: 0.7                 # 温度参数
    max_tokens: 4096                 # 最大token数
    batch_mode: "separate"           # 处理模式：separate（分别）/together（合并）
```

**预设提示词模板：**

| 模板名         | 用途   |
| ----------- | ---- |
| `translate` | 通用翻译 |
| `summarize` | 生成摘要 |
| `explain`   | 解释说明 |
| `abstract`  | 提取要点 |

**自定义提示词文件示例：**

```text
# prompts/translate_novel.txt

你是一位精通日中翻译的轻小说翻译者。

翻译原则：
1. 保持原文的情感张力
2. 角色人称和称呼要统一
3. 对话语气保留娇羞、挑逗感
4. 拟声词自然翻译

只输出翻译后的正文，不要包含任何解释。

待翻译内容：
{content}
```

**提示词中的变量：**

- `{content}` - 文件内容（必需）
- `{filename}` - 文件名
- `{title}` - 章节标题

---

### 4. replace - 文本替换

批量替换文本，用于人名统一、术语规范等。

**参数：**

```yaml
- name: 人名替换
  type: replace
  params:
    file_pattern: "*_zh_*.md"        # 要处理的文件
    backup: true                     # 是否备份原文件

    # 替换规则（方式1：内联定义）
    replacements:
      "罗特": "洛特"
      "阿莉莎": "阿丽莎"
      "埃伦菲亚": "埃伦菲娅"

    # 替换规则（方式2：从文件加载）
    # replacements_file: "names.json"

    # 正则替换（可选）
    regex_replacements:
      "罗[特黛蒂]": "洛特"
      "阿丽?莎": "阿丽莎"
```

**replacements.json 格式：**

```json
{
  "原文本": "更改后文本",
  "注释": "键是原文，值是替换后的文本"
}
```

---

### 5. merge - 合并文件

将多个文件合并为一个，支持排序和添加分隔符。

**参数：**

```yaml
- name: 合并章节
  type: merge
  params:
    file_pattern: "*_zh_*.md"        # 要合并的文件
    sort_by: "numeric"               # 排序方式：name/numeric/none

    # 输出设置
    output: "全书合并版.md"          # 输出文件名
    output_dir: "merged"             # 输出目录（可选，默认当前目录）

    # 内容格式
    header: |                        # 文件头部
      # ${novel_name}
      ## 全书合并版

    separator: "\n\n---\n\n"          # 章节分隔符
    add_chapter_headers: true        # 是否自动添加章节标题
    chapter_prefix: "第{num}話"      # 章节标题格式

    # 收集选项
    collect_files: true              # 是否收集文件到新目录
    collect_dir: "ZhChapters"        # 收集目录名
```

**排序方式：**

| 值         | 说明                 |
| --------- | ------------------ |
| `name`    | 按文件名排序             |
| `numeric` | 按文件名中的数字排序（推荐用于章节） |
| `none`    | 不排序，保持原有顺序         |

---

### 6. script - 运行脚本

执行自定义Python/Shell脚本。

**参数：**

```yaml
- name: 自定义处理
  type: script
  params:
    script: "scripts/post_process.py"  # 脚本路径
    interpreter: "python"              # 解释器：python/bash/node等
    args:                              # 传递给脚本的参数
      - "--input"
      - "${TASK_DIR}"
      - "--output"
      - "output.txt"
    timeout: 300                       # 超时时间（秒）
    working_dir: "${TASK_DIR}"         # 工作目录
```

**脚本可用环境变量：**

- `TASK_DIR` - 任务目录
- `TASK_NAME` - 任务名称
- 所有工作流变量

---

### 7. command - 执行命令

直接执行Shell命令。

**参数：**

```yaml
- name: 打包
  type: command
  params:
    command: "zip -r ${novel_name}.zip ZhChapters/"
    timeout: 60
    working_dir: "${TASK_DIR}"
```

---

## 变量系统

### 定义变量

```yaml
variables:
  novel_name: "我的轻小说"
  author: "作者名"
  target_lang: "简体中文"
```

### 使用变量

在任意参数字段中使用 `${变量名}`：

```yaml
stages:
  - name: 合并
    type: merge
    params:
      output: "${novel_name}_合并版.md"
      header: |
        # ${novel_name}
        ## 作者：${author}
```

### 运行时传递变量

```bash
webmdai workflow run -v novel_name="另一部小说" -v author="其他作者"
```

### 预定义变量

| 变量             | 说明        | 设置者     |
| -------------- | --------- | ------- |
| `TASK_DIR`     | 当前任务目录路径  | fetch阶段 |
| `TASK_NAME`    | 当前任务名称    | fetch阶段 |
| `WORKFLOW_DIR` | 工作流文件所在目录 | 自动设置    |

---

## 实际案例

### 案例1：カクヨム轻小说完整翻译流程

```yaml
name: 轻小说翻译示例
description: 完整的爬取-清理-翻译-替换-合并流程示例
version: "1.0"

variables:
  novel_name: "示例轻小说"
  author: "示例作者"

stages:
  # 阶段1: 爬取章节
  - name: 爬取章节
    type: fetch
    params:
      source: taskfile
      taskfile: TASK.md
      reader: jina
      delay: 1.5
      timeout: 30

  # 阶段2: 清理内容（关键！减少Token消耗）
  - name: 清理原始内容
    type: clean
    params:
      file_pattern: "*.md"
      rules_file: "rules/kakuyomu.yaml"  # 加载清理规则
      min_content_length: 1000           # 过滤提取失败的
      output_suffix: "_cleaned"           # 输出为 *_cleaned_*.md

  # 阶段3: LLM翻译
  - name: 翻译章节
    type: llm
    params:
      file_pattern: "*_cleaned_*.md"     # 使用清理后的文件
      output_suffix: "_zh"
      model: default
      prompt_file: "prompts/novel_translate.txt"  # 自定义翻译提示词
      temperature: 0.65
      max_tokens: 4096
      batch_mode: separate

  # 阶段4: 人名统一替换
  - name: 人名替换
    type: replace
    on_error: skip  # 即使替换失败也继续
    params:
      file_pattern: "*_zh_*.md"
      backup: true
      replacements_file: "names/novel_characters.json"

  # 阶段5: 合并为全书
  - name: 合并全书
    type: merge
    params:
      file_pattern: "*_zh_*.md"
      sort_by: numeric
      output: "${novel_name}_全书合并版.md"
      header: |
        # ${novel_name}
        ## ${author}

        **翻译说明**：本翻译由AI自动生成，仅供个人学习使用。

      separator: "\n\n---\n\n"
      add_chapter_headers: true
      chapter_prefix: "第{num}話"
      collect_files: true
      collect_dir: "ZhChapters_Collected"
```

### 案例2：技术文章翻译

```yaml
name: 技术文章翻译
description: 爬取技术文档并翻译

stages:
  - name: 爬取文章
    type: fetch
    params:
      source: taskfile
      taskfile: articles.md
      delay: 2.0

  - name: 翻译
    type: llm
    params:
      file_pattern: "*.md"
      output_suffix: "_zh"
      prompt_template: translate
      custom_prompt: |
        你是一位技术文档翻译专家。
        将以下技术文章翻译成简体中文，保留所有代码块、命令行和专有名词不变。
        只输出翻译内容。

  - name: 合并
    type: merge
    params:
      file_pattern: "*_zh_*.md"
      output: "技术文档合集.md"
```

---

## 故障排查

### 问题1: fetch阶段失败

**现象：** 403错误或连接超时

**解决方案：**

```yaml
- name: 爬取
  type: fetch
  params:
    reader: jina
    delay: 3.0          # 增加延迟
    timeout: 60         # 增加超时
    # 或配置API Key
    # 在 ~/.webmdai/config.json 中设置 jina_api_key
```

### 问题2: LLM阶段Token超限

**现象：** API返回token超限错误

**解决方案：**

1. 添加clean阶段减少输入长度
2. 减少max_tokens参数
3. 使用batch_mode: separate分别处理

```yaml
- name: 清理
  type: clean
  params:
    file_pattern: "*.md"
    remove_patterns:
      - "!\\[Image.*?\\)"  # 移除图片链接

- name: 翻译
  type: llm
  params:
    max_tokens: 2048      # 减少token数
    batch_mode: separate  # 分别处理每个文件
```

### 问题3: replace阶段没有匹配

**现象：** 替换规则没有生效

**检查：**

1. file_pattern是否正确
2. 是否有隐藏字符（使用regex_replacements更灵活）

```yaml
- name: 替换
  type: replace
  params:
    file_pattern: "*_zh_*.md"
    regex_replacements:  # 使用正则更灵活
      "罗[特黛蒂德]": "洛特"
```

### 问题4: merge阶段顺序错误

**现象：** 章节顺序不正确

**解决方案：**

```yaml
- name: 合并
  type: merge
  params:
    sort_by: numeric      # 确保使用数字排序
    # 文件名应包含数字：TASK_1_xxx.md, TASK_2_xxx.md
```

---

## 最佳实践

1. **始终在LLM之前添加clean阶段** - 减少Token消耗和干扰
2. **使用prompt_file管理复杂提示词** - 便于版本控制
3. **使用变量提高可复用性** - 修改novel_name即可用于其他小说
4. **为不同网站创建专门的清理规则文件** - rules/kakuyomu.yaml, rules/ncode.yaml等
5. **启用backup** - replace阶段始终开启backup: true
6. **分阶段测试** - 使用enabled: false暂时禁用某些阶段进行测试
