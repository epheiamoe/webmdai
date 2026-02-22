#!/usr/bin/env python3
"""
工作流模型定义
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from enum import Enum


class StageType(str, Enum):
    """工作流阶段类型"""
    FETCH = "fetch"           # 爬取网页
    CLEAN = "clean"           # 内容清理
    LLM = "llm"               # LLM处理（翻译/摘要等）
    REPLACE = "replace"       # 文本替换
    MERGE = "merge"           # 合并文件
    SCRIPT = "script"         # 运行自定义脚本
    COMMAND = "command"       # 运行shell命令
    FILTER = "filter"         # 文件过滤/选择


@dataclass
class StageConfig:
    """阶段配置"""
    name: str                           # 阶段名称
    type: StageType                     # 阶段类型
    enabled: bool = True                # 是否启用
    condition: Optional[str] = None     # 执行条件（可选）
    on_error: str = "stop"              # 错误处理: stop/skip/ignore
    params: Dict[str, Any] = field(default_factory=dict)  # 阶段参数
    
    
@dataclass
class WorkflowConfig:
    """工作流配置"""
    name: str                           # 工作流名称
    description: Optional[str] = None   # 工作流描述
    version: str = "1.0"                # 版本
    working_dir: Optional[str] = None   # 工作目录（默认当前目录）
    stages: List[StageConfig] = field(default_factory=list)  # 阶段列表
    variables: Dict[str, Any] = field(default_factory=dict)  # 全局变量
    
    # 全局设置
    settings: Dict[str, Any] = field(default_factory=lambda: {
        "backup": True,                 # 是否自动备份
        "parallel": False,              # 是否并行执行
        "max_workers": 4,               # 最大并行数
    })


# 内置工作流模板
WORKFLOW_TEMPLATES = {
    "translate-novel": {
        "name": "轻小说翻译工作流",
        "description": "爬取、翻译、替换、合并的完整流程",
        "stages": [
            {
                "name": "爬取章节",
                "type": "fetch",
                "params": {
                    "source": "taskfile",  # 或 urls
                    "taskfile": "TASK.md",
                    "reader": "jina",
                    "delay": 1.0,
                }
            },
            {
                "name": "翻译内容",
                "type": "llm",
                "params": {
                    "model": "default",  # 使用配置的默认模型
                    "prompt_template": "translate",  # 预设模板
                    "file_pattern": "*.md",
                    "output_suffix": "_zh",
                }
            },
            {
                "name": "人名替换",
                "type": "replace",
                "params": {
                    "file_pattern": "*_zh_*.md",
                    "replacements_file": "names.json",  # 或内联定义
                    "backup": True,
                }
            },
            {
                "name": "合并章节",
                "type": "merge",
                "params": {
                    "file_pattern": "*_zh_*.md",
                    "sort_by": "numeric",  # 数字排序
                    "output": "merged.md",
                    "header": "# 全书合并版\n",
                }
            }
        ]
    },
    
    "summarize-articles": {
        "name": "文章摘要工作流",
        "description": "爬取文章并生成摘要",
        "stages": [
            {
                "name": "爬取文章",
                "type": "fetch",
                "params": {
                    "source": "taskfile",
                    "taskfile": "articles.md",
                }
            },
            {
                "name": "生成摘要",
                "type": "llm",
                "params": {
                    "prompt_template": "summarize",
                    "file_pattern": "*.md",
                    "output_suffix": "_summary",
                }
            },
            {
                "name": "合并摘要",
                "type": "merge",
                "params": {
                    "file_pattern": "*_summary_*.md",
                    "output": "all_summaries.md",
                }
            }
        ]
    },
    
    "custom-pipeline": {
        "name": "自定义处理管道",
        "description": "空的模板供用户自定义",
        "stages": []
    }
}


def get_workflow_template(name: str) -> Optional[Dict[str, Any]]:
    """获取工作流模板"""
    return WORKFLOW_TEMPLATES.get(name)


def list_workflow_templates() -> Dict[str, str]:
    """列出所有工作流模板"""
    return {k: v["description"] for k, v in WORKFLOW_TEMPLATES.items()}
