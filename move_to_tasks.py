"""Move tasks from domain lists back to the main Tasks list.

Usage:
    python move_to_tasks.py                    # Interactive - prompts for which lists
    python move_to_tasks.py --list "LinkedIn"  # Move specific list
    python move_to_tasks.py --all              # Move all domain lists back
    python move_to_tasks.py --list "LinkedIn" --delete  # Move and delete the list
"""
import sys
import argparse
import time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.graph.todo_client import ToDoClient

# Domain lists we created (not system lists)
DOMAIN_LISTS = [
    'X (Twitter)',
    'LinkedIn',
    'YouTube',
    'ChatGPT',
    'GitHub',
    'Twitter Links',
    'Nature',
    'Google Scholar',
]

def move_task(client, task, target_list_id):
    """Move a task to the target list."""
    old_list_id = task.get('listId')
    task_id = task.get('id')

    if old_list_id == target_list_id:
        return 'skipped'

    try:
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

        client.create_task(target_list_id, new_task_data)
        client.delete_task(old_list_id, task_id)
        return 'moved'
    except Exception as e:
        print(f'  Error: {e}')
        return 'failed'

def get_lists_info(client):
    """Get all lists with their IDs."""
    lists = client.get_task_lists()
    return {l['displayName']: l['id'] for l in lists}

def move_list_to_tasks(client, source_list_name, lists_info, delete_after=False):
    """Move all tasks from a source list to Tasks."""
    if source_list_name not in lists_info:
        print(f"List '{source_list_name}' not found!")
        return

    source_list_id = lists_info[source_list_name]
    tasks_list_id = lists_info.get('Tasks')

    if not tasks_list_id:
        print("Main 'Tasks' list not found!")
        return

    print(f"\nMoving tasks from '{source_list_name}' to 'Tasks'...")

    # Get tasks from source list
    tasks = client.get_tasks(source_list_id)
    print(f"Found {len(tasks)} tasks to move")

    if not tasks:
        print("No tasks to move.")
        if delete_after:
            print(f"Deleting empty list '{source_list_name}'...")
            client.delete_list(source_list_id)
            print(f"Deleted '{source_list_name}'")
        return

    moved = 0
    failed = 0

    for i, task in enumerate(tasks):
        # Add listId for the move function
        task['listId'] = source_list_id
        result = move_task(client, task, tasks_list_id)

        if result == 'moved':
            moved += 1
            if moved % 10 == 0:
                print(f"  Moved {moved}/{len(tasks)}...")
        elif result == 'failed':
            failed += 1

        # Rate limiting
        if i % 20 == 0 and i > 0:
            time.sleep(0.5)

    print(f"Done: {moved} moved, {failed} failed")

    if delete_after and failed == 0:
        print(f"Deleting now-empty list '{source_list_name}'...")
        try:
            client.delete_list(source_list_id)
            print(f"Deleted '{source_list_name}'")
        except Exception as e:
            print(f"Failed to delete list: {e}")

def interactive_mode(client, lists_info):
    """Interactive mode to select which lists to move."""
    domain_lists_present = [name for name in DOMAIN_LISTS if name in lists_info]

    if not domain_lists_present:
        print("No domain lists found to move.")
        return

    print("\nDomain lists available:")
    for i, name in enumerate(domain_lists_present, 1):
        # Get task count
        tasks = client.get_tasks(lists_info[name])
        print(f"  {i}. {name} ({len(tasks)} tasks)")

    print(f"\n  A. Move ALL domain lists back to Tasks")
    print(f"  Q. Quit")

    choice = input("\nEnter number(s) separated by comma, 'A' for all, or 'Q' to quit: ").strip()

    if choice.upper() == 'Q':
        return

    delete_after = input("Delete lists after moving tasks? (y/n): ").strip().lower() == 'y'

    if choice.upper() == 'A':
        lists_to_move = domain_lists_present
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            lists_to_move = [domain_lists_present[i] for i in indices if 0 <= i < len(domain_lists_present)]
        except:
            print("Invalid input.")
            return

    for list_name in lists_to_move:
        move_list_to_tasks(client, list_name, lists_info, delete_after)
        # Refresh lists_info if we deleted a list
        if delete_after:
            lists_info = get_lists_info(client)

def main():
    parser = argparse.ArgumentParser(description="Move tasks from domain lists back to Tasks")
    parser.add_argument("--list", "-l", help="Specific list to move (can be used multiple times)", action='append')
    parser.add_argument("--all", "-a", action="store_true", help="Move all domain lists back to Tasks")
    parser.add_argument("--delete", "-d", action="store_true", help="Delete lists after moving tasks")
    args = parser.parse_args()

    client = ToDoClient()
    lists_info = get_lists_info(client)

    if args.all:
        for list_name in DOMAIN_LISTS:
            if list_name in lists_info:
                move_list_to_tasks(client, list_name, lists_info, args.delete)
                if args.delete:
                    lists_info = get_lists_info(client)
    elif args.list:
        for list_name in args.list:
            move_list_to_tasks(client, list_name, lists_info, args.delete)
            if args.delete:
                lists_info = get_lists_info(client)
    else:
        interactive_mode(client, lists_info)

    print("\nDone!")

if __name__ == '__main__':
    main()
