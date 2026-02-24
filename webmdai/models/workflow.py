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


class WorkflowValidationError(Exception):
    """工作流配置验证错误"""
    pass


def validate_workflow_config(config_dict: dict) -> None:
    """验证工作流配置完整性
    
    Args:
        config_dict: 从YAML加载的配置字典
        
    Raises:
        WorkflowValidationError: 配置验证失败
    """
    if not isinstance(config_dict, dict):
        raise WorkflowValidationError("工作流配置必须是字典类型")
    
    # 验证必需字段
    required = ['name', 'stages']
    for field in required:
        if field not in config_dict:
            raise WorkflowValidationError(f"缺少必需字段: {field}")
    
    # 验证name字段
    if not config_dict['name'] or not isinstance(config_dict['name'], str):
        raise WorkflowValidationError("name 字段必须是非空字符串")
    
    # 验证stages字段
    stages = config_dict.get('stages', [])
    if not isinstance(stages, list):
        raise WorkflowValidationError("stages 必须是列表类型")
    
    if not stages:
        raise WorkflowValidationError("stages 列表不能为空，至少需要一个阶段")
    
    # 验证每个阶段
    valid_stage_types = {t.value for t in StageType}
    
    for i, stage in enumerate(stages, 1):
        if not isinstance(stage, dict):
            raise WorkflowValidationError(f"阶段 {i} 必须是字典类型")
        
        # 验证必需字段
        if 'type' not in stage:
            raise WorkflowValidationError(f"阶段 {i} 缺少 type 字段")
        if 'name' not in stage:
            raise WorkflowValidationError(f"阶段 {i} 缺少 name 字段")
        
        # 验证type字段
        stage_type = stage.get('type')
        if stage_type not in valid_stage_types:
            raise WorkflowValidationError(
                f"阶段 {i} 的 type '{stage_type}' 无效，有效值: {', '.join(valid_stage_types)}"
            )
        
        # 验证name字段
        if not stage.get('name') or not isinstance(stage['name'], str):
            raise WorkflowValidationError(f"阶段 {i} 的 name 必须是非空字符串")
        
        # 验证on_error字段
        on_error = stage.get('on_error', 'stop')
        if on_error not in ('stop', 'skip', 'ignore'):
            raise WorkflowValidationError(
                f"阶段 {i} 的 on_error '{on_error}' 无效，有效值: stop, skip, ignore"
            )
        
        # 验证params字段
        params = stage.get('params', {})
        if not isinstance(params, dict):
            raise WorkflowValidationError(f"阶段 {i} 的 params 必须是字典类型")
    
    # 验证settings字段（如果存在）
    settings = config_dict.get('settings', {})
    if not isinstance(settings, dict):
        raise WorkflowValidationError("settings 必须是字典类型")
    
    # 验证variables字段（如果存在）
    variables = config_dict.get('variables', {})
    if not isinstance(variables, dict):
        raise WorkflowValidationError("variables 必须是字典类型")
