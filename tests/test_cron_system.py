"""
Cron 系统测试模块

包含 CronSystem 的测试用例
"""

import datetime
import logging
import time
import unittest

from nanobot.agent.cron_system import (
    CronSystem,
    JobConfig,
    JobType,
    add_cron_job,
    add_interval_job,
    add_once_job,
    create_cron_system,
)

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestCronSystem(unittest.TestCase):
    """
    Cron 系统测试类
    """

    def setUp(self):
        """
        测试前初始化
        """
        self.cron = create_cron_system()
        self.test_counter = 0
        logger.debug("CronSystem 测试初始化完成")

    def tearDown(self):
        """
        测试后清理
        """
        if self.cron.is_running():
            self.cron.stop()
        self.cron.clear_all_jobs()
        logger.debug("CronSystem 测试清理完成")

    def test_create_cron_system(self):
        """
        测试创建 Cron 系统实例
        """
        self.assertIsInstance(self.cron, CronSystem)
        self.assertFalse(self.cron.is_running())

    def test_add_interval_job(self):
        """
        测试添加间隔任务
        """

        def test_task():
            self.test_counter += 1

        job_id = add_interval_job(
            self.cron,
            name="test_interval_job",
            function=test_task,
            seconds=1,
            enabled=True,
        )

        self.assertIn(job_id, [job["job_id"] for job in self.cron.get_all_jobs()])

    def test_add_cron_job(self):
        """
        测试添加 Cron 任务
        """

        def test_task():
            self.test_counter += 1

        job_id = add_cron_job(
            self.cron,
            name="test_cron_job",
            function=test_task,
            cron_str="* * * * *",
            enabled=True,
        )

        self.assertIn(job_id, [job["job_id"] for job in self.cron.get_all_jobs()])

    def test_add_once_job(self):
        """
        测试添加一次性任务
        """

        def test_task():
            self.test_counter += 1

        run_at = datetime.datetime.now() + datetime.timedelta(seconds=30)
        job_id = add_once_job(
            self.cron,
            name="test_once_job",
            function=test_task,
            run_at=run_at,
            enabled=True,
        )

        self.assertIn(job_id, [job["job_id"] for job in self.cron.get_all_jobs()])

    def test_remove_job(self):
        """
        测试移除任务
        """

        def test_task():
            pass

        job_id = add_interval_job(
            self.cron,
            name="test_remove_job",
            function=test_task,
            seconds=60,
            enabled=True,
        )

        self.assertTrue(self.cron.remove_job(job_id))
        self.assertNotIn(job_id, [job["job_id"] for job in self.cron.get_all_jobs()])

    def test_enable_disable_job(self):
        """
        测试启用/禁用任务
        """

        def test_task():
            pass

        job_id = add_interval_job(
            self.cron,
            name="test_enable_job",
            function=test_task,
            seconds=60,
            enabled=True,
        )

        # 测试禁用
        self.assertTrue(self.cron.disable_job(job_id))
        self.assertFalse(self.cron.get_all_jobs()[0]["enabled"])

        # 测试启用
        self.assertTrue(self.cron.enable_job(job_id))
        self.assertTrue(self.cron.get_all_jobs()[0]["enabled"])

    def test_start_stop_system(self):
        """
        测试启动和停止调度器
        """
        self.assertFalse(self.cron.is_running())

        self.assertTrue(self.cron.start())
        self.assertTrue(self.cron.is_running())

        self.assertTrue(self.cron.stop())
        self.assertFalse(self.cron.is_running())

    def test_job_count(self):
        """
        测试获取任务计数
        """

        def test_task():
            pass

        # 添加 3 个任务
        job1 = add_interval_job(self.cron, "job1", test_task, 60)
        job2 = add_interval_job(self.cron, "job2", test_task, 60)
        job3 = add_interval_job(self.cron, "job3", test_task, 60)

        # 禁用一个任务
        self.cron.disable_job(job3)

        total, enabled, running = self.cron.get_job_count()
        self.assertEqual(total, 3)
        self.assertEqual(enabled, 2)
        self.assertEqual(running, 0)

    def test_job_status_tracking(self):
        """
        测试任务状态跟踪
        """

        def test_task():
            self.test_counter += 1

        job_id = add_interval_job(
            self.cron,
            name="test_status_job",
            function=test_task,
            seconds=1,
            enabled=True,
        )

        status = self.cron.get_job_status(job_id)
        self.assertIsNotNone(status)
        self.assertEqual(status.name, "test_status_job")
        self.assertEqual(status.job_type, JobType.INTERVAL)
        self.assertEqual(status.run_count, 0)

    def test_interval_job_execution(self):
        """
        测试间隔任务执行
        """

        def test_task():
            self.test_counter += 1

        job_id = add_interval_job(
            self.cron,
            name="test_execution_job",
            function=test_task,
            seconds=0.5,
            enabled=True,
        )

        self.cron.start()

        # 等待任务执行
        time.sleep(1.5)

        self.cron.stop()

        status = self.cron.get_job_status(job_id)
        logger.debug(f"任务执行计数: {status.run_count}")
        self.assertGreater(status.run_count, 0)
        self.assertEqual(self.test_counter, status.run_count)

    def test_job_error_handling(self):
        """
        测试任务错误处理
        """

        def error_task():
            raise Exception("测试错误")

        job_id = add_interval_job(
            self.cron,
            name="test_error_job",
            function=error_task,
            seconds=0.5,
            enabled=True,
        )

        self.cron.start()

        # 等待任务执行
        time.sleep(1.5)

        self.cron.stop()

        status = self.cron.get_job_status(job_id)
        self.assertGreater(status.run_count, 0)
        self.assertGreater(status.failure_count, 0)
        self.assertIsNotNone(status.error)
        logger.debug(f"任务错误信息: {status.error}")

    def test_job_metadata(self):
        """
        测试任务元数据
        """

        def test_task():
            pass

        metadata = {"description": "测试任务", "category": "test"}

        job_id = add_interval_job(
            self.cron,
            name="test_metadata_job",
            function=test_task,
            seconds=60,
            enabled=True,
            metadata=metadata,
        )

        jobs_info = self.cron.get_all_jobs()
        self.assertIn(job_id, [job["job_id"] for job in jobs_info])

        for job in jobs_info:
            if job["job_id"] == job_id:
                self.assertEqual(job["metadata"]["description"], "测试任务")
                self.assertEqual(job["metadata"]["category"], "test")


if __name__ == "__main__":
    logger.info("开始运行 Cron 系统测试")
    unittest.main()
