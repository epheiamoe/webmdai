# webmdai 快速开始指南

## 安装

```bash
# 从源码安装
cd webmdai
pip install -e .
```

## 5分钟上手

### 第1步：配置LLM模型

```bash
# 添加你的OpenAI API密钥
webmdai model add --name gpt4 --endpoint https://api.openai.com/v1 --model gpt-4 --key sk-your-key

# 设为默认
webmdai model set-default gpt4

# 验证
webmdai model list
```

### 第2步：爬取网页

```bash
# 交互模式 - 按提示输入
webmdai fetch interactive

# 或批量模式
webmdai fetch batch -w "https://example.com/article" -n myarticle -st
```

### 第3步：处理文本

```bash
# 进入爬取结果目录
cd myarticle

# 删除广告等内容
webmdai deal batch --re -f "\\[广告\\].*?\\[/广告\\]" -d .

# 或交互模式
webmdai deal interactive
```

### 第4步：LLM处理

```bash
# 翻译所有文章
webmdai llm batch -d . --all -t translate

# 或生成摘要
webmdai llm batch -d . --all -t summarize
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `webmdai model list` | 列出模型 |
| `webmdai model add --name X --endpoint Y --model Z --key K` | 添加模型 |
| `webmdai fetch batch -w "url1,url2" -n taskname` | 批量爬取 |
| `webmdai deal batch --text -f "old" -r "new" -d ./dir` | 文本替换 |
| `webmdai deal batch --re -f "pattern" -r "replace" -d ./dir` | 正则替换 |
| `webmdai llm batch -d ./dir --all -t translate` | 批量翻译 |
| `webmdai llm batch -d ./dir --separate -t summarize` | 分别摘要 |

## 预设任务

- `explain` - 解释技术文档
- `translate` - 翻译为中文
- `summarize` - 生成摘要
- `abstract` - 提取要点

## 获取帮助

```bash
webmdai --help
webmdai fetch --help
webmdai deal --help
webmdai llm --help
webmdai model --help
```

## 配置文件

位置: `~/.webmdai/config.json`

支持环境变量: `$ENV_VAR_NAME`

## 下一步

- 查看 [README.md](README.md) 获取完整文档
- 查看 [examples.md](examples.md) 获取更多示例
- 查看 [DEVELOPMENT.md](DEVELOPMENT.md) 了解开发细节
