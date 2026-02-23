#!/usr/bin/env python3
"""
LLM任务数据模型
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


@dataclass
class LLMTask:
    """LLM预设任务"""
    
    name: str
    description: str
    prompt_template: str
    output_suffix: str
    # LLM 参数（可选）
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    
    def format_prompt(self, content: str) -> str:
        """
        格式化提示词
        
        Args:
            content: 要处理的内容
            
        Returns:
            格式化后的提示词
        """
        return self.prompt_template.format(content=content)
    
    def get_llm_params(self) -> Dict[str, Any]:
        """
        获取非空的LLM参数
        
        Returns:
            参数字典
        """
        params = {}
        if self.temperature is not None:
            params['temperature'] = self.temperature
        if self.top_p is not None:
            params['top_p'] = self.top_p
        if self.max_tokens is not None:
            params['max_tokens'] = self.max_tokens
        if self.presence_penalty is not None:
            params['presence_penalty'] = self.presence_penalty
        if self.frequency_penalty is not None:
            params['frequency_penalty'] = self.frequency_penalty
        return params


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


# ========== 从 YAML 文件加载自定义提示词 ==========

def _load_custom_prompts_from_yaml() -> Dict[str, LLMTask]:
    """
    从 prompts/prompts.yaml 或 prompts/*.yaml 加载自定义提示词
    
    Returns:
        任务名称到LLMTask的映射
    """
    custom_tasks = {}
    prompts_dir = Path("prompts")
    
    if not prompts_dir.exists():
        return custom_tasks
    
    # 支持 prompts/prompts.yaml 或 prompts/*.yaml
    yaml_files = list(prompts_dir.glob("*.yaml")) + list(prompts_dir.glob("*.yml"))
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                continue
            
            for task_name, task_data in data.items():
                if not isinstance(task_data, dict):
                    continue
                
                # 构建 LLMTask
                task = LLMTask(
                    name=task_name,
                    description=task_data.get('description', f'自定义任务: {task_name}'),
                    prompt_template=task_data.get('prompt_template', '{content}'),
                    output_suffix=task_data.get('output_suffix', task_name),
                    temperature=task_data.get('temperature'),
                    top_p=task_data.get('top_p'),
                    max_tokens=task_data.get('max_tokens'),
                    presence_penalty=task_data.get('presence_penalty'),
                    frequency_penalty=task_data.get('frequency_penalty')
                )
                custom_tasks[task_name] = task
                
        except Exception as e:
            print(f"[Warning] 加载提示词文件 {yaml_file} 失败: {e}")
    
    return custom_tasks


def get_task(name: str) -> Optional[LLMTask]:
    """
    获取任务（优先从YAML文件加载，其次使用内置预设）
    
    Args:
        name: 任务名称
        
    Returns:
        LLMTask实例，如果不存在返回None
    """
    # 首先尝试从YAML加载（允许覆盖内置预设）
    custom_tasks = _load_custom_prompts_from_yaml()
    if name in custom_tasks:
        return custom_tasks[name]
    
    # 其次使用内置预设
    return PRESET_TASKS.get(name)


def list_all_tasks() -> Dict[str, str]:
    """
    列出所有可用任务（内置 + YAML自定义）
    
    Returns:
        任务名称到描述的映射
    """
    # 内置任务
    all_tasks = {name: task.description for name, task in PRESET_TASKS.items()}
    
    # 自定义任务（可能覆盖内置）
    custom_tasks = _load_custom_prompts_from_yaml()
    for name, task in custom_tasks.items():
        all_tasks[name] = task.description + " (自定义)"
    
    return all_tasks
