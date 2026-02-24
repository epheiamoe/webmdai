#!/usr/bin/env python3
"""
内容清理模块测试
"""

import json
import tempfile
import unittest
from pathlib import Path

from webmdai.modules.content_cleaner import ContentCleaner, CleanRule


class TestCleanRule(unittest.TestCase):
    """测试清理规则"""

    def test_clean_rule_creation(self):
        """测试创建清理规则"""
        rule = CleanRule(
            name="测试规则", remove_patterns=[r"广告.*", r"分享"], min_content_length=50
        )

        self.assertEqual(rule.name, "测试规则")
        self.assertEqual(len(rule.remove_patterns), 2)
        self.assertEqual(rule.min_content_length, 50)

    def test_clean_rule_defaults(self):
        """测试默认值"""
        rule = CleanRule("默认规则")

        self.assertEqual(rule.name, "默认规则")
        self.assertEqual(rule.remove_patterns, [])
        self.assertEqual(rule.min_content_length, 100)
        self.assertIsNone(rule.max_content_length)


class TestContentCleaner(unittest.TestCase):
    """测试内容清理器"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cleaner_creation(self):
        """测试清理器创建"""
        rule = CleanRule("测试")
        cleaner = ContentCleaner(rule)

        self.assertEqual(cleaner.rules.name, "测试")

    def test_cleaner_default_rules(self):
        """测试默认规则"""
        cleaner = ContentCleaner()

        self.assertEqual(cleaner.rules.name, "default")

    def test_stats_initialization(self):
        """测试统计信息初始化"""
        cleaner = ContentCleaner()

        self.assertEqual(cleaner.stats["original_length"], 0)
        self.assertEqual(cleaner.stats["cleaned_length"], 0)
        self.assertEqual(cleaner.stats["removed_patterns"], [])

    def test_clean_no_patterns(self):
        """测试无模式时的清理"""
        rule = CleanRule(name="无模式")
        cleaner = ContentCleaner(rule)

        content = "这是正常内容，不包含要清理的内容。"
        result, stats = cleaner.clean(content)

        # 无模式时，内容保持不变
        self.assertEqual(content, result)

    def test_clean_from_yaml_file(self):
        """测试从YAML文件加载规则"""
        rules_content = """
name: test_yaml_rule
remove_patterns:
  - "广告.*"
  - "推广"
min_content_length: 10
"""
        rules_file = Path(self.temp_dir) / "rules.yaml"
        rules_file.write_text(rules_content, encoding="utf-8")

        cleaner = ContentCleaner.from_file(rules_file)

        self.assertEqual(cleaner.rules.name, "test_yaml_rule")
        self.assertEqual(len(cleaner.rules.remove_patterns), 2)

    def test_clean_from_json_file(self):
        """测试从JSON文件加载规则"""
        rules_data = {
            "name": "test_json_rule",
            "remove_patterns": ["广告", "推广"],
            "min_content_length": 5,
        }
        rules_file = Path(self.temp_dir) / "rules.json"
        rules_file.write_text(json.dumps(rules_data), encoding="utf-8")

        cleaner = ContentCleaner.from_file(rules_file)

        self.assertEqual(cleaner.rules.name, "test_json_rule")
        self.assertEqual(len(cleaner.rules.remove_patterns), 2)

    def test_clean_whitespace_only(self):
        """测试只包含空白字符的内容"""
        rule = CleanRule(name="测试")
        cleaner = ContentCleaner(rule)

        content = "   \n\n  "
        result, stats = cleaner.clean(content)

        # 空白内容应该保留
        self.assertEqual(result, content)


class TestCleanerPresets(unittest.TestCase):
    """测试预设清理规则"""

    def test_kakuyomu_preset_structure(self):
        """测试小说网站预设结构"""
        # 测试创建轻小说网站规则
        rule = CleanRule(
            name="kakuyomu", remove_patterns=[r"广告.*", r"相关推荐.*", r"推广.*"]
        )
        cleaner = ContentCleaner(rule)

        # 验证规则创建成功
        self.assertEqual(cleaner.rules.name, "kakuyomu")
        self.assertEqual(len(cleaner.rules.remove_patterns), 3)


if __name__ == "__main__":
    unittest.main()
