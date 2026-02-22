#!/usr/bin/env python3
"""
爬取模块测试
"""

import unittest
from unittest.mock import Mock, patch

from webmdai.modules.fetcher import (
    JinaReader, DirectReader, get_reader, list_readers
)
from webmdai.models.fetch_result import FetchResult


class TestJinaReader(unittest.TestCase):
    """测试Jina Reader"""
    
    @patch('webmdai.modules.fetcher.requests.get')
    def test_fetch_success(self, mock_get):
        """测试成功爬取"""
        # 模拟响应
        mock_response = Mock()
        mock_response.text = "# Test Title\n\nTest content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        reader = JinaReader()
        result = reader.fetch("https://example.com")
        
        self.assertTrue(result.success)
        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.title, "Test Title")
        self.assertIn("Test content", result.content)
    
    @patch('webmdai.modules.fetcher.requests.get')
    def test_fetch_failure(self, mock_get):
        """测试爬取失败"""
        # 模拟异常
        from requests import RequestException
        mock_get.side_effect = RequestException("Network error")
        
        reader = JinaReader()
        result = reader.fetch("https://example.com")
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)


class TestDirectReader(unittest.TestCase):
    """测试Direct Reader"""
    
    def test_init(self):
        """测试初始化"""
        reader = DirectReader()
        self.assertEqual(reader.name, "direct")
        self.assertEqual(reader.timeout, 30)
        self.assertEqual(reader.retry_times, 3)
    
    def test_init_with_params(self):
        """测试带参数初始化"""
        reader = DirectReader(timeout=60, retry_times=5)
        self.assertEqual(reader.timeout, 60)
        self.assertEqual(reader.retry_times, 5)


class TestFetcherRegistry(unittest.TestCase):
    """测试Fetcher注册表"""
    
    def test_get_reader(self):
        """测试获取Reader"""
        reader = get_reader("jina")
        self.assertIsNotNone(reader)
        self.assertIsInstance(reader, JinaReader)
        
        reader = get_reader("nonexistent")
        self.assertIsNone(reader)
    
    def test_list_readers(self):
        """测试列出Reader"""
        readers = list_readers()
        self.assertIn("jina", readers)
        self.assertIn("direct", readers)


if __name__ == "__main__":
    unittest.main()
