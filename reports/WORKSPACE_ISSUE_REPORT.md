# Workspace 使用问题分析报告

## 🔍 问题概述

Nanobot 项目在 workspace 配置和使用方面存在多个不一致问题，导致文件操作混乱。

---

## 📊 当前配置状态

### 配置文件

**`~/.nanobot/config.json`**:
```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.nanobot/workspace",
      "model": "volcengine/glm-4.7",
      "maxTokens": 8192,
      "temperature": 0.7,
      "maxToolIterations": 20
    }
  }
}
```

### 实际路径

```bash
# config.json 中的配置
~/.nanobot/workspace

# 解析后的实际路径
/Users/jiangyayun/.nanobot/workspace

# 指向的实际目录（当前不是软链接）
/Users/jiangyayun/develop/code/work_code/nanobot
```

### 目录结构

```
~/.nanobot/
├── config.json
├── workspace/                    # 指向项目目录 (❌ 问题)
│   ├── AGENTS.md
│   ├── SOUL.md
│   ├── USER.md
│   └── memory/                      # 实际的 memory 目录
│
└── sessions/

# 项目目录
/Users/jiangyayun/develop/code/work_code/nanobot/
├── AGENTS.md                     # ❌ 重复
├── AGENTS_AND_SKILLS.md
├── MEMORY.md                      # ❌ 重复
├── memory/                        # ❌ 与 workspace/memory 混淆
└── workspace/                     # 项目内的 workspace 目录
```

---

## 🔴 发现的问题

### 问题 1：workspace 指向项目目录

**严重程度**: 🔴 高

**现象**:
- `~/.nanobot/workspace` 指向 `/Users/jiangyayun/develop/code/work_code/nanobot`
- 这导致工具在项目目录内操作文件
- 与配置的意图（独立 workspace）不一致

**影响**:
```
❌ 错误行为：
- 创建的文件在项目根目录
- memory/AGENTS.md 等文件在项目根目录和 workspace/ 中都有
- 与 nanobot/memory/ 目录混淆

✅ 正确行为应该是：
- 创建文件在 ~/.nanobot/workspace/ 中
- 独立于项目代码目录
- 不会污染项目源码
```

### 问题 2：配置的 workspace 值不明确

**严重程度**: 🟡 中

**问题**:
- 配置使用 `"~/.nanobot/workspace"`（字符串）
- 代码中使用 `config.workspace_path`（经过 expanduser() 处理的 Path）
- 如果用户直接修改 `~/.nanobot/config.json`，可能没有正确处理 `~`

**示例**:
```json
// 用户可能这样修改
{
  "workspace": "/Users/jiangyayun/.nanobot/workspace"  // ✅ 绝对路径
  // 或者
  "workspace": "~/.nanobot/workspace"          // ✅ 相对路径
}
```

### 问题 3：多个 memory 目录

**严重程度**: 🟡 中

**问题**:
```
nanobot/memory/                           # 1. 项目代码中的 memory
~/.nanobot/workspace/memory/              # 2. workspace 中的 memory
~/.nanobot/sessions/                      # 3. 会话存储目录
```

**影响**:
- SessionManager 使用 `~/.nanobot/sessions/`
- 但某些代码可能在 `nanobot/memory/` 中操作
- 导致记忆分散，无法统一管理

### 问题 4：系统提示词中的 workspace 路径显示不一致

**位置**: `agent/context.py:77-102`

**问题**:
```python
# 构建系统提示词
workspace_path = str(self.workspace.expanduser().resolve())

return f"""# nanobot 🐈
...
## Workspace
Your workspace is at: {workspace_path}
- Memory files: {workspace_path}/memory/MEMORY.md
- Daily notes: {workspace_path}/memory/YYYY-MM-DD.md
- Custom skills: {workspace_path}/skills/{{skill-name}}/SKILL.md
...
"""
```

**问题**:
- 提示词显示 workspace 中的路径
- 但如果 workspace 指向项目目录，用户会困惑
- 例如：`Your workspace is at: /Users/jiangyayun/develop/code/work_code/nanobot`

---

## 🛠️ 解决方案

### 方案 1：修复 workspace 软链接（最彻底）

**步骤**:
```bash
# 1. 备份当前 workspace 内容
cp -r ~/.nanobot/workspace ~/.nanobot/workspace.backup

# 2. 删除软链接（如果存在）
rm -f ~/.nanobot/workspace

# 3. 创建独立的 workspace 目录
mkdir -p ~/.nanobot/workspace

# 4. 从项目根目录复制基础文件
cp nanobot/AGENTS.md ~/.nanobot/workspace/
cp nanobot/SOUL.md ~/.nanobot/workspace/
cp nanobot/USER.md ~/.nanobot/workspace/

# 5. 创建 memory 和 skills 目录
mkdir -p ~/.nanobot/workspace/memory
mkdir -p ~/.nanobot/workspace/skills

# 6. 创建默认 MEMORY.md
cat > ~/.nanobot/workspace/memory/MEMORY.md << 'EOF'
# Long-term Memory

This file stores important information that should persist across sessions.

## User Information
(Important facts about user)

## Preferences
(User preferences learned over time)

## Important Notes
(Things to remember)
EOF

# 7. 清理备份
rm -rf ~/.nanobot/workspace.backup
```

### 方案 2：修改配置为绝对路径

**修改 `~/.nanobot/config.json`**:
```json
{
  "agents": {
    "defaults": {
      "workspace": "/Users/jiangyayun/.nanobot/workspace",
      "model": "volcengine/glm-4.7",
      "maxTokens": 8192,
      "temperature": 0.7,
      "maxToolIterations": 20
    }
  }
}
```

### 方案 3：统一 memory 管理

**方案**:
- 所有记忆操作都应该使用 `~/.nanobot/workspace/memory/`
- 删除或忽略项目代码中的 `nanobot/memory/` 目录
- SessionManager 继续使用 `~/.nanobot/sessions/`

### 方案 4：添加 workspace 验证

创建 `nanobot/utils/workspace_validator.py`:

```python
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def validate_workspace(config_workspace: str) -> dict:
    """
    验证 workspace 配置是否正确
    
    Args:
        config_workspace: config.json 中的 workspace 配置
    
    Returns:
        验证结果
    """
    issues = []
    warnings = []
    
    # 解析路径
    path = Path(config_workspace).expanduser().resolve()
    
    # 检查 1：是否是绝对路径
    if not str(path).startswith("/"):
        warnings.append("workspace 不是绝对路径")
    
    # 检查 2：是否在项目目录内
    try:
        project_root = Path(__file__).parent.parent.parent
        if path.is_relative_to(project_root):
            issues.append(f"workspace 在项目目录内: {path}")
            warnings.append(f"项目根: {project_root}")
    except:
        pass
    
    # 检查 3：是否是软链接
    if path.is_symlink():
        target = path.resolve()
        issues.append(f"workspace 是软链接: {path} -> {target}")
    
    # 检查 4：目录是否存在
    if not path.exists():
        issues.append("workspace 目录不存在")
    elif not path.is_dir():
        issues.append("workspace 不是目录")
    
    # 检查 5：是否可写
    import os
    if path.exists() and path.is_dir():
        if not os.access(path, os.W_OK):
            issues.append("workspace 不可写")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "path": str(path),
    }


def diagnose():
    """诊断 workspace 配置"""
    print("=" * 80)
    print("🔍 Workspace 配置诊断")
    print("=" * 80)
    print()
    
    # 读取配置
    import json
    try:
        with open("~/.nanobot/config.json") as f:
            config = json.load(f)
        
        workspace_config = config["agents"]["defaults"]["workspace"]
        print(f"📋 配置中的 workspace: {workspace_config}")
        print()
        
        # 验证
        result = validate_workspace(workspace_config)
        
        print("📊 验证结果:")
        if result["valid"]:
            print("  ✅ workspace 配置有效")
        else:
            print("  ❌ 发现问题:")
            for issue in result["issues"]:
                print(f"     - {issue}")
        
        if result["warnings"]:
            print("  ⚠️  警告:")
            for warning in result["warnings"]:
                print(f"     - {warning}")
        
        print()
        print(f"  解后的实际路径: {result['path']}")
        print(f"  路径类型: {'软链接' if Path(result['path']).is_symlink() else '普通目录'}")
        
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")


if __name__ == "__main__":
__":
    diagnose()
```

---

## 📝 修改建议

### 1. 立即修复（推荐）

```bash
# 运行快速修复脚本
python fix_workspace_config.py
```

### 2. 手动修复步骤

1. 删除现有软链接（如果存在）
   ```bash
   ls -la ~/.nanobot/workspace
   # 如果显示为软链接，删除它
   rm -f ~/.nanobot/workspace
   ```

2. 创建正确的 workspace 目录
   ```bash
   mkdir -p ~/.nanobot/workspace
   mkdir -p ~/.nanobot/workspace/memory
   mkdir -p ~/.nanobot/workspace/skills
   ```

3. 复制必要的模板文件
   ```bash
   cp nanobot/AGENTS.md ~/.nanobot/workspace/
   cp nanobot/SOUL.md ~/.nanobot/workspace/
   cp nanobot/USER.md ~/.nanobot/workspace/
   ```

4. 验证配置
   ```bash
   # 检查 config.json
   cat ~/.nanobot/config.json | grep -A 5 workspace
   
   # 应该看到:
   # "workspace": "~/.nanobot/workspace",
   ```

### 3. 重启服务验证

```bash
# 停止当前服务
# 重新启动 nanobot
python -m nanobot

# 测试文件操作
# 应该在 ~/.nanobot/workspace/memory/ 中创建文件
```

---

## 🔍 关键发现

1. **workspace 指向项目目录** - 这是最严重的问题
2. **配置使用相对路径 `~`** - 可能导致路径解析问题
3. **多个 memory 目录** - 导致记忆管理混乱
4. **缺少 workspace 验证** - 没有启动时验证配置

---

## ✅ 预期效果

修复后：

✅ workspace 在 `~/.nanobot/workspace/`（独立目录）
✅ 所有文件操作在 workspace 内
✅ 项目源码不会被污染
✅ memory/sessions 清晰分离
✅ 系统提示词显示正确的路径

---

## 📋 相关文件位置

| 文件                           | 行号 | 问题                        |
| ------------------------------ | ---- | --------------------------- |
| `~/.nanobot/config.json`     | -    | workspace 指向项目目录 |
| `nanobot/agent/context.py`  | 77-102 | 路径显示在提示词中       |
| `nanobot/agent/loop.py`    | 41-54 | workspace 传递给组件       |
| `nanobot/session/manager.py` | 65-68 | session 存储                  |
| `nanobot/utils/helpers.py`   | 18-27 | get_workspace_path 实现      |

---

**生成时间**: 2025-02-09
**版本**: 1.0
