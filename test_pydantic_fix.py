"""
测试 Pydantic V2 修复是否成功
"""

import sys
from pathlib import Path

# 添加项目路径
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

from nanobot.agent.memory.models import Memory
from nanobot.agent.planner.cancellation_detector import CancellationDetector
from nanobot.agent.planner.complexity_analyzer import ComplexityAnalyzer
from nanobot.agent.planner.correction_detector import CorrectionDetector
from nanobot.agent.planner.task_detector import TaskDetector
from nanobot.agent.planner.task_planner import TaskPlanner
from nanobot.agent.subagent.agno_subagent import AgnoSubagent
from nanobot.config.schema import Config


def test_pydantic_config_fix():
    """测试 Pydantic config 修复是否成功"""
    
    print("Testing Pydantic V2 ConfigDict fix...")
    
    # 测试 Memory 模型
    try:
        memory = Memory(
            id="test-1",
            content="测试记忆内容",
            tags=["test"],
            task_id="task-1"
        )
        print("✓ Memory model works correctly")
    except Exception as e:
        print(f"✗ Memory model failed: {e}")
        return False
    
    # 测试 CancellationDetector
    try:
        detector = CancellationDetector()
        print("✓ CancellationDetector works correctly")
    except Exception as e:
        print(f"✗ CancellationDetector failed: {e}")
        return False
    
    # 测试 ComplexityAnalyzer
    try:
        analyzer = ComplexityAnalyzer()
        print("✓ ComplexityAnalyzer works correctly")
    except Exception as e:
        print(f"✗ ComplexityAnalyzer failed: {e}")
        return False
    
    # 测试 CorrectionDetector
    try:
        detector = CorrectionDetector()
        print("✓ CorrectionDetector works correctly")
    except Exception as e:
        print(f"✗ CorrectionDetector failed: {e}")
        return False
    
    # 测试 TaskDetector
    try:
        detector = TaskDetector()
        print("✓ TaskDetector works correctly")
    except Exception as e:
        print(f"✗ TaskDetector failed: {e}")
        return False
    
    # 测试 TaskPlanner
    try:
        planner = TaskPlanner()
        print("✓ TaskPlanner works correctly")
    except Exception as e:
        print(f"✗ TaskPlanner failed: {e}")
        return False
    
    # 测试 AgnoSubagent
    try:
        subagent = AgnoSubagent(
            task_id="task-1",
            task="测试任务",
            label="测试标签"
        )
        print("✓ AgnoSubagent works correctly")
    except Exception as e:
        print(f"✗ AgnoSubagent failed: {e}")
        return False
    
    # 测试 Config
    try:
        config = Config()
        print("✓ Config works correctly")
    except Exception as e:
        print(f"✗ Config failed: {e}")
        return False
    
    print("\n✅ All Pydantic models are working correctly with ConfigDict")
    return True


def test_version():
    """测试版本号是否正确更新"""
    from nanobot import __version__
    
    print(f"Current version: {__version__}")
    
    if __version__ == "0.4.0":
        print("✓ Version number is correctly set to 0.4.0")
        return True
    else:
        print(f"✗ Version number is incorrect. Expected '0.4.0', got '{__version__}'")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Nanobot v0.4.0 Pydantic Fix Verification")
    print("=" * 50)
    
    success = True
    
    if not test_pydantic_config_fix():
        success = False
    
    print()
    
    if not test_version():
        success = False
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ All checks passed - Nanobot v0.4.0 is ready for use!")
    else:
        print("❌ Some checks failed - please check the errors")
        sys.exit(1)
