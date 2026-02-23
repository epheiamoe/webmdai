# WebMDAI TODO：修复计划与功能增强

> 基于零基础测试发现的问题，制定的详细修复和增强计划。

---

## 🔴 高优先级（必须修复）

### 1. Windows控制台编码问题

**问题描述**：
工作流运行时在Windows上会报错：
```
'gbk' codec can't encode character '\u2713' in position 0: illegal multibyte sequence
```

**原因**：工作流引擎使用 Unicode 字符 `✓` 表示成功，但 Windows 控制台默认 GBK 编码无法显示。

**影响范围**：
- `webmdai workflow run` 命令
- 所有工作流阶段执行

**修复方案**：
```python
# 在 workflow_engine.py 中
import sys

# 检测Windows系统
if sys.platform == 'win32':
    SUCCESS_MARK = "[OK]"    # Windows使用ASCII
    FAIL_MARK = "[FAIL]"
else:
    SUCCESS_MARK = "✓"       # Linux/Mac使用Unicode
    FAIL_MARK = "✗"

# 或者更简单的方案：统一使用ASCII
SUCCESS_MARK = "[OK]"
FAIL_MARK = "[FAIL]"
```

**预计工作量**：10分钟

---

## 🟡 中优先级（强烈建议）

### 2. 网络超时和重试机制优化

**问题描述**：
- 爬取某些网页时可能出现30秒超时
- 没有自动重试机制

**修复方案**：
```python
# 在 fetcher.py 中增强 _make_request 方法
def _make_request(self, url: str, **kwargs) -> requests.Response:
    last_error = None
    
    for attempt in range(self.retry_times):
        try:
            response = requests.get(url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.Timeout:
            last_error = "Timeout"
            print(f"  超时，第{attempt+1}次重试...")
        except requests.RequestException as e:
            last_error = e
        
        if attempt < self.retry_times - 1:
            wait_time = 2 ** attempt  # 指数退避
            time.sleep(wait_time)
    
    raise Exception(f"请求失败: {last_error}")
```

**预计工作量**：30分钟

---

### 3. 配置文件支持环境变量

**问题描述**：
当前需要在 `~/.webmdai/config.json` 中硬编码API密钥，不方便团队协作。

**修复方案**：
```json
// 已支持！但文档需要更新
{
  "models": {
    "deepseek": {
      "key": "$OPENROUTER_API_KEY"  // 使用$前缀引用环境变量
    }
  }
}
```

**需做**：
- [ ] 更新文档，说明环境变量用法
- [ ] 添加 `.env` 文件支持（使用 python-dotenv）

**预计工作量**：20分钟

---

## 🟢 低优先级（锦上添花）

### 4. 进度条显示

**问题描述**：
处理大量文件时，用户不知道进度。

**建议方案**：
使用 `tqdm` 库显示进度条：
```python
from tqdm import tqdm

for i, file in enumerate(tqdm(files, desc="处理文件")):
    process(file)
```

**预计工作量**：30分钟

---

### 5. 支持管道（Pipe）处理

**需求**：
用户问是否支持管道处理，这样更优雅：
```bash
# 理想的管道用法
cat urls.txt | webmdai fetch pipe -n mytask
webmdai fetch from-task | webmdai llm pipe -t translate
```

**技术方案**：

#### 5.1 添加 `fetch pipe` 子命令
```python
@fetch_cmd.command(name="pipe")
@click.option('-n', '--name', required=True, help='任务名称')
@click.option('-r', '--reader', default='jina', help='爬取服务商')
@click.option('-s/-t/-st', 'output_mode', default='both')
def fetch_pipe(name, reader, output_mode):
    """从标准输入读取URL"""
    import sys
    urls = []
    for line in sys.stdin:
        line = line.strip()
        if line and not line.startswith('#'):
            urls.append(line)
    
    if urls:
        _execute_fetch(urls, name, reader, 
                       separate='s' in output_mode,
                       together='t' in output_mode,
                       both='st' in output_mode)
```

#### 5.2 添加 `llm pipe` 子命令
```python
@llm_cmd.command(name="pipe")
@click.option('-m', '--model', help='模型别名')
@click.option('-t', '--task', required=True, help='任务类型')
@click.option('-o', '--output', help='输出文件')
def llm_pipe(model, task, output):
    """从标准输入读取内容处理"""
    import sys
    content = sys.stdin.read()
    
    # 获取模型和任务
    task_obj = get_preset_task(task)
    result = process_content(content, task_obj)
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(result)
    else:
        print(result)
```

**使用示例**：
```bash
# 示例1: 从文件读取URL爬取
cat urls.txt | webmdai fetch pipe -n mytask

# 示例2: 直接处理字符串
echo "要翻译的内容" | webmdai llm pipe -t translate

# 示例3: 管道链式处理
webmdai fetch batch -w "https://example.com" -n temp -s | \
  webmdai llm pipe -t translate | \
  webmdai deal pipe -f "旧词" -r "新词" > output.md
```

**预计工作量**：2-3小时

---

## 📋 详细实施计划

### 阶段1：紧急修复（今天完成）

```markdown
- [ ] 1.1 修复Windows编码问题
  - 文件: webmdai/modules/workflow_engine.py
  - 修改: 所有 Unicode 符号 `✓` `✗` 改为 `[OK]` `[FAIL]`
  - 测试: 在Windows运行 `webmdai workflow run`
  
- [ ] 1.2 验证修复
  - 重新运行工作流测试
  - 确认无编码错误
```

### 阶段2：稳定性增强（明天完成）

```markdown
- [ ] 2.1 优化网络超时处理
  - 文件: webmdai/modules/fetcher.py
  - 修改: 增强重试逻辑，增加指数退避
  
- [ ] 2.2 添加 .env 文件支持
  - 添加依赖: python-dotenv
  - 文件: webmdai/config.py
  - 修改: 启动时自动加载 .env 文件
  
- [ ] 2.3 更新文档
  - 文件: docs/零基础完全指南.md
  - 添加环境变量使用说明
```

### 阶段3：功能扩展（本周完成）

```markdown
- [ ] 3.1 实现管道支持
  - 文件: webmdai/cli.py
  - 添加: fetch pipe, llm pipe, deal pipe 命令
  
- [ ] 3.2 添加进度条
  - 添加依赖: tqdm
  - 文件: webmdai/modules/fetcher.py, llm_handler.py
  
- [ ] 3.3 完善测试
  - 为新增功能添加单元测试
```

---

## 🎯 优先级矩阵

| 功能 | 紧急度 | 影响范围 | 实现难度 | 建议优先级 |
|-----|-------|---------|---------|----------|
| Windows编码修复 | 🔴 高 | 所有Windows用户 | ⭐ 简单 | P0 |
| 网络超时优化 | 🟡 中 | 网络不稳定用户 | ⭐ 简单 | P1 |
| .env支持 | 🟡 中 | 所有用户 | ⭐ 简单 | P1 |
| 管道处理 | 🟢 低 | 高级用户 | ⭐⭐⭐ 复杂 | P2 |
| 进度条 | 🟢 低 | 所有用户 | ⭐⭐ 中等 | P2 |

---

## 💡 设计理念讨论

### 为什么需要管道支持？

**当前工作流的问题**：
```yaml
# 工作流需要预定义所有步骤
stages:
  - fetch
  - clean
  - llm
  - merge
```

**管道的优势**：
```bash
# 管道是即兴的、探索式的
cat urls.txt | webmdai fetch pipe | webmdai llm pipe -t translate

# 可以方便地组合外部工具
cat urls.txt | webmdai fetch pipe | grep -v "广告" | webmdai llm pipe
```

**结论**：管道和工作流是互补的：
- **工作流**：适合重复性任务（如翻译整部小说）
- **管道**：适合探索性处理（如临时处理几个链接）

**建议**：两者都支持，让用户根据场景选择。

---

## 🔧 具体代码修改清单

### 文件1: webmdai/modules/workflow_engine.py

**修改位置**: 第560行左右
```python
# 原代码
print(f"{Fore.GREEN}✓ {result.message}{Style.RESET_ALL}")
# ...
print(f"{Fore.RED}✗ {result.message}{Style.RESET_ALL}")

# 修改为
print(f"{Fore.GREEN}[OK] {result.message}{Style.RESET_ALL}")
# ...
print(f"{Fore.RED}[FAIL] {result.message}{Style.RESET_ALL}")
```

### 文件2: webmdai/cli.py

**添加管道命令**（在对应group中添加）：
```python
@fetch_cmd.command(name="pipe")
@click.option('-n', '--name', required=True)
@click.option('-r', '--reader', default='jina')
def fetch_pipe(name, reader):
    """从标准输入读取URL并爬取"""
    import sys
    urls = [line.strip() for line in sys.stdin if line.strip()]
    # ... 调用执行逻辑
```

### 文件3: requirements.txt

**添加依赖**：
```
tqdm>=4.65.0
python-dotenv>=1.0.0
```

---

## 📊 预期效果

修复/增强后：

| 场景 | 修复前 | 修复后 |
|-----|-------|-------|
| Windows运行工作流 | ❌ 编码错误 | ✅ 正常运行 |
| 网络不稳定爬取 | ❌ 容易失败 | ✅ 自动重试 |
| API密钥管理 | ⚠️ 硬编码 | ✅ 环境变量 |
| 临时处理几个URL | ⚠️ 需要创建文件 | ✅ 管道直接处理 |
| 大批量处理 | ⚠️ 无进度提示 | ✅ 进度条显示 |

---

*此TODO文档应根据实际情况定期更新。*
