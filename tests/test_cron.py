"""
定时任务模块测试
"""

import pytest
from nanobot.cron.types import CronJob, CronSchedule, CronAction
from nanobot.cron.config_loader import CronConfigLoader
from nanobot.cron.agent_trigger import AgentTrigger


def test_cron_job_creation():
    """测试定时任务创建"""
    job = CronJob(
        id="test_job_1",
        name="test_job",
        description="测试定时任务",
        schedule=CronSchedule(kind="cron", expr="*/5 * * * *"),
        action=CronAction(type="agent_turn", message="Hello from cron")
    )
    
    assert job is not None
    assert job.id == "test_job_1"
    assert job.name == "test_job"
    assert job.description == "测试定时任务"
    assert job.schedule.kind == "cron"
    assert job.schedule.expr == "*/5 * * * *"
    assert job.action.type == "agent_turn"
    
    print("定时任务创建测试通过")


def test_cron_config_loader():
    """测试定时任务配置加载器"""
    loader = CronConfigLoader()
    assert loader is not None
    assert hasattr(loader, "load_config")
    assert hasattr(loader, "validate_config")
    
    print("定时任务配置加载器测试通过")


def test_agent_trigger():
    """测试代理触发器"""
    trigger = AgentTrigger()
    assert trigger is not None
    assert hasattr(trigger, "trigger_agent")
    
    print("代理触发器测试通过")


def test_cron_job_validation():
    """测试定时任务验证"""
    # 注意：CronConfigLoader.validate_config 期望的是包含 version 和 jobs 的完整配置
    invalid_configs = [
        # 缺少 version
        {"jobs": [{"id": "test", "name": "test", "schedule": {"kind": "cron", "expr": "*/5 * * * *"}, "action": {"type": "agent_turn"}}]},
        # 缺少 jobs
        {"version": 2},
        # jobs 不是列表
        {"version": 2, "jobs": {"id": "test", "name": "test"}}
    ]
    
    loader = CronConfigLoader()
    
    for config_data in invalid_configs:
        assert not loader.validate_config(config_data)
    
    print("定时任务验证测试通过")


if __name__ == "__main__":
    test_cron_job_creation()
    test_cron_config_loader()
    test_agent_trigger()
    test_cron_job_validation()
    print("所有定时任务模块测试通过！")
