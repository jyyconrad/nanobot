import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nanobot.agent.planner.task_planner import TaskPlanner

async def debug_complex_task():
    planner = TaskPlanner()
    user_input = "实现一个高性能的图像识别系统，包含数据预处理、特征提取、模型训练和评估"
    
    print("用户输入:", user_input)
    
    # 获取任务类型
    task_type = await planner.get_task_type(user_input)
    print("任务类型:", task_type)
    
    # 分析复杂度
    complexity = await planner.complexity_analyzer.analyze_complexity(user_input, task_type)
    print("复杂度:", complexity)
    
    # 判断是否复杂
    is_complex = await planner.is_complex_task(user_input)
    print("是否复杂:", is_complex)

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_complex_task())
