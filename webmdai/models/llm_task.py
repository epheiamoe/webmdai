#!/usr/bin/env python3
"""
LLM任务数据模型
"""

from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class LLMTask:
    """LLM预设任务"""
    
    name: str
    description: str
    prompt_template: str
    output_suffix: str
    
    def format_prompt(self, content: str) -> str:
        """
        格式化提示词
        
        Args:
            content: 要处理的内容
            
        Returns:
            格式化后的提示词
        """
        return self.prompt_template.format(content=content)


# 预设任务定义
PRESET_TASKS = {
    "explain": LLMTask(
        name="explain",
        description="解释技术文档或代码",
        prompt_template="""请详细解释以下内容，包括：
1. 核心概念和原理
2. 关键步骤和流程
3. 重要术语说明
4. 实际应用场景

内容：
{content}

请用中文进行解释，保持结构清晰。""",
        output_suffix="explain"
    ),
    
    "translate": LLMTask(
        name="translate",
        description="翻译为中文",
        prompt_template="""请将以下内容翻译成中文，要求：
1. 保持原文的语气和风格
2. 专业术语准确
3. 语句通顺自然
4. 保留原文的格式和结构

内容：
{content}

请直接输出翻译结果。""",
        output_suffix="translate"
    ),
    
    "summarize": LLMTask(
        name="summarize",
        description="生成内容摘要",
        prompt_template="""请为以下内容生成摘要，要求：
1. 概括主要观点和结论
2. 保留关键信息
3. 简明扼要
4. 使用中文

内容：
{content}

请输出结构化的摘要。""",
        output_suffix="summarize"
    ),
    
    "abstract": LLMTask(
        name="abstract",
        description="提取关键要点",
        prompt_template="""请从以下内容中提取关键要点，要求：
1. 列出最重要的3-5个要点
2. 每个要点简洁明了
3. 使用 bullet points 格式
4. 使用中文

内容：
{content}

请输出关键要点列表。""",
        output_suffix="abstract"
    ),
}


def get_preset_task(name: str) -> Optional[LLMTask]:
    """
    获取预设任务
    
    Args:
        name: 任务名称
        
    Returns:
        LLMTask实例，如果不存在返回None
    """
    return PRESET_TASKS.get(name)


def list_preset_tasks() -> dict:
    """
    列出所有预设任务
    
    Returns:
        任务名称到描述的映射
    """
    return {name: task.description for name, task in PRESET_TASKS.items()}


def create_custom_task(prompt: str, output_suffix: str = "custom") -> LLMTask:
    """
    创建自定义任务
    
    Args:
        prompt: 自定义提示词模板（使用{content}作为内容占位符）
        output_suffix: 输出文件后缀
        
    Returns:
        LLMTask实例
    """
    return LLMTask(
        name="custom",
        description="自定义任务",
        prompt_template=prompt,
        output_suffix=output_suffix
    )
