"""
Execute GUS Task Use Case

This module contains the use case for executing GUS tasks, following
Clean Architecture principles by separating business logic from framework concerns.

Use Case:
- Execute various GUS tasks
- Validate task parameters
- Handle task execution lifecycle
- Return task results
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import uuid

from domain.entities.gus_agent import (
    GUSAgent, GUSTask, TaskStatus,
    GUSAgentError, TaskExecutionError
)


@dataclass
class ExecuteGUSTaskRequest:
    """Request DTO for executing GUS tasks"""
    task: str
    parameters: Dict[str, Any]
    user_id: str


@dataclass
class ExecuteGUSTaskResponse:
    """Response DTO for GUS task execution"""
    success: bool
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ExecuteGUSTaskUseCase:
    """
    Use case for executing GUS tasks.

    This use case encapsulates the business logic for executing GUS tasks,
    following Clean Architecture principles by being independent of frameworks.
    """

    def __init__(self, gus_agent: GUSAgent):
        """
        Initialize the use case.

        Args:
            gus_agent: GUS agent instance for executing tasks
        """
        self.gus_agent = gus_agent

    def execute(self, request: ExecuteGUSTaskRequest) -> ExecuteGUSTaskResponse:
        """
        Execute the GUS task execution use case.

        Args:
            request: GUS task request

        Returns:
            GUS task response

        Raises:
            TaskExecutionError: If execution fails
        """
        try:
            # Create domain task object
            task = GUSTask(
                id=str(uuid.uuid4()),
                task=request.task,
                parameters=request.parameters,
                user_id=request.user_id
            )

            # Execute task using domain entity
            result_task = self.gus_agent.execute_task(task)

            # Convert to response DTO
            return ExecuteGUSTaskResponse(
                success=True,
                task_id=result_task.id,
                status=result_task.status.value,
                result=result_task.result
            )

        except TaskExecutionError as e:
            return ExecuteGUSTaskResponse(
                success=False,
                task_id="",
                status=TaskStatus.FAILED.value,
                error_message=str(e)
            )
        except Exception as e:
            return ExecuteGUSTaskResponse(
                success=False,
                task_id="",
                status=TaskStatus.FAILED.value,
                error_message=f"Unexpected error: {str(e)}"
            )
