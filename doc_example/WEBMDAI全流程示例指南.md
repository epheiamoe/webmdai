# WebMDAI 全流程示例指南

> 从零基础到高级用法，一步一步教你使用webmdai

## 📋 目录
1. [基础概念](#基础概念)
2. [场景1：单个网页翻译](#场景1单个网页翻译)
3. [场景2：批量网页翻译](#场景2批量网页翻译)
4. [场景3：技术文档摘要](#场景3技术文档摘要)
5. [场景4：轻小说翻译完整流程](#场景4轻小说翻译完整流程)
6. [场景5：自定义工作流](#场景5自定义工作流)
7. [常见问题解答](#常见问题解答)

---

## 基础概念

### 核心文件说明
- **工作流文件** (`workflow.yaml`): 定义处理流程的配置文件
- **任务文件** (`TASK.md`): 包含要处理的网页链接
- **提示词文件** (`prompts/*.txt`): 告诉AI如何处理内容的指令
- **输出文件**: 处理完成后生成的文件

### 黄金规则：一切都在项目目录中
```
你的项目目录/
├── workflow.yaml    ← 工作流配置（核心）
├── TASK.md         ← 任务文件（链接列表）
├── prompts/        ← 提示词目录
│   └── *.txt      ← 各种提示词文件
└── （输出文件自动生成）
```

**重要**：所有文件都放在同一个目录下，相对路径才有效！

---

## 场景1：单个网页翻译

### 目标：翻译一个英文网页为中文

### 步骤1：创建项目目录
```bash
# 1. 创建项目目录并进入
mkdir my_first_translation
cd my_first_translation
```

### 步骤2：创建任务文件
```bash
# 2. 创建任务文件，包含要翻译的链接
cat > TASK.md << 'EOF'
# 单个网页翻译测试

## 要翻译的页面
- [Python教程](https://docs.python.org/3/tutorial/)
EOF
```

### 步骤3：创建提示词文件
```bash
# 3. 创建提示词目录和文件
mkdir -p prompts

cat > prompts/translate.txt << 'EOF'
请将以下英文技术文档翻译成简体中文，要求：
1. 保持技术术语的准确性
2. 语句通顺自然
3. 保留代码示例和格式
4. 专业名词首次出现时加注英文

内容：
{content}

请直接输出翻译结果。
EOF
```

### 步骤4：创建工作流配置
```bash
# 4. 创建工作流配置文件
cat > workflow.yaml << 'EOF'
name: 单个网页翻译
description: 翻译单个英文网页为中文

stages:
  # 阶段1：爬取网页
  - name: 爬取网页内容
    type: fetch
    params:
      source: taskfile      # 从任务文件读取链接
      taskfile: TASK.md     # 任务文件路径
      reader: jina          # 使用Jina Reader服务
      delay: 1.0            # 爬取间隔1秒
  
  # 阶段2：翻译内容
  - name: 翻译为中文
    type: llm
    params:
      model: default        # 使用默认配置的模型
      prompt_file: prompts/translate.txt  # 提示词文件
      file_pattern: "*.md"  # 处理所有.md文件
      output_suffix: "_zh"  # 输出文件后缀
EOF
```

### 步骤5：运行工作流
```bash
# 5. 运行工作流
webmdai workflow run workflow.yaml
```

### 步骤6：查看结果
```bash
# 6. 查看生成的文件
ls -la

# 你会看到类似这样的结构：
# 单个网页翻译/           ← 自动创建的输出目录
# ├── 单个网页翻译_1_Python Tutorial.md
# └── 单个网页翻译_合并.md
```

---

## 场景2：批量网页翻译

### 目标：批量翻译多个相关网页

### 项目结构
```bash
# 创建项目目录
mkdir batch_translation
cd batch_translation
```

### 创建批量任务文件
```bash
cat > TASK.md << 'EOF'
# Python官方文档翻译

## 基础教程章节
- [Python简介](https://docs.python.org/3/tutorial/introduction.html)
- [使用Python解释器](https://docs.python.org/3/tutorial/interpreter.html)
- [Python简介](https://docs.python.org/3/tutorial/introduction.html)
- [非正式介绍](https://docs.python.org/3/tutorial/appetite.html)

## 数据结构
- [列表](https://docs.python.org/3/tutorial/datastructures.html#more-on-lists)
- [元组和序列](https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences)
EOF
```

### 创建专业翻译提示词
```bash
mkdir -p prompts

cat > prompts/python_docs_translate.txt << 'EOF'
你是一位专业的Python技术文档翻译专家。请将以下Python官方文档翻译成简体中文。

## 翻译要求：
1. **技术准确性**：专业术语必须准确，参考Python官方中文术语表
2. **代码保留**：代码示例、函数名、变量名保持原样
3. **格式保持**：保留原有的标题层级、列表、代码块等格式
4. **一致性**：相同术语在整个文档中翻译一致
5. **可读性**：技术描述清晰易懂，避免生硬直译

## 特殊处理：
- `list` → 列表
- `tuple` → 元组  
- `dictionary` → 字典
- `function` → 函数
- `module` → 模块
- `package` → 包

## 内容：
{content}

请输出完整的翻译结果，不要添加额外说明。
EOF
```

### 创建工作流配置
```bash
cat > workflow.yaml << 'EOF'
name: Python文档批量翻译
description: 批量翻译Python官方文档章节

variables:
  project_name: "Python官方文档翻译"

stages:
  # 阶段1：批量爬取
  - name: 爬取所有章节
    type: fetch
    params:
      source: taskfile
      taskfile: TASK.md
      reader: jina
      delay: 1.5  # 稍微延长间隔，避免被限制
  
  # 阶段2：内容清理（可选，减少token消耗）
  - name: 清理网页内容
    type: clean
    params:
      file_pattern: "*.md"
      preset: "technical_docs"  # 使用技术文档预设规则
      output_suffix: "_cleaned"
  
  # 阶段3：专业翻译
  - name: 专业翻译
    type: llm
    params:
      model: default
      prompt_file: prompts/python_docs_translate.txt
      file_pattern: "*_cleaned_*.md"  # 处理清理后的文件
      output_suffix: "_zh"
      temperature: 0.3  # 较低温度，保持翻译一致性
  
  # 阶段4：合并所有章节
  - name: 合并文档
    type: merge
    params:
      file_pattern: "*_zh_*.md"
      sort_by: filename  # 按文件名排序
      output: "${project_name}_完整版.md"
      add_chapter_headers: true
      header: |
        # ${project_name}
        
        翻译时间: ${CURRENT_DATE}
        源文档: Python 3 Official Documentation
        
        ---
EOF
```

### 运行和查看
```bash
# 运行工作流
webmdai workflow run workflow.yaml

# 查看结果
ls -la "Python官方文档翻译_完整版.md"
```

---

## 场景3：技术文档摘要

### 目标：为技术文章生成结构化摘要

### 项目结构
```bash
mkdir tech_summary
cd tech_summary
```

### 创建任务文件
```bash
cat > TASK.md << 'EOF'
# 技术文章摘要

## AI相关文章
- [Transformer论文解读](https://arxiv.org/abs/1706.03762)
- [GPT技术原理](https://openai.com/research/gpt-4)
- [深度学习优化](https://distill.pub/2017/momentum/)

## 编程教程
- [Rust并发编程](https://doc.rust-lang.org/book/ch16-00-concurrency.html)
- [React Hooks指南](https://reactjs.org/docs/hooks-intro.html)
EOF
```

### 创建摘要提示词
```bash
mkdir -p prompts

cat > prompts/tech_summary.txt << 'EOF'
请为以下技术文档生成结构化摘要。

## 摘要要求：
### 1. 核心要点
- 用3-5个要点概括文档核心内容

### 2. 技术细节
- 关键算法或技术原理
- 重要实现细节

### 3. 应用场景
- 主要使用场景
- 解决的问题

### 4. 学习价值
- 对读者的主要价值
- 建议的先修知识

### 5. 相关资源
- 提到的参考文献或工具

## 格式要求：
- 使用中文
- 每个部分使用二级标题（##）
- 要点使用无序列表
- 保持专业性和准确性

## 内容：
{content}

请生成完整的结构化摘要。
EOF
```

### 创建工作流
```bash
cat > workflow.yaml << 'EOF'
name: 技术文档摘要生成
description: 为技术文章生成结构化摘要

stages:
  - name: 爬取技术文章
    type: fetch
    params:
      source: taskfile
      taskfile: TASK.md
      reader: jina
      separate: true  # 每个网页保存为单独文件
  
  - name: 生成摘要
    type: llm
    params:
      model: default
      prompt_file: prompts/tech_summary.txt
      file_pattern: "*.md"
      output_suffix: "_summary"
      temperature: 0.5
  
  - name: 创建摘要索引
    type: merge
    params:
      file_pattern: "*_summary_*.md"
      sort_by: filename
      output: "技术文章摘要索引.md"
      add_chapter_headers: true
      header: |
        # 技术文章摘要合集
        
        生成时间: ${CURRENT_DATE}
        文章数量: ${FILE_COUNT}
        
        ## 目录
        
EOF
```

### 运行命令
```bash
webmdai workflow run workflow.yaml
```

---

## 场景4：轻小说翻译完整流程

### 目标：完整的轻小说爬取、翻译、处理流程

### 项目结构
```bash
mkdir light_novel_translation
cd light_novel_translation
```

### 创建任务文件（小说章节链接）
```bash
cat > TASK.md << 'EOF'
# 《转生成为史莱姆》翻译

## 第一卷
- [第一章 转生](https://ncode.syosetu.com/n6316bn/1/)
- [第二章 魔物之森](https://ncode.syosetu.com/n6316bn/2/)
- [第三章 哥布林村落](https://ncode.syosetu.com/n6316bn/3/)
- [第四章 命名](https://ncode.syosetu.com/n6316bn/4/)
- [第五章 矮人王国](https://ncode.syosetu.com/n6316bn/5/)

## 说明
实际使用时替换为真实的小说链接
EOF
```

### 创建角色名称映射文件
```bash
cat > character_names.json << 'EOF'
{
  "リムル": "利姆露",
  "ヴェルドラ": "维鲁德拉",
  "シズ": "静",
  "ゴブタ": "哥布塔",
  "リグル": "利格鲁",
  "ミリム": "米莉姆",
  "シュナ": "朱菜",
  "ベニマル": "红丸",
  "ハクロウ": "黑曜",
  "ソウエイ": "苍影"
}
EOF
```

### 创建轻小说专用提示词
```bash
mkdir -p prompts

cat > prompts/novel_translation.txt << 'EOF'
你是一位专业的轻小说翻译家。请将以下日文轻小说章节翻译成简体中文。

## 翻译原则：
### 1. 风格保持
- 保留原文的文学风格和叙事节奏
- 对话部分要口语化、自然流畅
- 描述部分保持文学性

### 2. 术语处理
- 人名：使用约定俗成的中文译名
- 技能名：保留日文罗马音，括号加中文解释
- 魔法咒语：保留原样，必要时加注
- 拟声词：保留日文，括号加中文解释

### 3. 文化适配
- 日本特有的文化概念适当本地化
- 敬语系统转换为中文的礼貌表达
- 计量单位转换为公制

### 4. 格式规范
- 对话使用「」引号
- 内心独白使用『』引号
- 旁白和叙述分开处理
- 保留原文的段落分隔

## 特别注意事项：
- 角色语气词（ね、よ、わ等）根据语境适当翻译
- 拟声词（ざわざわ、どきどき等）保留并加注
- 标题和章节名保持原格式

## 内容：
{content}

请直接输出翻译结果，不要添加额外说明。
EOF
```

### 创建完整工作流
```bash
cat > workflow.yaml << 'EOF'
name: 轻小说翻译完整流程
description: 爬取→清理→翻译→替换→合并

variables:
  novel_title: "关于我转生变成史莱姆这档事"
  author: "伏濑"
  translator: "webmdai自动翻译"

stages:
  # 1. 爬取小说章节
  - name: 爬取小说章节
    type: fetch
    params:
      source: taskfile
      taskfile: TASK.md
      reader: jina
      delay: 2.0  # 小说网站需要更长的间隔
  
  # 2. 清理网页内容（关键步骤！）
  - name: 清理小说内容
    type: clean
    params:
      file_pattern: "*.md"
      preset: "kakuyomu"  # 针对小说网站的预设规则
      remove_patterns:
        - "广告"
        - "推荐作品"
        - "用户评论"
        - "分享按钮"
        - "©.*版权所有"
      output_suffix: "_cleaned"
  
  # 3. 翻译小说内容
  - name: 翻译章节
    type: llm
    params:
      model: default
      prompt_file: prompts/novel_translation.txt
      file_pattern: "*_cleaned_*.md"
      output_suffix: "_zh"
      temperature: 0.2  # 很低温度，保持翻译一致性
      max_tokens: 8000  # 小说章节可能较长
  
  # 4. 统一角色名称
  - name: 角色名替换
    type: replace
    params:
      file_pattern: "*_zh_*.md"
      replacements_file: character_names.json
      backup: true
  
  # 5. 合并为完整小说
  - name: 合并小说
    type: merge
    params:
      file_pattern: "*_zh_*.md"
      sort_by: numeric  # 按数字顺序（章节号）
      output: "${novel_title}_第一卷_中文版.md"
      add_chapter_headers: true
      header: |
        # ${novel_title}
        
        作者：${author}
        翻译：${translator}
        翻译时间：${CURRENT_DATE}
        
        ---
        
        ## 第一卷
        
      chapter_header_template: "### 第{chapter}章 {title}"
  
  # 6. 生成阅读统计（可选）
  - name: 生成统计信息
    type: command
    params:
      command: |
        echo "=== 翻译统计 ==="
        echo "小说标题: ${novel_title}"
        echo "章节数量: $(ls *_zh_*.md 2>/dev/null | wc -l)"
        echo "完成时间: $(date)"
        echo "输出文件: ${novel_title}_第一卷_中文版.md"
EOF
```

### 运行完整流程
```bash
# 运行完整工作流
webmdai workflow run workflow.yaml

# 查看最终结果
ls -la "*中文版.md"
```

---

## 场景5：自定义工作流

### 目标：创建自己的定制化处理流程

### 项目结构
```bash
mkdir custom_workflow
cd custom_workflow
```

### 创建多步骤提示词
```bash
mkdir -p prompts

# 分析提示词
cat > prompts/analyze.txt << 'EOF'
请分析以下技术文章，提取关键信息：

## 分析维度：
1. **技术领域**：属于哪个技术领域？
2. **难度级别**：入门/中级/高级
3. **核心概念**：最重要的3个概念
4. **实践价值**：对实际开发有什么帮助？
5. **学习路径**：建议的学习顺序

## 内容：
{content}

请以JSON格式输出分析结果。
EOF

# 简化提示词
cat > prompts/simplify.txt << 'EOF'
请将以下技术内容简化为初学者能理解的形式：

## 简化要求：
1. 用通俗语言解释专业概念
2. 使用比喻和例子帮助理解
3. 避免使用专业术语，必要时加解释
4. 保持核心信息不变

## 内容：
{content}

请输出简化后的版本。
EOF
```

### 创建复杂工作流
```bash
cat > workflow.yaml << 'EOF'
name: 自定义多阶段处理
description: 分析→简化→总结→格式化的完整流程

stages:
  # 阶段1：爬取或读取输入文件
  - name: 准备输入文件
    type: command
    enabled: true  # 可以禁用某些阶段
    params:
      command: |
        # 这里可以是任何命令
        echo "这是测试的技术内容..." > input.txt
        echo "更多技术细节..." >> input.txt
  
  # 阶段2：技术分析
  - name: 技术分析
    type: llm
    params:
      model: default
      prompt_file: prompts/analyze.txt
      file_pattern: "input.txt"
      output_suffix: "_analysis"
  
  # 阶段3：内容简化
  - name: 简化内容
    type: llm
    params:
      model: default
      prompt_file: prompts/simplify.txt
      file_pattern: "input.txt"
      output_suffix: "_simplified"
  
  # 阶段4：生成报告
  - name: 生成最终报告
    type: command
    params:
      command: |
        echo "# 处理报告" > final_report.md
        echo "" >> final_report.md
        echo "## 原始内容" >> final_report.md
        cat input.txt >> final_report.md
        echo "" >> final_report.md
        echo "## 分析结果" >> final_report.md
        cat *_analysis.txt 2>/dev/null >> final_report.md || echo "无分析结果"
        echo "" >> final_report.md
        echo "## 简化版本" >> final_report.md
        cat *_simplified.txt 2>/dev/null >> final_report.md || echo "无简化版本"
        echo "" >> final_report.md
        echo "---" >> final_report.md
        echo "生成时间: $(date)" >> final_report.md
  
  # 阶段5：清理临时文件（可选）
  - name: 清理工作
    type: command
    enabled: false  # 默认禁用，需要时启用
    params:
      command: |
        rm -f input.txt *_analysis.txt *_simplified.txt
        echo "临时文件已清理"
EOF
```

### 运行自定义工作流
```bash
# 运行工作流
webmdai workflow run workflow.yaml

# 带变量运行
webmdai workflow run workflow.yaml -v project_name="我的项目" -v version="1.0"
```

---

## 常见问题解答

### Q1：文件应该放在哪里？
**A：全部放在同一个目录下！**
```
cd /path/to/your/project
# 所有文件都创建在这里
# workflow.yaml、TASK.md、prompts/等都在这
```

### Q2：相对路径是什么意思？
**A：相对于你运行命令时的位置**
```bash
cd /home/user/myproject  # 进入项目目录
webmdai workflow run workflow.yaml  # 所有路径都相对于/home/user/myproject
```

### Q3：如何知道工作目录是什么？
**A：运行时会显示**
```
工作目录: /home/user/myproject
```

### Q4：可以嵌套目录吗？
**A：可以，但需要调整路径**
```
项目/
├── configs/workflow.yaml
├── tasks/TASK.md
└── prompts/translate.txt
```
工作流中需要写：`taskfile: "../tasks/TASK.md"`

### Q5：如何调试路径问题？
```bash
# 1. 确认当前目录
pwd

# 2. 列出所有文件
ls -la

# 3. 测试文件是否存在
test -f prompts/translate.txt && echo "文件存在" || echo "文件不存在"

# 4. 使用绝对路径（最可靠）
prompt_file: "/home/user/myproject/prompts/translate.txt"
```

### Q6：工作流失败了怎么办？
1. 检查所有文件是否存在
2. 检查相对路径是否正确
3. 查看错误信息中的完整路径
4. 尝试使用绝对路径

### Q7：如何复用配置？
1. 创建模板目录，复制整个结构
2. 使用变量使配置更灵活
3. 将常用提示词保存为模板

---

## 🚀 快速开始清单

### 新手必做：
1. ✅ 创建一个新目录：`mkdir myproject && cd myproject`
2. ✅ 创建`TASK.md`文件，写入链接
3. ✅ 创建`prompts/`目录和提示词文件
4. ✅ 创建`workflow.yaml`配置文件
5. ✅ 运行：`webmdai workflow run workflow.yaml`

### 进阶技巧：
1. 🔧 使用变量使配置更灵活
2. 🔧 添加`clean`阶段减少token消耗
3. 🔧 使用`replace`阶段统一术语
4. 🔧 添加`merge`阶段合并结果
5. 🔧 使用`command`阶段执行自定义操作

### 最佳实践：
1. 🌟 每个项目一个独立目录
2. 🌟 工作流文件放在项目根目录
3. 🌟 使用有意义的文件名
4. 🌟 保存成功的提示词作为模板
5. 🌟 记录每个项目的配置和结果

---

## 📞 需要帮助？

如果遇到问题：
1. 检查文件路径是否正确
2. 查看工作流运行时的"工作目录"显示
3. 确保所有文件都在工作目录中
4. 尝试使用绝对路径

记住：**简单就是美**。开始时保持所有文件在同一个目录，成功后再尝试复杂结构。

祝使用愉快！🎉