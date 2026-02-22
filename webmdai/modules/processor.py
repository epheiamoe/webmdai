#!/usr/bin/env python3
"""
文本处理模块 - 支持正则和普通文本替换/删除
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Callable

from ..utils.file_utils import find_markdown_files, read_file_content, write_file_content


@dataclass
class ProcessResult:
    """处理结果"""
    file_path: Path
    success: bool
    changes_made: int
    error_message: Optional[str] = None


class TextProcessor:
    """文本处理器"""
    
    def __init__(self, directory: Path):
        """
        初始化文本处理器
        
        Args:
            directory: 工作目录
        """
        self.directory = Path(directory).resolve()
        self.files = []
    
    def scan_files(self, recursive: bool = True) -> List[Path]:
        """
        扫描目录中的Markdown文件
        
        Args:
            recursive: 是否递归扫描
            
        Returns:
            文件路径列表
        """
        self.files = find_markdown_files(self.directory, recursive)
        return self.files
    
    def preview_text_replace(
        self,
        find: str,
        replace: str = "",
        files: Optional[List[Path]] = None
    ) -> List[Tuple[Path, str, str]]:
        """
        预览文本替换
        
        Args:
            find: 查找内容
            replace: 替换内容
            files: 要处理的文件列表，None表示所有文件
            
        Returns:
            (文件路径, 原始内容, 预览内容) 列表
        """
        if files is None:
            files = self.files or self.scan_files()
        
        previews = []
        for file_path in files:
            try:
                original = read_file_content(file_path)
                preview = original.replace(find, replace)
                previews.append((file_path, original, preview))
            except Exception as e:
                print(f"警告: 读取文件 {file_path} 失败: {e}")
        
        return previews
    
    def execute_text_replace(
        self,
        find: str,
        replace: str = "",
        files: Optional[List[Path]] = None
    ) -> List[ProcessResult]:
        """
        执行文本替换
        
        Args:
            find: 查找内容
            replace: 替换内容
            files: 要处理的文件列表，None表示所有文件
            
        Returns:
            处理结果列表
        """
        if files is None:
            files = self.files or self.scan_files()
        
        results = []
        for file_path in files:
            try:
                content = read_file_content(file_path)
                new_content = content.replace(find, replace)
                
                changes = content.count(find)
                
                if changes > 0:
                    write_file_content(file_path, new_content)
                
                results.append(ProcessResult(
                    file_path=file_path,
                    success=True,
                    changes_made=changes
                ))
            except Exception as e:
                results.append(ProcessResult(
                    file_path=file_path,
                    success=False,
                    changes_made=0,
                    error_message=str(e)
                ))
        
        return results
    
    def preview_regex_replace(
        self,
        pattern: str,
        replace: str = "",
        files: Optional[List[Path]] = None
    ) -> List[Tuple[Path, str, str, int]]:
        """
        预览正则替换
        
        Args:
            pattern: 正则表达式
            replace: 替换内容
            files: 要处理的文件列表，None表示所有文件
            
        Returns:
            (文件路径, 原始内容, 预览内容, 匹配次数) 列表
        """
        if files is None:
            files = self.files or self.scan_files()
        
        regex = re.compile(pattern, re.MULTILINE)
        previews = []
        
        for file_path in files:
            try:
                original = read_file_content(file_path)
                matches = len(regex.findall(original))
                preview = regex.sub(replace, original)
                previews.append((file_path, original, preview, matches))
            except Exception as e:
                print(f"警告: 读取文件 {file_path} 失败: {e}")
        
        return previews
    
    def execute_regex_replace(
        self,
        pattern: str,
        replace: str = "",
        files: Optional[List[Path]] = None
    ) -> List[ProcessResult]:
        """
        执行正则替换
        
        Args:
            pattern: 正则表达式
            replace: 替换内容
            files: 要处理的文件列表，None表示所有文件
            
        Returns:
            处理结果列表
        """
        if files is None:
            files = self.files or self.scan_files()
        
        regex = re.compile(pattern, re.MULTILINE)
        results = []
        
        for file_path in files:
            try:
                content = read_file_content(file_path)
                new_content, changes = regex.subn(replace, content)
                
                if changes > 0:
                    write_file_content(file_path, new_content)
                
                results.append(ProcessResult(
                    file_path=file_path,
                    success=True,
                    changes_made=changes
                ))
            except Exception as e:
                results.append(ProcessResult(
                    file_path=file_path,
                    success=False,
                    changes_made=0,
                    error_message=str(e)
                ))
        
        return results
    
    def preview_delete(
        self,
        find: str,
        use_regex: bool = False,
        files: Optional[List[Path]] = None
    ) -> List[Tuple[Path, str, str, int]]:
        """
        预览删除操作
        
        Args:
            find: 查找内容
            use_regex: 是否使用正则
            files: 要处理的文件列表
            
        Returns:
            预览结果列表
        """
        if use_regex:
            return self.preview_regex_replace(find, "", files)
        else:
            previews = self.preview_text_replace(find, "", files)
            return [(p[0], p[1], p[2], p[1].count(find)) for p in previews]
    
    def execute_delete(
        self,
        find: str,
        use_regex: bool = False,
        files: Optional[List[Path]] = None
    ) -> List[ProcessResult]:
        """
        执行删除操作
        
        Args:
            find: 查找内容
            use_regex: 是否使用正则
            files: 要处理的文件列表
            
        Returns:
            处理结果列表
        """
        if use_regex:
            return self.execute_regex_replace(find, "", files)
        else:
            return self.execute_text_replace(find, "", files)
    
    def get_statistics(self, results: List[ProcessResult]) -> dict:
        """
        获取处理统计信息
        
        Args:
            results: 处理结果列表
            
        Returns:
            统计信息字典
        """
        total_files = len(results)
        success_files = sum(1 for r in results if r.success)
        failed_files = total_files - success_files
        total_changes = sum(r.changes_made for r in results)
        files_with_changes = sum(1 for r in results if r.changes_made > 0)
        
        return {
            "total_files": total_files,
            "success_files": success_files,
            "failed_files": failed_files,
            "total_changes": total_changes,
            "files_with_changes": files_with_changes,
        }
    
    def print_preview(
        self,
        previews: List[Tuple],
        max_preview_length: int = 500
    ):
        """
        打印预览信息
        
        Args:
            previews: 预览结果
            max_preview_length: 最大预览长度
        """
        from colorama import Fore, Style
        
        for item in previews:
            file_path = item[0]
            original = item[1]
            preview = item[2]
            matches = item[3] if len(item) > 3 else 0
            
            print(f"\n{Fore.CYAN}文件: {file_path}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}匹配次数: {matches}{Style.RESET_ALL}")
            
            if matches > 0:
                print(f"\n{Fore.GREEN}--- 预览 ---{Style.RESET_ALL}")
                preview_text = preview[:max_preview_length]
                if len(preview) > max_preview_length:
                    preview_text += "\n... (内容已截断)"
                print(preview_text)


def interactive_preview_confirm(
    processor: TextProcessor,
    previews: List[Tuple],
    execute_func: Callable
) -> bool:
    """
    交互式预览确认
    
    Args:
        processor: 文本处理器
        previews: 预览结果
        execute_func: 执行函数
        
    Returns:
        是否执行
    """
    from colorama import Fore, Style
    
    if not previews:
        print(f"{Fore.YELLOW}没有找到匹配的文件{Style.RESET_ALL}")
        return False
    
    # 显示预览
    processor.print_preview(previews)
    
    # 统计
    total_matches = sum(item[3] for item in previews if len(item) > 3)
    files_with_matches = sum(1 for item in previews if len(item) > 3 and item[3] > 0)
    
    print(f"\n{Fore.CYAN}总计: {files_with_matches} 个文件将受影响, {total_matches} 处将被修改{Style.RESET_ALL}")
    
    # 确认
    try:
        response = input(f"\n{Fore.YELLOW}确认执行修改? (y/N): {Style.RESET_ALL}").strip().lower()
        if response in ['y', 'yes']:
            return True
    except (EOFError, KeyboardInterrupt):
        print("\n操作已取消")
    
    return False
