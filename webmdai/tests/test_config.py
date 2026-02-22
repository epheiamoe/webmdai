#!/usr/bin/env python3
"""
配置管理模块测试
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

from webmdai.config import Config


class TestConfig(unittest.TestCase):
    """测试配置管理类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".webmdai"
        self.config_file = self.config_dir / "config.json"
        
        # 修改配置路径
        self.original_config_dir = Config.CONFIG_DIR
        self.original_config_file = Config.CONFIG_FILE
        Config.CONFIG_DIR = self.config_dir
        Config.CONFIG_FILE = self.config_file
    
    def tearDown(self):
        """测试后清理"""
        # 恢复原始路径
        Config.CONFIG_DIR = self.original_config_dir
        Config.CONFIG_FILE = self.original_config_file
        
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ensure_config_exists(self):
        """测试配置文件创建"""
        config = Config()
        self.assertTrue(self.config_dir.exists())
        self.assertTrue(self.config_file.exists())
    
    def test_add_model(self):
        """测试添加模型"""
        config = Config()
        config.add_model("test", "https://api.test.com", "model-1", "key-123")
        
        model = config.get_model("test")
        self.assertIsNotNone(model)
        self.assertEqual(model["endpoint"], "https://api.test.com")
        self.assertEqual(model["model"], "model-1")
        self.assertEqual(model["key"], "key-123")
    
    def test_set_default_model(self):
        """测试设置默认模型"""
        config = Config()
        config.add_model("model1", "https://api1.com", "m1", "k1")
        config.add_model("model2", "https://api2.com", "m2", "k2")
        
        # 第一个模型应该自动成为默认
        self.assertEqual(config.config["default_model"], "model1")
        
        # 设置新的默认
        config.set_default_model("model2")
        self.assertEqual(config.config["default_model"], "model2")
    
    def test_remove_model(self):
        """测试删除模型"""
        config = Config()
        config.add_model("test", "https://api.test.com", "model-1", "key-123")
        
        self.assertTrue(config.remove_model("test"))
        self.assertIsNone(config.get_model("test"))
        self.assertFalse(config.remove_model("nonexistent"))
    
    def test_list_models(self):
        """测试列出模型"""
        config = Config()
        config.add_model("model1", "https://api1.com", "m1", "k1")
        config.add_model("model2", "https://api2.com", "m2", "k2")
        
        models = config.list_models()
        self.assertEqual(len(models), 2)
        self.assertIn("model1", models)
        self.assertIn("model2", models)
    
    def test_resolve_env_vars(self):
        """测试环境变量解析"""
        config = Config()
        
        # 设置环境变量
        os.environ["TEST_API_KEY"] = "secret123"
        
        model = {
            "endpoint": "https://api.test.com",
            "model": "test-model",
            "key": "$TEST_API_KEY"
        }
        
        resolved = config._resolve_env_vars(model)
        self.assertEqual(resolved["key"], "secret123")
        
        # 清理
        del os.environ["TEST_API_KEY"]
    
    def test_get_set_config(self):
        """测试配置项读写"""
        config = Config()
        
        # 设置配置
        config.set("fetch.timeout", 60)
        self.assertEqual(config.get("fetch.timeout"), 60)
        
        # 获取默认值
        self.assertEqual(config.get("nonexistent", "default"), "default")


if __name__ == "__main__":
    unittest.main()
