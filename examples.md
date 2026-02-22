# webmdai 使用示例

## 1. 模型管理

### 添加模型
```bash
# 添加OpenAI模型
webmdai model add --name gpt4 --endpoint https://api.openai.com/v1 --model gpt-4 --key your-api-key

# 添加本地模型
webmdai model add --name local --endpoint http://localhost:8000/v1 --model llama2 --key dummy-key
```

### 列出模型
```bash
webmdai model list
```

### 设置默认模型
```bash
webmdai model set-default gpt4
```

## 2. 网页爬取

### 交互模式
```bash
webmdai fetch interactive
```

### 批量模式
```bash
# 爬取多个网页并保存为单独文件
webmdai fetch batch -w "https://example.com,https://example2.com" -n mytask -s

# 爬取并合并为一个文件
webmdai fetch batch -w "https://example.com" -n mytask -t

# 同时生成单独文件和合并文件
webmdai fetch batch -w "https://a.com,https://b.com" -n mytask -st

# 使用不同的Reader
webmdai fetch batch -w "https://example.com" -n mytask -r direct
```

## 3. 文本处理

### 交互模式
```bash
webmdai deal interactive
```

### 批量文本替换
```bash
# 普通文本替换
webmdai deal batch --text -f "old_text" -r "new_text" -d ./docs

# 正则表达式替换
webmdai deal batch --re -f "\\d+" -r "[NUMBER]" -d ./docs

# 删除内容（替换为空）
webmdai deal batch --text -f " unwanted_text " -d ./docs

# 预览模式（不实际执行）
webmdai deal batch --text -f "test" -r "replaced" -d ./docs --preview

# 禁用Git管理
webmdai deal batch --text -f "old" -r "new" -d ./docs --no-git
```

## 4. LLM处理

### 交互模式
```bash
webmdai llm interactive
```

### 批量翻译
```bash
# 合并处理所有文件
webmdai llm batch -d ./articles --all -t translate -m gpt4

# 分别处理每个文件
webmdai llm batch -d ./articles --separate -t translate -m gpt4
```

### 批量摘要
```bash
webmdai llm batch -d ./docs --all -t summarize -m gpt4
```

### 自定义提示词
```bash
webmdai llm batch -d ./articles --all -p "请总结以下内容的主要观点：{content}" -m gpt4
```

## 5. 完整工作流程示例

### 场景1：收集资料并翻译
```bash
# 1. 爬取网页
webmdai fetch batch -w "https://blog.example.com/article1,https://blog.example.com/article2" -n articles -st

# 2. 翻译内容
webmdai llm batch -d ./articles --separate -t translate -m gpt4 -o ./articles/translated
```

### 场景2：整理文档并生成摘要
```bash
# 1. 处理文档（删除广告等无用内容）
webmdai deal batch --re -f "\\[Advertisement\\].*?\\[/Advertisement\\]" -d ./docs

# 2. 生成摘要
webmdai llm batch -d ./docs --all -t summarize -m gpt4 -o ./docs/summary
```

### 场景3：技术文档解释
```bash
# 解释代码文档
webmdai llm batch -d ./code_docs --separate -t explain -m gpt4 -o ./code_docs/explained
```

## 6. 配置文件示例

`~/.webmdai/config.json`:
```json
{
  "default_model": "gpt4",
  "models": {
    "gpt4": {
      "endpoint": "https://api.openai.com/v1",
      "model": "gpt-4",
      "key": "$OPENAI_API_KEY"
    },
    "gpt3": {
      "endpoint": "https://api.openai.com/v1",
      "model": "gpt-3.5-turbo",
      "key": "$OPENAI_API_KEY"
    },
    "local": {
      "endpoint": "http://localhost:8000/v1",
      "model": "llama2",
      "key": "dummy-key"
    }
  },
  "fetch": {
    "default_reader": "jina",
    "timeout": 30,
    "retry_times": 3
  },
  "llm": {
    "default_output_dir": "llm_output",
    "max_tokens": 4000,
    "temperature": 0.7
  }
}
```

## 7. 环境变量使用

在配置文件中使用环境变量:
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

设置环境变量:
```bash
export OPENAI_API_KEY="sk-..."
```

## 8. 交互模式命令

在交互模式下可用命令:
- `/start` - 结束URL列表输入
- `/exit` - 退出程序
- `/help` - 显示帮助信息
