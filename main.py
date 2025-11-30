"""Main orchestration script for Microsoft To Do AI Task Manager."""

import logging
import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse, parse_qs, urlencode

from src.config import Config
from src.utils.logging_config import setup_logging
from src.graph.todo_client import ToDoClient
from src.fetch.content_extractor import ContentExtractor
from src.llm.ai_analyzer import TaskAnalyzer
from src.rules.priority_ranker import PriorityRanker
from src.writers.brief_generator import BriefGenerator
from src.writers.task_updater import TaskUpdater
from src.writers.email_sender import EmailSender
from src.writers.email_sender_enhanced import EmailSenderEnhanced
from src.analytics.weekly_trends import WeeklyTrendsAnalyzer
from src.cache.analysis_cache import AnalysisCache

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize URL for duplicate comparison."""
    url = url.lower().strip()
    parsed = urlparse(url)
    netloc = parsed.netloc
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                       'fbclid', 'gclid', 'ref', 's', 't', 'si', 'igshid'}
    query_params = parse_qs(parsed.query)
    filtered_params = {k: v for k, v in query_params.items() if k.lower() not in tracking_params}
    clean_query = urlencode(filtered_params, doseq=True) if filtered_params else ''
    path = parsed.path.rstrip('/')
    if clean_query:
        return f'{parsed.scheme}://{netloc}{path}?{clean_query}'
    return f'{parsed.scheme}://{netloc}{path}'


def remove_duplicate_urls(todo_client: ToDoClient, parsed_tasks: list) -> int:
    """
    Remove duplicate URL tasks, keeping the newest copy.

    Returns:
        Number of duplicates removed.
    """
    url_to_tasks = defaultdict(list)

    for task in parsed_tasks:
        for url in task.get('urls', []):
            normalized = normalize_url(url)
            url_to_tasks[normalized].append(task)

    # Filter to duplicates only
    duplicates = {url: items for url, items in url_to_tasks.items() if len(items) > 1}

    if not duplicates:
        return 0

    deleted = 0
    for url, items in duplicates.items():
        # Sort by created date (newest first), keep first, delete rest
        sorted_items = sorted(items, key=lambda x: x.get('created_at', '') or '', reverse=True)
        for item in sorted_items[1:]:
            try:
                success = todo_client.delete_task(item['list_id'], item['id'])
                if success:
                    deleted += 1
                    logger.info(f"Deleted duplicate: {item['title'][:50]}")
            except Exception as e:
                logger.warning(f"Failed to delete duplicate {item['id']}: {e}")

    return deleted


def main():
    """Main execution flow."""
    # Setup logging
    setup_logging()
    logger.info("=== Microsoft To Do AI Task Manager ===")

    # Validate configuration
    try:
        Config.validate()
        Config.setup_output_dir()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please copy .env.example to .env and fill in your credentials")
        sys.exit(1)

    try:
        # Step 1: Fetch tasks from Microsoft To Do
        logger.info("Step 1: Fetching tasks from Microsoft To Do")
        todo_client = ToDoClient()
        tasks = todo_client.get_all_tasks(include_completed=False)
        logger.info(f"Retrieved {len(tasks)} tasks")

        if not tasks:
            logger.info("No tasks found. Exiting.")
            return

        # Step 2: Parse tasks and extract metadata
        logger.info("Step 2: Parsing task metadata")
        parsed_tasks = []
        for task in tasks:
            parsed = todo_client.parse_task_metadata(task)
            parsed_tasks.append(parsed)

        # Step 2.5: Remove duplicate URLs (if enabled)
        if Config.AUTO_REMOVE_DUPLICATES:
            logger.info("Step 2.5: Checking for duplicate URLs")
            duplicates_removed = remove_duplicate_urls(todo_client, parsed_tasks)
            if duplicates_removed > 0:
                logger.info(f"Removed {duplicates_removed} duplicate URL tasks")
                print(f"\n[CLEANUP] Removed {duplicates_removed} duplicate URL tasks")
                # Re-fetch tasks after cleanup
                tasks = todo_client.get_all_tasks(include_completed=False)
                parsed_tasks = [todo_client.parse_task_metadata(t) for t in tasks]
                logger.info(f"Tasks after cleanup: {len(tasks)}")
            else:
                logger.info("No duplicate URLs found")
        else:
            logger.info("Step 2.5: Auto-remove duplicates disabled (set AUTO_REMOVE_DUPLICATES=true to enable)")

        # Step 3: Fetch web content for tasks with URLs (skip if cached)
        logger.info("Step 3: Fetching web content for URLs")
        content_extractor = ContentExtractor()
        task_contents = {}

        # Initialize cache early to check which tasks need URL fetching
        analysis_cache = AnalysisCache(Config.OUTPUT_DIR / "cache")

        urls_fetched = 0
        urls_skipped = 0

        for task in parsed_tasks:
            task_id = task["id"]
            task_title = task.get("title", "")
            urls = task.get("urls", [])

            if urls:
                # Check if we already have cached analysis for this task
                if analysis_cache.get(task_id, task_title, urls):
                    urls_skipped += 1
                    continue  # Skip URL fetch - we'll use cached analysis

                # Fetch first URL only (to avoid rate limits)
                url = urls[0]
                logger.info(f"Fetching content for: {url}")
                content_data = content_extractor.fetch_url(url)
                if content_data:
                    task_contents[task_id] = content_data.get("content", "")
                urls_fetched += 1

        logger.info(f"URL fetching: {urls_fetched} fetched, {urls_skipped} skipped (cached)")
        if urls_skipped > 0:
            print(f"[CACHE] Skipped {urls_skipped} URL fetches (already analyzed)")

        # Step 4: Analyze tasks with AI (with caching)
        logger.info("Step 4: Analyzing tasks with AI")
        analyzer = TaskAnalyzer()
        # analysis_cache already initialized in Step 3
        tasks_with_analysis = []

        # Clean up cache for completed/deleted tasks
        active_task_ids = {task["id"] for task in parsed_tasks}
        analysis_cache.cleanup_completed(active_task_ids)

        cache_hits = 0
        cache_misses = 0

        for task in parsed_tasks:
            task_id = task["id"]
            task_title = task.get("title", "")
            urls = task.get("urls", [])

            # Check cache first
            cached_analysis = analysis_cache.get(task_id, task_title, urls)

            if cached_analysis:
                # Use cached analysis
                analysis = cached_analysis
                cache_hits += 1
            else:
                # Need to analyze - fetch content if needed
                content = task_contents.get(task_id)
                analysis = analyzer.analyze_task(task, content)
                # Cache the result
                analysis_cache.set(task_id, task_title, urls, analysis)
                cache_misses += 1

            tasks_with_analysis.append({
                "task": task,
                "analysis": analysis
            })

        logger.info(f"Analysis cache: {cache_hits} hits, {cache_misses} new analyses")
        print(f"\n[CACHE] {cache_hits} cached, {cache_misses} new analyses")

        # Step 5: Rank and prioritize tasks
        logger.info("Step 5: Ranking tasks by priority")
        ranker = PriorityRanker()
        ranked_tasks = ranker.rank_tasks(tasks_with_analysis)

        # Step 6: Categorize by timeframe
        logger.info("Step 6: Categorizing tasks by timeframe")
        categorized = ranker.categorize_by_timeframe(ranked_tasks)

        # Step 7: Generate markdown brief
        logger.info("Step 7: Generating daily brief")
        brief_generator = BriefGenerator(Config.OUTPUT_DIR)
        brief_path = brief_generator.generate_daily_brief(categorized)
        logger.info(f"Daily brief saved to: {brief_path}")

        # Step 8: Update tasks (if enabled)
        if Config.ENABLE_TASK_UPDATES:
            logger.info("Step 8: Updating tasks in Microsoft To Do")
            updater = TaskUpdater(todo_client)
            stats = updater.batch_update_tasks(ranked_tasks, dry_run=False)
            logger.info(f"Update stats: {stats}")
        else:
            logger.info("Step 8: Task updates disabled (set ENABLE_TASK_UPDATES=true to enable)")

        # Step 9: Send email brief (if enabled)
        if Config.SEND_EMAIL_BRIEF:
            logger.info("Step 9: Sending email brief")

            # Use enhanced email if enabled
            if Config.USE_ENHANCED_EMAIL:
                email_sender = EmailSenderEnhanced()
                logger.info("Using enhanced email with Morning Insight and Quick Actions")
            else:
                email_sender = EmailSender()

            email_sent = email_sender.send_daily_brief(brief_path, ranked_tasks)
            if email_sent:
                logger.info(f"Email brief sent to {Config.EMAIL_TO}")
                print(f"\n[SUCCESS] Email brief sent to {Config.EMAIL_TO}")
            else:
                logger.warning("Failed to send email brief")
                print("\n[WARNING] Failed to send email brief - check logs")
        else:
            logger.info("Step 9: Email notifications disabled (set SEND_EMAIL_BRIEF=true to enable)")

        # Step 10: Generate weekly analytics (if enabled and appropriate day)
        if Config.GENERATE_WEEKLY_REPORT:
            from datetime import datetime
            today = datetime.now()
            is_report_day = Config.WEEKLY_REPORT_DAY == today.strftime("%A").lower()

            # Always generate on Sundays, or force generate if it's been a week
            if is_report_day or today.weekday() == 6:  # 6 = Sunday
                logger.info("Step 10: Generating weekly analytics report")
                # Pass parsed_tasks for live analysis (stale tasks, URL domains, list breakdown)
                trends_analyzer = WeeklyTrendsAnalyzer(Config.OUTPUT_DIR, tasks=parsed_tasks)
                weekly_report = trends_analyzer.generate_weekly_report(weeks_back=0)
                analytics = trends_analyzer.analyze_week(weeks_back=0)

                weekly_report_path = Config.OUTPUT_DIR / f"weekly_report_{today.strftime('%Y-%m-%d')}.md"
                weekly_report_path.write_text(weekly_report, encoding='utf-8')

                logger.info(f"Weekly report saved to: {weekly_report_path}")
                print(f"\n[ANALYTICS] Weekly report generated: {weekly_report_path}")

                # Send weekly digest email if enabled
                if Config.SEND_WEEKLY_DIGEST and Config.SEND_EMAIL_BRIEF:
                    logger.info("Sending weekly digest email")
                    email_sender = EmailSenderEnhanced()

                    # Prepare week stats for email (including all enhanced analytics)
                    week_stats = {
                        "week_start": analytics.get("week_start", ""),
                        "week_end": analytics.get("week_end", ""),
                        "total_tasks": analytics.get("task_stats", {}).get("total_tasks_tracked", 0),
                        "net_change": analytics.get("completion_insights", {}).get("net_tasks_added", 0),
                        "avg_priority": analytics.get("priority_distribution", {}).get("avg_priority", 0),
                        # Enhanced analytics for rich email formatting
                        "stale_count": analytics.get("stale_tasks", {}).get("stale_count", 0),
                        "stale_tasks": analytics.get("stale_tasks", {}).get("stale_tasks", []),
                        "velocity": analytics.get("velocity", {}),
                        "url_domains": analytics.get("url_domains", {}),
                        "list_breakdown": analytics.get("list_breakdown", {}),
                        "recommendations": analytics.get("recommendations", []),
                    }

                    digest_sent = email_sender.send_weekly_digest(str(weekly_report_path), week_stats)
                    if digest_sent:
                        logger.info(f"Weekly digest emailed to {Config.EMAIL_TO}")
                        print(f"[EMAIL] Weekly digest sent to {Config.EMAIL_TO}")
                    else:
                        logger.warning("Failed to send weekly digest email")
            else:
                logger.info(f"Step 10: Skipping weekly report (generated on {Config.WEEKLY_REPORT_DAY}s)")
        else:
            logger.info("Step 10: Weekly analytics disabled (set GENERATE_WEEKLY_REPORT=true to enable)")

        # Summary
        logger.info("=== Execution Complete ===")
        logger.info(f"Total tasks processed: {len(tasks)}")
        logger.info(f"Focus today: {len(categorized['today'])}")
        logger.info(f"This week: {len(categorized['this_week'])}")
        logger.info(f"Brief: {brief_path}")

        # Print top 5 priorities
        print("\n=== Top 5 Priorities for Today ===\n")
        for i, item in enumerate(ranked_tasks[:5], 1):
            task = item["task"]
            score = item["priority_score"]
            print(f"{i}. [{score:.1f}] {task['title']}")

        print(f"\nFull brief available at: {brief_path}\n")

    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
