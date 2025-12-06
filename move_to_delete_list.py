"""Move tasks to Delete Now list."""
import json
import requests
from src.auth.graph_auth import GraphAuthenticator
from src.graph.todo_client import ToDoClient
from src.config import Config

auth = GraphAuthenticator()
token = auth.get_access_token()
client = ToDoClient(token)

# Get all lists
lists = client.get_task_lists()
print("=== TASK LISTS ===")
list_map = {}
delete_now_list_id = None
safe_to_delete_list_ids = []

for l in lists:
    list_map[l["id"]] = l["displayName"]
    print(f"  {l['displayName']}: {l['id'][:20]}...")

    if l["displayName"] == "Delete Now":
        delete_now_list_id = l["id"]
    elif "Safe to Delete" in l["displayName"]:
        safe_to_delete_list_ids.append(l["id"])

# Create "Delete Now" list if it doesn't exist
if not delete_now_list_id:
    print("\n=== CREATING 'Delete Now' LIST ===")
    result = client.create_list("Delete Now")
    delete_now_list_id = result["id"]
    print(f"Created list: {delete_now_list_id[:20]}...")

# Load delete candidates
with open("output/delete_candidates.json", "r", encoding="utf-8") as f:
    delete_candidates = json.load(f)

print(f"\n=== TASKS TO MOVE ({len(delete_candidates)} broken links) ===")

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
    return response.status_code == 204

# Get tasks from "Safe to Delete" lists
print(f"\n=== CHECKING 'SAFE TO DELETE' LISTS ({len(safe_to_delete_list_ids)} lists) ===")
safe_to_delete_tasks = []
for list_id in safe_to_delete_list_ids:
    list_name = list_map[list_id]
    tasks = get_request(f"me/todo/lists/{list_id}/tasks")
    task_list = tasks.get("value", [])
    print(f"  {list_name}: {len(task_list)} tasks")
    for task in task_list:
        safe_to_delete_tasks.append({
            "id": task["id"],
            "title": task.get("title", "")[:100],
            "list_id": list_id,
            "list_name": list_name
        })

print(f"\nTotal from 'Safe to Delete' lists: {len(safe_to_delete_tasks)} tasks")

# Combine all tasks to move
all_tasks_to_move = []

# Add broken link tasks
for task in delete_candidates:
    all_tasks_to_move.append({
        "id": task["id"],
        "title": task["title"],
        "list_id": task.get("list_id"),
        "reason": task["reason"]
    })

# Add safe to delete tasks
for task in safe_to_delete_tasks:
    all_tasks_to_move.append({
        "id": task["id"],
        "title": task["title"],
        "list_id": task["list_id"],
        "reason": f"Already in {task['list_name']}"
    })

print(f"\n=== TOTAL TASKS TO MOVE: {len(all_tasks_to_move)} ===")

# Actually move the tasks
print("\n=== MOVING TASKS ===")
moved = 0
failed = 0

for task in all_tasks_to_move:
    try:
        # Get the full task first to get its current list
        # For tasks without list_id, we need to find it
        if not task.get("list_id"):
            # Search through all lists to find this task
            for list_id in list_map.keys():
                try:
                    task_data = get_request(f"me/todo/lists/{list_id}/tasks/{task['id']}")
                    if task_data:
                        task["list_id"] = list_id
                        break
                except:
                    continue

        if not task.get("list_id"):
            print(f"  SKIP: Could not find list for task: {task['title'][:50]}...")
            failed += 1
            continue

        if task["list_id"] == delete_now_list_id:
            print(f"  SKIP (already in Delete Now): {task['title'][:50]}...")
            continue

        # Move task to Delete Now list
        # Microsoft Graph API doesn't have a direct move, so we:
        # 1. Get the full task
        # 2. Create a copy in the new list
        # 3. Delete the original

        full_task = get_request(f"me/todo/lists/{task['list_id']}/tasks/{task['id']}")

        # Create new task in Delete Now list
        new_task_data = {
            "title": full_task.get("title", "Untitled"),
            "body": full_task.get("body"),
            "importance": full_task.get("importance", "normal"),
        }
        if full_task.get("dueDateTime"):
            new_task_data["dueDateTime"] = full_task["dueDateTime"]

        new_task = post_request(f"me/todo/lists/{delete_now_list_id}/tasks", new_task_data)

        # Delete original task
        delete_request(f"me/todo/lists/{task['list_id']}/tasks/{task['id']}")

        title_safe = task['title'].encode('ascii', 'replace').decode('ascii')[:50]
        print(f"  MOVED: {title_safe}...")
        moved += 1

    except Exception as e:
        title_safe = task['title'].encode('ascii', 'replace').decode('ascii')[:50]
        print(f"  ERROR moving {title_safe}: {str(e)[:50]}")
        failed += 1

print(f"\n=== SUMMARY ===")
print(f"Moved: {moved}")
print(f"Failed: {failed}")
print(f"Delete Now list ID: {delete_now_list_id}")
