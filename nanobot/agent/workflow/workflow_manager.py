"""
Workflow manager for Nanobot - manages workflow creation, state tracking, and task management.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    MessageCategory,
    TaskState,
    WorkflowState,
    WorkflowStep,
)


class WorkflowManager:
    """
    Workflow manager that handles workflow creation, state tracking, and task management.
    """

    def __init__(self, workspace: Path = Path("workspace")):
        self.workspace = workspace
        self.workflows: Dict[str, Dict] = {}
        self.tasks: Dict[str, Dict] = {}
        self._initialize_workspace()
        self._load_workflows_from_file()

    def _initialize_workspace(self):
        """Initialize workspace directory if it doesn't exist."""
        if not self.workspace.exists():
            self.workspace.mkdir(parents=True, exist_ok=True)

        # Create workflows directory if it doesn't exist
        self.workflows_dir = self.workspace / "workflows"
        if not self.workflows_dir.exists():
            self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def _load_workflows_from_file(self):
        """Load workflows from configuration file."""
        config_file = self.workflows_dir / "workflows.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.workflows = data.get("workflows", {})
                    self.tasks = data.get("tasks", {})
                    print(f"Loaded {len(self.workflows)} workflows and {len(self.tasks)} tasks from {config_file}")
            except Exception as e:
                print(f"Failed to load workflows from {config_file}: {e}")

    def _save_workflows_to_file(self):
        """Save workflows to configuration file."""
        config_file = self.workflows_dir / "workflows.json"
        try:
            data = {
                "workflows": self.workflows,
                "tasks": self.tasks,
            }
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            print(f"Saved {len(self.workflows)} workflows and {len(self.tasks)} tasks to {config_file}")
        except Exception as e:
            print(f"Failed to save workflows to {config_file}: {e}")

    def create_workflow(self, name: str, steps: List[WorkflowStep]) -> str:
        """
        Create a new workflow.

        Args:
            name: Workflow name
            steps: List of workflow steps

        Returns:
            str: Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        self.workflows[workflow_id] = {
            "name": name,
            "steps": [step.__dict__() for step in steps],
            "state": WorkflowState.PLANNING.value,
            "created_at": self._get_current_time(),
            "updated_at": self._get_current_time(),
        }

        # Create tasks from steps
        for step in steps:
            self.create_task(workflow_id, step.step_id, step.description)

        self._save_workflows_to_file()
        return workflow_id

    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Get the current state of a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Optional[WorkflowState]: Current workflow state or None if not found
        """
        if workflow_id not in self.workflows:
            return None

        return WorkflowState(self.workflows[workflow_id]["state"])

    def create_task(self, workflow_id: str, task_id: str, description: str) -> str:
        """
        Create a new task in a workflow.

        Args:
            workflow_id: Workflow ID
            task_id: Task ID
            description: Task description

        Returns:
            str: Task ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.tasks[task_id] = {
            "workflow_id": workflow_id,
            "description": description,
            "status": TaskState.PENDING.value,
            "created_at": self._get_current_time(),
            "updated_at": self._get_current_time(),
        }

        self._save_workflows_to_file()
        return task_id

    def get_task_status(self, task_id: str) -> Optional[TaskState]:
        """
        Get the current status of a task.

        Args:
            task_id: Task ID

        Returns:
            Optional[TaskState]: Current task state or None if not found
        """
        if task_id not in self.tasks:
            return None

        return TaskState(self.tasks[task_id]["status"])

    def pause_workflow(self, workflow_id: str) -> None:
        """
        Pause a workflow.

        Args:
            workflow_id: Workflow ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.workflows[workflow_id]["state"] = WorkflowState.PAUSED.value
        self.workflows[workflow_id]["updated_at"] = self._get_current_time()

        # Pause all tasks in this workflow
        for task_id, task in self.tasks.items():
            if task["workflow_id"] == workflow_id:
                self.tasks[task_id]["status"] = TaskState.PAUSED.value
                self.tasks[task_id]["updated_at"] = self._get_current_time()

        self._save_workflows_to_file()

    def resume_workflow(self, workflow_id: str) -> None:
        """
        Resume a paused workflow.

        Args:
            workflow_id: Workflow ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.workflows[workflow_id]["state"] = WorkflowState.ACTIVE.value
        self.workflows[workflow_id]["updated_at"] = self._get_current_time()

        # Resume all pending tasks in this workflow
        for task_id, task in self.tasks.items():
            if task["workflow_id"] == workflow_id and task["status"] == TaskState.PAUSED.value:
                self.tasks[task_id]["status"] = TaskState.PENDING.value
                self.tasks[task_id]["updated_at"] = self._get_current_time()

        self._save_workflows_to_file()

    def start_workflow(self, workflow_id: str) -> None:
        """
        Start a workflow.

        Args:
            workflow_id: Workflow ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.workflows[workflow_id]["state"] = WorkflowState.ACTIVE.value
        self.workflows[workflow_id]["updated_at"] = self._get_current_time()

        self._save_workflows_to_file()

    def complete_workflow(self, workflow_id: str) -> None:
        """
        Complete a workflow.

        Args:
            workflow_id: Workflow ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.workflows[workflow_id]["state"] = WorkflowState.COMPLETED.value
        self.workflows[workflow_id]["updated_at"] = self._get_current_time()

        # Complete all tasks in this workflow
        for task_id, task in self.tasks.items():
            if task["workflow_id"] == workflow_id:
                self.tasks[task_id]["status"] = TaskState.COMPLETED.value
                self.tasks[task_id]["updated_at"] = self._get_current_time()

        self._save_workflows_to_file()

    def cancel_workflow(self, workflow_id: str) -> None:
        """
        Cancel a workflow.

        Args:
            workflow_id: Workflow ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.workflows[workflow_id]["state"] = WorkflowState.PAUSED.value
        self.workflows[workflow_id]["updated_at"] = self._get_current_time()

        # Cancel all tasks in this workflow
        for task_id, task in self.tasks.items():
            if task["workflow_id"] == workflow_id:
                self.tasks[task_id]["status"] = TaskState.CANCELLED.value
                self.tasks[task_id]["updated_at"] = self._get_current_time()

        self._save_workflows_to_file()

    def update_task_status(self, task_id: str, status: TaskState) -> None:
        """
        Update the status of a task.

        Args:
            task_id: Task ID
            status: New status
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        self.tasks[task_id]["status"] = status.value
        self.tasks[task_id]["updated_at"] = self._get_current_time()

        self._save_workflows_to_file()

    def get_workflow_tasks(self, workflow_id: str) -> List[str]:
        """
        Get all tasks in a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List[str]: List of task IDs
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        return [
            task_id for task_id, task in self.tasks.items() if task["workflow_id"] == workflow_id
        ]

    def list_workflows(self) -> List[Dict]:
        """
        List all workflows.

        Returns:
            List[Dict]: List of workflow information
        """
        return [
            {
                "workflow_id": workflow_id,
                "name": workflow["name"],
                "state": workflow["state"],
                "created_at": workflow["created_at"],
                "updated_at": workflow["updated_at"],
                "task_count": len(self.get_workflow_tasks(workflow_id)),
            }
            for workflow_id, workflow in self.workflows.items()
        ]

    def handle_task_message(self, category: MessageCategory, message: str) -> str:
        """
        Handle task-related messages.

        Args:
            category: Message category
            message: The message

        Returns:
            str: Response to the message
        """
        if category == MessageCategory.TASK_CREATE:
            return self._handle_task_create(message)
        elif category == MessageCategory.TASK_STATUS:
            return self._handle_task_status(message)
        elif category == MessageCategory.TASK_CANCEL:
            return self._handle_task_cancel(message)
        elif category == MessageCategory.TASK_COMPLETE:
            return self._handle_task_complete(message)
        elif category == MessageCategory.TASK_LIST:
            return self._handle_task_list(message)

        return "Unknown task command"

    def _handle_task_create(self, message: str) -> str:
        """Handle task creation messages."""
        # This is a simplified version - in real implementation, you would
        # extract task details from the message
        return "Task creation functionality will be implemented in future version"

    def _handle_task_status(self, message: str) -> str:
        """Handle task status messages."""
        return "Task status functionality will be implemented in future version"

    def _handle_task_cancel(self, message: str) -> str:
        """Handle task cancel messages."""
        return "Task cancel functionality will be implemented in future version"

    def _handle_task_complete(self, message: str) -> str:
        """Handle task complete messages."""
        return "Task complete functionality will be implemented in future version"

    def _handle_task_list(self, message: str) -> str:
        """Handle task list messages."""
        workflows = self.list_workflows()
        if not workflows:
            return "No active workflows"

        response = "Active Workflows:\n"
        for workflow in workflows:
            response += (
                f"- {workflow['name']} (ID: {workflow['workflow_id']})\n"
                f"  State: {workflow['state']}\n"
                f"  Tasks: {workflow['task_count']}\n"
            )

        return response

    def _get_current_time(self) -> float:
        """Get current time as timestamp (for simplicity)."""
        import time

        return time.time()
