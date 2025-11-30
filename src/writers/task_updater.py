"""Update Microsoft To Do tasks with AI insights."""

import logging
from typing import Dict, List
from datetime import datetime, timedelta

from src.graph.todo_client import ToDoClient

logger = logging.getLogger(__name__)


class TaskUpdater:
    """Updates Microsoft To Do tasks with analysis results."""

    def __init__(self, todo_client: ToDoClient):
        """
        Initialize the task updater.

        Args:
            todo_client: Authenticated To Do client.
        """
        self.client = todo_client

    def update_task_priority(self, task: Dict, priority_score: float, analysis: Dict, show_score_in_title: bool = False) -> bool:
        """
        Update a task's priority based on AI analysis.

        Args:
            task: Task metadata.
            priority_score: Calculated priority score (0-100).
            analysis: AI analysis results.
            show_score_in_title: Whether to add priority score to task title.

        Returns:
            True if successful, False otherwise.
        """
        from src.config import Config

        # Support both camelCase (raw) and snake_case (parsed) task formats
        list_id = task.get("listId") or task.get("list_id")
        task_id = task.get("id")

        if not list_id or not task_id:
            logger.error(f"Missing list_id or task_id for task: {task.get('title', 'unknown')[:50]}")
            return False

        # Map priority score to Microsoft To Do importance
        if priority_score >= 75:
            importance = "high"
        elif priority_score >= 40:
            importance = "normal"
        else:
            importance = "low"

        updates = {
            "importance": importance
        }

        # Add priority score to title if enabled
        if show_score_in_title or Config.SHOW_PRIORITY_SCORES_IN_TASKS:
            original_title = task.get("title", "")
            # Remove existing score if present
            import re
            clean_title = re.sub(r'^\[[\d\.]+\]\s*', '', original_title)
            # Add new score
            new_title = f"[{priority_score:.0f}] {clean_title}"
            updates["title"] = new_title

        # Optionally set due date if not already set
        if not task.get("due_date"):
            urgency = analysis.get("urgency_level", "medium")
            if urgency in ["critical", "high"]:
                # Set due date to tomorrow
                due_date = datetime.now() + timedelta(days=1)
                updates["dueDateTime"] = {
                    "dateTime": due_date.isoformat(),
                    "timeZone": "UTC"
                }

        try:
            self.client.update_task(list_id, task_id, updates)
            logger.info(f"Updated task {task_id} with importance={importance}")
            return True
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return False

    def add_tags_to_task(self, task: Dict, tags: List[str]) -> bool:
        """
        Add tags to a task's body.

        Args:
            task: Task metadata.
            tags: List of tags to add.

        Returns:
            True if successful, False otherwise.
        """
        # Support both camelCase (raw) and snake_case (parsed) task formats
        list_id = task.get("listId") or task.get("list_id")
        task_id = task.get("id")

        if not list_id or not task_id:
            return False

        current_body = task.get("body", "")
        tag_line = f"\n\nTags: {', '.join(tags)}"

        # Avoid duplicate tags
        if "Tags:" not in current_body:
            new_body = current_body + tag_line

            updates = {
                "body": {
                    "content": new_body,
                    "contentType": "text"
                }
            }

            try:
                self.client.update_task(list_id, task_id, updates)
                logger.info(f"Added tags to task {task_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to add tags to task {task_id}: {e}")
                return False

        return True

    def batch_update_tasks(self, tasks_with_analysis: List[Dict], dry_run: bool = False) -> Dict:
        """
        Update multiple tasks with analysis results.

        Args:
            tasks_with_analysis: List of tasks with analysis.
            dry_run: If True, don't actually update tasks.

        Returns:
            Dictionary with update statistics.
        """
        logger.info(f"Batch updating {len(tasks_with_analysis)} tasks (dry_run={dry_run})")

        stats = {
            "total": len(tasks_with_analysis),
            "updated": 0,
            "failed": 0,
            "skipped": 0
        }

        for item in tasks_with_analysis:
            task = item["task"]
            analysis = item["analysis"]
            score = item["priority_score"]

            if dry_run:
                logger.info(f"[DRY RUN] Would update task: {task.get('title')}")
                stats["skipped"] += 1
                continue

            success = self.update_task_priority(task, score, analysis)
            if success:
                stats["updated"] += 1
            else:
                stats["failed"] += 1

        logger.info(f"Batch update complete: {stats}")
        return stats
