# Nanobot 工具清单

{{TOOLS}}

## 使用指导

{{TOOL_GUIDE}}

## 系统工具

### 1. 文件管理器
**描述**: 管理文件和文件夹
**功能**: 创建、读取、编辑、删除文件和文件夹

| 操作 | 参数 | 说明 |
|------|------|------|
| 创建文件 | `name`, `content` | 创建新文件 |
| 编辑文件 | `name`, `content` | 向文件追加内容 |
| 删除文件 | `name` | 删除文件 |
| 读取文件 | `name` | 读取文件内容 |
| 创建文件夹 | `name` | 创建新文件夹 |
| 列出文件夹 | `name` | 列出文件夹内容 |

### 使用示例

#### 示例 1: 创建文件
**用户输入**: "创建一个名为 'example.txt' 的文件"
**Nanobot 响应**: "文件 'example.txt' 已创建"

#### 示例 2: 编辑文件
**用户输入**: "在 'test.txt' 文件中添加内容 '这是一个测试'"
**Nanobot 响应**: "文件 'test.txt' 已更新"

#### 示例 3: 查看文件
**用户输入**: "查看 'test.txt' 文件的内容"
**Nanobot 响应**: "文件 'test.txt' 的内容是：'这是一个测试'"

---

## 网络工具

### 2. 网页工具
**描述**: 问答网页并提取内容
**功能**: 抓取指定 URL 的网页内容、搜索相关内容

| 操作 | 参数 | 说明 |
|------|------|------|
| 网页抓取 | `url` | 询问指定 URL 的网页内容 |
| 搜索 | `query` | 搜索相关内容 |

### 使用示例

#### 示例 1: 网页抓取
**用户输入**: "查看这个网站的内容：https://example.com"
**Nanobot 响应**: "已抓取网页内容，摘要：[摘要内容]"

#### 示例 2: 搜索
**用户输入**: "搜索关于 Python 并发编程教程"
**Nanobot 响应**: "搜索到相关结果：
- [Python 官方编程教程](https://docs.python.org/zh-cn/latest/)
- [Python 官方编程教程](https://www.liaoxue.com/article/70283/11/)"

---

## 编程工具

### 3. 命令执行工具
**描述**: 执行系统命令和脚本
**功能**: Git 操作、包管理、编译等

| 操作 | 参数 | 说明 |
|------|------|------|
| 运行命令 | `command` | 执行 shell 命�令 |
| Git 操作 | `action`, `path`, `...` | Git 操作（clone, commit, push） |

### 使用示例

#### 示例 1: 运行命令
**用户输入**: "执行 `ls -la` 命令"
**Nanobot 响应**: "执行结果：文件列表..."

#### 例 2: Git 提交
**用户输入**: "提交当前修改"
**Nanobot 响应**: "已提交到远程仓库"

---

## 工具开发指南

### 开发流程
1. 创建工具配置文件
2. 实现工具逻辑
3. 添加到工具注册表
4. 测试工具功能

### 配置格式

```yaml
name: "工具名称"
description: "工具描述"
parameters:
  - name: "参数名"
    type: "string"
    required: true
    - name: "参数名"
    type: "string"
```

### 接口
工具需要实现以下接口：

```python
class Tool:
    def execute(self, **kwargs) -> str:
        """执行工具操作"""
        pass
    
    def get_status(self) -> dict:
        """获取工具状态"""
        pass
```

### 使用示例

```python
from nanobot.agent.tools.registry import ToolRegistry

# 注册工具
registry = ToolRegistry()
registry.register(MyTool())

# 通过工具管理器调用
result = registry.execute("工具名称", 参数)
```
```

---

## 常见

### 1. 文件管理器
```python
# 示例：创建文件
result = registry.execute("file_manager", {
    "action": "create_file",
    "name": "example.txt",
    "content": "Hello World"
})
```

### 2. 网页工具
```python
# 示例：网页抓取
result = registry.execute("web_fetch", {
    "url": "https://example.com"
})
```

### 3. 命程工具
```python
# 示例：执行命令
result = registry.execute("command", {
    "command": "git status"
})
```
