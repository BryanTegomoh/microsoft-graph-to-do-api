"""Main orchestration script for Microsoft To Do AI Task Manager."""

import logging
import sys
from pathlib import Path

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

logger = logging.getLogger(__name__)


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

        # Step 3: Fetch web content for tasks with URLs
        logger.info("Step 3: Fetching web content for URLs")
        content_extractor = ContentExtractor()
        task_contents = {}

        for task in parsed_tasks:
            urls = task.get("urls", [])
            if urls:
                # Fetch first URL only (to avoid rate limits)
                url = urls[0]
                logger.info(f"Fetching content for: {url}")
                content_data = content_extractor.fetch_url(url)
                if content_data:
                    task_contents[task["id"]] = content_data.get("content", "")

        # Step 4: Analyze tasks with AI
        logger.info("Step 4: Analyzing tasks with AI")
        analyzer = TaskAnalyzer()
        tasks_with_analysis = []

        for task in parsed_tasks:
            content = task_contents.get(task["id"])
            analysis = analyzer.analyze_task(task, content)

            tasks_with_analysis.append({
                "task": task,
                "analysis": analysis
            })

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
                trends_analyzer = WeeklyTrendsAnalyzer(Config.OUTPUT_DIR)
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

                    # Prepare week stats for email
                    week_stats = {
                        "week_start": analytics.get("week_start", ""),
                        "week_end": analytics.get("week_end", ""),
                        "total_tasks": analytics.get("task_stats", {}).get("total_tasks_tracked", 0),
                        "net_change": analytics.get("completion_insights", {}).get("net_tasks_added", 0),
                        "avg_priority": analytics.get("priority_distribution", {}).get("avg_priority", 0),
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
