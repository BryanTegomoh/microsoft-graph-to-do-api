"""Debug task structure."""
import re
from src.auth.graph_auth import GraphAuthenticator
from src.graph.todo_client import ToDoClient

auth = GraphAuthenticator()
token = auth.get_access_token()
client = ToDoClient(token)

url_pattern = re.compile(r'https?://[^\s]+', re.IGNORECASE)
all_tasks = client.get_all_tasks()

# Check a task without URL
for task in all_tasks:
    title = task.get('title', '')
    if not url_pattern.search(title):
        print('Task without URL found:')
        print(f'  Title: {title[:60]}')
        task_id = task.get("id", "")
        print(f'  ID: {task_id}')
        parent = task.get("parentFolderId", "MISSING")
        print(f'  parentFolderId: {parent}')
        print(f'  Keys: {list(task.keys())}')
        print()
        break

# Count tasks with/without parentFolderId
with_parent = 0
without_parent = 0
for task in all_tasks:
    if task.get("parentFolderId"):
        with_parent += 1
    else:
        without_parent += 1

print(f"Tasks with parentFolderId: {with_parent}")
print(f"Tasks without parentFolderId: {without_parent}")
