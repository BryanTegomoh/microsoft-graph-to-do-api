"""Create and organize priority-based lists."""
import sys
import time
import re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.graph.todo_client import ToDoClient

# Keywords for career/job tasks
CAREER_KEYWORDS = [
    'job', 'jobs', 'hiring', 'career', 'postdoc', 'position', 'role', 'opportunity',
    'interview', 'resume', 'cv', 'salary', 'offer', 'recruiter', 'linkedin job',
    'apply', 'application', 'employer', 'employment', 'work at', 'join us',
    'we are hiring', "i'm hiring", 'looking for', 'opening', 'vacancy',
    'medeanalytics', 'ai fund', 'venture advisor', 'sme contract', 'freelance',
    'gig', 'contract', 'consultant', 'fellowship', 'internship'
]

# Keywords for low-value/safe to delete tasks
LOW_VALUE_INDICATORS = [
    # Social media noise
    'likes', 'replies', 'retweet', 'follow', 'follower',
    # Generic/vague content
    'check out', 'look at this', 'thread', 'say more',
    # Old/stale indicators (will also check date)
    'breaking', 'just in', 'happening now',
    # Promotional
    'giveaway', 'contest', 'win a', 'discount', 'sale',
    # Memes/entertainment
    'meme', 'funny', 'lol', 'lmao',
]

# Domains that often have low-value content
LOW_VALUE_DOMAINS = [
    'threads.net',  # Often just profile links
]

def is_career_task(task):
    """Check if task is career/job related."""
    title = task.get('title', '').lower()
    body = task.get('body', {})
    body_content = body.get('content', '').lower() if isinstance(body, dict) else ''

    combined = title + ' ' + body_content

    for keyword in CAREER_KEYWORDS:
        if keyword in combined:
            return True
    return False

def is_high_priority(task):
    """Check if task is high priority (starred or high importance)."""
    # Check importance field - 'high' means starred in Microsoft To Do
    if task.get('importance') == 'high':
        return True
    # Also check if the task is flagged
    if task.get('isReminderOn'):
        return True
    return False

def is_safe_to_delete(task, client):
    """Determine if a task is safe to delete based on various factors."""
    title = task.get('title', '').lower()
    body = task.get('body', {})
    body_content = body.get('content', '').lower() if isinstance(body, dict) else ''
    combined = title + ' ' + body_content

    # Extract URLs
    urls = client.extract_urls_from_task(task)

    reasons = []

    # Check for low-value keywords
    for keyword in LOW_VALUE_INDICATORS:
        if keyword in combined:
            reasons.append(f"contains '{keyword}'")
            break

    # Check for low-value domains
    for url in urls:
        for domain in LOW_VALUE_DOMAINS:
            if domain in url.lower():
                reasons.append(f"links to {domain}")
                break

    # Very short titles with no real content
    if len(title) < 20 and not urls:
        reasons.append("very short title, no URLs")

    # Tasks that are just "View article" or similar
    if title.strip().lower() in ['view article', 'view', 'read', 'check']:
        reasons.append("generic view/read task")

    # Low importance
    if task.get('importance') == 'low':
        reasons.append("marked as low importance")

    # If multiple reasons, it's likely safe to delete
    return len(reasons) >= 1, reasons

def move_task(client, task, target_list_id):
    """Move a task to a new list."""
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

def main():
    client = ToDoClient()

    # Create the three new lists
    print("Creating lists...")

    try:
        high_priority_list = client.create_list('High Priority Tasks')
        print(f"Created: High Priority Tasks")
    except Exception as e:
        print(f"High Priority Tasks may already exist: {e}")
        lists = client.get_task_lists()
        high_priority_list = next((l for l in lists if l['displayName'] == 'High Priority Tasks'), None)

    try:
        career_list = client.create_list('Career/Jobs')
        print(f"Created: Career/Jobs")
    except Exception as e:
        print(f"Career/Jobs may already exist: {e}")
        lists = client.get_task_lists()
        career_list = next((l for l in lists if l['displayName'] == 'Career/Jobs'), None)

    try:
        delete_list = client.create_list('Tasks Safe to Delete')
        print(f"Created: Tasks Safe to Delete")
    except Exception as e:
        print(f"Tasks Safe to Delete may already exist: {e}")
        lists = client.get_task_lists()
        delete_list = next((l for l in lists if l['displayName'] == 'Tasks Safe to Delete'), None)

    # Get list IDs
    lists = client.get_task_lists()
    lists_info = {l['displayName']: l['id'] for l in lists}

    high_priority_id = lists_info.get('High Priority Tasks')
    career_id = lists_info.get('Career/Jobs')
    delete_id = lists_info.get('Tasks Safe to Delete')

    # Get all tasks
    print("\nFetching all tasks...")
    all_tasks = client.get_all_tasks()
    print(f"Found {len(all_tasks)} total tasks")

    # Categorize tasks
    high_priority_tasks = []
    career_tasks = []
    delete_tasks = []

    for task in all_tasks:
        # Skip tasks already in our new lists
        if task.get('listName') in ['High Priority Tasks', 'Career/Jobs', 'Tasks Safe to Delete']:
            continue

        # Check categories (priority order: high priority > career > delete)
        if is_high_priority(task):
            high_priority_tasks.append(task)
        elif is_career_task(task):
            career_tasks.append(task)
        else:
            safe, reasons = is_safe_to_delete(task, client)
            if safe:
                task['_delete_reasons'] = reasons
                delete_tasks.append(task)

    print(f"\nCategorized:")
    print(f"  High Priority: {len(high_priority_tasks)}")
    print(f"  Career/Jobs: {len(career_tasks)}")
    print(f"  Safe to Delete: {len(delete_tasks)}")

    # Move high priority tasks
    if high_priority_tasks:
        print(f"\n=== Moving {len(high_priority_tasks)} High Priority Tasks ===")
        moved = 0
        for task in high_priority_tasks:
            result = move_task(client, task, high_priority_id)
            if result == 'moved':
                moved += 1
                if moved % 5 == 0:
                    print(f"  Moved {moved}/{len(high_priority_tasks)}...")
            time.sleep(0.1)
        print(f"  Done: {moved} moved")

    # Move career tasks
    if career_tasks:
        print(f"\n=== Moving {len(career_tasks)} Career/Jobs Tasks ===")
        moved = 0
        for task in career_tasks:
            result = move_task(client, task, career_id)
            if result == 'moved':
                moved += 1
                if moved % 5 == 0:
                    print(f"  Moved {moved}/{len(career_tasks)}...")
            time.sleep(0.1)
        print(f"  Done: {moved} moved")

    # Move safe-to-delete tasks
    if delete_tasks:
        print(f"\n=== Moving {len(delete_tasks)} Tasks Safe to Delete ===")
        moved = 0
        for task in delete_tasks:
            result = move_task(client, task, delete_id)
            if result == 'moved':
                moved += 1
                if moved % 10 == 0:
                    print(f"  Moved {moved}/{len(delete_tasks)}...")
            time.sleep(0.1)
        print(f"  Done: {moved} moved")

    print("\n=== Complete ===")

if __name__ == '__main__':
    main()
