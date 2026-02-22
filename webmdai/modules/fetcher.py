#!/usr/bin/env python3
"""
网页爬取模块 - 支持多种Reader服务
"""

import time
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Type

import requests

from ..models.fetch_result import FetchResult
from ..utils.validators import normalize_url


class BaseReader(ABC):
    """Reader基类"""
    
    name: str = "base"
    
    def __init__(self, timeout: int = 30, retry_times: int = 3):
        """
        初始化Reader
        
        Args:
            timeout: 请求超时时间（秒）
            retry_times: 重试次数
        """
        self.timeout = timeout
        self.retry_times = retry_times
    
    @abstractmethod
    def fetch(self, url: str) -> FetchResult:
        """
        爬取网页内容
        
        Args:
            url: 目标URL
            
        Returns:
            FetchResult实例
        """
        pass
    
    def _extract_title(self, content: str) -> Optional[str]:
        """
        从内容中提取标题
        
        Args:
            content: 内容
            
        Returns:
            标题，如果没有找到返回None
        """
        import re
        # 尝试匹配Markdown标题
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # 尝试匹配HTML标题
        match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # 返回内容的第一行（非空）
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        if lines:
            return lines[0][:100]  # 限制长度
        
        return None
    
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """
        发起HTTP请求（带重试）
        
        Args:
            url: 请求URL
            **kwargs: 额外请求参数
            
        Returns:
            Response对象
            
        Raises:
            requests.RequestException: 请求失败
        """
        last_error = None
        
        for attempt in range(self.retry_times):
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_error = e
                if attempt < self.retry_times - 1:
                    time.sleep(2 ** attempt)  # 指数退避
        
        raise last_error


class JinaReader(BaseReader):
    """Jina Reader实现"""
    
    name = "jina"
    BASE_URL = "https://r.jina.ai/http://"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        初始化Jina Reader
        
        Args:
            api_key: Jina AI API密钥（可选，用于提高速率限制）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.api_key = api_key
    
    def _normalize_url_for_jina(self, url: str) -> str:
        """
        为Jina Reader规范化URL
        Jina期望 http://domain 格式，不带 https://
        
        Args:
            url: 原始URL
            
        Returns:
            规范化后的URL (去掉协议前缀)
        """
        url = url.strip()
        # 去掉协议前缀
        if url.startswith('https://'):
            url = url[8:]  # 去掉 https://
        elif url.startswith('http://'):
            url = url[7:]  # 去掉 http://
        return url
    
    def fetch(self, url: str) -> FetchResult:
        """
        使用Jina Reader爬取网页
        
        Args:
            url: 目标URL
            
        Returns:
            FetchResult实例
        """
        # 保存原始 URL 用于返回结果
        original_url = normalize_url(url)
        # 为 Jina 规范化 URL（去掉协议前缀）
        jina_url = self._normalize_url_for_jina(url)
        fetch_url = f"{self.BASE_URL}{jina_url}"
        
        try:
            # 构造请求头
            # 注意：Jina Reader 对复杂的浏览器 User-Agent 可能返回 403
            # 使用简单的 headers 即可
            headers = {
                "Accept": "text/html,*/*",
            }
            
            # 如果有API Key，添加到请求头
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = self._make_request(fetch_url, headers=headers)
            content = response.text
            title = self._extract_title(content)
            
            return FetchResult(
                url=original_url,
                content=content,
                title=title
            )
        except Exception as e:
            return FetchResult.from_error(url, str(e))


class FirecrawlReader(BaseReader):
    """Firecrawl Reader实现（需要API密钥）"""
    
    name = "firecrawl"
    BASE_URL = "https://api.firecrawl.dev/v1/scrape"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        初始化Firecrawl Reader
        
        Args:
            api_key: Firecrawl API密钥
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.api_key = api_key
    
    def fetch(self, url: str) -> FetchResult:
        """
        使用Firecrawl爬取网页
        
        Args:
            url: 目标URL
            
        Returns:
            FetchResult实例
        """
        url = normalize_url(url)
        
        if not self.api_key:
            return FetchResult.from_error(url, "Firecrawl需要API密钥")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "url": url,
                "formats": ["markdown"]
            }
            
            response = self._make_request(
                self.BASE_URL,
                headers=headers,
                json=data,
                method='POST'
            )
            
            result = response.json()
            
            if result.get("success"):
                data = result.get("data", {})
                content = data.get("markdown", "")
                title = data.get("metadata", {}).get("title")
                
                return FetchResult(
                    url=url,
                    content=content,
                    title=title
                )
            else:
                return FetchResult.from_error(url, result.get("error", "未知错误"))
                
        except Exception as e:
            return FetchResult.from_error(url, str(e))
    
    def _make_request(self, url: str, **kwargs):
        """重写以支持POST请求"""
        method = kwargs.pop('method', 'GET')
        
        for attempt in range(self.retry_times):
            try:
                if method == 'POST':
                    response = requests.post(url, timeout=self.timeout, **kwargs)
                else:
                    response = requests.get(url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt < self.retry_times - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise


class DirectReader(BaseReader):
    """直接爬取（使用requests和BeautifulSoup）"""
    
    name = "direct"
    
    def fetch(self, url: str) -> FetchResult:
        """
        直接爬取网页
        
        Args:
            url: 目标URL
            
        Returns:
            FetchResult实例
        """
        url = normalize_url(url)
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
            }
            
            response = self._make_request(url, headers=headers)
            
            # 使用BeautifulSoup解析
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取标题
            title = None
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # 提取主要内容
            # 移除脚本和样式
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # 获取文本
            text = soup.get_text()
            
            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = '\n'.join(chunk for chunk in chunks if chunk)
            
            return FetchResult(
                url=url,
                content=content,
                title=title
            )
            
        except Exception as e:
            return FetchResult.from_error(url, str(e))


# Reader注册表
READER_REGISTRY: Dict[str, Type[BaseReader]] = {
    "jina": JinaReader,
    "firecrawl": FirecrawlReader,
    "direct": DirectReader,
}


def get_reader(name: str, **kwargs) -> Optional[BaseReader]:
    """
    获取Reader实例
    
    Args:
        name: Reader名称
        **kwargs: 额外参数
        
    Returns:
        Reader实例，如果不存在返回None
    """
    reader_class = READER_REGISTRY.get(name)
    if reader_class:
        return reader_class(**kwargs)
    return None


def list_readers() -> Dict[str, str]:
    """
    列出所有可用的Reader
    
    Returns:
        Reader名称到描述的映射
    """
    return {
        "jina": "Jina Reader (免费，可选API密钥提高速率限制)",
        "firecrawl": "Firecrawl (需要API密钥，功能更强)",
        "direct": "直接爬取 (使用requests+BeautifulSoup)",
    }


def register_reader(name: str, reader_class: Type[BaseReader]):
    """
    注册新的Reader
    
    Args:
        name: Reader名称
        reader_class: Reader类
    """
    READER_REGISTRY[name] = reader_class


class Fetcher:
    """网页爬取器"""
    
    def __init__(self, reader_name: str = "jina", delay: float = 1.0, **reader_kwargs):
        """
        初始化爬取器
        
        Args:
            reader_name: Reader名称
            delay: 爬取间隔（秒），默认1秒
            **reader_kwargs: Reader参数
        """
        self.reader = get_reader(reader_name, **reader_kwargs)
        if not self.reader:
            raise ValueError(f"未知的Reader: {reader_name}")
        self.delay = delay
    
    def fetch(self, url: str) -> FetchResult:
        """
        爬取单个网页
        
        Args:
            url: 目标URL
            
        Returns:
            FetchResult实例
        """
        return self.reader.fetch(url)
    
    def fetch_multiple(self, urls: List[str]) -> List[FetchResult]:
        """
        爬取多个网页
        
        Args:
            urls: URL列表
            
        Returns:
            FetchResult列表
        """
        results = []
        for i, url in enumerate(urls, 1):
            print(f"正在爬取 ({i}/{len(urls)}): {url}")
            result = self.fetch(url)
            results.append(result)
            
            if result.success:
                print(f"  [OK] 成功")
            else:
                print(f"  [FAIL] 失败: {result.error_message}")
            
            # 添加延迟，避免请求过快（最后一个URL不需要等待）
            if i < len(urls) and self.delay > 0:
                time.sleep(self.delay)
        
        return results
