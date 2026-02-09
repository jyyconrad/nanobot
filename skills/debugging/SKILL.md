---
name: debugging
description: "调试技能 - 定位和修复代码错误。用于调试、错误分析、问题诊断等任务。"
version: "1.0.0"
metadata:
  nanobot:
    emoji: "🐛"
    keywords: ["bug", "错误", "调试", "修复", "debug", "异常"]
---

# Debugging Skill

调试技能 - 定位和修复代码错误。

## 何时使用此技能

当任务涉及以下内容时使用：
- 分析错误消息
- 定位代码 bug
- 修复运行时错误
- 调试逻辑问题
- 性能问题诊断

## 调试方法论

### 1. 理解错误

首先，完整理解错误信息：
- 错误类型（TypeError, ValueError, IndexError 等）
- 错误消息
- 堆栈跟踪
- 发生错误的代码行

### 2. 重现问题

确保能够稳定重现错误：
- 记录触发步骤
- 识别输入条件
- 确定环境因素

### 3. 隔离问题

逐步缩小问题范围：
- 二分法：注释掉一半代码
- 最小化示例：创建最简单的失败用例
- 添加日志：跟踪执行流程

### 4. 定位原因

分析代码逻辑，找到根本原因：
- 检查变量值
- 验证假设
- 审查相关代码

### 5. 修复问题

实施修复方案：
- 修改代码
- 添加防御性检查
- 改进错误处理

### 6. 验证修复

确保修复有效且不引入新问题：
- 运行测试
- 尝试重现原始错误
- 检查相关功能

## 常见错误类型

### Python 错误

**TypeError**：类型不匹配
```python
# 错误
result = "5" + 3  # TypeError: can only concatenate str (not "int") to str

# 修复
result = int("5") + 3
```

**ValueError**：值无效
```python
# 错误
value = int("abc")  # ValueError: invalid literal for int()

# 修复
try:
    value = int("abc")
except ValueError:
    value = 0
```

**KeyError**：字典键不存在
```python
# 错误
data = {"name": "John"}
age = data["age"]  # KeyError: 'age'

# 修复
age = data.get("age", 0)  # 提供默认值
```

**AttributeError**：对象属性不存在
```python
# 错误
text = None
print(text.lower())  # AttributeError: 'NoneType' object has no attribute 'lower'

# 修复
if text:
    print(text.lower())
```

### JavaScript 错误

**ReferenceError**：变量未定义
```javascript
// 错误
console.log(myVariable);  // ReferenceError: myVariable is not defined

// 修复
let myVariable = "Hello";
console.log(myVariable);
```

**TypeError**：类型错误
```javascript
// 错误
let list = null;
list.push("item");  // TypeError: Cannot read property 'push' of null

// 修复
let list = [];
list.push("item");
```

## 调试技巧

### 1. 打印调试

在关键位置添加 print/logging：
```python
print(f"变量 x 的值: {x}")  # Python
console.log("变量 x 的值:", x);  // JavaScript
```

### 2. 使用调试器

使用 IDE 调试器：
- 设置断点
- 单步执行
- 检查变量
- 调用堆栈

### 3. 断言

使用断言验证假设：
```python
assert x > 0, "x 必须大于 0"
```

### 4. 异常处理

捕获并记录异常：
```python
try:
    # 可能出错的代码
    pass
except Exception as e:
    print(f"错误: {e}")
    raise
```

## 性能调试

### 1. 测量时间

测量代码执行时间：
```python
import time

start = time.time()
# 执行代码
duration = time.time() - start
print(f"执行时间: {duration:.2f} 秒")
```

### 2. 性能分析

使用性能分析工具：
- Python: cProfile, line_profiler
- JavaScript: Chrome DevTools, Node.js Profiler

### 3. 内存分析

检测内存泄漏：
- Python: memory_profiler, objgraph
- JavaScript: Chrome Memory Profiler

## 日志记录

使用结构化日志：
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告")
logger.error("错误")
logger.critical("严重错误")
```

## 调试检查清单

调试问题时，检查：
- [ ] 完整理解错误信息
- [ ] 能够稳定重现问题
- [ ] 已逐步隔离问题范围
- [ ] 识别根本原因
- [ ] 修复方案合理
- [ ] 已验证修复有效
- [ ] 未引入新问题

## 常见调试场景

### 1. 无限循环

症状：程序卡住，CPU 占用高

解决：
- 检查循环条件
- 确保有退出条件
- 添加循环计数器

### 2. 内存泄漏

症状：内存持续增长，性能下降

解决：
- 检查全局变量
- 确保释放资源
- 使用对象池

### 3. 竞态条件

症状：随机失败，难以重现

解决：
- 使用锁和同步机制
- 避免共享状态
- 使用不可变对象

## 参考资源

详见 [DEBUGGING_PATTERNS.md](references/DEBUGGING_PATTERNS.md) 了解常见调试模式。
详见 [ERROR_GUIDE.md](references/ERROR_GUIDE.md) 了解常见错误和解决方案。

## 工具使用

此技能通常配合以下工具使用：
- `ReadFileTool` - 读取代码文件
- `ExecTool` - 运行代码查看错误
- `WebSearchTool` - 搜索错误信息

记住：好的调试是系统性的，而不是猜测的。
