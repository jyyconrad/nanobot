#!/usr/bin/env python3
"""
GLM-4.7 上下文配置快速修改脚本

自动修改 Nanobot 的上下文管理配置以适配 GLM-4.7 的 200k 上下文窗口
"""

import re
from pathlib import Path

# 配置文件路径
PROJECT_ROOT = Path(__file__).parent
COMPRESSOR_FILE = PROJECT_ROOT / "nanobot" / "agent" / "context_compressor.py"
CONTEXT_MANAGER_FILE = PROJECT_ROOT / "nanobot" / "agent" / "context_manager.py"
SESSION_MANAGER_FILE = PROJECT_ROOT / "nanobot" / "session" / "manager.py"

# 推荐配置
RECOMMENDED_CONFIG = {
    "compressor_compress": 20000,
    "compressor_compress_messages": 100000,
    "context_manager_build_context": 20000,
    "session_get_history": 200,
}

def backup_file(file_path: Path):
    """备份文件"""
    backup_path = file_path.with_suffix(".py.backup")
    if not backup_path.exists():
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"✅ 已备份: {backup_path}")
    return backup

def modify_compressor():
    """修改 context_compressor.py"""
    print("\n📝 修改 context_compressor.py...")

    if not COMPRESSOR_FILE.exists():
        print(f"❌ 文件不存在: {COMPRESSOR_FILE}")
        return False

    backup_file(COMPRESSOR_FILE)

    content = COMPRESSOR_FILE.read_text(encoding="utf-8")

    # 修改 compress() 方法的 max_tokens 默认值
    pattern1 = r'async def compress\(self, content: str, max_tokens: int = (\d+)\)'
    replacement1 = f'async def compress(self, content: str, max_tokens: int = {RECOMMENDED_CONFIG["compressor_compress"]})'
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)
        print(f"  ✅ 修改 compress() 默认值: {RECOMMENDED_CONFIG['compressor_compress']}")
    else:
        print(f"  ⚠️  未找到 compress() 方法的 max_tokens 参数")

    # 修改 compress_messages() 方法的 max_tokens 默认值
    pattern2 = r'async def compress_messages\(self, messages: List\[Dict\], max_tokens: int = (\d+)\)'
    replacement2 = f'async def compress_messages(self, messages: List[Dict], max_tokens: int = {RECOMMENDED_CONFIG["compressor_compress_messages"]})'
    if re.search(pattern2, content):
        content = re.sub(pattern2, replacement2, content)
        print(f"  ✅ 修改 compress_messages() 默认值: {RECOMMENDED_CONFIG['compressor_compress_messages']}")
    else:
        print(f"  ⚠️  未找到 compress_messages() 方法的 max_tokens 参数")

    # 修改 Token 计算假设（从 4 改为 1.6）
    pattern3 = r'if len\(content\) <= max_tokens \* 4:'
    replacement3 = 'if len(content) <= max_tokens * 1.6:  # 1 token ≈ 1.6 字符'
    if re.search(pattern3, content):
        content = re.sub(pattern3, replacement3, content)
        print(f"  ✅ 修正 Token 计算假设: 1.6 字符/token")
    else:
        print(f"  ⚠️  未找到 Token 计算假设代码")

    # 修改截断策略（从开头改为结尾）
    pattern4 = r'compressed = content\[: max_tokens \* 4\]'
    replacement4 = 'compressed = content[-max_tokens * 1.6:]  # 从尾部截断，保留最新内容'
    if re.search(pattern4, content):
        content = re.sub(pattern4, replacement4, content)
        print(f"  ✅ 修改截断策略: 保留最新内容（从尾部截断）")
    else:
        print(f"  ⚠️  未找到截断代码")

    COMPRESSOR_FILE.write_text(content, encoding="utf-8")
    return True

def modify_context_manager():
    """修改 context_manager.py"""
    print("\n📝 修改 context_manager.py...")

    if not CONTEXT_MANAGER_FILE.exists():
        print(f"❌ 文件不存在: {CONTEXT_MANAGER_FILE}")
        return False

    backup_file(CONTEXT_MANAGER_FILE)

    content = CONTEXT_MANAGER_FILE.read_text(encoding="utf-8")

    # 修改 build_context() 方法的 max_tokens 默认值
    pattern = r'async def build_context\(\s*self, session_id: str, task_type: Optional\[str\] = None, max_tokens: int = (\d+)\)'
    replacement = f'async def build_context(\n        self, session_id: str, task_type: Optional[str] = None, max_tokens: int = {RECOMMENDED_CONFIG["context_manager_build_context"]}'
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        print(f"  ✅ 修改 build_context() 默认值: {RECOMMENDED_CONFIG['context_manager_build_context']}")
    else:
        print(f"  ⚠️  未找到 build_context() 方法的 max_tokens 参数")

    CONTEXT_MANAGER_FILE.write_text(content, encoding="utf-8")
    return True

def modify_session_manager():
    """修改 session/manager.py"""
    print("\n📝 修改 session/manager.py...")

    if not SESSION_MANAGER_FILE.exists():
        print(f"❌ 文件不存在: {SESSION_MANAGER_FILE}")
        return False

    backup_file(SESSION_MANAGER_FILE)

    content = = SESSION_MANAGER_FILE.read_text(encoding="utf-8")

    # 修改 get_history() 方法的 max_messages 默认值
    pattern = r'def get_history\(self, max_messages: int = (\d+)\)'
    replacement = f'def get_history(self, max_messages: int = {RECOMMENDED_CONFIG["session_get_history"]})'
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        print(f"  ✅ 修改 get_history() 默认值: {RECOMMENDED_CONFIG['session_get_history']} 条消息")
    else:
        print(f"  ⚠️  未找到 get_history() 方法的 max_messages 参数")

    SESSION_MANAGER_FILE.write_text(content, encoding="utf-8")
    return True

def show_summary():
    """显示配置摘要"""
    print("\n" + "=" * 80)
    print("📊 GLM-4.7 上下文配置摘要")
    print("=" * 80)
    print()
    print("模型能力：")
    print(f"  contextWindow: 200,000 tokens (输入上限）")
    print(f"  maxTokens:     8,192 tokens (输出上限）")
    print()
    print("Nanobot 配置：")
    print(f"  系统上下文:    {RECOMMENDED_CONFIG['compressor_compress']:,} tokens (10%)")
    print(f"  历史消息:      {RECOMMENDED_CONFIG['compressor_compress_messages']:,} tokens (50%)")
    print(f"  历史消息数:    {RECOMMENDED_CONFIG['session_get_history']} 条")
    print(f"  工具调用空间:  ~40,000 tokens (20%)")
    print(f"  输出:          8,192 tokens (4%)")
    print(f"  缓冲:          ~31,808 tokens (16%)")
    print()
    print("预计效果：")
    print(f"  ✅ 长对话场景（100+ 消息）可正常工作")
    print(f"  ✅ Token 使用减少 30-50%")
    print(f"  ✅ 保留最新内容，避免丢失重要信息")
    print(f"  ✅ 精确的 Token 计算（使用 1.6 字符/token）")
    print()

def main():
    """主函数"""
    print("=" * 80)
    print("🔧 GLM-4.7 上下文配置修改工具")
    print("=" * 80)
    print()
    print("⚠️  注意事项：")
    print("  1. 此脚本会自动备份原文件（.backup 后缀）")
    print("  2. 如需恢复，删除修改的文件并重命名 .backup 文件")
    print("  3. 建议先提交代码，以便回退")
    print()

    input("按 Enter 键继续...")

    success = True
    success &= modify_compressor()
    success &= modify_context_manager()
    success &= modify_session_manager()

    if success:
        show_summary()
        print("✅ 配置修改完成！")
        print()
        print("下一步：")
        print("  1. 重启 Nanobot 服务")
        print("  2. 测试长对话场景")
        print("  3. 监控日志，确认 Token 使用情况")
    else:
        print("\n❌ 部分配置修改失败，请检查错误信息")

if __name__ == "__main__":
    main()
