"""Find tasks that should be deleted."""
import json
from src.auth.graph_auth import GraphAuthenticator
from src.graph.todo_client import ToDoClient

auth = GraphAuthenticator()
token = auth.get_access_token()
client = ToDoClient(token)

# Get all lists
lists = client.get_task_lists()
print("=== TASK LISTS ===")
list_map = {}
for l in lists:
    list_map[l["id"]] = l["displayName"]
    print(f"  {l['displayName']}")

# Get all tasks
print("\n=== FETCHING TASKS ===")
all_tasks = client.get_all_tasks()
print(f"Total tasks: {len(all_tasks)}")

# Analyze tasks for deletion candidates
# Criteria for deletion:
# 1. Broken/truncated URLs (like "https://t...")
# 2. Very old tasks with past due dates (more than 6 months old)
# 3. Tasks with broken links or "page not found" type content
# 4. Duplicate tasks
# 5. Tasks that are clearly outdated (expired events, old dates in title)

from datetime import datetime, timedelta
import re

delete_candidates = []
six_months_ago = datetime.now() - timedelta(days=180)
one_year_ago = datetime.now() - timedelta(days=365)

for task in all_tasks:
    title = task.get("title", "")
    body = task.get("body", {}).get("content", "") if task.get("body") else ""
    due_date_str = task.get("dueDateTime", {}).get("dateTime", "") if task.get("dueDateTime") else ""
    created_str = task.get("createdDateTime", "")
    list_id = task.get("parentFolderId", "")
    list_name = list_map.get(list_id, "Unknown")

    reason = None

    # 1. Broken/truncated URLs
    if re.search(r'https?://t\.\.\.|https?://\S{1,5}$', title):
        reason = "Broken/truncated URL"

    # 2. URLs that are just "t.co" short links without context
    elif title.strip().startswith("https://t.co/") and len(title) < 30:
        reason = "Just a t.co link without context"

    # 3. Very old overdue tasks (more than 1 year past due)
    elif due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            if due_date.replace(tzinfo=None) < one_year_ago:
                reason = f"Overdue by more than 1 year (due: {due_date.strftime('%Y-%m-%d')})"
        except:
            pass

    # 4. Check for expired event indicators in title
    year_patterns = [
        r'\b202[0-3]\b',  # Years 2020-2023
        r'\b201[0-9]\b',  # Years 2010-2019
    ]
    for pattern in year_patterns:
        match = re.search(pattern, title)
        if match:
            year = int(match.group())
            if year < 2024:
                # Check if it looks like an event or dated content
                if any(word in title.lower() for word in ['conference', 'webinar', 'deadline', 'expires', 'event', 'summit', 'workshop', 'registration']):
                    reason = f"Likely expired event from {year}"
                    break

    # 5. Check for "page not found", "404", "unavailable" in body
    if body:
        body_lower = body.lower()
        if any(phrase in body_lower for phrase in ['page not found', '404', 'no longer available', 'has been removed', 'this page doesn\'t exist']):
            reason = "Link appears broken/unavailable"

    if reason:
        delete_candidates.append({
            "id": task.get("id"),
            "title": title[:100],
            "list": list_name,
            "list_id": list_id,
            "reason": reason
        })

# Sort by reason
delete_candidates.sort(key=lambda x: x["reason"])

# Save to file FIRST for review
with open("output/delete_candidates.json", "w", encoding="utf-8") as f:
    json.dump(delete_candidates, f, indent=2, ensure_ascii=False)

print(f"\n=== TASKS TO DELETE ({len(delete_candidates)}) ===\n")
for i, task in enumerate(delete_candidates, 1):
    # Handle Unicode safely for Windows console
    title = task['title'].encode('ascii', 'replace').decode('ascii')
    print(f"{i}. [{task['reason']}]")
    print(f"   List: {task['list']}")
    print(f"   Title: {title}")
    print()

print(f"\nSaved {len(delete_candidates)} candidates to output/delete_candidates.json")
