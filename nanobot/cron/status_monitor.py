"""
状态监听器
============

监听 Agent 状态并根据条件触发响应
"""

import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger

from nanobot.agent.subagent import SubagentManager
from nanobot.agent.task import TaskStatus
from nanobot.agent.task_manager import TaskManager
from nanobot.bus.queue import MessageBus
from nanobot.cron.agent_trigger import AgentTrigger


class AgentStatusMonitor:
    """
    Agent 状态监听器：监听 Agent 状态并根据条件触发响应
    
    主要功能：
    - 定期监控 Agent 和任务状态
    - 根据预设条件检查状态
    - 触发相应的响应动作
    """

    def __init__(
        self,
        task_manager: TaskManager,
        subagent_manager: SubagentManager,
        agent_trigger: AgentTrigger,
        bus: MessageBus
    ):
        self._task_manager = task_manager
        self._subagent_manager = subagent_manager
        self._agent_trigger = agent_trigger
        self._bus = bus

    async def monitor_agent(self, agent: str, checks: List[str]) -> Dict[str, Any]:
        """
        监听指定 Agent 的状态
        
        Args:
            agent: 目标 Agent
            checks: 要执行的检查类型列表
            
        Returns:
            监听结果
        """
        logger.info(f"Monitoring agent: {agent} with checks: {checks}")

        # 收集 Agent 状态
        status = await self._get_agent_status(agent)

        # 执行检查
        results = {}
        alerts = []

        for check_type in checks:
            check_result = await self._perform_check(agent, check_type, status)
            results[check_type] = check_result

            if "alert" in check_result and check_result["alert"]:
                alerts.append(check_result["alert"])

        # 如果有告警，处理告警
        if alerts:
            await self._handle_alerts(alerts)

        return {
            "agent": agent,
            "status": status,
            "checks": results,
            "alerts": alerts
        }

    async def _get_agent_status(self, agent: str) -> Dict[str, Any]:
        """
        获取 Agent 状态
        
        Args:
            agent: Agent 名称
            
        Returns:
            Agent 状态信息
        """
        if agent == "mainAgent":
            # 获取 mainAgent 状态
            return await self._agent_trigger.trigger_agent("mainAgent", "check_status")
        else:
            # 获取子代理状态
            return await self._agent_trigger.trigger_agent(agent, "check_status")

    async def _perform_check(
        self,
        agent: str,
        check_type: str,
        status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行特定类型的检查
        
        Args:
            agent: Agent 名称
            check_type: 检查类型
            status: Agent 状态信息
            
        Returns:
            检查结果
        """
        if check_type == "high_failure_rate":
            return await self._check_high_failure_rate(status)
        elif check_type == "stalled_tasks":
            return await self._check_stalled_tasks(status)
        elif check_type == "high_subagent_count":
            return await self._check_high_subagent_count(status)
        elif check_type == "message_bus_backlog":
            return await self._check_message_bus_backlog(status)
        elif check_type == "task_timeout":
            return await self._check_task_timeout()
        else:
            logger.warning(f"Unknown check type: {check_type}")
            return {"success": False, "error": f"Unknown check type: {check_type}"}

    async def _check_high_failure_rate(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """检查任务失败率是否过高"""
        tasks = status.get("tasks", {})
        total_tasks = tasks.get("active", 0) + tasks.get("completed", 0) + tasks.get("failed", 0)

        if total_tasks > 0:
            failure_rate = tasks.get("failed", 0) / total_tasks

            if failure_rate > 0.3:  # 30% 失败率
                return {
                    "success": False,
                    "alert": {
                        "type": "high_failure_rate",
                        "severity": "high",
                        "message": f"High failure rate detected: {failure_rate:.1%}",
                        "suggested_action": "Investigate failing tasks"
                    },
                    "failure_rate": failure_rate
                }

        return {"success": True, "failure_rate": 0}

    async def _check_stalled_tasks(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """检查是否有停滞的任务"""
        stalled_tasks = []

        # 查找超过 5 分钟未更新的任务
        active_tasks = self._task_manager.get_active_tasks()

        for task in active_tasks:
            time_since_update = (
                asyncio.get_event_loop().time() - task.updated_at.timestamp()
            )
            if time_since_update > 300:  # 5分钟
                stalled_tasks.append(task.id)

        if stalled_tasks:
            return {
                "success": False,
                "alert": {
                    "type": "stalled_tasks",
                    "severity": "medium",
                    "message": f"Found {len(stalled_tasks)} stalled tasks",
                    "suggested_action": "Restart or cancel stalled tasks",
                    "task_ids": stalled_tasks
                },
                "stalled_tasks": len(stalled_tasks)
            }

        return {"success": True, "stalled_tasks": 0}

    async def _check_high_subagent_count(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """检查子代理数量是否过多"""
        subagent_count = status.get("subagents", 0)

        if subagent_count > 20:  # 超过20个运行中的子代理
            return {
                "success": False,
                "alert": {
                    "type": "high_subagent_count",
                    "severity": "medium",
                    "message": f"High subagent count detected: {subagent_count}",
                    "suggested_action": "Check for zombie processes"
                },
                "subagent_count": subagent_count
            }

        return {"success": True, "subagent_count": subagent_count}

    async def _check_message_bus_backlog(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """检查消息总线是否有积压"""
        bus_status = status.get("message_bus", {})

        if bus_status.get("inbound", 0) > 100:
            return {
                "success": False,
                "alert": {
                    "type": "message_bus_backlog",
                    "severity": "high",
                    "message": f"Message bus backlog: {bus_status['inbound']} inbound messages",
                    "suggested_action": "Check agent processing speed"
                },
                "backlog_size": bus_status["inbound"]
            }

        return {"success": True, "backlog_size": 0}

    async def _check_task_timeout(self) -> Dict[str, Any]:
        """检查任务超时"""
        timeout_tasks = []

        # 查找运行时间超过 30 分钟的任务
        running_tasks = self._task_manager.get_tasks_by_status(TaskStatus.RUNNING)

        for task in running_tasks:
            runtime = (
                asyncio.get_event_loop().time() - task.created_at.timestamp()
            )
            if runtime > 1800:  # 30分钟
                timeout_tasks.append(task.id)

        if timeout_tasks:
            return {
                "success": False,
                "alert": {
                    "type": "task_timeout",
                    "severity": "high",
                    "message": f"Found {len(timeout_tasks)} timed out tasks",
                    "suggested_action": "Cancel timed out tasks",
                    "task_ids": timeout_tasks
                },
                "timeout_tasks": len(timeout_tasks)
            }

        return {"success": True, "timeout_tasks": 0}

    async def _handle_alerts(self, alerts: List[Dict[str, Any]]):
        """
        处理告警
        
        Args:
            alerts: 告警列表
        """
        for alert in alerts:
            logger.warning(f"Handling alert: {alert['type']} - {alert['message']}")

            # 根据告警类型触发响应动作
            if alert["type"] == "stalled_tasks" and "task_ids" in alert:
                await self._handle_stalled_tasks(alert["task_ids"])
            elif alert["type"] == "task_timeout" and "task_ids" in alert:
                await self._handle_timeout_tasks(alert["task_ids"])
            elif alert["type"] == "high_failure_rate":
                await self._handle_high_failure_rate(alert)
            elif alert["type"] == "high_subagent_count":
                await self._handle_high_subagent_count(alert)

    async def _handle_stalled_tasks(self, task_ids: List[str]):
        """处理停滞的任务"""
        for task_id in task_ids:
            logger.info(f"Handling stalled task: {task_id}")

            # 尝试取消任务
            subagent_id = self._subagent_manager.get_subagent_by_task_id(task_id)
            if subagent_id:
                await self._subagent_manager.cancel_subagent(subagent_id)

            # 更新任务状态
            task = self._task_manager.get_task(task_id)
            if task:
                task.mark_failed("Task stalled (no progress for 5 minutes)")

    async def _handle_timeout_tasks(self, task_ids: List[str]):
        """处理超时任务"""
        for task_id in task_ids:
            logger.info(f"Handling timed out task: {task_id}")

            subagent_id = self._subagent_manager.get_subagent_by_task_id(task_id)
            if subagent_id:
                await self._subagent_manager.cancel_subagent(subagent_id)

            task = self._task_manager.get_task(task_id)
            if task:
                task.mark_failed("Task timed out (running for over 30 minutes)")

    async def _handle_high_failure_rate(self, alert: Dict[str, Any]):
        """处理高失败率"""
        logger.warning(f"High failure rate detected: {alert['message']}")

    async def _handle_high_subagent_count(self, alert: Dict[str, Any]):
        """处理高子代理数量"""
        logger.warning(f"High subagent count detected: {alert['message']}")

    async def check_conditions(self, status: Dict[str, Any], conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查指定条件是否满足
        
        Args:
            status: Agent 状态
            conditions: 要检查的条件
            
        Returns:
            满足条件的列表
        """
        alerts = []

        for condition_name, condition_config in conditions.items():
            if condition_config.get("enabled", True):
                alert = await self._check_condition(condition_name, condition_config, status)
                if alert:
                    alerts.append(alert)

        return alerts

    async def _check_condition(
        self,
        name: str,
        config: Dict[str, Any],
        status: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        检查单个条件
        
        Args:
            name: 条件名称
            config: 条件配置
            status: Agent 状态
            
        Returns:
            告警信息（如条件满足），否则返回None
        """
        condition_type = config.get("type")

        if condition_type == "threshold":
            return await self._check_threshold_condition(name, config, status)
        elif condition_type == "absent":
            return await self._check_absent_condition(name, config, status)
        elif condition_type == "contains":
            return await self._check_contains_condition(name, config, status)

        logger.warning(f"Unknown condition type: {condition_type}")
        return None

    async def _check_threshold_condition(
        self,
        name: str,
        config: Dict[str, Any],
        status: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """检查阈值条件"""
        field = config.get("field")
        threshold = config.get("threshold")
        operator = config.get("operator", ">")

        try:
            value = status
            for part in field.split("."):
                value = value.get(part, 0)

            # 比较值与阈值
            if operator == ">" and value > threshold:
                return {
                    "type": "threshold_exceeded",
                    "name": name,
                    "severity": config.get("severity", "medium"),
                    "message": config.get("message", f"{field} exceeds {threshold}"),
                    "field": field,
                    "value": value,
                    "threshold": threshold
                }
            elif operator == "<" and value < threshold:
                return {
                    "type": "threshold_breached",
                    "name": name,
                    "severity": config.get("severity", "medium"),
                    "message": config.get("message", f"{field} falls below {threshold}"),
                    "field": field,
                    "value": value,
                    "threshold": threshold
                }

        except Exception as e:
            logger.error(f"Failed to check condition '{name}': {e}")

        return None

    async def _check_absent_condition(
        self,
        name: str,
        config: Dict[str, Any],
        status: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """检查不存在条件"""
        # 简化实现
        logger.warning("Absent condition check not fully implemented")
        return None

    async def _check_contains_condition(
        self,
        name: str,
        config: Dict[str, Any],
        status: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """检查包含条件"""
        # 简化实现
        logger.warning("Contains condition check not fully implemented")
        return None
