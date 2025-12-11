"""Move tasks without URLs to a 'NO URL' list."""
import json
import re
import requests
from src.auth.graph_auth import GraphAuthenticator
from src.graph.todo_client import ToDoClient
from src.config import Config

auth = GraphAuthenticator()
token = auth.get_access_token()
client = ToDoClient(token)

# Helper functions for API calls
def get_request(endpoint):
    url = f"{Config.GRAPH_API_BASE}/{endpoint}"
    response = requests.get(url, headers=client.headers)
    response.raise_for_status()
    return response.json()

def post_request(endpoint, data):
    url = f"{Config.GRAPH_API_BASE}/{endpoint}"
    response = requests.post(url, headers=client.headers, json=data)
    response.raise_for_status()
    return response.json()

def delete_request(endpoint):
    url = f"{Config.GRAPH_API_BASE}/{endpoint}"
    response = requests.delete(url, headers=client.headers)
    response.raise_for_status()

# Get all lists
lists = client.get_task_lists()
print("=== TASK LISTS ===")
list_map = {}
no_url_list_id = None

for l in lists:
    list_map[l["id"]] = l["displayName"]
    print(f"  {l['displayName']}")
    if l["displayName"] == "NO URL":
        no_url_list_id = l["id"]

# Create "NO URL" list if it doesn't exist
if not no_url_list_id:
    print("\n=== CREATING 'NO URL' LIST ===")
    result = client.create_list("NO URL")
    no_url_list_id = result["id"]
    print(f"Created list: NO URL")

# URL pattern
url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE)

# Get all tasks directly and find ones without URLs
print("\n=== FETCHING ALL TASKS ===")
all_tasks = client.get_all_tasks()
print(f"Total tasks: {len(all_tasks)}")

# Find tasks without URLs
tasks_to_move = []
for task in all_tasks:
    title = task.get("title", "")
    body_content = ""
    if task.get("body"):
        body_content = task["body"].get("content", "")

    # Check if there's a URL in title or body
    has_url = bool(url_pattern.search(title)) or bool(url_pattern.search(body_content))

    if not has_url:
        # Try both parentFolderId and listId fields
        list_id = task.get("parentFolderId") or task.get("listId", "")
        list_name = task.get("listName") or list_map.get(list_id, "Unknown")

        # Skip if already in NO URL or Delete Now list
        if list_name in ["NO URL", "Delete Now"]:
            continue

        tasks_to_move.append({
            "id": task.get("id"),
            "title": title,
            "list_id": list_id,
            "list_name": list_name
        })

print(f"\n=== MOVING {len(tasks_to_move)} TASKS TO 'NO URL' LIST ===\n")

moved = 0
failed = 0

for task in tasks_to_move:
    try:
        task_id = task["id"]
        list_id = task["list_id"]

        if not list_id:
            print(f"  SKIP: No list_id for: {task['title'][:50]}...")
            failed += 1
            continue

        # Get full task data
        full_task = get_request(f"me/todo/lists/{list_id}/tasks/{task_id}")

        # Create new task in NO URL list
        new_task_data = {
            "title": full_task.get("title", "Untitled"),
            "body": full_task.get("body"),
            "importance": full_task.get("importance", "normal"),
        }
        if full_task.get("dueDateTime"):
            new_task_data["dueDateTime"] = full_task["dueDateTime"]

        post_request(f"me/todo/lists/{no_url_list_id}/tasks", new_task_data)

        # Delete original task
        delete_request(f"me/todo/lists/{list_id}/tasks/{task_id}")

        title_safe = task['title'].encode('ascii', 'replace').decode('ascii')[:50]
        print(f"  MOVED: {title_safe}...")
        moved += 1

    except Exception as e:
        title_safe = task['title'].encode('ascii', 'replace').decode('ascii')[:50]
        print(f"  ERROR: {title_safe} - {str(e)[:30]}")
        failed += 1

print(f"\n=== SUMMARY ===")
print(f"Moved: {moved}")
print(f"Failed: {failed}")
