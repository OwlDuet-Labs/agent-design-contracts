"""Simple Python library for testing Universal Library Loader.

ADC-IMPLEMENTS: <test-lib-01>
"""


# ADC-IMPLEMENTS: <test-lib-create-task>
def create_task(title: str, description: str) -> dict:
    """Create a new task.

    Args:
        title: Task title
        description: Task description

    Returns:
        Task dictionary with id, title, and description
    """
    return {
        "id": "task-123",
        "title": title,
        "description": description,
        "completed": False,
    }


# ADC-IMPLEMENTS: <test-lib-list-tasks>
def list_tasks() -> list:
    """List all tasks.

    Returns:
        List of task dictionaries
    """
    return [
        {"id": "task-1", "title": "Task 1", "completed": False},
        {"id": "task-2", "title": "Task 2", "completed": True},
    ]


# ADC-IMPLEMENTS: <test-lib-complete-task>
def complete_task(task_id: str) -> dict:
    """Mark a task as completed.

    Args:
        task_id: ID of task to complete

    Returns:
        Updated task dictionary
    """
    return {
        "id": task_id,
        "completed": True,
    }
