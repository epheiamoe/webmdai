#!/usr/bin/env python3
"""
工作流引擎 - 执行多阶段处理管道
"""

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from colorama import Fore, Style

from ..models.workflow import WorkflowConfig, StageConfig, StageType
from ..utils.file_utils import (
    read_file_content, write_file_content, 
    merge_markdown_files, find_markdown_files
)
from ..utils.validators import parse_url_list


@dataclass
class StageResult:
    """阶段执行结果"""
    success: bool
    message: str
    output_files: List[Path] = None
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []
        if self.data is None:
            self.data = {}


class WorkflowContext:
    """工作流执行上下文"""
    
    def __init__(self, config: WorkflowConfig, working_dir: Path):
        self.config = config
        self.working_dir = working_dir
        self.variables = dict(config.variables)  # 全局变量
        self.stage_outputs = {}  # 各阶段输出
        self.current_stage = None
        self.start_time = None
        
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
        
    def get_variable(self, name: str, default=None) -> Any:
        """获取变量"""
        return self.variables.get(name, default)
    
    def interpolate(self, text: str) -> str:
        """插值变量 ${varname}"""
        result = text
        for name, value in self.variables.items():
            result = result.replace(f"${{{name}}}", str(value))
        return result


class StageExecutor:
    """阶段执行器基类"""
    
    def __init__(self, context: WorkflowContext):
        self.context = context
        
    def execute(self, stage: StageConfig) -> StageResult:
        """执行阶段"""
        raise NotImplementedError


class FetchStageExecutor(StageExecutor):
    """爬取阶段执行器"""
    
    def execute(self, stage: StageConfig) -> StageResult:
        from .fetcher import Fetcher
        from ..utils.file_utils import parse_task_markdown, create_task_directory, sanitize_filename
        
        params = stage.params
        source = params.get("source", "urls")
        
        urls = []
        task_name = params.get("task_name", "workflow_task")
        
        # 获取URL列表
        if source == "taskfile":
            taskfile = Path(params.get("taskfile", "TASK.md"))
            if not taskfile.is_absolute():
                taskfile = self.context.working_dir / taskfile
            
            if not taskfile.exists():
                return StageResult(False, f"任务文件不存在: {taskfile}")
            
            task_name, urls = parse_task_markdown(taskfile)
            
        elif source == "urls":
            urls_str = params.get("urls", "")
            urls = parse_url_list(urls_str)
            task_name = params.get("task_name", "url_task")
            
        if not urls:
            return StageResult(False, "没有要爬取的URL")
        
        # 创建Fetcher并爬取
        reader = params.get("reader", "jina")
        delay = params.get("delay", 1.0)
        timeout = params.get("timeout", 30)
        
        fetcher = Fetcher(reader, delay=delay, timeout=timeout)
        results = fetcher.fetch_multiple(urls)
        
        # 创建任务目录并保存
        task_dir = create_task_directory(self.context.working_dir, task_name)
        saved_files = []
        
        for i, result in enumerate(results, 1):
            if not result.success:
                continue
            
            title = result.title or f"page_{i}"
            filename = f"{sanitize_filename(task_name)}_{i}_{sanitize_filename(title)}.md"
            filepath = task_dir / filename
            
            content = result.markdown
            write_file_content(filepath, content)
            saved_files.append(filepath)
        
        success_count = len(saved_files)
        self.context.set_variable("TASK_DIR", str(task_dir))
        self.context.set_variable("TASK_NAME", task_name)
        
        return StageResult(
            success=success_count > 0,
            message=f"爬取完成: {success_count}/{len(urls)} 成功",
            output_files=saved_files,
            data={"task_dir": task_dir, "task_name": task_name}
        )


class LLMStageExecutor(StageExecutor):
    """LLM处理阶段执行器"""
    
    def execute(self, stage: StageConfig) -> StageResult:
        from .llm_handler import create_llm_handler_from_config
        from ..models.llm_task import get_preset_task, create_custom_task
        from ..config import get_config
        
        params = stage.params
        config = get_config()
        
        # 获取模型配置
        model_alias = params.get("model", "default")
        if model_alias == "default":
            model_config = config.get_default_model()
        else:
            model_config = config.get_model(model_alias)
        
        if not model_config:
            return StageResult(False, f"未找到模型配置: {model_alias}")
        
        # 获取任务模板（支持多种方式）
        prompt_file = params.get("prompt_file")
        prompt_template = params.get("prompt_template", "custom")
        custom_prompt = params.get("custom_prompt", "")
        
        if prompt_file:
            # 方式1：从文件加载提示词
            prompt_path = Path(prompt_file)
            if not prompt_path.is_absolute():
                prompt_path = self.context.working_dir / prompt_path
            
            if not prompt_path.exists():
                return StageResult(False, f"提示词文件不存在: {prompt_path}")
            
            prompt_content = read_file_content(prompt_path)
            task = create_custom_task(prompt_content, "custom_file")
        elif custom_prompt:
            # 方式2：使用内联自定义提示词
            task = create_custom_task(custom_prompt, "custom")
        else:
            # 方式3：使用预设模板
            task = get_preset_task(prompt_template)
            if not task:
                return StageResult(False, f"未知任务模板: {prompt_template}")
        
        # 查找文件
        file_pattern = params.get("file_pattern", "*.md")
        task_dir = self.context.get_variable("TASK_DIR", str(self.context.working_dir))
        search_dir = Path(task_dir)
        
        files = list(search_dir.glob(file_pattern))
        if not files:
            return StageResult(False, f"未找到匹配文件: {file_pattern}")
        
        # 创建LLM处理器
        output_suffix = params.get("output_suffix", "_processed")
        output_dir = search_dir / f"llm_{output_suffix}"
        
        handler = create_llm_handler_from_config(model_config, output_dir)
        
        # 处理文件
        output_files = handler.process_files_separate(search_dir, task, output_dir)
        
        return StageResult(
            success=len(output_files) > 0,
            message=f"LLM处理完成: {len(output_files)} 个文件",
            output_files=output_files
        )


class ReplaceStageExecutor(StageExecutor):
    """替换阶段执行器"""
    
    def execute(self, stage: StageConfig) -> StageResult:
        from .processor import TextProcessor
        from ..modules.git_handler import GitHandler
        
        params = stage.params
        file_pattern = params.get("file_pattern", "*.md")
        
        # 查找文件
        task_dir = self.context.get_variable("TASK_DIR", str(self.context.working_dir))
        search_dir = Path(task_dir)
        
        # 获取替换规则
        replacements = {}
        
        # 从文件加载
        if "replacements_file" in params:
            rep_file = Path(params["replacements_file"])
            if rep_file.exists():
                with open(rep_file, 'r', encoding='utf-8') as f:
                    replacements = json.load(f)
        
        # 合并内联规则
        if "replacements" in params:
            replacements.update(params["replacements"])
        
        if not replacements:
            return StageResult(False, "没有定义替换规则")
        
        # 备份
        if params.get("backup", True):
            git = GitHandler(search_dir, enabled=True)
            git.create_backup_commit("workflow", "name-replace", "")
        
        # 执行替换
        processor = TextProcessor(search_dir)
        files = list(search_dir.glob(file_pattern))
        
        total_changes = 0
        for file_path in files:
            try:
                content = read_file_content(file_path)
                new_content = content
                
                for old, new in replacements.items():
                    new_content = new_content.replace(old, new)
                
                if new_content != content:
                    write_file_content(file_path, new_content)
                    total_changes += 1
            except Exception as e:
                print(f"  处理文件失败 {file_path}: {e}")
        
        return StageResult(
            success=True,
            message=f"替换完成: {total_changes} 个文件被修改",
            output_files=files
        )


class MergeStageExecutor(StageExecutor):
    """合并阶段执行器"""
    
    def execute(self, stage: StageConfig) -> StageResult:
        params = stage.params
        file_pattern = params.get("file_pattern", "*.md")
        
        task_dir = self.context.get_variable("TASK_DIR", str(self.context.working_dir))
        search_dir = Path(task_dir)
        
        files = list(search_dir.glob(file_pattern))
        if not files:
            return StageResult(False, f"未找到匹配文件: {file_pattern}")
        
        # 排序
        sort_by = params.get("sort_by", "name")
        if sort_by == "numeric":
            import re
            def extract_number(f):
                match = re.search(r'(\d+)', f.name)
                return int(match.group(1)) if match else 0
            files.sort(key=extract_number)
        else:
            files.sort()
        
        # 合并
        output = params.get("output", "merged.md")
        output_path = search_dir / output
        
        header = params.get("header", "")
        separator = params.get("separator", "\n\n---\n\n")
        
        # 构建合并内容
        contents = []
        if header:
            contents.append(header)
        
        for i, file in enumerate(files):
            if i > 0:
                contents.append(separator)
            
            content = read_file_content(file)
            
            # 可选：为每个文件添加章节标题
            if params.get("add_chapter_headers", False):
                chapter_title = file.stem
                contents.append(f"\n## {chapter_title}\n\n")
            
            contents.append(content)
        
        write_file_content(output_path, "".join(contents))
        
        # 收集到新目录
        if params.get("collect_files", False):
            collect_dir = search_dir / params.get("collect_dir", "collected")
            collect_dir.mkdir(exist_ok=True)
            
            for file in files:
                import shutil
                shutil.copy2(file, collect_dir)
        
        return StageResult(
            success=True,
            message=f"合并完成: {len(files)} 个文件 → {output}",
            output_files=[output_path]
        )


class CommandStageExecutor(StageExecutor):
    """命令执行器（运行shell命令或脚本）"""
    
    def execute(self, stage: StageConfig) -> StageResult:
        params = stage.params
        command = params.get("command", "")
        
        if not command:
            return StageResult(False, "没有指定命令")
        
        # 变量插值
        command = self.context.interpolate(command)
        
        working_dir = self.context.get_variable("TASK_DIR", str(self.context.working_dir))
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=params.get("timeout", 300)
            )
            
            success = result.returncode == 0
            message = result.stdout if success else result.stderr
            
            return StageResult(success, message.strip())
            
        except subprocess.TimeoutExpired:
            return StageResult(False, "命令执行超时")
        except Exception as e:
            return StageResult(False, f"命令执行失败: {e}")


class ScriptStageExecutor(StageExecutor):
    """脚本执行器（运行Python/JS等脚本）"""
    
    def execute(self, stage: StageConfig) -> StageResult:
        params = stage.params
        script_path = params.get("script", "")
        interpreter = params.get("interpreter", "python")
        
        if not script_path:
            return StageResult(False, "没有指定脚本")
        
        script_file = Path(script_path)
        if not script_file.is_absolute():
            script_file = self.context.working_dir / script_file
        
        if not script_file.exists():
            return StageResult(False, f"脚本不存在: {script_file}")
        
        # 构建命令
        args = params.get("args", [])
        args_str = " ".join(f'"{arg}"' for arg in args)
        command = f'{interpreter} "{script_file}" {args_str}'
        
        # 复用CommandExecutor
        executor = CommandStageExecutor(self.context)
        return executor.execute(StageConfig(
            name=stage.name,
            type=StageType.COMMAND,
            params={"command": command, "timeout": params.get("timeout", 300)}
        ))


# 执行器映射
class CleanStageExecutor(StageExecutor):
    """内容清理阶段执行器"""
    
    def execute(self, stage: StageConfig) -> StageResult:
        from .content_cleaner import ContentCleaner, CleanRule, get_preset_rule
        
        params = stage.params
        file_pattern = params.get("file_pattern", "*.md")
        
        # 查找文件
        task_dir = self.context.get_variable("TASK_DIR", str(self.context.working_dir))
        search_dir = Path(task_dir)
        files = list(search_dir.glob(file_pattern))
        
        if not files:
            return StageResult(False, f"未找到匹配文件: {file_pattern}")
        
        # 获取清理规则
        rules_file = params.get("rules_file")
        preset_name = params.get("preset")
        
        if rules_file:
            # 从文件加载规则
            rule_path = Path(rules_file)
            if not rule_path.is_absolute():
                rule_path = self.context.working_dir / rule_path
            
            if not rule_path.exists():
                return StageResult(False, f"规则文件不存在: {rule_path}")
            
            cleaner = ContentCleaner.from_file(rule_path)
        elif preset_name:
            # 使用预设规则
            rule = get_preset_rule(preset_name)
            if not rule:
                return StageResult(False, f"未知预设规则: {preset_name}")
            cleaner = ContentCleaner(rule)
        else:
            # 使用内联规则
            rule = CleanRule(
                name="inline",
                remove_patterns=params.get("remove_patterns", []),
                start_markers=params.get("start_markers", []),
                end_markers=params.get("end_markers", []),
                min_content_length=params.get("min_content_length", 100),
                max_content_length=params.get("max_content_length"),
            )
            cleaner = ContentCleaner(rule)
        
        # 执行清理
        output_suffix = params.get("output_suffix", "_cleaned")
        processed_files = []
        total_reduction = 0
        
        for file_path in files:
            try:
                # 生成输出文件名
                if output_suffix:
                    output_name = f"{file_path.stem}{output_suffix}{file_path.suffix}"
                else:
                    output_name = file_path.name
                output_path = file_path.parent / output_name
                
                # 清理文件
                success, stats = cleaner.clean_file(file_path, output_path)
                
                if success:
                    processed_files.append(output_path)
                    original = stats.get("original_length", 0)
                    cleaned = stats.get("cleaned_length", 0)
                    if original > 0:
                        reduction = (original - cleaned) / original * 100
                        total_reduction += reduction
                        
                    # 显示统计
                    print(f"  {file_path.name}:")
                    print(f"    原始: {original} 字符 → 清理后: {cleaned} 字符")
                    if "removed_patterns" in stats:
                        for p in stats["removed_patterns"]:
                            print(f"    移除: {p}")
                else:
                    print(f"  清理失败 {file_path.name}: {stats.get('error')}")
                    
            except Exception as e:
                print(f"  处理文件失败 {file_path.name}: {e}")
        
        avg_reduction = total_reduction / len(processed_files) if processed_files else 0
        
        return StageResult(
            success=len(processed_files) > 0,
            message=f"清理完成: {len(processed_files)} 个文件, 平均减少 {avg_reduction:.1f}%",
            output_files=processed_files
        )


EXECUTOR_MAP = {
    StageType.FETCH: FetchStageExecutor,
    StageType.CLEAN: CleanStageExecutor,
    StageType.LLM: LLMStageExecutor,
    StageType.REPLACE: ReplaceStageExecutor,
    StageType.MERGE: MergeStageExecutor,
    StageType.COMMAND: CommandStageExecutor,
    StageType.SCRIPT: ScriptStageExecutor,
}


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self, config: WorkflowConfig, working_dir: Optional[Path] = None):
        self.config = config
        self.working_dir = working_dir or Path.cwd()
        self.context = WorkflowContext(config, self.working_dir)
        self.results: List[StageResult] = []
        
    def run(self) -> bool:
        """运行工作流"""
        print(f"{Fore.CYAN}=== 工作流: {self.config.name} ==={Style.RESET_ALL}")
        print(f"描述: {self.config.description or '无'}")
        print(f"阶段数: {len(self.config.stages)}\n")
        
        self.context.start_time = time.time()
        
        for i, stage in enumerate(self.config.stages, 1):
            if not stage.enabled:
                print(f"{Fore.YELLOW}[{i}/{len(self.config.stages)}] {stage.name} - 已跳过 (禁用){Style.RESET_ALL}")
                continue
            
            print(f"\n{Fore.CYAN}[{i}/{len(self.config.stages)}] 执行阶段: {stage.name}{Style.RESET_ALL}")
            print(f"类型: {stage.type.value}")
            
            self.context.current_stage = stage
            
            # 获取执行器
            executor_class = EXECUTOR_MAP.get(stage.type)
            if not executor_class:
                print(f"{Fore.RED}错误: 未知的阶段类型 {stage.type}{Style.RESET_ALL}")
                return False
            
            # 执行
            try:
                executor = executor_class(self.context)
                result = executor.execute(stage)
                self.results.append(result)
                
                if result.success:
                    print(f"{Fore.GREEN}✓ {result.message}{Style.RESET_ALL}")
                    # 保存阶段输出
                    self.context.stage_outputs[stage.name] = result
                else:
                    print(f"{Fore.RED}✗ {result.message}{Style.RESET_ALL}")
                    
                    if stage.on_error == "stop":
                        print(f"{Fore.RED}工作流中止{Style.RESET_ALL}")
                        return False
                    elif stage.on_error == "skip":
                        print(f"{Fore.YELLOW}跳过此阶段，继续执行{Style.RESET_ALL}")
                    # ignore: 继续执行
                    
            except Exception as e:
                print(f"{Fore.RED}阶段执行异常: {e}{Style.RESET_ALL}")
                if stage.on_error == "stop":
                    return False
        
        elapsed = time.time() - self.context.start_time
        print(f"\n{Fore.GREEN}=== 工作流完成 ==={Style.RESET_ALL}")
        print(f"总耗时: {elapsed:.1f} 秒")
        
        return True
