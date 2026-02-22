#!/usr/bin/env python3
"""
输入验证工具模块
"""

import re
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    验证URL格式
    
    Args:
        url: 要验证的URL
        
    Returns:
        (是否有效, 错误信息)
    """
    if not url:
        return False, "URL不能为空"
    
    # 检查是否有协议前缀
    has_protocol = url.startswith(('http://', 'https://', 'ftp://', 'file://'))
    
    # 如果已有协议但不是http/https，返回错误
    if has_protocol and not url.startswith(('http://', 'https://')):
        return False, "仅支持HTTP/HTTPS协议"
    
    # 添加协议前缀（如果没有）
    if not has_protocol:
        url = 'https://' + url
    
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "URL格式无效"
        
        if result.scheme not in ['http', 'https']:
            return False, "仅支持HTTP/HTTPS协议"
        
        return True, None
    except Exception as e:
        return False, f"URL解析错误: {e}"


def normalize_url(url: str) -> str:
    """
    规范化URL
    
    Args:
        url: 原始URL
        
    Returns:
        规范化后的URL
    """
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url


def validate_directory(path: str) -> Tuple[bool, Optional[str]]:
    """
    验证目录路径
    
    Args:
        path: 目录路径
        
    Returns:
        (是否有效, 错误信息)
    """
    if not path:
        return True, None  # 空路径表示使用当前目录
    
    try:
        dir_path = Path(path)
        if dir_path.exists():
            if not dir_path.is_dir():
                return False, f"'{path}' 不是目录"
            if not os.access(dir_path, os.R_OK | os.W_OK):
                return False, f"没有 '{path}' 的读写权限"
        else:
            # 目录不存在，检查父目录是否可写
            parent = dir_path.parent
            if parent.exists() and not os.access(parent, os.W_OK):
                return False, f"无法在 '{parent}' 创建目录"
        
        return True, None
    except Exception as e:
        return False, f"路径验证错误: {e}"


def validate_task_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    验证任务名称
    
    Args:
        name: 任务名称
        
    Returns:
        (是否有效, 错误信息)
    """
    if not name:
        return False, "任务名称不能为空"
    
    if len(name) > 100:
        return False, "任务名称不能超过100个字符"
    
    # 检查非法字符
    if re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
        return False, "任务名称包含非法字符"
    
    return True, None


def validate_regex_pattern(pattern: str) -> Tuple[bool, Optional[str]]:
    """
    验证正则表达式
    
    Args:
        pattern: 正则表达式
        
    Returns:
        (是否有效, 错误信息)
    """
    if not pattern:
        return False, "正则表达式不能为空"
    
    try:
        re.compile(pattern)
        return True, None
    except re.error as e:
        return False, f"正则表达式错误: {e}"


def validate_model_config(endpoint: str, model: str, key: str) -> Tuple[bool, Optional[str]]:
    """
    验证模型配置
    
    Args:
        endpoint: API端点
        model: 模型名称
        key: API密钥
        
    Returns:
        (是否有效, 错误信息)
    """
    if not endpoint:
        return False, "API端点不能为空"
    
    if not model:
        return False, "模型名称不能为空"
    
    if not key:
        return False, "API密钥不能为空"
    
    # 验证端点URL
    is_valid, error = validate_url(endpoint)
    if not is_valid:
        return False, f"API端点无效: {error}"
    
    return True, None


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    清理用户输入
    
    Args:
        text: 原始输入
        max_length: 最大长度
        
    Returns:
        清理后的输入
    """
    # 移除控制字符
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    
    # 限制长度
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def confirm_action(message: str, default: bool = False) -> bool:
    """
    请求用户确认
    
    Args:
        message: 确认消息
        default: 默认选项
        
    Returns:
        用户是否确认
    """
    default_str = "Y/n" if default else "y/N"
    prompt = f"{message} [{default_str}]: "
    
    try:
        response = input(prompt).strip().lower()
        if not response:
            return default
        return response in ['y', 'yes']
    except (EOFError, KeyboardInterrupt):
        return False


def parse_url_list(urls_str: str) -> list:
    """
    解析逗号分隔的URL列表
    
    Args:
        urls_str: URL字符串
        
    Returns:
        URL列表
    """
    if not urls_str:
        return []
    
    urls = []
    for url in urls_str.split(','):
        url = url.strip()
        if url:
            url = normalize_url(url)
            urls.append(url)
    
    return urls


import os
