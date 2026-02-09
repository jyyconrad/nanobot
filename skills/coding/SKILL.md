---
name: coding
description: "编码技能 - 支持多种编程语言、代码审查、重构和优化。用于代码编写、修改、调试等任务。"
version: "1.0.0"
metadata:
  nanobot:
    emoji: "💻"
    keywords: ["代码", "函数", "class", "python", "javascript", "编程", "开发"]
---

# Coding Skill

编码技能 - 支持多种编程语言和代码任务。

## 何时使用此技能

当任务涉及以下内容时使用：
- 编写新代码或函数
- 修改或重构现有代码
- 代码审查和优化
- 解决编程问题
- 多语言代码开发

## 支持的语言

- **Python** - 通用编程、数据处理、Web 开发
- **JavaScript/TypeScript** - 前端开发、Node.js 后端
- **Java** - 企业级应用、Android 开发
- **Go** - 高性能服务、微服务
- **Rust** - 系统编程、高性能应用
- **SQL** - 数据库查询和操作

## 编码原则

### 1. 清晰和可读性

- 使用有意义的变量和函数名
- 添加必要的注释说明复杂逻辑
- 遵循语言的 PEP8、ESLint 等规范
- 保持函数短小，单一职责

### 2. 错误处理

- 始终处理可能的异常
- 提供有意义的错误消息
- 使用适当的错误类型
- 记录关键错误信息

### 3. 性能考虑

- 避免不必要的计算
- 使用高效的数据结构
- 考虑缓存策略
- 优化热点代码

### 4. 安全性

- 验证输入数据
- 防止注入攻击
- 使用安全的库和函数
- 遵循最小权限原则

## 代码模式

### Python 模式

**读取文件**：
```python
with open('file.txt', 'r') as f:
    content = f.read()
```

**处理 JSON**：
```python
import json
data = json.loads(json_string)
```

**异步任务**：
```python
async def process_task(task):
    async with aiohttp.ClientSession() as session:
        # 处理任务
        pass
```

### JavaScript/TypeScript 模式

**异步函数**：
```typescript
async function fetchData(url: string): Promise<Data> {
    const response = await fetch(url);
    return response.json();
}
```

**错误处理**：
```typescript
try {
    // 尝试操作
} catch (error) {
    console.error('Error:', error);
    throw error;
}
```

## 代码审查清单

在提交代码前，检查：
- [ ] 代码可读性
- [ ] 错误处理完整
- [ ] 无安全漏洞
- [ ] 性能合理
- [ ] 测试覆盖关键路径
- [ ] 遵循代码规范
- [ ] 文档清晰

## 调试技巧

1. **日志记录**：添加详细的日志输出
2. **断点调试**：使用调试器设置断点
3. **单元测试**：编写测试用例重现问题
4. **简化代码**：逐步简化以定位问题
5. **查看错误**：仔细阅读错误消息和堆栈跟踪

## 性能优化

1. **测量性能**：使用性能分析工具
2. **优化算法**：选择更高效的算法
3. **减少 I/O**：批量处理，避免频繁读写
4. **使用缓存**：缓存重复计算
5. **并行处理**：利用多线程/协程

## 安全最佳实践

1. **输入验证**：始终验证和清理输入
2. **参数化查询**：防止 SQL 注入
3. **最小权限**：使用最小的系统权限
4. **敏感数据**：加密存储和传输
5. **依赖更新**：定期更新依赖库

## 参考资源

详见 [PYTHON_PATTERNS.md](references/PYTHON_PATTERNS.md) 了解 Python 常见模式。
详见 [JAVASCRIPT_BEST_PRACTICES.md](references/JAVASCRIPT_BEST_PRACTICES.md) 了解 JavaScript 最佳实践。

## 工具使用

此技能通常配合以下工具使用：
- `ReadFileTool` - 读取代码文件
- `WriteFileTool` - 写入代码文件
- `ExecTool` - 运行代码（Python、Node.js 等）
- `WebSearchTool` - 查找解决方案和示例

记住：好的代码是可读、可维护、可测试的。
