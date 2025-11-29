"""Script to find and remove duplicate URLs in Microsoft To Do tasks."""

import sys
import argparse
from collections import defaultdict
from urllib.parse import urlparse, parse_qs, urlencode

from src.config import Config
from src.utils.logging_config import setup_logging
from src.graph.todo_client import ToDoClient

import logging

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize URL for comparison (removes tracking params, www, trailing slashes)."""
    url = url.lower().strip()

    # Parse URL
    parsed = urlparse(url)

    # Remove www
    netloc = parsed.netloc
    if netloc.startswith('www.'):
        netloc = netloc[4:]

    # Remove common tracking parameters
    tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                       'fbclid', 'gclid', 'ref', 's', 't', 'si', 'igshid'}

    query_params = parse_qs(parsed.query)
    filtered_params = {k: v for k, v in query_params.items() if k.lower() not in tracking_params}
    clean_query = urlencode(filtered_params, doseq=True) if filtered_params else ''

    # Rebuild URL without tracking params
    path = parsed.path.rstrip('/')

    if clean_query:
        return f"{parsed.scheme}://{netloc}{path}?{clean_query}"
    return f"{parsed.scheme}://{netloc}{path}"


def find_url_duplicates(tasks: list) -> dict:
    """Find tasks with the same URL."""
    url_to_tasks = defaultdict(list)

    for task in tasks:
        urls = task.get('urls', [])
        for url in urls:
            normalized = normalize_url(url)
            url_to_tasks[normalized].append({
                'task': task,
                'original_url': url
            })

    # Filter to only duplicates
    return {
        url: items
        for url, items in url_to_tasks.items()
        if len(items) > 1
    }


def delete_duplicates(todo_client: ToDoClient, url_duplicates: dict, dry_run: bool = True) -> dict:
    """
    Delete duplicate tasks, keeping the newest one for each URL.

    Args:
        todo_client: Authenticated To Do client.
        url_duplicates: Dictionary of normalized URLs to list of tasks.
        dry_run: If True, only show what would be deleted without actually deleting.

    Returns:
        Dictionary with deletion statistics.
    """
    stats = {"deleted": 0, "failed": 0, "skipped": 0}

    for url, items in url_duplicates.items():
        # Sort by created date (newest first)
        sorted_items = sorted(
            items,
            key=lambda x: x['task'].get('created_at', '') or '',
            reverse=True
        )

        # Keep the newest, delete the rest
        keeper = sorted_items[0]
        to_delete = sorted_items[1:]

        print(f"\nURL: {url[:60]}...")
        print(f"  [KEEP] \"{keeper['task'].get('title', 'No title')[:50]}\" (Created: {keeper['task'].get('created_at', '')[:10] if keeper['task'].get('created_at') else 'Unknown'})")

        for item in to_delete:
            task = item['task']
            title = task.get('title', 'No title')[:50]
            task_id = task.get('id')
            list_id = task.get('list_id')
            created = task.get('created_at', '')[:10] if task.get('created_at') else 'Unknown'

            if dry_run:
                print(f"  [WOULD DELETE] \"{title}\" (Created: {created})")
                stats["skipped"] += 1
            else:
                try:
                    success = todo_client.delete_task(list_id, task_id)
                    if success:
                        print(f"  [DELETED] \"{title}\" (Created: {created})")
                        stats["deleted"] += 1
                    else:
                        print(f"  [FAILED] \"{title}\" (Created: {created})")
                        stats["failed"] += 1
                except Exception as e:
                    print(f"  [ERROR] \"{title}\": {e}")
                    stats["failed"] += 1

    return stats


def main():
    """Main function to find and optionally delete URL duplicates."""
    parser = argparse.ArgumentParser(description="Find and remove duplicate URLs in Microsoft To Do tasks.")
    parser.add_argument("--delete", action="store_true", help="Actually delete duplicates (keeps newest)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    setup_logging()
    logger.info("=== Microsoft To Do URL Duplicate Finder ===")

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Fetch tasks
    print("\nFetching tasks from Microsoft To Do...")
    todo_client = ToDoClient()
    tasks = todo_client.get_all_tasks(include_completed=False)

    # Parse task metadata to extract URLs
    parsed_tasks = []
    for task in tasks:
        parsed = todo_client.parse_task_metadata(task)
        parsed_tasks.append(parsed)

    print(f"Found {len(parsed_tasks)} tasks")

    # Count tasks with URLs
    tasks_with_urls = [t for t in parsed_tasks if t.get('urls')]
    print(f"Tasks with URLs: {len(tasks_with_urls)}")

    # Find URL duplicates
    print("\n" + "=" * 60)
    print("DUPLICATE URLs")
    print("=" * 60)

    url_duplicates = find_url_duplicates(parsed_tasks)

    if not url_duplicates:
        print("\nNo duplicate URLs found. Your task list is clean!")
        return

    total_dupes = sum(len(items) for items in url_duplicates.values())
    to_remove = total_dupes - len(url_duplicates)

    print(f"\nFound {len(url_duplicates)} duplicate URLs ({total_dupes} tasks)")
    print(f"Tasks to remove (keeping newest): {to_remove}")

    if args.delete:
        # Confirm before deleting
        if not args.yes:
            print("\n" + "=" * 60)
            print("WARNING: This will permanently delete tasks!")
            print("=" * 60)
            confirm = input(f"\nType 'DELETE' to confirm removal of {to_remove} duplicate tasks: ")
            if confirm != "DELETE":
                print("Aborted. No tasks were deleted.")
                return

        print("\n" + "=" * 60)
        print("DELETING DUPLICATES")
        print("=" * 60)

        stats = delete_duplicates(todo_client, url_duplicates, dry_run=False)

        print("\n" + "=" * 60)
        print("DELETION COMPLETE")
        print("=" * 60)
        print(f"Deleted: {stats['deleted']}")
        print(f"Failed: {stats['failed']}")

    else:
        # Dry run - just show what would be deleted
        print("\n" + "=" * 60)
        print("DRY RUN (use --delete to actually remove)")
        print("=" * 60)

        for i, (url, items) in enumerate(url_duplicates.items(), 1):
            print(f"\n{i}. {url[:80]}{'...' if len(url) > 80 else ''}")
            print(f"   [{len(items)} copies]")

            # Sort by created date (newest first)
            sorted_items = sorted(
                items,
                key=lambda x: x['task'].get('created_at', '') or '',
                reverse=True
            )

            for j, item in enumerate(sorted_items):
                task = item['task']
                title = task.get('title', 'No title')[:60]
                created = task.get('created_at', '')[:10] if task.get('created_at') else 'Unknown'
                status = "[KEEP]" if j == 0 else "[DELETE]"
                print(f"   {status} \"{title}{'...' if len(task.get('title', '')) > 60 else ''}\"")
                print(f"          Created: {created}")

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"\nDuplicate URL groups: {len(url_duplicates)}")
        print(f"Total duplicate tasks: {total_dupes}")
        print(f"Tasks to remove (keeping newest): {to_remove}")
        print("\nRun with --delete to remove duplicates.")
        print("Example: python find_duplicates.py --delete")


if __name__ == "__main__":
    main()
