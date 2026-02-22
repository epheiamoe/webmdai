#!/usr/bin/env python3
"""
测试任务Markdown解析功能
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from webmdai.utils.file_utils import (
    extract_urls_from_markdown,
    parse_task_markdown,
    write_file_content,
)


class TestExtractUrlsFromMarkdown(unittest.TestCase):
    """测试从Markdown提取URL"""
    
    def test_inline_links(self):
        """测试行内链接 [text](url)"""
        content = """
# 标题

一些介绍文字。

- [Example](https://example.com)
- [GitHub](https://github.com)
- [相对路径](./local/path)  # 不应该被提取
- [邮件](mailto:test@example.com)  # 不应该被提取

更多文字 [内联链接](https://python.org) 在这里。
"""
        urls = extract_urls_from_markdown(content)
        
        self.assertIn("https://example.com", urls)
        self.assertIn("https://github.com", urls)
        self.assertIn("https://python.org", urls)
        self.assertNotIn("./local/path", urls)
        self.assertNotIn("mailto:test@example.com", urls)
    
    def test_bracket_urls(self):
        """测试尖括号包裹的URL"""
        content = """
直接粘贴的URL: <https://example.com>

还有这个: <https://github.com/user/repo>
"""
        urls = extract_urls_from_markdown(content)
        
        self.assertIn("https://example.com", urls)
        self.assertIn("https://github.com/user/repo", urls)
    
    def test_reference_links(self):
        """测试引用链接 [ref]: url"""
        content = """
[Example][ex] 是一个示例。

[ex]: https://example.com
[GitHub]: https://github.com
"""
        urls = extract_urls_from_markdown(content)
        
        self.assertIn("https://example.com", urls)
        self.assertIn("https://github.com", urls)
    
    def test_duplicate_urls(self):
        """测试重复URL去重"""
        content = """
[链接1](https://example.com)
[链接2](https://example.com)
<https://example.com>
"""
        urls = extract_urls_from_markdown(content)
        
        # 应该只保留一个
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://example.com")
    
    def test_empty_content(self):
        """测试空内容"""
        urls = extract_urls_from_markdown("")
        self.assertEqual(urls, [])
        
        urls = extract_urls_from_markdown("# 标题\n\n没有链接的内容")
        self.assertEqual(urls, [])


class TestParseTaskMarkdown(unittest.TestCase):
    """测试解析任务Markdown文件"""
    
    def test_parse_valid_task_file(self):
        """测试解析有效的任务文件"""
        with TemporaryDirectory() as tmpdir:
            task_file = Path(tmpdir) / "TASK.md"
            content = """# 我的爬取任务

## 链接列表

- [Example](https://example.com)
- [GitHub](https://github.com)

## 说明

一些描述文字。
"""
            write_file_content(task_file, content)
            
            task_name, urls = parse_task_markdown(task_file)
            
            self.assertEqual(task_name, "我的爬取任务")
            self.assertEqual(len(urls), 2)
            self.assertIn("https://example.com", urls)
            self.assertIn("https://github.com", urls)
    
    def test_use_filename_as_task_name(self):
        """测试使用文件名作为任务名"""
        with TemporaryDirectory() as tmpdir:
            task_file = Path(tmpdir) / "my-task.md"
            content = """
没有标题的任务文件

- [Example](https://example.com)
"""
            write_file_content(task_file, content)
            
            task_name, urls = parse_task_markdown(task_file)
            
            self.assertEqual(task_name, "my-task")
            self.assertEqual(len(urls), 1)
    
    def test_no_urls_in_file(self):
        """测试文件中没有URL"""
        with TemporaryDirectory() as tmpdir:
            task_file = Path(tmpdir) / "TASK.md"
            content = """# 空任务

这个文件没有链接。
"""
            write_file_content(task_file, content)
            
            task_name, urls = parse_task_markdown(task_file)
            
            self.assertEqual(task_name, "空任务")
            self.assertEqual(urls, [])
    
    def test_file_not_found(self):
        """测试文件不存在"""
        with self.assertRaises(FileNotFoundError):
            parse_task_markdown(Path("/nonexistent/TASK.md"))


if __name__ == '__main__':
    unittest.main()
