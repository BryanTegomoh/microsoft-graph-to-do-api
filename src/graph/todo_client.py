"""Microsoft To Do client for interacting with tasks."""

import logging
from typing import List, Dict, Optional
from datetime import datetime

import requests

from src.config import Config
from src.auth.graph_auth import get_authenticated_session

logger = logging.getLogger(__name__)


class ToDoClient:
    """Client for Microsoft To Do API operations."""

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize the To Do client.

        Args:
            access_token: Microsoft Graph access token. If None, will authenticate.
        """
        self.access_token = access_token or get_authenticated_session()
        self.base_url = Config.GRAPH_API_BASE
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_task_lists(self) -> List[Dict]:
        """
        Get all To Do task lists.

        Returns:
            List of task list dictionaries.
        """
        url = f"{self.base_url}/me/todo/lists"
        logger.info("Fetching task lists")

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        lists = response.json().get("value", [])
        logger.info(f"Found {len(lists)} task lists")
        return lists

    def get_tasks(self, list_id: str, filter_query: Optional[str] = None) -> List[Dict]:
        """
        Get tasks from a specific list.

        Args:
            list_id: The ID of the task list.
            filter_query: Optional OData filter query.

        Returns:
            List of task dictionaries.
        """
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks"

        params = {}
        if filter_query:
            params["$filter"] = filter_query

        logger.info(f"Fetching tasks from list {list_id}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        tasks = response.json().get("value", [])
        logger.info(f"Found {len(tasks)} tasks")
        return tasks

    def get_all_tasks(self, include_completed: bool = False) -> List[Dict]:
        """
        Get all tasks from all lists.

        Args:
            include_completed: Whether to include completed tasks.

        Returns:
            List of all task dictionaries with list metadata.
        """
        all_tasks = []
        lists = self.get_task_lists()

        for task_list in lists:
            list_id = task_list["id"]
            list_name = task_list["displayName"]

            filter_query = None if include_completed else "status ne 'completed'"
            tasks = self.get_tasks(list_id, filter_query)

            # Add list metadata to each task
            for task in tasks:
                task["listId"] = list_id
                task["listName"] = list_name
                all_tasks.append(task)

        logger.info(f"Total tasks retrieved: {len(all_tasks)}")
        return all_tasks

    def get_tasks_delta(self, list_id: str, delta_link: Optional[str] = None) -> tuple:
        """
        Get task changes using delta query.

        Args:
            list_id: The ID of the task list.
            delta_link: Previous delta link for incremental sync.

        Returns:
            Tuple of (tasks, new_delta_link)
        """
        if delta_link:
            url = delta_link
        else:
            url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/delta"

        logger.info("Fetching task delta")
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        tasks = data.get("value", [])
        new_delta_link = data.get("@odata.deltaLink")

        logger.info(f"Delta sync: {len(tasks)} changes")
        return tasks, new_delta_link

    def update_task(self, list_id: str, task_id: str, updates: Dict) -> Dict:
        """
        Update a task.

        Args:
            list_id: The ID of the task list.
            task_id: The ID of the task.
            updates: Dictionary of fields to update.

        Returns:
            Updated task dictionary.
        """
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks/{task_id}"

        logger.info(f"Updating task {task_id}")
        response = requests.patch(url, headers=self.headers, json=updates)
        response.raise_for_status()

        return response.json()

    def create_task(self, list_id: str, task_data: Dict) -> Dict:
        """
        Create a new task.

        Args:
            list_id: The ID of the task list.
            task_data: Task data dictionary.

        Returns:
            Created task dictionary.
        """
        url = f"{self.base_url}/me/todo/lists/{list_id}/tasks"

        logger.info(f"Creating new task in list {list_id}")
        response = requests.post(url, headers=self.headers, json=task_data)
        response.raise_for_status()

        return response.json()

    def extract_urls_from_task(self, task: Dict) -> List[str]:
        """
        Extract URLs from a task's title and body.

        Args:
            task: Task dictionary.

        Returns:
            List of URLs found in the task.
        """
        import re

        urls = []
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

        # Check title
        title = task.get("title", "")
        urls.extend(re.findall(url_pattern, title))

        # Check body
        body = task.get("body", {})
        if isinstance(body, dict):
            content = body.get("content", "")
            urls.extend(re.findall(url_pattern, content))

        return list(set(urls))  # Remove duplicates

    def parse_task_metadata(self, task: Dict) -> Dict:
        """
        Parse task metadata into a structured format.

        Args:
            task: Task dictionary from Graph API.

        Returns:
            Parsed task metadata.
        """
        return {
            "id": task.get("id"),
            "title": task.get("title", ""),
            "status": task.get("status", "notStarted"),
            "importance": task.get("importance", "normal"),
            "created_at": task.get("createdDateTime"),
            "due_date": task.get("dueDateTime", {}).get("dateTime") if task.get("dueDateTime") else None,
            "reminder": task.get("reminderDateTime", {}).get("dateTime") if task.get("reminderDateTime") else None,
            "list_id": task.get("listId"),
            "list_name": task.get("listName"),
            "body": task.get("body", {}).get("content", ""),
            "urls": self.extract_urls_from_task(task),
            "completed_at": task.get("completedDateTime", {}).get("dateTime") if task.get("completedDateTime") else None,
        }
