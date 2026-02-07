import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nanobot.agent.planner.correction_detector import CorrectionDetector


async def main():
    detector = CorrectionDetector()

    # 测试删除类型修正检测
    test_cases = ["删除不必要的代码", "移除多余的文件", "去掉无效的配置", "取消过时的功能"]

    for i, test_input in enumerate(test_cases):
        print(f'测试用例 {i + 1}: "{test_input}"')

        # 检查是否是否定句
        is_negation = await detector._is_negation(test_input)
        print(f"  是否定句: {is_negation}")

        # 检查是否包含修正模式
        has_pattern = await detector._contains_correction_pattern(test_input)
        print(f"  包含修正模式: {has_pattern}")

        # 检查检测到的修正类型
        correction_type = await detector._detect_correction_type(test_input)
        print(f"  修正类型检测: {correction_type}")

        correction = await detector.detect_correction(test_input)
        if correction:
            print(f"  修正类型: {correction.type}")
            print(f"  内容: {correction.content}")
            print(f"  目标: {correction.target}")
            print(f"  置信度: {correction.confidence}")
        else:
            print("  未检测到修正")
        print()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
