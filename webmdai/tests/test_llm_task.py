#!/usr/bin/env python3
"""
LLM任务模型测试
"""

import unittest

from webmdai.models.llm_task import LLMTask, get_preset_task, create_custom_task


class TestLLMTask(unittest.TestCase):
    """测试LLM任务模型"""

    def test_custom_task_creation(self):
        """测试创建自定义任务"""
        task = create_custom_task("你是翻译助手。", "custom")

        self.assertEqual(task.name, "custom")
        self.assertIn("翻译助手", task.prompt_template)

    def test_preset_translate(self):
        """测试翻译预设"""
        task = get_preset_task("translate")

        self.assertIsNotNone(task)
        self.assertEqual(task.name, "translate")
        self.assertIn("{content}", task.prompt_template)

    def test_preset_summarize(self):
        """测试摘要预设"""
        task = get_preset_task("summarize")

        self.assertIsNotNone(task)
        self.assertEqual(task.name, "summarize")

    def test_preset_explain(self):
        """测试解释预设"""
        task = get_preset_task("explain")

        self.assertIsNotNone(task)
        self.assertEqual(task.name, "explain")

    def test_preset_abstract(self):
        """测试要点预设"""
        task = get_preset_task("abstract")

        self.assertIsNotNone(task)
        self.assertEqual(task.name, "abstract")

    def test_preset_not_found(self):
        """测试不存在的预设"""
        task = get_preset_task("nonexistent_preset")

        self.assertIsNone(task)

    def test_task_format_content(self):
        """测试任务格式化"""
        task = get_preset_task("translate")
        content = "Hello World"

        formatted = task.format_prompt(content)

        self.assertIn(content, formatted)
        self.assertIn("翻译成中文", formatted)

    def test_task_output_suffix(self):
        """测试输出后缀"""
        task = get_preset_task("translate")

        self.assertEqual(task.output_suffix, "translate")

    def test_custom_task_format(self):
        """测试自定义任务格式化"""
        task = create_custom_task("翻译这个：{content}", "my_task")

        formatted = task.format_prompt("测试内容")

        self.assertIn("测试内容", formatted)
        self.assertIn("翻译这个", formatted)


if __name__ == "__main__":
    unittest.main()
