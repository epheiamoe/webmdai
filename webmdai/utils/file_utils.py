#!/usr/bin/env python3
"""
文件操作工具模块
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制长度
    filename = filename[:100]
    # 移除首尾空格和点
    filename = filename.strip('. ')
    return filename or 'untitled'


def create_task_directory(base_path: Path, task_name: str) -> Path:
    """
    创建任务目录
    
    Args:
        base_path: 基础路径
        task_name: 任务名称
        
    Returns:
        创建的目录路径
    """
    task_dir = base_path / sanitize_filename(task_name)
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def generate_metadata(url: str, title: Optional[str] = None) -> str:
    """
    生成Markdown元数据头
    
    Args:
        url: 来源URL
        title: 页面标题
        
    Returns:
        元数据字符串
    """
    metadata = [
        "---",
        f"fetch_time: {datetime.now().isoformat()}",
        f"source_url: {url}",
    ]
    if title:
        metadata.append(f"title: {title}")
    metadata.append("---")
    return "\n".join(metadata)


def find_markdown_files(directory: Path, recursive: bool = True) -> List[Path]:
    """
    查找目录中的Markdown文件
    
    Args:
        directory: 搜索目录
        recursive: 是否递归搜索
        
    Returns:
        Markdown文件路径列表
    """
    pattern = "**/*.md" if recursive else "*.md"
    return list(directory.glob(pattern))


def read_file_content(filepath: Path, encoding: str = 'utf-8') -> str:
    """
    读取文件内容
    
    Args:
        filepath: 文件路径
        encoding: 文件编码
        
    Returns:
        文件内容
        
    Raises:
        FileNotFoundError: 文件不存在
        IOError: 读取失败
    """
    with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
        return f.read()


def write_file_content(filepath: Path, content: str, encoding: str = 'utf-8'):
    """
    写入文件内容
    
    Args:
        filepath: 文件路径
        content: 文件内容
        encoding: 文件编码
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding=encoding) as f:
        f.write(content)


def merge_markdown_files(files: List[Path], output_path: Path, separator: str = "\n\n---\n\n"):
    """
    合并多个Markdown文件
    
    Args:
        files: 要合并的文件列表
        output_path: 输出文件路径
        separator: 文件分隔符
    """
    contents = []
    for file in files:
        try:
            content = read_file_content(file)
            contents.append(content)
        except Exception as e:
            print(f"警告: 读取文件 {file} 失败: {e}")
    
    merged_content = separator.join(contents)
    write_file_content(output_path, merged_content)


def extract_title_from_markdown(content: str) -> Optional[str]:
    """
    从Markdown内容中提取标题
    
    Args:
        content: Markdown内容
        
    Returns:
        标题，如果没有找到返回None
    """
    # 匹配一级标题
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    # 匹配YAML frontmatter中的title
    match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    
    return None


def get_unique_filename(directory: Path, filename: str) -> Path:
    """
    获取唯一的文件名（如果存在则添加序号）
    
    Args:
        directory: 目录
        filename: 原始文件名
        
    Returns:
        唯一的文件路径
    """
    filepath = directory / filename
    if not filepath.exists():
        return filepath
    
    stem = filepath.stem
    suffix = filepath.suffix
    counter = 1
    
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_filepath = directory / new_filename
        if not new_filepath.exists():
            return new_filepath
        counter += 1


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def count_tokens_approx(text: str) -> int:
    """
    估算文本的token数量（粗略估计）
    
    Args:
        text: 文本内容
        
    Returns:
        估算的token数
    """
    # 简单的估算：英文单词 + 中文字符
    # 实际应用中可能需要更精确的tokenizer
    import re
    
    # 中文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 英文单词
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    # 数字和符号
    others = len(re.findall(r'\d+|[!"#$%&\'()*+,-./:;<=>?@[\\\]^_`{|}~]', text))
    
    # 粗略估算：中文字符1:1，英文单词1:1.3，其他1:1
    return int(chinese_chars + english_words * 1.3 + others * 0.5)


def extract_urls_from_markdown(content: str) -> List[str]:
    """
    从Markdown内容中提取所有URL链接
    
    支持的格式：
    - 行内链接: [text](url)
    - 裸URL: <url> 或 直接 http://...
    - 引用链接: [text]: url
    
    Args:
        content: Markdown内容
        
    Returns:
        URL列表（去重，保持原顺序）
    """
    urls = []
    
    # 匹配行内链接 [text](url)
    inline_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    for _, url in inline_links:
        # 过滤掉锚点链接和邮件链接
        if url.startswith('http://') or url.startswith('https://'):
            urls.append(url)
    
    # 匹配裸URL <http://...> 或 https://...
    # 先匹配尖括号包裹的URL
    bracket_urls = re.findall(r'<(https?://[^>]+)>', content)
    urls.extend(bracket_urls)
    
    # 匹配引用链接 [text]: url
    ref_links = re.findall(r'^\[[^\]]+\]:\s*(https?://\S+)', content, re.MULTILINE)
    urls.extend(ref_links)
    
    # 去重但保持顺序
    seen = set()
    unique_urls = []
    for url in urls:
        # 去除URL中的markdown标记和查询参数后的锚点
        clean_url = url.split(' ')[0].rstrip(').,;!?')
        if clean_url not in seen:
            seen.add(clean_url)
            unique_urls.append(clean_url)
    
    return unique_urls


def parse_task_markdown(filepath: Path) -> Tuple[str, List[str]]:
    """
    解析任务Markdown文件，提取任务名和URL列表
    
    文件格式示例：
    # 任务名
    
    - [链接描述](https://example.com)
    - [链接描述2](https://example2.com)
    
    Args:
        filepath: Markdown文件路径
        
    Returns:
        (任务名, URL列表)
        
    Raises:
        FileNotFoundError: 文件不存在
    """
    content = read_file_content(filepath)
    
    # 提取任务名（从一级标题）
    task_name = None
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        task_name = title_match.group(1).strip()
    
    # 如果没有标题，使用文件名（不含扩展名）
    if not task_name:
        task_name = filepath.stem
    
    # 提取URL
    urls = extract_urls_from_markdown(content)
    
    return task_name, urls
