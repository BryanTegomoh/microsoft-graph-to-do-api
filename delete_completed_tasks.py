"""Delete all completed tasks from a specified list."""
import requests
from src.auth.graph_auth import GraphAuthenticator
from src.graph.todo_client import ToDoClient
from src.config import Config

auth = GraphAuthenticator()
token = auth.get_access_token()
client = ToDoClient(token)

# Helper function for API calls
def delete_request(endpoint):
    url = f"{Config.GRAPH_API_BASE}/{endpoint}"
    response = requests.delete(url, headers=client.headers)
    response.raise_for_status()

def get_request(endpoint):
    url = f"{Config.GRAPH_API_BASE}/{endpoint}"
    response = requests.get(url, headers=client.headers)
    response.raise_for_status()
    return response.json()

# Get all lists
lists = client.get_task_lists()
print("=== TASK LISTS ===")
list_map = {}
for l in lists:
    list_map[l["displayName"]] = l["id"]
    print(f"  {l['displayName']}")

# Lists to clean up completed tasks
lists_to_clean = ["NO URL", "Delete Now"]

for list_name in lists_to_clean:
    if list_name not in list_map:
        print(f"\n'{list_name}' list not found, skipping...")
        continue

    list_id = list_map[list_name]
    print(f"\n=== CLEANING '{list_name}' LIST ===")

    # Get all tasks from this list
    tasks = get_request(f"me/todo/lists/{list_id}/tasks")
    task_list = tasks.get("value", [])

    # Filter for completed tasks
    completed_tasks = [t for t in task_list if t.get("status") == "completed"]

    print(f"Found {len(completed_tasks)} completed tasks out of {len(task_list)} total")

    if not completed_tasks:
        print("No completed tasks to delete.")
        continue

    # Delete completed tasks
    deleted = 0
    failed = 0

    for task in completed_tasks:
        try:
            task_id = task["id"]
            title = task.get("title", "Untitled")[:50]
            title_safe = title.encode('ascii', 'replace').decode('ascii')

            delete_request(f"me/todo/lists/{list_id}/tasks/{task_id}")
            print(f"  DELETED: {title_safe}...")
            deleted += 1

        except Exception as e:
            print(f"  ERROR: {str(e)[:50]}")
            failed += 1

    print(f"\nDeleted: {deleted}, Failed: {failed}")

print("\n=== DONE ===")
