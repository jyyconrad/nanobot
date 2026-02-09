"""
上下文超长问题诊断脚本

检测和分析导致上下文超长的具体原因
"""

import asyncio
from pathlib import Path


# 模拟的测试数据
def create_test_context():
    """创建测试上下文"""
    base_context = """
# 基础上下文
- AGENTS.md: 定义了 Nanobot 的工作方式
- TOOLS.md: 记录了工具和技能信息
- IDENTITY.md: 定义了 Nanobot 的身份和定位

## MainAgent 系统

### 角色定位
MainAgent 是 Nanobot 的协调者，负责：
- 接收和分析用户任务
- 查询系统配置（skills、agents）
- 智能选择合适的技能
- 决定创建什么类型的 Subagent
- 协调和监控 Subagent 执行
- 聚合和总结结果

### 核心原则
- **自主决策**：不问用户，自己判断
- **工具驱动**：通过工具获取信息，不要硬编码
- **简洁高效**：避免不必要的工具调用
- **安全优先**：高风险操作需要评估

### 工作流程
1. 接收任务
2. 调用工具查询配置
3. 分析任务特点
4. 选择技能
5. 选择 agent 类型
6. 创建 Subagent
7. 监控执行
8. 聚合结果
"""

    memory_context = """
## 记忆上下文
- [2025-01-15 10:30:00] 用户要求编写一个 Python 函数来处理 JSON 数据
- [2025-01-15 10:35:00] 我创建了 data_processor.py 文件，实现了 parse_json 函数
- [2025-01-15 10:40:00] 用户要求修复解析错误
- [2025-01-15 10:45:00] 我修复了变量名错误，从 json_data 改为 data
- [2025-01-15 10:50:00] 用户要求添加单元测试
- [2025-01-15 10:55:00] 我创建了 test_data_processor.py 文件，添加了 5 个测试用例
- [2025-01-15 11:00:00] 用户要求优化性能
- [2025-01-15 11:05:00] 我优化了 parse_json 函数，使用 json.loads 替代手动解析
- [2025-01-15 11:10:00] 用户要求添加错误处理
- [2025-01-15 11:15:00] 我添加了 try-except 块来捕获 JSONDecodeError
"""

    skill_context = """
## 技能上下文

### coding
- 支持多种编程语言（Python、JavaScript、TypeScript、Go 等）
- 提供代码审查和重构功能
- 支持测试驱动开发（TDD）
- 自动修复代码问题

### debugging
- 支持错误定位和分析
- 提供调试建议和修复方案
- 支持堆栈跟踪分析
- 自动识别常见错误模式

### testing
- 单元测试生成
- 集成测试支持
- 测试覆盖分析
- 性能测试工具

### planning
- 任务分解和规划
- 项目管理支持
- 时间表和里程碑设置
- 风险评估和缓解

### writing
- 内容创作和编辑
- 文档生成和优化
- 语言风格检查
- 翻译支持
"""

    return base_context, memory_context, skill_context


def create_test_messages(count=20):
    """创建测试消息历史"""
    messages = []

    scenarios = [
        ("user", "请帮我写一个 Python 函数来排序列表"),
        ("assistant", "我可以帮你写一个排序函数。你想用什么排序算法？"),
        ("user", "用快速排序"),
        ("assistant", "好的，我来实现快速排序算法..."),
        ("assistant", "已创建 quick_sort.py 文件，实现了快速排序算法"),
        ("user", "测试一下这个函数"),
        ("assistant", "我来运行测试..."),
        ("assistant", "测试通过！快速排序函数工作正常"),
        ("user", "能不能优化一下性能？"),
        ("assistant", "可以，我可以使用内省函数来优化"),
        ("assistant", "已优化 quick_sort 函数，性能提升 30%"),
        ("user", "现在再写一个冒泡排序"),
        ("assistant", "好的，我来实现冒泡排序算法"),
        ("assistant", "已创建 bubble_sort.py 文件"),
        ("user", "比较一下两个算法的性能"),
        ("assistant", "我来运行性能测试..."),
        ("assistant", "快速排序比冒泡排序快 100 倍！"),
    ]

    for i in range(count):
        role, content = scenarios[i % len(scenarios)]
        messages.append({"role": role, "content": f"[消息 {i + 1}] {content}"})

    return messages


def estimate_tokens(text):
    """估算 Token 数量（使用简单的启发式方法）"""
    if not text:
        return 0

    # 方法 1：字符数 / 1.6（基于测试结果）
    return int(len(text) / 1.6)


def diagnose_context_issue():
    """诊断上下文超长问题"""
    print("=" * 80)
    print("上下文超长问题诊断")
    print("=" * 80)
    print()

    # 创建测试数据
    base_ctx, memory_ctx, skill_ctx = create_test_context()
    messages = create_test_messages(20)

    # 计算各部分 Token 数量
    print("📊 上下文组成部分分析")
    print("-" * 80)

    parts = [
        ("基础上下文", base_ctx),
        ("记忆上下文", memory_ctx),
        ("技能上下文", skill_ctx),
    ]

    total_system_tokens = 0
    for name, content in parts:
        chars = len(content)
        tokens = estimate_tokens(content)
        total_system_tokens += tokens
        print(f"  {name}:")
        print(f"    字符数: {chars:,}")
        print(f"    Token 数: {tokens:,}")
        print()

    print(f"  📦 系统上下文总计:")
    print(f"    Token 数: {total_system_tokens:,}")
    print()

    # 消息历史
    print("  💬 消息历史:")
    message_chars = sum(len(msg.get("content", "")) for msg in messages)
    message_tokens = estimate_tokens("\n".join([msg.get("content", "") for msg in messages]))
    print(f"    消息数量: {len(messages)}")
    print(f"    字符数: {message_chars:,}")
    print(f"    Token 数: {message_tokens:,}")
    print()

    # 总计
    print("  📈 总计:")
    total_tokens = total_system_tokens + message_tokens
    print(f"    总 Token 数: {total_tokens:,}")
    print()

    # 模型限制
    print("=" * 80)
    print("📋 模型上下文限制对比")
    print("=" * 80)
    print()

    model_limits = {
        "GPT-4o / 4o-mini": 128000,
        "Claude 3.5 Sonnet": 200000,
        "Claude 3 Opus": 200000,
        "Claude Opus 4.5": 200000,
        "GPT-4 Turbo": 128000,
    }

    for model, limit in model_limits.items():
        percentage = (total_tokens / limit) * 100
        status = "✅" if percentage <= 80 else "⚠️" if percentage <= 95 else "❌"
        print(f"  {status} {model}:")
        print(f"      使用: {total_tokens:,} / {limit:,} tokens ({percentage:.1f}%)")
        if percentage > 100:
            print(f"      超出: {total_tokens - limit:,} tokens ({percentage - 100:.1f}%)")
        elif percentage > 80:
            print(f"      接近上限: {limit - total_tokens:,} tokens 可用")
        else:
            print(f"      可用: {limit - total_tokens:,} tokens ({100 - percentage:.1f}%)")
        print()

    # 问题诊断
    print("=" * 80)
    print("🔍 问题诊断")
    print("=" * 80)
    print()

    issues = []

    # 检查 1：消息历史过多
    if len(messages) > 10:
        issues.append(
            {
                "severity": "🔴 高",
                "problem": "消息历史过多",
                "description": f"当前有 {len(messages)} 条消息历史",
                "impact": f"占用 {message_tokens:,} tokens ({message_tokens / total_tokens * 100:.1f}% of total)",
                "solution": "使用智能压缩策略：保留最新 3-5 条消息，总结旧消息",
            }
        )

    # 检查 2：系统上下文过大
    if total_system_tokens > 4000:
        issues.append(
            {
                "severity": "🟡 中",
                "problem": "系统上下文过大",
                "description": f"系统上下文占用 {total_system_tokens:,} tokens",
                "impact": "超过推荐的 4000 tokens 限制",
                "solution": "压缩技能内容，只加载必要的技能；减少 bootstrap 文件内容",
            }
        )

    # 检查 3：技能内容重复
    if skill_ctx:
        issue = {
            "severity": "🟡 中",
            "problem": "技能内容可能重复",
            "description": "技能上下文包含多个技能的完整描述",
            "impact": "增加不必要的 Token 消耗",
            "solution": "渐进式加载：技能元数据始终可见，详细内容按需加载",
        }
        issues.append(issue)

    # 检查 4：Token 计算不准确
    issues.append(
        {
            "severity": "🟠 低",
            "problem": "Token 计算可能不准确",
            "description": "当前使用字符数 / 1.6 的估算方法",
            "impact": "可能导致实际 Token 数量与计算不符",
            "solution": "使用 tiktoken 进行精确计算",
        }
    )

    if not issues:
        print("  ✅ 未发现明显问题")
    else:
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue['severity']} {issue['problem']}")
            print(f"     描述: {issue['description']}")
            print(f"     影响: {issue['impact']}")
            print(f"     解决方案: {issue['solution']}")
            print()

    # 推荐配置
    print("=" * 80)
    print("⚙️  推荐配置")
    print("=" * 80)
    print()

    print("  建议的配置值：")
    print()
    print("  # nanobot/config/schema.py")
    print("  AgentDefaults:")
    print("    max_tokens: 8192  # 保持不变")
    print()
    print("  # nanobot/agent/context_manager.py")
    print("  ContextManager:")
    print("    max_system_tokens: 4000    # 系统上下文限制")
    print("    max_history_tokens: 4000    # 历史消息限制")
    print()
    print("  # nanobot/agent/context_compressor.py")
    print("  ContextCompressor:")
    print("    compress(): max_tokens=4000   # 与 context_manager 一致")
    print("    compress_messages(): max_tokens=4000  # 提高到合理值")
    print()
    print("  # nanobot/session/manager.py")
    print("  Session:")
    print("    get_history(): max_messages=20  # 从 50 降低到 20")
    print()

    # 压缩策略
    print("=" * 80)
    print("🗜️  智能压缩策略")
    print("=" * 80)
    print()

    print("  推荐的压缩策略：")
    print()
    print("  1. 消息历史压缩：")
    print("     - 保留系统消息（总是保留）")
    print("     - 保留最新 3-5 条用户消息")
    print("     - 保留最新 5-10 条工具调用结果")
    print("     - 对旧助手消息进行总结")
    print()
    print("  2. 技能内容压缩：")
    print("     - 只加载任务相关的技能")
    print("     - 限制技能数量（最多 5-10 个）")
    print("     - 使用技能元数据代替完整内容")
    print()
    print("  3. 记忆上下文压缩：")
    print("     - 限制记忆数量（最多 10-20 条）")
    print("     - 按时间倒序排列（最新优先）")
    print("     - 截断长记忆内容（最多 200 字符）")
    print()


if __name__ == "__main__":
    diagnose_context_issue()
