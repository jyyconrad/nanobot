"""
Tests for WorkflowManager.
"""

from pathlib import Path

from nanobot.agent.workflow.models import (
    MessageCategory,
    TaskState,
    WorkflowState,
    WorkflowStep,
)
from nanobot.agent.workflow.workflow_manager import WorkflowManager


class TestWorkflowManager:
    """Tests for WorkflowManager class."""

    def setup_method(self):
        """Setup method to create a new instance for each test."""
        import tempfile
        from pathlib import Path

        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.manager = WorkflowManager(workspace=self.tmp_path)

    def teardown_method(self):
        """Teardown method to clean up after each test."""
        self.tmp_dir.cleanup()

    def test_initialization(self):
        """Test that WorkflowManager initializes correctly."""
        assert self.manager is not None
        assert len(self.manager.workflows) == 0
        assert len(self.manager.tasks) == 0

    def test_create_workflow(self):
        """Test creating a workflow."""
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Initial Step",
                description="Initial step of the workflow",
                status=TaskState.PENDING,
            ),
            WorkflowStep(
                step_id="step2",
                name="Main Step",
                description="Main processing step",
                dependencies=["step1"],
                status=TaskState.PENDING,
            ),
        ]

        workflow_id = self.manager.create_workflow("Test Workflow", steps)

        assert workflow_id is not None
        assert len(self.manager.workflows) == 1
        assert workflow_id in self.manager.workflows

        workflow = self.manager.workflows[workflow_id]
        assert workflow["name"] == "Test Workflow"
        assert workflow["state"] == WorkflowState.PLANNING.value
        assert len(workflow["steps"]) == 2

        # Check that tasks were created
        task_ids = [step["step_id"] for step in workflow["steps"]]
        assert len(self.manager.tasks) == 2
        for task_id in task_ids:
            assert task_id in self.manager.tasks
            task = self.manager.tasks[task_id]
            assert task["workflow_id"] == workflow_id

    def test_get_workflow_state(self):
        """Test getting workflow state."""
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Initial Step",
                description="Initial step",
                status=TaskState.PENDING,
            ),
        ]

        workflow_id = self.manager.create_workflow("Test Workflow", steps)

        state = self.manager.get_workflow_state(workflow_id)
        assert state == WorkflowState.PLANNING

    def test_get_workflow_state_nonexistent(self):
        """Test getting state of nonexistent workflow."""
        state = self.manager.get_workflow_state("nonexistent")
        assert state is None

    def test_get_task_status(self):
        """Test getting task status."""
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Initial Step",
                description="Initial step",
                status=TaskState.PENDING,
            ),
        ]

        self.manager.create_workflow("Test Workflow", steps)

        task_id = steps[0].step_id
        status = self.manager.get_task_status(task_id)
        assert status == TaskState.PENDING

    def test_get_task_status_nonexistent(self):
        """Test getting status of nonexistent task."""
        status = self.manager.get_task_status("nonexistent")
        assert status is None

    def test_update_task_status(self):
        """Test updating task status."""
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Initial Step",
                description="Initial step",
                status=TaskState.PENDING,
            ),
        ]

        self.manager.create_workflow("Test Workflow", steps)

        task_id = steps[0].step_id
        self.manager.update_task_status(task_id, TaskState.RUNNING)

        status = self.manager.get_task_status(task_id)
        assert status == TaskState.RUNNING

    def test_pause_workflow(self):
        """Test pausing a workflow."""
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Initial Step",
                description="Initial step",
                status=TaskState.PENDING,
            ),
            WorkflowStep(
                step_id="step2",
                name="Main Step",
                description="Main processing step",
                dependencies=["step1"],
                status=TaskState.PENDING,
            ),
        ]

        workflow_id = self.manager.create_workflow("Test Workflow", steps)

        self.manager.start_workflow(workflow_id)
        assert self.manager.get_workflow_state(workflow_id) == WorkflowState.ACTIVE

        self.manager.pause_workflow(workflow_id)
        assert self.manager.get_workflow_state(workflow_id) == WorkflowState.PAUSED

        # Check all tasks are paused
        for task_id, task in self.manager.tasks.items():
            if task["workflow_id"] == workflow_id:
                assert task["status"] == TaskState.PAUSED.value

    def test_resume_workflow(self):
        """Test resuming a paused workflow."""
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Initial Step",
                description="Initial step",
                status=TaskState.PENDING,
            ),
        ]

        workflow_id = self.manager.create_workflow("Test Workflow", steps)

        self.manager.start_workflow(workflow_id)
        self.manager.pause_workflow(workflow_id)
        assert self.manager.get_workflow_state(workflow_id) == WorkflowState.PAUSED

        self.manager.resume_workflow(workflow_id)
        assert self.manager.get_workflow_state(workflow_id) == WorkflowState.ACTIVE

        # Check tasks are resumed to pending
        for task_id, task in self.manager.tasks.items():
            if task["workflow_id"] == workflow_id:
                assert task["status"] == TaskState.PENDING.value

    def test_complete_workflow(self):
        """Test completing a workflow."""
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Initial Step",
                description="Initial step",
                status=TaskState.PENDING,
            ),
        ]

        workflow_id = self.manager.create_workflow("Test Workflow", steps)

        self.manager.start_workflow(workflow_id)
        self.manager.complete_workflow(workflow_id)

        assert self.manager.get_workflow_state(workflow_id) == WorkflowState.COMPLETED

        # Check all tasks are completed
        for task_id, task in self.manager.tasks.items():
            if task["workflow_id"] == workflow_id:
                assert task["status"] == TaskState.COMPLETED.value

    def test_cancel_workflow(self):
        """Test cancelling a workflow."""
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Initial Step",
                description="Initial step",
                status=TaskState.PENDING,
            ),
        ]

        workflow_id = self.manager.create_workflow("Test Workflow", steps)

        self.manager.start_workflow(workflow_id)
        self.manager.cancel_workflow(workflow_id)

        assert self.manager.get_workflow_state(workflow_id) == WorkflowState.PAUSED

        # Check all tasks are cancelled
        for task_id, task in self.manager.tasks.items():
            if task["workflow_id"] == workflow_id:
                assert task["status"] == TaskState.CANCELLED.value

    def test_list_workflows(self):
        """Test listing all workflows."""
        assert len(self.manager.list_workflows()) == 0

        steps1 = [
            WorkflowStep(
                step_id="step1",
                name="Initial Step",
                description="Initial step",
                status=TaskState.PENDING,
            ),
        ]

        steps2 = [
            WorkflowStep(
                step_id="stepA",
                name="Step A",
                description="Step A",
                status=TaskState.PENDING,
            ),
        ]

        workflow1_id = self.manager.create_workflow("Workflow 1", steps1)
        workflow2_id = self.manager.create_workflow("Workflow 2", steps2)

        workflows = self.manager.list_workflows()
        assert len(workflows) == 2

        workflow_ids = [w["workflow_id"] for w in workflows]
        assert workflow1_id in workflow_ids
        assert workflow2_id in workflow_ids

    def test_get_workflow_tasks(self):
        """Test getting tasks in a workflow."""
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Step 1",
                description="Step 1",
                status=TaskState.PENDING,
            ),
            WorkflowStep(
                step_id="step2",
                name="Step 2",
                description="Step 2",
                dependencies=["step1"],
                status=TaskState.PENDING,
            ),
            WorkflowStep(
                step_id="step3",
                name="Step 3",
                description="Step 3",
                dependencies=["step2"],
                status=TaskState.PENDING,
            ),
        ]

        workflow_id = self.manager.create_workflow("Test Workflow", steps)

        tasks = self.manager.get_workflow_tasks(workflow_id)
        assert len(tasks) == 3

        task_ids = [step.step_id for step in steps]
        assert set(tasks) == set(task_ids)

    def test_handle_task_message(self):
        """Test handling task-related messages."""
        # Test task list message
        response = self.manager.handle_task_message(
            MessageCategory.TASK_LIST, "列出任务"
        )
        assert "No active workflows" in response

        # Create a workflow and test again
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Step 1",
                description="Step 1",
                status=TaskState.PENDING,
            ),
        ]

        workflow_id = self.manager.create_workflow("Test Workflow", steps)

        response = self.manager.handle_task_message(
            MessageCategory.TASK_LIST, "列出任务"
        )
        assert "Test Workflow" in response
        assert workflow_id in response

    def test_workflow_manager_session_isolation(self, tmp_path: Path):
        """Test that workflow managers are isolated between sessions."""
        manager1 = WorkflowManager(workspace=tmp_path)
        manager2 = WorkflowManager(workspace=tmp_path)

        # Create a workflow in manager1
        steps = [
            WorkflowStep(
                step_id="step1",
                name="Step 1",
                description="Step 1",
                status=TaskState.PENDING,
            ),
        ]

        workflow_id = manager1.create_workflow("Test Workflow", steps)

        assert workflow_id in manager1.workflows
        assert workflow_id not in manager2.workflows
