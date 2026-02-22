#!/usr/bin/env python3
"""
内容清理模块 - 移除无关元素，提取正文，减少Token消耗
"""

import re
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from ..utils.file_utils import read_file_content, write_file_content


@dataclass
class CleanRule:
    """清理规则"""
    name: str
    remove_patterns: List[str] = field(default_factory=list)
    remove_selectors: List[str] = field(default_factory=list)  # CSS选择器（HTML）
    start_markers: List[str] = field(default_factory=list)
    end_markers: List[str] = field(default_factory=list)
    min_content_length: int = 100
    max_content_length: Optional[int] = None


class ContentCleaner:
    """内容清理器"""
    
    def __init__(self, rules: Optional[CleanRule] = None):
        self.rules = rules or CleanRule("default")
        self.stats = {
            "original_length": 0,
            "cleaned_length": 0,
            "removed_patterns": [],
        }
    
    @classmethod
    def from_file(cls, filepath: Path) -> "ContentCleaner":
        """从文件加载清理规则"""
        content = read_file_content(filepath)
        
        # 尝试YAML格式
        if filepath.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(content)
        # 尝试JSON格式
        elif filepath.suffix == '.json':
            data = json.loads(content)
        else:
            # 默认YAML
            data = yaml.safe_load(content)
        
        rule = CleanRule(
            name=data.get("name", "from_file"),
            remove_patterns=data.get("remove_patterns", []),
            remove_selectors=data.get("remove_selectors", []),
            start_markers=data.get("start_markers", []),
            end_markers=data.get("end_markers", []),
            min_content_length=data.get("min_content_length", 100),
            max_content_length=data.get("max_content_length"),
        )
        
        return cls(rule)
    
    def clean(self, content: str) -> Tuple[str, Dict]:
        """
        清理内容
        
        Returns:
            (清理后的内容, 统计信息)
        """
        self.stats["original_length"] = len(content)
        original = content
        
        # 1. 应用移除正则
        for pattern in self.rules.remove_patterns:
            try:
                count = len(re.findall(pattern, content, re.MULTILINE | re.DOTALL))
                if count > 0:
                    content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
                    self.stats["removed_patterns"].append(f"{pattern}: {count}处")
            except re.error as e:
                self.stats["removed_patterns"].append(f"{pattern}: 正则错误 - {e}")
        
        # 2. 提取正文范围（根据开始/结束标记）
        content = self._extract_content_range(content)
        
        # 3. 基本清理
        content = self._basic_cleanup(content)
        
        # 4. 长度检查
        if len(content) < self.rules.min_content_length:
            # 如果提取结果太短，返回原始内容（可能提取失败）
            content = original
            self.stats["warning"] = f"清理后内容太短({len(content)}字符)，使用原始内容"
        
        if self.rules.max_content_length and len(content) > self.rules.max_content_length:
            content = content[:self.rules.max_content_length]
            self.stats["warning"] = f"内容超过最大长度，已截断至{self.rules.max_content_length}字符"
        
        self.stats["cleaned_length"] = len(content)
        self.stats["reduction"] = f"{((self.stats['original_length'] - self.stats['cleaned_length']) / self.stats['original_length'] * 100):.1f}%"
        
        return content, self.stats.copy()
    
    def _extract_content_range(self, content: str) -> str:
        """根据开始/结束标记提取内容范围"""
        if not self.rules.start_markers and not self.rules.end_markers:
            return content
        
        start_pos = 0
        end_pos = len(content)
        
        # 查找开始位置
        if self.rules.start_markers:
            for marker in self.rules.start_markers:
                try:
                    match = re.search(marker, content)
                    if match:
                        start_pos = match.start()
                        break
                except re.error:
                    # 如果不是正则，作为普通字符串查找
                    pos = content.find(marker)
                    if pos != -1:
                        start_pos = pos
                        break
        
        # 查找结束位置
        if self.rules.end_markers:
            for marker in self.rules.end_markers:
                try:
                    match = re.search(marker, content[start_pos:])
                    if match:
                        end_pos = start_pos + match.start()
                        break
                except re.error:
                    pos = content.find(marker, start_pos)
                    if pos != -1:
                        end_pos = pos
                        break
        
        return content[start_pos:end_pos]
    
    def _basic_cleanup(self, content: str) -> str:
        """基本清理"""
        # 移除多余空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        # 移除行首尾空格
        content = '\n'.join(line.strip() for line in content.split('\n'))
        # 移除HTML注释
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        return content.strip()
    
    def clean_file(self, filepath: Path, output_path: Optional[Path] = None) -> Tuple[bool, Dict]:
        """
        清理文件
        
        Args:
            filepath: 输入文件路径
            output_path: 输出文件路径（None则覆盖原文件）
            
        Returns:
            (是否成功, 统计信息)
        """
        try:
            content = read_file_content(filepath)
            cleaned, stats = self.clean(content)
            
            if output_path is None:
                output_path = filepath
            
            write_file_content(output_path, cleaned)
            stats["output_file"] = str(output_path)
            
            return True, stats
            
        except Exception as e:
            return False, {"error": str(e)}


def create_default_kakuyomu_rules() -> CleanRule:
    """创建カクヨム网站的默认清理规则"""
    return CleanRule(
        name="kakuyomu",
        remove_patterns=[
            r'^---.*?^---',  # YAML frontmatter
            r'Title:.*?URL Source:.*?Markdown Content:\n',
            r'!\[Image.*?\)\n?',  # 图片
            r'https?://[^\s]+(?:购[入买]|カクヨムネクスト|書籍を購入).*?\n',
            r'\*   \[!.*?\]\(.*?\)\n',
            r'### 作者を応援しよう！.*?(?=###|新規登録)',
            r'新規登録で充実の読書を.*?(?=次のエピソード)',
            r'\[次のエピソード.*?\]\(.*?\)\n',
            r'### \[.*?\]\[.*?\].*?(?=### 目次)',  # 移除作品信息区块
            r'### 目次.*?(?=### エピソード情報|$)',
            r'連載中 全\d+話.*?\d{4}年\d+月\d+日 更新.*?(?=ネクスト限定エピソード|$)',
            r'### ネクスト限定エピソード.*?$',
            r'!\[Image \d+\]\(https?://t\.co/.*?\)\n?',
        ],
        start_markers=[
            r"プロローグ",
            r"第\d+話",
            r"――",
        ],
        end_markers=[
            r'\d+/\d+（土）発売予定！',
            r'### ',
        ],
        min_content_length=500,
    )


def create_default_ncode_rules() -> CleanRule:
    """创建小説家になろう的默认清理规则"""
    return CleanRule(
        name="ncode",
        remove_patterns=[
            r'^---.*?^---',
            r'!\[.*?\]\(.*?\)',
            r'<a href=.*?</a>',
            r'＼.*?］',
            r'【.*?】',
        ],
        start_markers=[
            r"^\s*\d+\s*$",  # 章节编号
            r"プロローグ",
            r"第\d+章",
        ],
        end_markers=[
            r"■\s*あとがき",
            r"＼\s*\d+\s*］",
        ],
        min_content_length=500,
    )


# 预设规则库
PRESET_RULES = {
    "kakuyomu": create_default_kakuyomu_rules,
    "ncode": create_default_ncode_rules,
}


def get_preset_rule(name: str) -> Optional[CleanRule]:
    """获取预设清理规则"""
    factory = PRESET_RULES.get(name)
    if factory:
        return factory()
    return None


def list_preset_rules() -> Dict[str, str]:
    """列出所有预设规则"""
    return {
        "kakuyomu": "カクヨム (kakuyomu.jp) - 日本轻小说网站",
        "ncode": "小説家になろう (ncode.syosetu.com)",
    }
