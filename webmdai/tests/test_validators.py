#!/usr/bin/env python3
"""
验证器模块测试
"""

import unittest
from pathlib import Path

from webmdai.utils.validators import (
    validate_url, normalize_url, validate_directory,
    validate_task_name, validate_regex_pattern, parse_url_list
)


class TestValidators(unittest.TestCase):
    """测试验证器函数"""
    
    def test_validate_url_valid(self):
        """测试有效URL"""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "example.com",
            "https://example.com/path?query=1",
        ]
        
        for url in valid_urls:
            is_valid, error = validate_url(url)
            self.assertTrue(is_valid, f"URL应该有效: {url}")
            self.assertIsNone(error)
    
    def test_validate_url_invalid(self):
        """测试无效URL"""
        invalid_urls = [
            "",
            "ftp://example.com",
        ]
        
        for url in invalid_urls:
            is_valid, error = validate_url(url)
            self.assertFalse(is_valid, f"URL应该无效: {url}")
            self.assertIsNotNone(error)
    
    def test_normalize_url(self):
        """测试URL规范化"""
        self.assertEqual(
            normalize_url("example.com"),
            "https://example.com"
        )
        self.assertEqual(
            normalize_url("https://example.com"),
            "https://example.com"
        )
        self.assertEqual(
            normalize_url("  example.com  "),
            "https://example.com"
        )
    
    def test_validate_task_name(self):
        """测试任务名验证"""
        # 有效名称
        self.assertTrue(validate_task_name("test")[0])
        self.assertTrue(validate_task_name("test_task")[0])
        self.assertTrue(validate_task_name("test-task")[0])
        
        # 无效名称
        self.assertFalse(validate_task_name("")[0])
        self.assertFalse(validate_task_name("test/file")[0])
        self.assertFalse(validate_task_name("test<file>")[0])
    
    def test_validate_regex_pattern(self):
        """测试正则表达式验证"""
        # 有效模式
        self.assertTrue(validate_regex_pattern("test")[0])
        self.assertTrue(validate_regex_pattern(r"\d+")[0])
        self.assertTrue(validate_regex_pattern(r"[a-z]+")[0])
        
        # 无效模式
        self.assertFalse(validate_regex_pattern("")[0])
        self.assertFalse(validate_regex_pattern(r"[invalid")[0])
        self.assertFalse(validate_regex_pattern(r"(")[0])
    
    def test_parse_url_list(self):
        """测试URL列表解析"""
        # 单个URL
        urls = parse_url_list("https://example.com")
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://example.com")
        
        # 多个URL
        urls = parse_url_list("https://a.com, https://b.com, https://c.com")
        self.assertEqual(len(urls), 3)
        
        # 空字符串
        urls = parse_url_list("")
        self.assertEqual(len(urls), 0)
        
        # 带空格
        urls = parse_url_list("  https://a.com  ,  https://b.com  ")
        self.assertEqual(len(urls), 2)


if __name__ == "__main__":
    unittest.main()
