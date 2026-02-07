import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nanobot.agent.planner.correction_detector import CorrectionDetector

async def debug_remove():
    detector = CorrectionDetector()
    test_input = "删除不必要的代码"
    
    print("测试输入:", test_input)
    
    # 检查是否是否定句
    is_negation = await detector._is_negation(test_input)
    print("是否定句:", is_negation)
    
    # 检查是否包含修正模式
    has_pattern = await detector._contains_correction_pattern(test_input)
    print("包含修正模式:", has_pattern)
    
    # 检查是否与任务相关
    context = {"last_task": {"description": "编写Python函数"}}
    is_related = await detector._is_related_to_last_task(test_input, context["last_task"])
    print("与任务相关:", is_related)
    
    # 检测修正
    correction = await detector.detect_correction(test_input, context)
    print("检测到修正:", correction)
    
    # 直接调用 _detect_correction_type
    correction_type = await detector._detect_correction_type(test_input)
    print("直接检测修正类型:", correction_type)

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_remove())
