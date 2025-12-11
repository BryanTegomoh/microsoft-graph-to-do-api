"""Find tasks that don't have a URL in the title or body."""
import json
import re
from src.auth.graph_auth import GraphAuthenticator
from src.graph.todo_client import ToDoClient

auth = GraphAuthenticator()
token = auth.get_access_token()
client = ToDoClient(token)

# URL pattern
url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE)

# Get all lists
lists = client.get_task_lists()
list_map = {}
for l in lists:
    list_map[l["id"]] = l["displayName"]

# Get all tasks
print("=== FETCHING TASKS ===")
all_tasks = client.get_all_tasks()
print(f"Total tasks: {len(all_tasks)}")

# Find tasks without URLs
tasks_without_urls = []

for task in all_tasks:
    title = task.get("title", "")
    body_content = ""
    if task.get("body"):
        body_content = task["body"].get("content", "")

    # Check if there's a URL in title or body
    has_url = bool(url_pattern.search(title)) or bool(url_pattern.search(body_content))

    if not has_url:
        list_id = task.get("parentFolderId", "")
        list_name = list_map.get(list_id, "Unknown")

        # Skip if it's in the Delete Now list
        if list_name == "Delete Now":
            continue

        tasks_without_urls.append({
            "id": task.get("id"),
            "title": title,
            "list": list_name,
            "list_id": list_id,
            "created": task.get("createdDateTime", ""),
            "importance": task.get("importance", "normal"),
            "status": task.get("status", "")
        })

# Sort by list name then title
tasks_without_urls.sort(key=lambda x: (x["list"], x["title"]))

# Save to JSON
with open("output/tasks_without_urls.json", "w", encoding="utf-8") as f:
    json.dump(tasks_without_urls, f, indent=2, ensure_ascii=False)

# Print results
print(f"\n=== TASKS WITHOUT URLs ({len(tasks_without_urls)}) ===\n")

current_list = None
for task in tasks_without_urls:
    if task["list"] != current_list:
        current_list = task["list"]
        print(f"\n--- {current_list} ---")

    title_safe = task['title'].encode('ascii', 'replace').decode('ascii')[:80]
    importance = "[!]" if task["importance"] == "high" else "   "
    print(f"{importance} {title_safe}")

print(f"\n\nTotal: {len(tasks_without_urls)} tasks without URLs")
print(f"Saved to output/tasks_without_urls.json")
