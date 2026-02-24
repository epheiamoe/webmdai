#!/bin/bash
# WebMDAI 快速开始脚本
# 用法：bash 快速开始脚本.sh

echo "=== WebMDAI 快速开始 ==="
echo ""

# 1. 创建项目目录
PROJECT_NAME="my_webmdai_project"
if [ -d "$PROJECT_NAME" ]; then
    echo "⚠️  目录 $PROJECT_NAME 已存在，跳过创建"
else
    echo "1. 创建项目目录: $PROJECT_NAME"
    mkdir -p "$PROJECT_NAME"
fi

cd "$PROJECT_NAME" || exit 1

# 2. 创建任务文件
echo "2. 创建任务文件: TASK.md"
cat > TASK.md << 'EOF'
# 我的第一个WebMDAI任务

## 测试链接
- [示例页面](https://example.com)
- [Python官网](https://www.python.org)

## 说明
这是一个测试任务，实际使用时替换为你要处理的链接。
EOF

# 3. 创建提示词目录和文件
echo "3. 创建提示词文件: prompts/translate.txt"
mkdir -p prompts

cat > prompts/translate.txt << 'EOF'
请将以下内容翻译成简体中文，要求：
1. 保持原文意思准确
2. 语句通顺自然
3. 保留格式和结构

内容：
{content}

请直接输出翻译结果。
EOF

# 4. 创建工作流配置
echo "4. 创建工作流配置: workflow.yaml"
cat > workflow.yaml << 'EOF'
name: 我的第一个工作流
description: 测试WebMDAI基本功能

stages:
  - name: 爬取网页
    type: fetch
    params:
      source: taskfile
      taskfile: TASK.md
      reader: jina
      delay: 1.0
  
  - name: 翻译内容
    type: llm
    params:
      model: default
      prompt_file: prompts/translate.txt
      file_pattern: "*.md"
      output_suffix: "_zh"
EOF

# 5. 显示项目结构
echo ""
echo "=== 项目结构 ==="
echo "当前目录: $(pwd)"
echo ""
find . -type f -name "*.md" -o -name "*.yaml" -o -name "*.txt" | sort
echo ""

# 6. 运行说明
echo "=== 运行说明 ==="
echo "1. 确保已安装webmdai: pip install -e ."
echo "2. 配置LLM模型: webmdai model add ..."
echo "3. 运行工作流: webmdai workflow run workflow.yaml"
echo ""
echo "当前目录已准备好，可以直接运行！"
echo "命令: webmdai workflow run workflow.yaml"
echo ""

# 7. 创建进阶示例目录
echo "=== 进阶示例 ==="
echo "如需更多示例，请查看 doc_example/ 目录"
echo "包含："
echo "  - 单个网页翻译"
echo "  - 批量网页翻译" 
echo "  - 技术文档摘要"
echo "  - 轻小说完整流程"
echo "  - 自定义工作流"
echo ""