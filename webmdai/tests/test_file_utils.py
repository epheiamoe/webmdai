#!/usr/bin/env python3
"""
文件工具模块测试
"""

import tempfile
import unittest
from pathlib import Path

from webmdai.utils.file_utils import (
    sanitize_filename, create_task_directory,
    generate_metadata, find_markdown_files,
    read_file_content, write_file_content,
    extract_title_from_markdown, count_tokens_approx
)


class TestFileUtils(unittest.TestCase):
    """测试文件工具函数"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_sanitize_filename(self):
        """测试文件名清理"""
        self.assertEqual(sanitize_filename("test"), "test")
        self.assertEqual(sanitize_filename("test/file"), "test_file")
        self.assertEqual(sanitize_filename("test<file>"), "test_file_")
        self.assertEqual(sanitize_filename("  test  "), "test")
        self.assertEqual(sanitize_filename(".test."), "test")
    
    def test_create_task_directory(self):
        """测试任务目录创建"""
        task_dir = create_task_directory(self.temp_dir, "test_task")
        self.assertTrue(task_dir.exists())
        self.assertEqual(task_dir.parent, self.temp_dir)
        self.assertIn("test_task", task_dir.name)
    
    def test_generate_metadata(self):
        """测试元数据生成"""
        metadata = generate_metadata("https://example.com", "Test Title")
        self.assertIn("---", metadata)
        self.assertIn("source_url: https://example.com", metadata)
        self.assertIn("title: Test Title", metadata)
        self.assertIn("fetch_time:", metadata)
    
    def test_find_markdown_files(self):
        """测试查找Markdown文件"""
        # 创建测试文件
        (self.temp_dir / "file1.md").write_text("test")
        (self.temp_dir / "file2.md").write_text("test")
        (self.temp_dir / "file3.txt").write_text("test")
        
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file4.md").write_text("test")
        
        # 递归查找
        files = find_markdown_files(self.temp_dir, recursive=True)
        self.assertEqual(len(files), 3)
        
        # 非递归查找
        files = find_markdown_files(self.temp_dir, recursive=False)
        self.assertEqual(len(files), 2)
    
    def test_read_write_file_content(self):
        """测试文件读写"""
        test_file = self.temp_dir / "test.txt"
        content = "Hello, World!"
        
        write_file_content(test_file, content)
        read_content = read_file_content(test_file)
        
        self.assertEqual(content, read_content)
    
    def test_extract_title_from_markdown(self):
        """测试提取Markdown标题"""
        # 从一级标题提取
        content = "# Test Title\n\nSome content"
        self.assertEqual(extract_title_from_markdown(content), "Test Title")
        
        # 从YAML frontmatter提取
        content = "---\ntitle: YAML Title\n---\n\nContent"
        self.assertEqual(extract_title_from_markdown(content), "YAML Title")
        
        # 无标题
        content = "Just some content"
        self.assertIsNone(extract_title_from_markdown(content))
    
    def test_count_tokens_approx(self):
        """测试token估算"""
        # 英文
        tokens = count_tokens_approx("Hello world")
        self.assertGreater(tokens, 0)
        
        # 中文
        tokens = count_tokens_approx("你好世界")
        self.assertEqual(tokens, 4)  # 每个中文字符算1个token
        
        # 混合
        tokens = count_tokens_approx("Hello 你好 world 世界")
        self.assertGreater(tokens, 0)


if __name__ == "__main__":
    unittest.main()
