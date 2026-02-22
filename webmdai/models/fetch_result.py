#!/usr/bin/env python3
"""
爬取结果数据模型
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FetchResult:
    """网页爬取结果"""
    
    url: str
    content: str
    title: Optional[str] = None
    fetch_time: datetime = None
    success: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.fetch_time is None:
            self.fetch_time = datetime.now()
    
    @property
    def markdown(self) -> str:
        """
        生成Markdown格式的内容（包含元数据）
        
        Returns:
            Markdown字符串
        """
        lines = [
            "---",
            f"fetch_time: {self.fetch_time.isoformat()}",
            f"source_url: {self.url}",
        ]
        
        if self.title:
            lines.append(f"title: {self.title}")
        
        lines.extend([
            "---",
            "",
            self.content
        ])
        
        return "\n".join(lines)
    
    @classmethod
    def from_error(cls, url: str, error_message: str) -> 'FetchResult':
        """
        从错误创建结果对象
        
        Args:
            url: 请求URL
            error_message: 错误信息
            
        Returns:
            FetchResult实例
        """
        return cls(
            url=url,
            content="",
            success=False,
            error_message=error_message
        )
