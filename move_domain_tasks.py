"""Move tasks to domain-specific lists."""
import sys
import json
import time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.graph.todo_client import ToDoClient

def get_domain_from_url(url):
    """Extract domain from URL."""
    url = url.lower()
    if 'x.com' in url or 'twitter.com' in url:
        return 'x.com'
    elif 'linkedin.com' in url:
        return 'linkedin.com'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube.com'
    elif 'chatgpt.com' in url or 'chat.openai.com' in url:
        return 'chatgpt.com'
    elif 'github.com' in url:
        return 'github.com'
    elif 't.co/' in url:
        return 't.co'
    elif 'nature.com' in url:
        return 'nature.com'
    return None

def move_task(client, task, new_list_id):
    """Move a task to a new list."""
    old_list_id = task.get('listId')
    task_id = task.get('id')

    # Skip if already in target list
    if old_list_id == new_list_id:
        return 'skipped'

    try:
        # Create task in new list
        new_task_data = {
            'title': task.get('title'),
            'importance': task.get('importance', 'normal'),
            'status': task.get('status', 'notStarted'),
        }

        if task.get('body'):
            new_task_data['body'] = task.get('body')
        if task.get('dueDateTime'):
            new_task_data['dueDateTime'] = task.get('dueDateTime')
        if task.get('reminderDateTime'):
            new_task_data['reminderDateTime'] = task.get('reminderDateTime')

        client.create_task(new_list_id, new_task_data)
        client.delete_task(old_list_id, task_id)
        return 'moved'
    except Exception as e:
        print(f'  Error: {e}')
        return 'failed'

def main():
    client = ToDoClient()

    # Load list IDs
    with open('domain_lists.json', 'r') as f:
        domain_lists = json.load(f)

    # Map domains to list IDs
    domain_to_list = {
        'x.com': domain_lists.get('X (Twitter)'),
        'linkedin.com': domain_lists.get('LinkedIn'),
        'youtube.com': domain_lists.get('YouTube'),
        'chatgpt.com': domain_lists.get('ChatGPT'),
        'github.com': domain_lists.get('GitHub'),
        't.co': domain_lists.get('Twitter Links'),
        'nature.com': domain_lists.get('Nature'),
    }

    print("Fetching all tasks...")
    all_tasks = client.get_all_tasks()
    print(f"Found {len(all_tasks)} total tasks\n")

    # Group tasks by domain
    domain_tasks = {d: [] for d in domain_to_list.keys()}

    for task in all_tasks:
        # Check URLs in task
        urls = client.extract_urls_from_task(task)
        for url in urls:
            domain = get_domain_from_url(url)
            if domain and domain in domain_tasks:
                domain_tasks[domain].append(task)
                break  # Only add to one list

    # Move tasks for each domain
    stats = {}
    for domain, tasks in domain_tasks.items():
        if not tasks:
            continue

        list_id = domain_to_list[domain]
        list_name = [k for k, v in domain_lists.items() if v == list_id][0]

        print(f"\n=== Moving {len(tasks)} tasks to '{list_name}' ===")

        moved = 0
        skipped = 0
        failed = 0

        for i, task in enumerate(tasks):
            result = move_task(client, task, list_id)
            if result == 'moved':
                moved += 1
                if moved % 10 == 0:
                    print(f"  Moved {moved}/{len(tasks)}...")
            elif result == 'skipped':
                skipped += 1
            else:
                failed += 1

            # Small delay to avoid rate limiting
            if i % 20 == 0 and i > 0:
                time.sleep(0.5)

        stats[list_name] = {'moved': moved, 'skipped': skipped, 'failed': failed}
        print(f"  Done: {moved} moved, {skipped} skipped, {failed} failed")

    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    total_moved = 0
    for list_name, s in stats.items():
        print(f"{list_name}: {s['moved']} moved, {s['skipped']} skipped, {s['failed']} failed")
        total_moved += s['moved']
    print(f"\nTotal tasks moved: {total_moved}")

if __name__ == '__main__':
    main()
