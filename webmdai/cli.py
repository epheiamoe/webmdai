#!/usr/bin/env python3
"""
webmdai - 命令行入口
"""

import sys
from pathlib import Path

import click
from colorama import Fore, Style, init

from .config import get_config
from .models.llm_task import (
    get_preset_task,
    list_preset_tasks,
    create_custom_task,
    get_task,
    list_all_tasks,
)
from .modules.fetcher import Fetcher, list_readers
from .modules.processor import TextProcessor, interactive_preview_confirm
from .modules.git_handler import GitHandler
from .modules.llm_handler import LLMHandler, create_llm_handler_from_config
from .utils.file_utils import (
    create_task_directory,
    sanitize_filename,
    get_unique_filename,
    merge_markdown_files,
    parse_task_markdown,
)
from .utils.validators import (
    validate_url,
    validate_directory,
    validate_task_name,
    validate_regex_pattern,
    parse_url_list,
    confirm_action,
)

# 初始化colorama
init(autoreset=True)


# ========== 上下文 ==========


class Context:
    """CLI上下文"""

    def __init__(self):
        self.config = get_config()


pass_context = click.make_pass_decorator(Context, ensure=True)


# ========== 主命令 ==========


@click.group()
@click.version_option(version="0.2.0", prog_name="webmdai")
@click.pass_context
def cli(ctx):
    """webmdai - 网页内容爬取、文本处理和LLM处理命令行工具"""
    ctx.obj = Context()


# ========== Fetch 命令 ==========


@cli.group(name="fetch")
def fetch_cmd():
    """网页内容爬取"""
    pass


@fetch_cmd.command(name="interactive")
@click.option("-r", "--reader", default="jina", help="爬取服务商 (默认: jina)")
@click.option("-s", "--separate", is_flag=True, help="每个网页保存为单独文件")
@click.option("-t", "--together", is_flag=True, help="所有网页合并为一个文件")
@click.option("-st", "both", is_flag=True, help="同时生成单独文件和合并文件")
@pass_context
def fetch_interactive(ctx, reader, separate, together, both):
    """交互式爬取网页"""
    print(f"{Fore.CYAN}=== 网页爬取 (交互模式) ==={Style.RESET_ALL}\n")

    # 显示可用的reader
    print(f"{Fore.GREEN}可用服务商:{Style.RESET_ALL}")
    for name, desc in list_readers().items():
        marker = " *" if name == reader else ""
        print(f"  - {name}: {desc}{marker}")
    print()

    # 收集URL
    urls = []
    print(f"{Fore.YELLOW}请输入网址 (每行一个，输入 /start 结束):{Style.RESET_ALL}")
    while True:
        try:
            line = input("> ").strip()
            if line == "/start":
                break
            if line == "/exit":
                print("已退出")
                return
            if line == "/help":
                print_help()
                continue
            if line:
                is_valid, error = validate_url(line)
                if is_valid:
                    urls.append(line)
                    print(f"  已添加: {line}")
                else:
                    print(f"  {Fore.RED}无效URL: {error}{Style.RESET_ALL}")
        except (EOFError, KeyboardInterrupt):
            print("\n已取消")
            return

    if not urls:
        print(f"{Fore.YELLOW}未输入任何网址{Style.RESET_ALL}")
        return

    print(f"\n共输入 {len(urls)} 个网址\n")

    # 输入任务名
    while True:
        task_name = input(f"{Fore.YELLOW}任务名称: {Style.RESET_ALL}").strip()
        is_valid, error = validate_task_name(task_name)
        if is_valid:
            break
        print(f"{Fore.RED}{error}{Style.RESET_ALL}")

    # 确定输出模式
    if not separate and not together and not both:
        both = True  # 默认同时生成

    # 执行爬取
    _execute_fetch(ctx, urls, task_name, reader, separate, together, both)


@fetch_cmd.command(name="batch")
@click.option("-w", "--websites", required=True, help="网址列表（逗号分隔）")
@click.option("-n", "--name", required=True, help="任务名称")
@click.option("-r", "--reader", default="jina", help="爬取服务商")
@click.option("-s", "--separate", is_flag=True, help="每个网页保存为单独文件")
@click.option("-t", "--together", is_flag=True, help="所有网页合并为一个文件")
@click.option("-st", "both", is_flag=True, help="同时生成单独文件和合并文件")
@pass_context
def fetch_batch(ctx, websites, name, reader, separate, together, both):
    """批量爬取网页"""
    # 解析URL
    urls = parse_url_list(websites)
    if not urls:
        print(f"{Fore.RED}未提供有效网址{Style.RESET_ALL}")
        return

    # 验证任务名
    is_valid, error = validate_task_name(name)
    if not is_valid:
        print(f"{Fore.RED}{error}{Style.RESET_ALL}")
        return

    # 确定输出模式
    if not separate and not together and not both:
        both = True

    # 执行爬取
    _execute_fetch(ctx, urls, name, reader, separate, together, both)


@fetch_cmd.command(name="from-task")
@click.argument("taskfile", required=False, default="TASK.md")
@click.option("-r", "--reader", default="jina", help="爬取服务商")
@click.option("-s", "--separate", is_flag=True, help="每个网页保存为单独文件")
@click.option("-t", "--together", is_flag=True, help="所有网页合并为一个文件")
@click.option("-st", "both", is_flag=True, help="同时生成单独文件和合并文件")
@click.option("-n", "--name", help="覆盖任务名称（默认使用文件中的标题）")
@pass_context
def fetch_from_task(ctx, taskfile, reader, separate, together, both, name):
    """从任务Markdown文件爬取网页

    TASKFILE: 任务Markdown文件路径（默认: TASK.md）

    文件格式示例：
    \b
    # 我的爬取任务

    ## 参考链接
    - [Example](https://example.com)\n    - [GitHub](https://github.com)
    """
    from pathlib import Path

    task_path = Path(taskfile)
    if not task_path.is_absolute():
        task_path = Path.cwd() / task_path

    # 检查文件是否存在
    if not task_path.exists():
        print(f"{Fore.RED}任务文件不存在: {task_path}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}请创建 {taskfile} 文件并添加要爬取的链接{Style.RESET_ALL}")
        print(f"\n文件格式示例：")
        print(f"  # 任务名称")
        print(f"  - [链接描述](https://example.com)")
        print(f"  - [链接描述2](https://example2.com)")
        return

    # 解析任务文件
    try:
        task_name, urls = parse_task_markdown(task_path)
    except Exception as e:
        print(f"{Fore.RED}解析任务文件失败: {e}{Style.RESET_ALL}")
        return

    # 使用命令行提供的名称覆盖
    if name:
        task_name = name

    # 检查是否有URL
    if not urls:
        print(f"{Fore.YELLOW}任务文件中没有找到有效的URL链接{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}=== 从任务文件爬取 ==={Style.RESET_ALL}")
    print(f"文件: {task_path}")
    print(f"任务: {task_name}")
    print(f"链接: {len(urls)} 个\n")

    # 显示找到的链接
    print(f"{Fore.GREEN}找到的链接:{Style.RESET_ALL}")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
    print()

    # 确定输出模式
    if not separate and not together and not both:
        both = True

    # 执行爬取
    _execute_fetch(ctx, urls, task_name, reader, separate, together, both)


@fetch_cmd.command(name="pipe")
@click.option("-n", "--name", required=True, help="任务名称")
@click.option("-r", "--reader", default="jina", help="爬取服务商")
@click.option("-s", "--separate", is_flag=True, help="每个网页保存为单独文件")
@click.option("-t", "--together", is_flag=True, help="所有网页合并为一个文件")
@click.option("-st", "both", is_flag=True, help="同时生成单独文件和合并文件")
@pass_context
def fetch_pipe(ctx, name, reader, separate, together, both):
    """从标准输入读取URL并爬取

    示例:
        echo "https://example.com" | webmdai fetch pipe -n mytask
        cat urls.txt | webmdai fetch pipe -n mytask -st
    """
    import sys

    # 从stdin读取URL
    urls = []
    print(f"{Fore.CYAN}=== 从管道读取URL ==={Style.RESET_ALL}")
    print("提示: 每行输入一个URL，输入完成后按Ctrl+D(Unix)或Ctrl+Z+Enter(Windows)\n")

    for line in sys.stdin:
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)

    if not urls:
        print(f"{Fore.YELLOW}没有从管道读取到URL{Style.RESET_ALL}")
        return

    print(f"读取到 {len(urls)} 个URL\n")

    # 确定输出模式
    if not separate and not together and not both:
        both = True

    # 执行爬取
    _execute_fetch(ctx, urls, name, reader, separate, together, both)


def _execute_fetch(ctx, urls, task_name, reader_name, separate, together, both):
    """执行爬取操作"""
    print(f"\n{Fore.CYAN}开始爬取...{Style.RESET_ALL}")

    # 获取爬取配置
    timeout = ctx.config.get("fetch.timeout", 30)
    retry_times = ctx.config.get("fetch.retry_times", 3)
    delay = ctx.config.get("fetch.delay", 1.0)
    jina_api_key = ctx.config.get("fetch.jina_api_key")

    # 创建Fetcher
    try:
        reader_kwargs = {
            "timeout": timeout,
            "retry_times": retry_times,
        }
        # 如果是jina reader且有api key，传递它
        if reader_name == "jina" and jina_api_key:
            reader_kwargs["api_key"] = jina_api_key
            print(f"{Fore.GREEN}使用Jina API Key进行认证{Style.RESET_ALL}")

        fetcher = Fetcher(reader_name, delay=delay, **reader_kwargs)
        print(f"{Fore.CYAN}爬取间隔: {delay}秒{Style.RESET_ALL}")
    except ValueError as e:
        print(f"{Fore.RED}{e}{Style.RESET_ALL}")
        return

    # 爬取
    results = fetcher.fetch_multiple(urls)

    # 统计
    success_count = sum(1 for r in results if r.success)
    print(f"\n{Fore.GREEN}成功: {success_count}/{len(urls)}{Style.RESET_ALL}")

    if success_count == 0:
        print(f"{Fore.RED}所有爬取都失败了{Style.RESET_ALL}")
        return

    # 创建任务目录
    task_dir = create_task_directory(Path.cwd(), task_name)
    print(f"{Fore.CYAN}输出目录: {task_dir}{Style.RESET_ALL}\n")

    # 保存结果
    saved_files = []

    # 单独文件模式
    if separate or both:
        for i, result in enumerate(results, 1):
            if not result.success:
                continue

            # 生成文件名
            title = result.title or f"page_{i}"
            filename = (
                f"{sanitize_filename(task_name)}_{i}_{sanitize_filename(title)}.md"
            )
            filepath = get_unique_filename(task_dir, filename)

            # 保存
            content = result.markdown
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            saved_files.append(filepath)
            print(f"  保存: {filepath.name}")

    # 合并文件模式
    if together or both:
        # 合并内容
        merged_content = []
        for i, result in enumerate(results, 1):
            if result.success:
                if i > 1:
                    merged_content.append("\n\n---\n\n")
                merged_content.append(result.markdown)

        # 保存
        merged_filename = f"{sanitize_filename(task_name)}_合并.md"
        merged_path = task_dir / merged_filename

        with open(merged_path, "w", encoding="utf-8") as f:
            f.write("".join(merged_content))

        saved_files.append(merged_path)
        print(f"  保存合并文件: {merged_path.name}")

    print(f"\n{Fore.GREEN}完成！共保存 {len(saved_files)} 个文件{Style.RESET_ALL}")


# ========== Deal 命令 ==========


@cli.group(name="deal")
def deal_cmd():
    """文本处理"""
    pass


@deal_cmd.command(name="interactive")
@click.option("-d", "--directory", default=".", help="工作目录")
@click.option("--no-git", is_flag=True, help="禁用Git自动管理")
@pass_context
def deal_interactive(ctx, directory, no_git):
    """交互式文本处理"""
    print(f"{Fore.CYAN}=== 文本处理 (交互模式) ==={Style.RESET_ALL}\n")

    # 验证目录
    is_valid, error = validate_directory(directory)
    if not is_valid:
        print(f"{Fore.RED}{error}{Style.RESET_ALL}")
        return

    work_dir = Path(directory).resolve()
    print(f"工作目录: {work_dir}\n")

    # 初始化Git
    git = GitHandler(work_dir, enabled=not no_git)
    if git.is_git_repo():
        print(f"{Fore.GREEN}{git.get_status_summary()}{Style.RESET_ALL}\n")

    # 选择模式
    print(f"{Fore.YELLOW}选择处理模式:{Style.RESET_ALL}")
    print("  1. 普通文本模式")
    print("  2. 正则表达式模式")

    while True:
        choice = input("\n选择 (1/2): ").strip()
        if choice in ["1", "2"]:
            use_regex = choice == "2"
            break
        print(f"{Fore.RED}无效选择{Style.RESET_ALL}")

    # 输入查找内容
    print(f"\n{Fore.YELLOW}输入要查找的内容:{Style.RESET_ALL}")
    find = input("> ").strip()

    if use_regex:
        is_valid, error = validate_regex_pattern(find)
        if not is_valid:
            print(f"{Fore.RED}{error}{Style.RESET_ALL}")
            return

    if not find:
        print(f"{Fore.RED}查找内容不能为空{Style.RESET_ALL}")
        return

    # 输入替换内容
    print(f"\n{Fore.YELLOW}输入替换内容 (留空表示删除):{Style.RESET_ALL}")
    replace = input("> ").strip()

    # 初始化处理器
    processor = TextProcessor(work_dir)
    files = processor.scan_files()

    if not files:
        print(f"{Fore.YELLOW}目录中没有Markdown文件{Style.RESET_ALL}")
        return

    print(f"\n找到 {len(files)} 个Markdown文件\n")

    # 预览
    if use_regex:
        previews = processor.preview_regex_replace(find, replace, files)
    else:
        previews = processor.preview_text_replace(find, replace, files)
        previews = [(p[0], p[1], p[2], p[1].count(find)) for p in previews]

    # 确认执行
    if not interactive_preview_confirm(processor, previews, None):
        print(f"\n{Fore.YELLOW}操作已取消{Style.RESET_ALL}")
        return

    # Git备份
    if git.enabled:
        operation = "正则替换" if use_regex else "文本替换"
        git.create_backup_commit(operation, find, replace)
        print(f"{Fore.GREEN}已创建Git备份{Style.RESET_ALL}\n")

    # 执行
    if use_regex:
        results = processor.execute_regex_replace(find, replace, files)
    else:
        results = processor.execute_text_replace(find, replace, files)

    # 统计
    stats = processor.get_statistics(results)
    print(f"\n{Fore.GREEN}处理完成:{Style.RESET_ALL}")
    print(f"  总文件数: {stats['total_files']}")
    print(f"  成功: {stats['success_files']}")
    print(f"  失败: {stats['failed_files']}")
    print(f"  修改处数: {stats['total_changes']}")
    print(f"  受影响文件: {stats['files_with_changes']}")


@deal_cmd.command(name="batch")
@click.option("-d", "--directory", default=".", help="工作目录")
@click.option("--text", "mode", flag_value="text", help="普通文本模式")
@click.option("--re", "mode", flag_value="regex", help="正则表达式模式")
@click.option("-f", "--find", required=True, help="查找内容")
@click.option("-r", "--replace", default="", help="替换内容")
@click.option("--preview", is_flag=True, help="仅预览不执行")
@click.option("--no-git", is_flag=True, help="禁用Git自动管理")
@pass_context
def deal_batch(ctx, directory, mode, find, replace, preview, no_git):
    """批量文本处理"""
    # 验证目录
    is_valid, error = validate_directory(directory)
    if not is_valid:
        print(f"{Fore.RED}{error}{Style.RESET_ALL}")
        return

    work_dir = Path(directory).resolve()
    use_regex = mode == "regex"

    # 验证查找内容
    if use_regex:
        is_valid, error = validate_regex_pattern(find)
        if not is_valid:
            print(f"{Fore.RED}{error}{Style.RESET_ALL}")
            return

    # 初始化
    processor = TextProcessor(work_dir)
    files = processor.scan_files()

    if not files:
        print(f"{Fore.YELLOW}目录中没有Markdown文件{Style.RESET_ALL}")
        return

    # Git
    git = GitHandler(work_dir, enabled=not no_git)

    # 预览
    if use_regex:
        previews = processor.preview_regex_replace(find, replace, files)
    else:
        previews = processor.preview_text_replace(find, replace, files)
        previews = [(p[0], p[1], p[2], p[1].count(find)) for p in previews]

    processor.print_preview(previews)

    if preview:
        return

    # 确认
    total_matches = sum(item[3] for item in previews if len(item) > 3)
    if total_matches == 0:
        print(f"{Fore.YELLOW}没有找到匹配项{Style.RESET_ALL}")
        return

    # Git备份
    if git.enabled:
        operation = "正则替换" if use_regex else "文本替换"
        git.create_backup_commit(operation, find, replace)

    # 执行
    if use_regex:
        results = processor.execute_regex_replace(find, replace, files)
    else:
        results = processor.execute_text_replace(find, replace, files)

    stats = processor.get_statistics(results)
    print(f"\n{Fore.GREEN}处理完成: {stats['total_changes']} 处修改{Style.RESET_ALL}")


@deal_cmd.command(name="pipe")
@click.option("--text", "mode", flag_value="text", help="普通文本模式（默认）")
@click.option("--re", "mode", flag_value="regex", help="正则表达式模式")
@click.option("-f", "--find", required=True, help="查找内容")
@click.option("-r", "--replace", default="", help="替换内容（留空表示删除）")
@click.option("-o", "--output", help="输出文件路径（默认输出到stdout）")
def deal_pipe(mode, find, replace, output):
    """从标准输入读取内容进行文本替换

    示例:
        echo "hello world" | webmdai deal pipe -f "world" -r "Python"
        cat article.md | webmdai deal pipe -f "广告文字" --re -o cleaned.md
        echo "123abc" | webmdai deal pipe --re -f "\\d+" -r "[数字]"
    """
    import sys
    import re

    # 从stdin读取内容
    print(f"{Fore.CYAN}=== 从管道读取内容 ==={Style.RESET_ALL}")
    print("提示: 输入内容，完成后按Ctrl+D(Unix)或Ctrl+Z+Enter(Windows)\n")

    content = sys.stdin.read()

    if not content:
        print(f"{Fore.YELLOW}没有从管道读取到内容{Style.RESET_ALL}")
        return

    print(f"读取到 {len(content)} 字符")
    print(f"模式: {'正则表达式' if mode == 'regex' else '普通文本'}")
    print(f"查找: {find}")
    print(f"替换: {replace if replace else '(删除)'}\n")

    # 执行替换
    try:
        if mode == "regex":
            new_content = re.sub(find, replace, content, flags=re.MULTILINE)
            count = len(re.findall(find, content, flags=re.MULTILINE))
        else:
            new_content = content.replace(find, replace)
            count = content.count(find)

        if output:
            # 保存到文件
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(
                f"{Fore.GREEN}结果已保存: {output_path} ({count} 处修改){Style.RESET_ALL}"
            )
        else:
            # 输出到stdout
            print(f"{Fore.GREEN}=== 处理结果 ({count} 处修改) ==={Style.RESET_ALL}\n")
            print(new_content)
    except re.error as e:
        print(f"{Fore.RED}正则表达式错误: {e}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}处理失败: {e}{Style.RESET_ALL}")


# ========== LLM 命令 ==========


@cli.group(name="llm")
def llm_cmd():
    """LLM处理"""
    pass


@llm_cmd.command(name="interactive")
@click.option("-d", "--directory", default=".", help="工作目录")
@click.option("-m", "--model", help="模型别名")
@click.option("-t", "--task", help="任务类型")
@click.option("--separate", is_flag=True, help="分批处理")
@click.option("--all", "merge", is_flag=True, help="合并处理")
@click.option("-p", "--prompt", help="自定义提示词")
@click.option("-o", "--output", help="输出目录")
@pass_context
def llm_interactive(ctx, directory, model, task, separate, merge, prompt, output):
    """交互式LLM处理"""
    print(f"{Fore.CYAN}=== LLM处理 (交互模式) ==={Style.RESET_ALL}\n")

    # 验证目录
    work_dir = Path(directory).resolve()
    if not work_dir.exists():
        print(f"{Fore.RED}目录不存在: {work_dir}{Style.RESET_ALL}")
        return

    # 获取模型配置
    if model:
        model_config = ctx.config.get_model(model)
    else:
        model_config = ctx.config.get_default_model()

    if not model_config:
        print(
            f"{Fore.RED}未配置模型，请先使用 'webmdai model add' 添加模型{Style.RESET_ALL}"
        )
        return

    print(f"使用模型: {model or ctx.config.config.get('default_model')}\n")

    # 选择任务
    if prompt:
        # 使用自定义提示词
        task_obj = create_custom_task(prompt, "custom")
    elif task:
        # 使用预设任务
        task_obj = get_task(task)
        if not task_obj:
            print(f"{Fore.RED}未知任务: {task}{Style.RESET_ALL}")
            print(f"可用任务: {', '.join(list_all_tasks().keys())}")
            return
    else:
        # 交互选择
        print(f"{Fore.YELLOW}选择任务类型:{Style.RESET_ALL}")
        tasks = list_all_tasks()
        for i, (name, desc) in enumerate(tasks.items(), 1):
            print(f"  {i}. {name}: {desc}")
        print(f"  {len(tasks) + 1}. 自定义提示词")

        while True:
            choice = input("\n选择: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(tasks):
                    task_obj = get_task(list(tasks.keys())[idx])
                    break
                elif idx == len(tasks):
                    custom_prompt = input(
                        "\n输入自定义提示词 (使用 {content} 作为内容占位符):\n> "
                    )
                    task_obj = create_custom_task(custom_prompt, "custom")
                    break
            except ValueError:
                pass
            print(f"{Fore.RED}无效选择{Style.RESET_ALL}")

    print(f"\n任务: {task_obj.name} - {task_obj.description}\n")

    # 选择处理模式
    if not separate and not merge:
        print(f"{Fore.YELLOW}选择处理模式:{Style.RESET_ALL}")
        print("  1. 分别处理每个文件")
        print("  2. 合并所有文件处理")

        while True:
            choice = input("\n选择 (1/2): ").strip()
            if choice == "1":
                separate = True
                break
            elif choice == "2":
                merge = True
                break
            print(f"{Fore.RED}无效选择{Style.RESET_ALL}")

    # 确定输出目录
    if output:
        output_dir = Path(output)
    else:
        output_dir = work_dir / f"llm_{task_obj.output_suffix}"

    # 创建LLM处理器
    handler = create_llm_handler_from_config(model_config, output_dir)

    # 执行处理
    print(f"\n{Fore.CYAN}开始处理...{Style.RESET_ALL}\n")

    try:
        if separate:
            output_files = handler.process_files_separate(
                work_dir, task_obj, output_dir
            )
            print(
                f"\n{Fore.GREEN}完成！生成 {len(output_files)} 个文件{Style.RESET_ALL}"
            )
        else:
            output_path = handler.process_files_together(
                work_dir, task_obj, output_dir / f"merged_{task_obj.output_suffix}.md"
            )
            print(f"\n{Fore.GREEN}完成！输出: {output_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}处理失败: {e}{Style.RESET_ALL}")


@llm_cmd.command(name="batch")
@click.option("-d", "--directory", default=".", help="工作目录")
@click.option("-m", "--model", help="模型别名")
@click.option("-t", "--task", required=True, help="任务类型")
@click.option("--separate", is_flag=True, help="分批处理")
@click.option("--all", "merge", is_flag=True, help="合并处理")
@click.option("-p", "--prompt", help="自定义提示词（覆盖任务）")
@click.option("-o", "--output", help="输出目录")
@pass_context
def llm_batch(ctx, directory, model, task, separate, merge, prompt, output):
    """批量LLM处理"""
    # 验证目录
    work_dir = Path(directory).resolve()
    if not work_dir.exists():
        print(f"{Fore.RED}目录不存在: {work_dir}{Style.RESET_ALL}")
        return

    # 获取模型配置
    if model:
        model_config = ctx.config.get_model(model)
    else:
        model_config = ctx.config.get_default_model()

    if not model_config:
        print(f"{Fore.RED}未配置模型{Style.RESET_ALL}")
        return

    # 获取任务
    if prompt:
        task_obj = create_custom_task(prompt, "custom")
    else:
        task_obj = get_task(task)
        if not task_obj:
            print(f"{Fore.RED}未知任务: {task}{Style.RESET_ALL}")
            return

    # 确定输出目录
    if output:
        output_dir = Path(output)
    else:
        output_dir = work_dir / f"llm_{task_obj.output_suffix}"

    # 默认合并处理
    if not separate and not merge:
        merge = True

    # 创建处理器
    handler = create_llm_handler_from_config(model_config, output_dir)

    # 执行
    try:
        if separate:
            output_files = handler.process_files_separate(
                work_dir, task_obj, output_dir
            )
            print(f"{Fore.GREEN}完成！生成 {len(output_files)} 个文件{Style.RESET_ALL}")
        else:
            output_path = handler.process_files_together(
                work_dir, task_obj, output_dir / f"merged_{task_obj.output_suffix}.md"
            )
            print(f"{Fore.GREEN}完成！输出: {output_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}处理失败: {e}{Style.RESET_ALL}")


@llm_cmd.command(name="pipe")
@click.option("-m", "--model", help="模型别名（默认使用默认模型）")
@click.option("-t", "--task", help="任务类型（translate/summarize/explain/abstract）")
@click.option("-p", "--prompt", help="自定义提示词（覆盖任务类型）")
@click.option("-o", "--output", help="输出文件路径（默认输出到stdout）")
@pass_context
def llm_pipe(ctx, model, task, prompt, output):
    """从标准输入读取内容并进行LLM处理

    示例:
        echo "要翻译的内容" | webmdai llm pipe -t translate
        cat article.md | webmdai llm pipe -t summarize -o summary.md
        echo "解释这段代码" | webmdai llm pipe -p "请解释这段代码：{content}"
    """
    import sys

    # 从stdin读取内容
    print(f"{Fore.CYAN}=== 从管道读取内容 ==={Style.RESET_ALL}")
    print("提示: 输入内容，完成后按Ctrl+D(Unix)或Ctrl+Z+Enter(Windows)\n")

    content = sys.stdin.read()

    if not content.strip():
        print(f"{Fore.YELLOW}没有从管道读取到内容{Style.RESET_ALL}")
        return

    print(f"读取到 {len(content)} 字符\n")

    # 获取模型配置
    if model:
        model_config = ctx.config.get_model(model)
    else:
        model_config = ctx.config.get_default_model()

    if not model_config:
        print(
            f"{Fore.RED}未配置模型，请先使用 'webmdai model add' 添加模型{Style.RESET_ALL}"
        )
        return

    # 获取任务
    if prompt:
        task_obj = create_custom_task(prompt, "custom")
        print(f"任务: 自定义提示词")
    elif task:
        task_obj = get_task(task)
        if not task_obj:
            print(f"{Fore.RED}未知任务: {task}{Style.RESET_ALL}")
            print(f"可用任务: {', '.join(list_all_tasks().keys())}")
            return
        print(f"任务: {task_obj.name} - {task_obj.description}")
    else:
        print(f"{Fore.RED}请指定任务类型(-t)或自定义提示词(-p){Style.RESET_ALL}")
        return

    # 创建处理器
    from .modules.llm_handler import create_llm_handler_from_config

    handler = create_llm_handler_from_config(model_config, None)

    # 处理
    try:
        print(f"\n{Fore.CYAN}正在处理...{Style.RESET_ALL}\n")
        result = handler.client.process_content(content, task_obj)

        if output:
            # 保存到文件
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"{Fore.GREEN}结果已保存: {output_path}{Style.RESET_ALL}")
        else:
            # 输出到stdout
            print(f"{Fore.GREEN}=== 处理结果 ==={Style.RESET_ALL}\n")
            print(result)
    except Exception as e:
        print(f"{Fore.RED}处理失败: {e}{Style.RESET_ALL}")


# ========== Model 命令 ==========


@cli.group(name="model")
def model_cmd():
    """模型管理"""
    pass


@model_cmd.command(name="list")
@pass_context
def model_list(ctx):
    """列出所有已配置模型"""
    print(f"{Fore.CYAN}=== 已配置模型 ==={Style.RESET_ALL}\n")

    models = ctx.config.list_models()
    default = ctx.config.config.get("default_model")

    if not models:
        print(f"{Fore.YELLOW}没有配置任何模型{Style.RESET_ALL}")
        print(f"使用 'webmdai model add' 添加模型")
        return

    for name, config in models.items():
        marker = f" {Fore.GREEN}[默认]{Style.RESET_ALL}" if name == default else ""
        print(f"{Fore.YELLOW}{name}{Style.RESET_ALL}{marker}")
        print(f"  端点: {config['endpoint']}")
        print(f"  模型: {config['model']}")
        print(f"  密钥: {'*' * 8}")
        print()


@model_cmd.command(name="add")
@click.option("--name", required=True, help="模型别名")
@click.option("--endpoint", required=True, help="API端点")
@click.option("--model", "model_name", required=True, help="模型名称")
@click.option(
    "--key",
    required=False,
    help="API密钥（如不提供，会自动查找相同端点的现有模型复用密钥）",
)
@pass_context
def model_add(ctx, name, endpoint, model_name, key):
    """添加新模型

    示例:
        # 添加新模型并提供密钥
        webmdai model add --name gpt4 --endpoint https://api.openai.com/v1 --model gpt-4 --key sk-xxx

        # 添加同端点的新模型，自动复用密钥
        webmdai model add --name gpt3 --endpoint https://api.openai.com/v1 --model gpt-3.5
    """
    from .utils.validators import validate_model_config

    # 如果未提供密钥，尝试查找相同端点的现有模型复用密钥
    if not key:
        print(
            f"{Fore.YELLOW}未提供密钥，尝试查找相同端点的现有模型...{Style.RESET_ALL}"
        )

        existing_models = ctx.config.list_models()
        reused_key = None
        reused_model_name = None

        for existing_name, existing_config in existing_models.items():
            if existing_config.get("endpoint") == endpoint:
                reused_key = existing_config.get("key")
                reused_model_name = existing_name
                break

        if reused_key:
            key = reused_key
            print(
                f"{Fore.GREEN}已复用模型 '{reused_model_name}' 的密钥{Style.RESET_ALL}"
            )
        else:
            print(
                f"{Fore.RED}错误: 未找到相同端点的现有模型，请提供 --key 参数{Style.RESET_ALL}"
            )
            print(
                f"{Fore.YELLOW}提示: 使用 'webmdai model list' 查看已配置的模型{Style.RESET_ALL}"
            )
            return

    is_valid, error = validate_model_config(endpoint, model_name, key)
    if not is_valid:
        print(f"{Fore.RED}{error}{Style.RESET_ALL}")
        return

    ctx.config.add_model(name, endpoint, model_name, key)
    print(f"{Fore.GREEN}模型 '{name}' 已添加{Style.RESET_ALL}")

    # 如果是第一个模型，设为默认
    if len(ctx.config.list_models()) == 1:
        ctx.config.set_default_model(name)
        print(f"{Fore.GREEN}已设为默认模型{Style.RESET_ALL}")


@model_cmd.command(name="remove")
@click.argument("name")
@pass_context
def model_remove(ctx, name):
    """删除模型"""
    if ctx.config.remove_model(name):
        print(f"{Fore.GREEN}模型 '{name}' 已删除{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}模型 '{name}' 不存在{Style.RESET_ALL}")


@model_cmd.command(name="set-default")
@click.argument("name")
@pass_context
def model_set_default(ctx, name):
    """设置默认模型"""
    if ctx.config.set_default_model(name):
        print(f"{Fore.GREEN}默认模型已设为 '{name}'{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}模型 '{name}' 不存在{Style.RESET_ALL}")


# ========== Workflow 命令 ==========


@cli.group(name="workflow")
def workflow_cmd():
    """工作流管理 - 自动化多阶段处理管道"""
    pass


@workflow_cmd.command(name="run")
@click.argument("workflow_file", required=False, default="workflow.yaml")
@click.option(
    "-d", "--working-dir", help="工作/产物目录 (默认: workflow.yaml 所在目录)"
)
@click.option("-v", "--variable", multiple=True, help="设置变量 (key=value)")
@pass_context
def workflow_run(ctx, workflow_file, working_dir, variable):
    """运行工作流配置文件

    WORKFLOW_FILE: 工作流配置文件路径 (默认: workflow.yaml)
                   支持相对路径或绝对路径

    示例:
        webmdai workflow run                    # 运行当前目录的 workflow.yaml
        webmdai workflow run myproject/workflow.yaml  # 自动设置工作目录为 myproject/
        webmdai workflow run -d ./output        # 指定产物输出目录
    """
    from pathlib import Path
    import yaml

    from .models.workflow import (
        WorkflowConfig,
        StageConfig,
        StageType,
        validate_workflow_config,
    )
    from .modules.workflow_engine import WorkflowEngine

    # 解析工作流文件路径
    workflow_path = Path(workflow_file)
    if not workflow_path.is_absolute():
        workflow_path = Path.cwd() / workflow_path
    workflow_path = workflow_path.resolve()

    # 智能错误提示：如果文件不存在，搜索可能的工作流文件
    if not workflow_path.exists():
        print(f"{Fore.RED}工作流文件不存在: {workflow_path}{Style.RESET_ALL}")

        # 搜索可能的工作流文件（只在当前目录及其子目录中搜索）
        try:
            candidates = list(Path(".").rglob("workflow*.yaml")) + list(
                Path(".").rglob("workflow*.yml")
            )
            # 过滤掉__pycache__等目录中的文件
            candidates = [c for c in candidates if "__pycache__" not in str(c)]
        except Exception:
            candidates = []

        if candidates:
            print(f"\n{Fore.YELLOW}是否想用这些文件？{Style.RESET_ALL}")
            for i, c in enumerate(candidates[:5], 1):
                try:
                    rel_path = c.relative_to(Path.cwd())
                    print(f"  {i}. {rel_path}")
                except ValueError:
                    print(f"  {i}. {c}")
            print(
                f"\n{Fore.CYAN}提示: 运行 'webmdai workflow run <文件路径>'{Style.RESET_ALL}"
            )
        else:
            print(
                f"\n{Fore.YELLOW}使用 'webmdai workflow init' 创建示例工作流{Style.RESET_ALL}"
            )
        return

    # 自动推断工作目录：使用 workflow.yaml 所在目录
    if working_dir:
        work_dir = Path(working_dir).resolve()
    else:
        work_dir = workflow_path.parent

    print(f"{Fore.CYAN}工作流: {workflow_path.name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}工作目录: {work_dir}{Style.RESET_ALL}\n")

    # 解析变量
    variables = {}
    for var in variable:
        if "=" in var:
            key, value = var.split("=", 1)
            variables[key] = value

    # 加载工作流配置
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

        # 验证配置完整性
        if config_dict is None:
            print(f"{Fore.RED}工作流文件为空或格式错误{Style.RESET_ALL}")
            return

        from .models.workflow import validate_workflow_config, WorkflowValidationError

        try:
            validate_workflow_config(config_dict)
        except WorkflowValidationError as e:
            print(f"{Fore.RED}配置验证失败: {e}{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}配置文件: {workflow_path}{Style.RESET_ALL}")
            return

        # 构建配置对象
        stages = []
        for s in config_dict.get("stages", []):
            stage = StageConfig(
                name=s["name"],
                type=StageType(s["type"]),
                enabled=s.get("enabled", True),
                on_error=s.get("on_error", "stop"),
                params=s.get("params", {}),
            )
            stages.append(stage)

        config = WorkflowConfig(
            name=config_dict.get("name", "未命名工作流"),
            description=config_dict.get("description"),
            version=config_dict.get("version", "1.0"),
            working_dir=str(work_dir),
            stages=stages,
            variables={**config_dict.get("variables", {}), **variables},
            settings=config_dict.get("settings", {}),
        )

    except Exception as e:
        print(f"{Fore.RED}加载工作流配置失败: {e}{Style.RESET_ALL}")
        return

    # 运行工作流
    engine = WorkflowEngine(config, work_dir)
    success = engine.run()

    sys.exit(0 if success else 1)


@workflow_cmd.command(name="init")
@click.argument("template", required=False, default="translate-novel")
@click.option("-o", "--output", default="workflow.yaml", help="输出文件名")
@pass_context
def workflow_init(ctx, template, output):
    """初始化工作流配置文件

    TEMPLATE: 模板名称 (translate-novel, summarize-articles, custom-pipeline)
    """
    from pathlib import Path
    from .models.workflow import get_workflow_template, list_workflow_templates

    tmpl = get_workflow_template(template)
    if not tmpl:
        print(f"{Fore.RED}未知模板: {template}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}可用模板:{Style.RESET_ALL}")
        for name, desc in list_workflow_templates().items():
            print(f"  - {name}: {desc}")
        return

    output_path = Path(output)
    if output_path.exists():
        confirm = input(f"文件 {output} 已存在，覆盖吗? (y/N): ")
        if confirm.lower() != "y":
            print("已取消")
            return

    # 生成YAML
    import yaml

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(tmpl, f, allow_unicode=True, sort_keys=False)

    print(f"{Fore.GREEN}工作流模板已创建: {output_path}{Style.RESET_ALL}")
    print(f"模板: {tmpl['name']}")
    print(f"描述: {tmpl['description']}")
    print(f"\n{Fore.CYAN}编辑 {output} 自定义你的工作流，然后运行:{Style.RESET_ALL}")
    print(f"  webmdai workflow run {output}")


@workflow_cmd.command(name="templates")
def workflow_templates():
    """列出可用的工作流模板"""
    from .models.workflow import list_workflow_templates

    print(f"{Fore.CYAN}=== 可用工作流模板 ==={Style.RESET_ALL}\n")

    for name, desc in list_workflow_templates().items():
        print(f"{Fore.YELLOW}{name}{Style.RESET_ALL}")
        print(f"  {desc}")
        print()


@workflow_cmd.command(name="wizard")
@pass_context
def workflow_wizard(ctx):
    """交互式向导 - 引导你创建工作流配置"""
    import yaml
    from pathlib import Path
    from .models.workflow import get_workflow_template, WORKFLOW_TEMPLATES

    print(f"{Fore.CYAN}=== WebMDAI 工作流向导 ==={Style.RESET_ALL}\n")
    print("我会引导你创建工作流配置文件。\n")

    # 步骤1: 选择使用场景
    print(f"{Fore.YELLOW}你想做什么？{Style.RESET_ALL}")
    print("  1. 翻译网页内容（如轻小说、文章）")
    print("  2. 生成文章摘要")
    print("  3. 创建自定义工作流")

    choice = ""
    while choice not in ["1", "2", "3"]:
        choice = input(f"\n选择 (1-3): ").strip()
        if choice not in ["1", "2", "3"]:
            print(f"{Fore.RED}无效选择，请输入 1、2 或 3{Style.RESET_ALL}")

    # 根据选择设置模板和任务
    if choice == "1":
        template_name = "translate-novel"
        task_type = "translate"
        default_output = "workflow.yaml"
    elif choice == "2":
        template_name = "summarize-articles"
        task_type = "summarize"
        default_output = "workflow.yaml"
    else:
        template_name = "custom-pipeline"
        task_type = "custom"
        default_output = "workflow.yaml"

    # 步骤2: 输入URL或选择已有任务文件
    print(f"\n{Fore.YELLOW}输入你的网页链接:{Style.RESET_ALL}")
    print("  (每行一个链接，输入空行结束)")

    urls = []
    while True:
        url = input("> ").strip()
        if not url:
            break
        is_valid, error = validate_url(url)
        if is_valid:
            urls.append(url)
            print(f"  {Fore.GREEN}✓{Style.RESET_ALL} 已添加")
        else:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {error}")

    # 步骤3: 任务名称（用于文件夹名）
    print(f"\n{Fore.YELLOW}输入任务名称:{Style.RESET_ALL}")
    print("  (这将作为输出文件夹的名称)")

    task_name = ""
    while not task_name:
        task_name = input("> ").strip()
        if not task_name:
            print(f"{Fore.RED}任务名称不能为空{Style.RESET_ALL}")
        else:
            is_valid, error = validate_task_name(task_name)
            if not is_valid:
                print(f"{Fore.RED}{error}{Style.RESET_ALL}")
                task_name = ""

    # 步骤4: 选择输出语言（仅翻译场景）
    if choice == "1":
        print(f"\n{Fore.YELLOW}选择输出语言:{Style.RESET_ALL}")
        print("  1. 简体中文")
        print("  2. 繁体中文")
        print("  3. English")
        print("  4. 其他")

        lang_choice = ""
        while lang_choice not in ["1", "2", "3", "4"]:
            lang_choice = input("\n选择 (1-4): ").strip()

        languages = {"1": "简体中文", "2": "繁体中文", "3": "English", "4": "其他"}
        target_lang = languages[lang_choice]
    else:
        target_lang = None

    # 步骤5: 配置文件输出路径
    print(f"\n{Fore.YELLOW}配置文件输出路径:{Style.RESET_ALL}")
    output = input(f"  (默认: {default_output}): ").strip() or default_output

    output_path = Path(output)
    if output_path.exists():
        confirm = input(
            f"{Fore.YELLOW}文件 {output} 已存在，覆盖吗? (y/N): {Style.RESET_ALL}"
        )
        if confirm.lower() != "y":
            print("已取消")
            return

    # 创建TASK.md文件（如果有URL）
    task_md_path = (
        output_path.parent / "TASK.md"
        if output_path.parent != Path(".")
        else Path("TASK.md")
    )
    if urls and not task_md_path.exists():
        task_md_content = f"# {task_name}\n\n"
        task_md_content += "## 参考链接\n\n"
        for url in urls:
            task_md_content += f"- [{url}]({url})\n"

        with open(task_md_path, "w", encoding="utf-8") as f:
            f.write(task_md_content)
        print(f"\n{Fore.GREEN}✓{Style.RESET_ALL} 已创建任务文件: {task_md_path}")

    # 获取并自定义模板
    tmpl = get_workflow_template(template_name).copy()

    # 根据用户输入自定义模板
    tmpl["name"] = task_name
    if target_lang:
        tmpl["description"] = f"{task_name} - 翻译为{target_lang}"
    else:
        tmpl["description"] = f"{task_name}"

    # 如果用户提供了URL，修改fetch阶段的taskfile
    if urls and tmpl.get("stages"):
        for stage in tmpl["stages"]:
            if stage.get("type") == "fetch":
                stage["params"]["taskfile"] = str(task_md_path)
                break

    # 保存工作流配置
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(tmpl, f, allow_unicode=True, sort_keys=False)

    print(f"{Fore.GREEN}✓{Style.RESET_ALL} 已创建工作流配置: {output_path}")

    # 显示完成信息
    print(f"\n{Fore.CYAN}=== 准备就绪！==={Style.RESET_ALL}")
    print(f"\n下一步：")
    if output_path.parent != Path("."):
        print(f"  1. cd {output_path.parent}")
        print(f"  2. webmdai workflow run")
    else:
        print(f"  运行: webmdai workflow run")
    print(
        f"\n{Fore.YELLOW}提示: 编辑 {output_path} 可以自定义工作流配置{Style.RESET_ALL}"
    )


# ========== 帮助 ==========


def print_help():
    """打印帮助信息"""
    print(f"""
{Fore.CYAN}可用命令:{Style.RESET_ALL}
  /start  - 结束URL列表输入
  /exit   - 退出程序
  /help   - 显示帮助信息
""")


# ========== Path 命令 ==========


@cli.group(name="path")
def path_cmd():
    """路径工具 - 帮助理解和调试路径问题"""
    pass


@path_cmd.command(name="info")
@click.argument("path", default=".")
@click.option("-d", "--directory", default=None, help="指定工作目录")
@pass_context
def path_info(ctx, path, directory):
    """显示路径解析信息

    PATH: 要检查的路径（可以是相对路径或绝对路径）

    示例:
      webmdai path info workflow.yaml
      webmdai path info prompts/translate.txt -d /path/to/project
    """
    from pathlib import Path

    # 确定工作目录
    if directory:
        work_dir = Path(directory).resolve()
    else:
        work_dir = Path.cwd()

    input_path = Path(path)

    print(f"{Fore.CYAN}=== 路径解析信息 ==={Style.RESET_ALL}\n")

    # 显示输入
    print(f"{Fore.YELLOW}输入路径:{Style.RESET_ALL} {path}")
    print(f"{Fore.YELLOW}工作目录:{Style.RESET_ALL} {work_dir}")

    # 解析路径
    if input_path.is_absolute():
        resolved_path = input_path
        is_absolute = True
    else:
        resolved_path = work_dir / input_path
        is_absolute = False

    print(f"{Fore.YELLOW}解析路径:{Style.RESET_ALL} {resolved_path}")
    print()

    # 检查文件是否存在
    if resolved_path.exists():
        print(f"{Fore.GREEN}✓ 文件存在{Style.RESET_ALL}")
        if resolved_path.is_dir():
            print(f"  类型: 目录")
            print(f"  内容: {len(list(resolved_path.iterdir()))} 个项目")
        else:
            print(f"  类型: 文件")
            print(f"  大小: {resolved_path.stat().st_size} 字节")
    else:
        print(f"{Fore.RED}✗ 文件不存在{Style.RESET_ALL}")

        # 尝试找到类似的文件
        if resolved_path.parent.exists():
            similar = list(
                resolved_path.parent.glob(f"*{resolved_path.name.split('/')[-1]}*")
            )
            if similar:
                print(
                    f"\n{Fore.YELLOW}在 {resolved_path.parent} 找到类似文件:{Style.RESET_ALL}"
                )
                for f in similar[:5]:
                    print(f"  - {f.name}")

    # 对于工作流文件，显示更多信息
    if resolved_path.suffix in [".yaml", ".yml"]:
        if resolved_path.exists():
            print(f"\n{Fore.CYAN}=== 工作流文件信息 ==={Style.RESET_ALL}")
            try:
                import yaml

                with open(resolved_path, "r", encoding="utf-8") as f:
                    wf = yaml.safe_load(f)

                if wf:
                    print(f"工作流名称: {wf.get('name', '未命名')}")
                    print(f"描述: {wf.get('description', '无')}")
                    print(f"阶段数量: {len(wf.get('stages', []))}")

                    # 显示各阶段使用的文件路径
                    print(f"\n{Fore.CYAN}各阶段使用的相对路径:{Style.RESET_ALL}")
                    for stage in wf.get("stages", []):
                        stage_name = stage.get("name", "未命名")
                        stage_type = stage.get("type", "")
                        params = stage.get("params", {})

                        # 检查相关的相对路径
                        file_paths = []
                        for key in [
                            "taskfile",
                            "prompt_file",
                            "replacements_file",
                            "rules_file",
                            "file_pattern",
                        ]:
                            if key in params:
                                val = params[key]
                                if (
                                    val
                                    and not val.startswith("*")
                                    and not val.startswith("${")
                                ):
                                    if (
                                        isinstance(val, str)
                                        and not Path(val).is_absolute()
                                    ):
                                        file_paths.append(f"  {key}: {val}")

                        if file_paths:
                            print(f"\n  {stage_name} ({stage_type}):")
                            for fp in file_paths:
                                print(fp)

            except Exception as e:
                print(f"  {Fore.RED}无法解析YAML: {e}{Style.RESET_ALL}")


@path_cmd.command(name="check")
@click.argument("workflow_file", default="workflow.yaml")
@click.option("-d", "--directory", default=None, help="指定工作目录")
@pass_context
def path_check(ctx, workflow_file, directory):
    """检查工作流中所有路径的有效性

    WORKFLOW_FILE: 工作流配置文件路径

    示例:
      webmdai path check workflow.yaml
      webmdai path check my_workflow.yaml -d /path/to/project
    """
    from pathlib import Path
    import yaml

    # 确定工作目录
    if directory:
        work_dir = Path(directory).resolve()
    else:
        # 尝试找到workflow文件所在目录
        wf_path = Path(workflow_file)
        if not wf_path.is_absolute():
            wf_path = Path.cwd() / wf_path

        if wf_path and wf_path.is_file():
            work_dir = wf_path.parent
        else:
            work_dir = Path.cwd()

    print(f"{Fore.CYAN}=== 工作流路径检查 ==={Style.RESET_ALL}\n")
    print(f"工作流文件: {workflow_file}")
    print(f"工作目录: {work_dir}\n")

    # 加载工作流
    wf_full_path = (
        work_dir / workflow_file
        if not Path(workflow_file).is_absolute()
        else Path(workflow_file)
    )

    if not wf_full_path.exists():
        print(f"{Fore.RED}✗ 工作流文件不存在: {wf_full_path}{Style.RESET_ALL}")
        return

    try:
        with open(wf_full_path, "r", encoding="utf-8") as f:
            wf = yaml.safe_load(f)
    except Exception as e:
        print(f"{Fore.RED}✗ 无法读取工作流文件: {e}{Style.RESET_ALL}")
        return

    if not wf:
        print(f"{Fore.RED}✗ 工作流文件为空{Style.RESET_ALL}")
        return

    # 检查所有路径
    issues = []
    warnings = []

    for stage in wf.get("stages", []):
        stage_name = stage.get("name", "未命名")
        stage_type = stage.get("type", "")
        params = stage.get("params", {})

        # 需要检查的路径参数
        path_keys = {
            "taskfile": "任务文件",
            "prompt_file": "提示词文件",
            "replacements_file": "替换规则文件",
            "rules_file": "清理规则文件",
        }

        for key, desc in path_keys.items():
            if key in params:
                val = params[key]
                if val and isinstance(val, str):
                    if not val.startswith("*") and not val.startswith("${"):
                        if not Path(val).is_absolute():
                            # 相对路径，相对于工作目录
                            full_path = work_dir / val
                            if not full_path.exists():
                                issues.append(f"  {stage_name}: {desc} '{val}' 不存在")
                        else:
                            # 绝对路径
                            if not Path(val).exists():
                                issues.append(f"  {stage_name}: {desc} '{val}' 不存在")

    # 输出结果
    if not issues:
        print(f"{Fore.GREEN}✓ 所有路径检查通过！{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ 发现 {len(issues)} 个问题:{Style.RESET_ALL}")
        for issue in issues:
            print(issue)

    if warnings:
        print(f"\n{Fore.YELLOW}⚠ 警告:{Style.RESET_ALL}")
        for warning in warnings:
            print(warning)


@path_cmd.command(name="tree")
@click.argument("directory", default=".")
@pass_context
def path_tree(ctx, directory):
    """显示项目目录结构

    DIRECTORY: 要显示的目录（默认当前目录）

    示例:
      webmdai path tree
      webmdai path tree /path/to/project
    """
    from pathlib import Path

    dir_path = Path(directory)
    if not dir_path.is_absolute():
        dir_path = Path.cwd() / dir_path

    if not dir_path.exists():
        print(f"{Fore.RED}目录不存在: {dir_path}{Style.RESET_ALL}")
        return

    if not dir_path.is_dir():
        print(f"{Fore.RED}不是目录: {dir_path}{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}=== 目录结构: {dir_path} ==={Style.RESET_ALL}\n")

    def print_tree(path, prefix="", is_last=True):
        """递归打印目录树"""
        # 排除不需要显示的目录
        exclude_dirs = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".venv",
            "venv",
        }

        if path.is_file():
            # 只显示特定类型的文件
            if path.suffix in [".md", ".yaml", ".yml", ".txt", ".json", ".sh"]:
                connector = "└── " if is_last else "├── "
                print(f"{prefix}{connector}{path.name}")

        elif path.is_dir():
            if path.name in exclude_dirs:
                return

            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{path.name}/")

            # 获取子项
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                print(f"{prefix}    [权限不足]")
                return

            # 打印子项
            for i, item in enumerate(items):
                new_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(item, new_prefix, i == len(items) - 1)

    print_tree(dir_path)
    print(
        f"\n{Fore.GREEN}提示:{Style.RESET_ALL} 只显示 .md, .yaml, .yml, .txt, .json, .sh 文件"
    )


# ========== 主入口 ==========


def main():
    """主入口函数"""
    try:
        cli()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}已取消{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}错误: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
