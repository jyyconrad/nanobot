# 基于 OpenClaw 提示词组织方式的 Nanobot-Agno 升级方案

## 1. OpenClaw 提示词组织方式分析

### 1.1 OpenClaw 提示词架构特点

OpenClaw 采用分散式、文件化的提示词组织方式，核心文件包括：

| 文件名 | 功能描述 |
|--------|----------|
| AGENTS.md | 工作区配置和智能体行为准则 |
| SOUL.md | 智能体核心身份和行为哲学 |
| USER.md | 用户信息和偏好设置 |
| TOOLS.md | 本地工具和配置信息 |
| IDENTITY.md | 智能体基本身份信息 |
| HEARTBEAT.md | 心跳检查和定期任务清单 |
| MEMORY.md | 长时记忆和语义搜索配置 |

### 1.2 OpenClaw 加载逻辑

- **初始化流程**：每次会话重新加载所有提示词文件
- **读取顺序**：AGENTS.md → SOUL.md → USER.md → 记忆文件 → 其他配置
- **上下文整合**：将所有文件内容整合成完整的系统提示词
- **动态更新**：支持会话过程中读取和更新记忆文件

## 2. 新的提示词架构设计

### 2.1 目录结构

```
nanobot-agno/
├── config/
│   ├── prompts/                 # 所有内置提示词文件
│   │   ├── agents.md           # 工作区配置和智能体行为准则
│   │   ├── soul.md             # 核心身份和行为哲学
│   │   ├── user.md             # 用户信息和偏好
│   │   ├── tools.md            # 工具配置信息
│   │   ├── identity.md         # 基本身份信息
│   │   ├── heartbeat.md        # 心跳检查和定期任务
│   │   └── memory.md           # 长时记忆配置
│   ├── model_config.py         # 模型配置
│   └── system_config.py        # 系统配置
├── tools/                       # 工具集合
│   ├── framework/              # 框架级工具
│   ├── project/                # 项目级工具
│   └── user/                   # 用户级工具
├── skills/                      # 技能集合
│   ├── base/                   # 基础技能
│   └── specialized/            # 专业技能
├── context/                     # 上下文管理
│   ├── memory/                 # 用户记忆（每日文件）
│   │   ├── YYYY-MM-DD.md
│   │   └── heartbeat-state.json
│   └── session/                # 会话状态
├── main.py                      # MainAgent 入口
└── registry.py                  # 组件注册表
```

### 2.2 提示词加载逻辑

#### 2.2.1 MainAgent 加载流程

```python
def load_prompts() -> dict:
    """加载所有提示词文件"""
    prompts = {}
    prompt_files = [
        "agents.md", "soul.md", "user.md", 
        "tools.md", "identity.md", "heartbeat.md", "memory.md"
    ]
    
    for filename in prompt_files:
        file_path = os.path.join("config/prompts", filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                prompts[filename.split(".")[0]] = f.read().strip()
    
    return prompts


def build_system_prompt(prompts: dict, context: dict) -> str:
    """构建完整的系统提示词"""
    # 基础架构信息
    system_prompt = f"""# Nanobot-Agno MainAgent

## 身份信息
{prompts.get('identity', '')}

## 核心哲学
{prompts.get('soul', '')}

## 工作区准则
{prompts.get('agents', '')}

## 用户信息
{prompts.get('user', '')}

## 工具配置
{prompts.get('tools', '')}

## 心跳任务
{prompts.get('heartbeat', '')}

## 记忆管理
{prompts.get('memory', '')}

## 当前上下文
{json.dumps(context, ensure_ascii=False, indent=2)}
"""
    
    return system_prompt
```

#### 2.2.2 SubAgent 加载流程

```python
def load_subagent_prompts(agent_type: str) -> dict:
    """加载 SubAgent 特定提示词"""
    base_prompts = load_prompts()
    
    # SubAgent 特定配置
    subagent_prompt_file = os.path.join("config/prompts", f"subagent-{agent_type}.md")
    if os.path.exists(subagent_prompt_file):
        with open(subagent_prompt_file, "r", encoding="utf-8") as f:
            base_prompts["subagent"] = f.read().strip()
    
    return base_prompts


def build_subagent_prompt(prompts: dict, context: dict, agent_type: str) -> str:
    """构建 SubAgent 系统提示词"""
    # 基础提示词（包含 MainAgent 核心信息）
    base_prompt = build_system_prompt(prompts, context)
    
    # SubAgent 特定提示词
    subagent_prompt = prompts.get("subagent", "")
    
    # 完整提示词
    complete_prompt = f"""# {agent_type.capitalize()} SubAgent

{base_prompt}

## SubAgent 特定职责
{subagent_prompt}
"""
    
    return complete_prompt
```

## 3. 提示词协作机制

### 3.1 层次化协作架构

```mermaid
graph TD
    A[MainAgent] -->|加载| B[config/prompts/agents.md]
    A -->|加载| C[config/prompts/soul.md]
    A -->|加载| D[config/prompts/user.md]
    A -->|加载| E[config/prompts/tools.md]
    A -->|加载| F[config/prompts/identity.md]
    A -->|加载| G[config/prompts/heartbeat.md]
    A -->|加载| H[config/prompts/memory.md]
    
    I[SubAgent (coding)] -->|继承| A
    I -->|加载| J[config/prompts/subagent-coding.md]
    
    K[SubAgent (research)] -->|继承| A
    K -->|加载| L[config/prompts/subagent-research.md]
    
    M[SubAgent (data)] -->|继承| A
    M -->|加载| N[config/prompts/subagent-data.md]
```

### 3.2 提示词更新策略

#### 3.2.1 动态更新机制

```python
def watch_prompt_files(callback: callable):
    """监视提示词文件变化"""
    watch_dir = "config/prompts"
    previous_state = {}
    
    for filename in os.listdir(watch_dir):
        if filename.endswith(".md"):
            file_path = os.path.join(watch_dir, filename)
            previous_state[filename] = os.path.getmtime(file_path)
    
    while True:
        time.sleep(5)  # 检查间隔
        
        for filename in os.listdir(watch_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(watch_dir, filename)
                current_mtime = os.path.getmtime(file_path)
                
                if current_mtime != previous_state.get(filename):
                    print(f"提示词文件更新: {filename}")
                    callback(filename)
                    previous_state[filename] = current_mtime
```

#### 3.2.2 版本控制

```python
def save_prompt_version(prompt_name: str, content: str):
    """保存提示词版本"""
    version_dir = "config/prompts/versions"
    os.makedirs(version_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    version_file = os.path.join(version_dir, f"{prompt_name}-{timestamp}.md")
    
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    # 保留最近 10 个版本
    versions = sorted(
        [f for f in os.listdir(version_dir) if f.startswith(prompt_name)],
        reverse=True
    )
    
    for old_version in versions[10:]:
        os.remove(os.path.join(version_dir, old_version))
```

## 4. 实现步骤

### 4.1 阶段一：架构搭建（1周）

1. 创建 config/prompts/ 目录结构
2. 实现提示词加载和解析模块
3. 创建基础提示词文件（agents.md, soul.md, user.md 等）
4. 实现系统提示词构建逻辑

### 4.2 阶段二：MainAgent 升级（1-2周）

1. 更新 MainAgent 初始化流程
2. 实现提示词分层加载机制
3. 测试完整系统提示词生成
4. 添加提示词更新检测功能

### 4.3 阶段三：SubAgent 集成（1-2周）

1. 实现 SubAgent 提示词继承机制
2. 创建 SubAgent 特定提示词文件
3. 测试 SubAgent 系统提示词生成
4. 验证 MainAgent 和 SubAgent 协作

### 4.4 阶段四：优化和测试（1-2周）

1. 优化提示词加载性能
2. 实现版本控制和回滚功能
3. 测试各种场景下的提示词整合
4. 完善错误处理和边界情况

### 4.5 阶段五：部署和上线（1周）

1. 生产环境配置和部署
2. 监控和日志配置
3. 备份和恢复策略
4. 上线后的维护

## 5. 关键改进点

### 5.1 统一提示词管理

- 所有内置提示词集中在 config/prompts/ 目录
- 标准化的文件命名和内容结构
- 简化维护和更新流程

### 5.2 层次化继承机制

- MainAgent 加载完整提示词集
- SubAgent 继承 MainAgent 核心信息
- 支持 SubAgent 特定提示词扩展

### 5.3 动态更新能力

- 实时监控提示词文件变化
- 支持热更新，无需重启系统
- 版本控制和回滚功能

### 5.4 上下文注入优化

- 更智能的上下文分析和注入
- 支持多维度上下文信息
- 提高提示词针对性和准确性

## 6. 测试策略

### 6.1 功能测试

1. 提示词加载完整性测试
2. 系统提示词构建正确性测试
3. SubAgent 提示词继承测试
4. 提示词更新和热加载测试

### 6.2 性能测试

1. 提示词加载性能测试
2. 系统提示词构建时间测试
3. 大量提示词文件处理测试
4. 高并发场景下的提示词管理测试

### 6.3 安全测试

1. 提示词文件权限测试
2. 版本控制安全性测试
3. 敏感信息过滤测试
4. 攻击向量防护测试

## 7. 迁移计划

### 7.1 现有系统迁移

1. 分析现有系统提示词结构
2. 将现有提示词内容迁移到新目录结构
3. 更新提示词加载和构建逻辑
4. 测试和验证迁移后的功能

### 7.2 数据迁移

1. 迁移现有用户记忆文件
2. 更新记忆管理模块
3. 测试记忆功能的连续性
4. 确保历史数据的可访问性

## 8. 未来扩展

### 8.1 多语言支持

- 支持不同语言的提示词文件
- 实现语言切换和本地化
- 支持跨语言上下文理解

### 8.2 机器学习优化

- 使用机器学习分析提示词效果
- 自动优化提示词结构和内容
- 实现个性化提示词生成

### 8.3 可视化管理

- 提供提示词管理的可视化界面
- 支持拖拽式提示词组合
- 实时预览提示词效果

## 9. 结论

本升级方案基于 OpenClaw 的提示词组织方式，设计了一个更清晰、更高效的 Nanobot-Agno 架构。通过将所有内置提示词集中在 config/prompts/ 目录，实现了统一管理和版本控制。MainAgent 和 SubAgent 之间的层次化继承机制，确保了提示词的一致性和可扩展性。

该方案充分利用了 OpenClaw 的优秀设计理念，包括分散式文件管理、动态更新能力和层次化协作架构。通过这些改进，Nanobot-Agno 将能够更灵活地适应不同场景，提供更高效、更智能的服务。

升级过程分为五个阶段，每个阶段都有明确的目标和交付物。通过逐步实现和测试，确保系统的稳定性和可靠性。最终实现的 Nanobot-Agno 系统将能够处理各种复杂任务，为用户提供高效、专业的 AI 辅助服务。