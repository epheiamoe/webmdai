# webmdai 开发文档

## 项目结构

```
webmdai/
├── cli.py              # 命令行入口（Click框架）
├── config.py           # 配置管理（JSON配置文件）
├── models/             # 数据模型
│   ├── fetch_result.py # 爬取结果模型
│   └── llm_task.py     # LLM任务模型
├── modules/            # 功能模块
│   ├── fetcher.py      # 爬取模块（Reader基类）
│   ├── processor.py    # 文本处理模块
│   ├── llm_handler.py  # LLM处理模块
│   └── git_handler.py  # Git自动管理
├── utils/              # 工具函数
│   ├── file_utils.py   # 文件操作
│   └── validators.py   # 输入验证
└── tests/              # 单元测试
```

## 核心设计

### 1. 配置管理 (config.py)

- 单例模式管理全局配置
- 配置文件位置: `~/.webmdai/config.json`
- 支持环境变量引用: `$ENV_VAR`

```python
from webmdai.config import get_config

config = get_config()
config.add_model("gpt4", "https://api.openai.com/v1", "gpt-4", "key")
model = config.get_model("gpt4")
```

### 2. 爬取模块 (fetcher.py)

- Reader基类支持扩展
- 内置Reader: JinaReader, DirectReader, FirecrawlReader

```python
from webmdai.modules.fetcher import BaseReader, register_reader

class MyReader(BaseReader):
    name = "myreader"
    
    def fetch(self, url: str) -> FetchResult:
        # 实现爬取逻辑
        pass

register_reader("myreader", MyReader)
```

### 3. 文本处理模块 (processor.py)

- 支持普通文本和正则表达式模式
- 提供预览功能
- 批量处理Markdown文件

### 4. Git管理 (git_handler.py)

- 自动检查/初始化Git仓库
- 操作前自动提交备份
- 支持回滚

### 5. LLM处理 (llm_handler.py)

- 兼容OpenAI API格式
- 支持预设任务和自定义提示词
- 分批或合并处理模式

## 扩展开发

### 添加新的Reader

```python
from webmdai.modules.fetcher import BaseReader, FetchResult, register_reader

class CustomReader(BaseReader):
    name = "custom"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自定义初始化
    
    def fetch(self, url: str) -> FetchResult:
        try:
            # 爬取逻辑
            content = self._fetch_content(url)
            title = self._extract_title(content)
            
            return FetchResult(
                url=url,
                content=content,
                title=title
            )
        except Exception as e:
            return FetchResult.from_error(url, str(e))

register_reader("custom", CustomReader)
```

### 添加新的LLM客户端

```python
from webmdai.modules.llm_handler import BaseLLMClient, register_llm_client

class CustomLLMClient(BaseLLMClient):
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        # 实现API调用
        response = self._call_api(messages, **kwargs)
        return response

register_llm_client("custom", CustomLLMClient)
```

### 添加新的预设任务

```python
from webmdai.models.llm_task import LLMTask, PRESET_TASKS

PRESET_TASKS["custom"] = LLMTask(
    name="custom",
    description="自定义任务",
    prompt_template="请处理以下内容：\n{content}",
    output_suffix="custom"
)
```

## 测试

```bash
# 运行所有测试
python -m pytest webmdai/tests/ -v

# 运行特定测试
python -m pytest webmdai/tests/test_config.py -v

# 生成覆盖率报告
python -m pytest --cov=webmdai webmdai/tests/ --cov-report=html
```

## 代码规范

- 遵循PEP 8
- 使用类型注解
- 编写docstring
- 保持测试覆盖率>80%

## 发布流程

1. 更新版本号 (`__init__.py`, `setup.py`)
2. 更新CHANGELOG
3. 运行测试确保通过
4. 构建分发包: `python setup.py sdist bdist_wheel`
5. 上传到PyPI: `twine upload dist/*`
