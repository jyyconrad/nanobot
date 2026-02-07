"""
Tests for workflow data models.
"""


from nanobot.agent.workflow.models import (
    MessageCategory,
    TaskState,
    WorkflowState,
    WorkflowStep,
)


class TestMessageCategory:
    """Tests for MessageCategory enum."""

    def test_message_category_values(self):
        """Test that all expected message categories are defined."""
        expected_categories = [
            "chat", "inquiry", "task_create", "task_status",
            "task_cancel", "task_complete", "task_list", "control",
            "help", "unknown"
        ]

        actual_categories = [category.value for category in MessageCategory]

        assert set(expected_categories) == set(actual_categories)

    def test_message_category_names(self):
        """Test that all expected message category names are defined."""
        expected_names = [
            "CHAT", "INQUIRY", "TASK_CREATE", "TASK_STATUS",
            "TASK_CANCEL", "TASK_COMPLETE", "TASK_LIST", "CONTROL",
            "HELP", "UNKNOWN"
        ]

        actual_names = [category.name for category in MessageCategory]

        assert set(expected_names) == set(actual_names)


class TestTaskState:
    """Tests for TaskState enum."""

    def test_task_state_values(self):
        """Test that all expected task states are defined."""
        expected_states = [
            "pending", "running", "paused", "completed", "cancelled", "failed"
        ]

        actual_states = [state.value for state in TaskState]

        assert set(expected_states) == set(actual_states)

    def test_task_state_names(self):
        """Test that all expected task state names are defined."""
        expected_names = [
            "PENDING", "RUNNING", "PAUSED", "COMPLETED", "CANCELLED", "FAILED"
        ]

        actual_names = [state.name for state in TaskState]

        assert set(expected_names) == set(actual_names)


class TestWorkflowState:
    """Tests for WorkflowState enum."""

    def test_workflow_state_values(self):
        """Test that all expected workflow states are defined."""
        expected_states = [
            "planning", "active", "paused", "completed", "failed"
        ]

        actual_states = [state.value for state in WorkflowState]

        assert set(expected_states) == set(actual_states)

    def test_workflow_state_names(self):
        """Test that all expected workflow state names are defined."""
        expected_names = [
            "PLANNING", "ACTIVE", "PAUSED", "COMPLETED", "FAILED"
        ]

        actual_names = [state.name for state in WorkflowState]

        assert set(expected_names) == set(actual_names)


class TestWorkflowStep:
    """Tests for WorkflowStep data model."""

    def test_workflow_step_creation(self):
        """Test that WorkflowStep can be created with basic parameters."""
        step = WorkflowStep(
            step_id="test_step",
            name="Test Step",
            description="This is a test step",
            dependencies=["step1", "step2"],
            status=TaskState.PENDING
        )

        assert step.step_id == "test_step"
        assert step.name == "Test Step"
        assert step.description == "This is a test step"
        assert step.dependencies == ["step1", "step2"]
        assert step.status == TaskState.PENDING
        assert step.start_time is None
        assert step.end_time is None
        assert step.output is None
        assert step.error is None

    def test_workflow_step_with_output(self):
        """Test that WorkflowStep can store output."""
        step = WorkflowStep(
            step_id="test_step",
            name="Test Step",
            description="This is a test step",
            status=TaskState.COMPLETED,
            output="Test output"
        )

        assert step.status == TaskState.COMPLETED
        assert step.output == "Test output"

    def test_workflow_step_with_error(self):
        """Test that WorkflowStep can store error information."""
        step = WorkflowStep(
            step_id="test_step",
            name="Test Step",
            description="This is a test step",
            status=TaskState.FAILED,
            error="Test error message"
        )

        assert step.status == TaskState.FAILED
        assert step.error == "Test error message"
