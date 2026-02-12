#!/usr/bin/env python3
"""
性能测试脚本 - 测试技能加载和任务分析速度
"""

import asyncio
import time
from uuid import uuid4

from nanobot.agent.enhanced_main_agent import EnhancedMainAgent
from nanobot.agent.skill_loader import SkillLoader


async def test_skill_loading_performance():
    """测试技能加载性能"""
    print("=== 技能加载性能测试 ===")
    
    skill_loader = SkillLoader()
    
    # 测试加载不同任务类型的技能
    task_types = ["coding", "debugging", "security", "testing", "planning", "writing", "research", "translation"]
    
    times = []
    for task_type in task_types:
        start_time = time.time()
        skills = await skill_loader.load_skills_for_task(task_type)
        end_time = time.time()
        
        duration = end_time - start_time
        times.append(duration)
        
        print(f"{task_type}: {len(skills)} 个技能，耗时 {duration:.3f} 秒")
    
    avg_time = sum(times) / len(times)
    print(f"\n平均加载时间: {avg_time:.3f} 秒")
    
    return avg_time


async def test_task_analysis_performance():
    """测试任务分析性能"""
    print("\n=== 任务分析性能测试 ===")
    
    main_agent = EnhancedMainAgent(session_id=str(uuid4()))
    
    test_messages = [
        "修复 Python 代码中的 bug",
        "编写文档",
        "进行安全审计",
        "分析数据",
        "测试功能",
        "设计架构",
        "优化算法",
        "翻译文档",
        "研究新技术",
        "调试系统"
    ]
    
    times = []
    for message in test_messages:
        start_time = time.time()
        decision = await main_agent._make_skill_decision(message)
        end_time = time.time()
        
        duration = end_time - start_time
        times.append(duration)
        
        print(f"\"{message[:30]}...\": 决策时间 {duration:.3f} 秒")
    
    avg_time = sum(times) / len(times)
    print(f"\n平均分析时间: {avg_time:.3f} 秒")
    
    return avg_time


async def test_concurrency_performance():
    """测试并发性能"""
    print("\n=== 并发性能测试 ===")
    
    main_agent = EnhancedMainAgent(session_id=str(uuid4()))
    
    test_messages = [
        "修复 Python 代码中的 bug",
        "编写文档",
        "进行安全审计",
        "分析数据",
        "测试功能"
    ]
    
    # 并发执行
    start_time = time.time()
    tasks = []
    for message in test_messages:
        task = asyncio.create_task(main_agent._make_skill_decision(message))
        tasks.append(task)
    
    decisions = await asyncio.gather(*tasks)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"并发分析 5 个任务: 总耗时 {duration:.3f} 秒")
    
    return duration


async def main():
    """主函数"""
    skill_time = await test_skill_loading_performance()
    analysis_time = await test_task_analysis_performance()
    concurrency_time = await test_concurrency_performance()
    
    print("\n=== 性能测试总结 ===")
    print(f"技能加载平均时间: {skill_time:.3f} 秒")
    print(f"任务分析平均时间: {analysis_time:.3f} 秒")
    print(f"并发 5 个任务: {concurrency_time:.3f} 秒")
    
    print("\n✅ 性能测试完成")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
