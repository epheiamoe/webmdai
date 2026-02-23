#!/usr/bin/env python3
"""
LLM处理模块 - 调用兼容OpenAI格式的API
"""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Iterator

import requests

from ..models.llm_task import LLMTask, get_preset_task, create_custom_task
from ..utils.file_utils import (
    read_file_content, write_file_content, 
    find_markdown_files, count_tokens_approx
)


class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        timeout: int = 120,
        max_retries: int = 3
    ):
        """
        初始化LLM客户端
        
        Args:
            endpoint: API端点
            api_key: API密钥
            model: 模型名称
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Returns:
            响应内容
        """
        pass
    
    def process_content(
        self,
        content: str,
        task: LLMTask,
        **kwargs
    ) -> str:
        """
        处理内容
        
        Args:
            content: 要处理的内容
            task: LLM任务
            **kwargs: 额外参数（会覆盖task中的参数）
            
        Returns:
            处理结果
        """
        prompt = task.format_prompt(content)
        messages = [{"role": "user", "content": prompt}]
        
        # 合并task的参数（kwargs优先级更高）
        task_params = task.get_llm_params()
        task_params.update(kwargs)
        
        return self.chat_completion(messages, **task_params)


class OpenAICompatibleClient(BaseLLMClient):
    """兼容OpenAI格式的客户端"""
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            **kwargs: 额外参数
            
        Returns:
            响应内容
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        # 合并额外参数
        data.update(kwargs)
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.endpoint}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.timeout,
                    stream=stream
                )
                response.raise_for_status()
                
                if stream:
                    return self._handle_stream(response)
                else:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                    
            except requests.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
            except (KeyError, IndexError) as e:
                raise Exception(f"API响应格式错误: {e}")
        
        raise Exception(f"API请求失败: {last_error}")
    
    def _handle_stream(self, response) -> str:
        """处理流式响应"""
        content_parts = []
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"]
                        if "content" in delta:
                            content_parts.append(delta["content"])
                    except (json.JSONDecodeError, KeyError):
                        pass
        return ''.join(content_parts)


class LLMHandler:
    """LLM处理器"""
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        output_dir: Optional[Path] = None,
        client_class = OpenAICompatibleClient
    ):
        """
        初始化LLM处理器
        
        Args:
            endpoint: API端点
            api_key: API密钥
            model: 模型名称
            output_dir: 输出目录
            client_class: LLM客户端类
        """
        self.client = client_class(
            endpoint=endpoint,
            api_key=api_key,
            model=model
        )
        self.output_dir = output_dir
        self.model = model
    
    def process_file(
        self,
        file_path: Path,
        task: LLMTask,
        output_path: Optional[Path] = None
    ) -> str:
        """
        处理单个文件
        
        Args:
            file_path: 输入文件路径
            task: LLM任务
            output_path: 输出文件路径
            
        Returns:
            处理结果
        """
        # 读取内容
        content = read_file_content(file_path)
        
        # 估算token数
        tokens = count_tokens_approx(content)
        print(f"文件: {file_path.name}")
        print(f"估算token数: ~{tokens}")
        
        # 调用LLM
        print("正在处理...")
        result = self.client.process_content(content, task)
        
        # 保存结果
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_file_content(output_path, result)
            print(f"结果已保存: {output_path}")
        
        return result
    
    def process_files_separate(
        self,
        directory: Path,
        task: LLMTask,
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """
        分别处理多个文件
        
        Args:
            directory: 输入目录
            task: LLM任务
            output_dir: 输出目录
            
        Returns:
            输出文件路径列表
        """
        if output_dir is None:
            output_dir = directory / f"llm_{task.output_suffix}"
        
        files = find_markdown_files(directory)
        output_files = []
        
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}] 处理: {file_path.name}")
            
            # 生成输出文件名
            output_name = f"{file_path.stem}_{task.output_suffix}.md"
            output_path = output_dir / output_name
            
            try:
                self.process_file(file_path, task, output_path)
                output_files.append(output_path)
            except Exception as e:
                print(f"处理失败: {e}")
        
        return output_files
    
    def process_files_together(
        self,
        directory: Path,
        task: LLMTask,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        合并处理多个文件
        
        Args:
            directory: 输入目录
            task: LLM任务
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        files = find_markdown_files(directory)
        
        if not files:
            raise ValueError("目录中没有Markdown文件")
        
        # 合并内容
        contents = []
        for file_path in files:
            content = read_file_content(file_path)
            contents.append(f"## 文件: {file_path.name}\n\n{content}")
        
        merged_content = "\n\n---\n\n".join(contents)
        
        # 估算token数
        tokens = count_tokens_approx(merged_content)
        print(f"合并文件数: {len(files)}")
        print(f"估算token数: ~{tokens}")
        
        # 调用LLM
        print("正在处理...")
        result = self.client.process_content(merged_content, task)
        
        # 保存结果
        if output_path is None:
            output_path = directory / f"merged_{task.output_suffix}.md"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_file_content(output_path, result)
        print(f"结果已保存: {output_path}")
        
        return output_path
    
    def process_with_custom_prompt(
        self,
        content: str,
        prompt: str,
        **kwargs
    ) -> str:
        """
        使用自定义提示词处理内容
        
        Args:
            content: 要处理的内容
            prompt: 自定义提示词（使用{content}作为占位符）
            **kwargs: 额外参数
            
        Returns:
            处理结果
        """
        task = create_custom_task(prompt)
        return self.client.process_content(content, task, **kwargs)


def create_llm_handler_from_config(
    model_config: Dict[str, str],
    output_dir: Optional[Path] = None
) -> LLMHandler:
    """
    从配置创建LLM处理器
    
    Args:
        model_config: 模型配置
        output_dir: 输出目录
        
    Returns:
        LLMHandler实例
    """
    return LLMHandler(
        endpoint=model_config["endpoint"],
        api_key=model_config["key"],
        model=model_config["model"],
        output_dir=output_dir
    )


# LLM客户端注册表
LLM_CLIENT_REGISTRY = {
    "openai": OpenAICompatibleClient,
}


def register_llm_client(name: str, client_class: type):
    """
    注册LLM客户端
    
    Args:
        name: 客户端名称
        client_class: 客户端类
    """
    LLM_CLIENT_REGISTRY[name] = client_class
