"""Standalone script to generate weekly analytics report."""

import sys
from pathlib import Path
from datetime import datetime

from src.config import Config
from src.utils.logging_config import setup_logging
from src.analytics.weekly_trends import WeeklyTrendsAnalyzer

import logging

logger = logging.getLogger(__name__)


def main():
    """Generate weekly analytics report."""
    setup_logging()
    logger.info("=== Weekly Analytics Report Generator ===")

    # Setup output directory
    Config.setup_output_dir()

    # Parse command line arguments
    weeks_back = 0
    if len(sys.argv) > 1:
        try:
            weeks_back = int(sys.argv[1])
            logger.info(f"Generating report for {weeks_back} weeks back")
        except ValueError:
            print("Usage: python generate_weekly_report.py [weeks_back]")
            print("  weeks_back: 0 = current week (default), 1 = last week, etc.")
            sys.exit(1)

    # Initialize analyzer
    trends_analyzer = WeeklyTrendsAnalyzer(Config.OUTPUT_DIR)

    # Generate report
    logger.info("Analyzing weekly trends...")
    weekly_report = trends_analyzer.generate_weekly_report(weeks_back=weeks_back)

    # Save report
    today = datetime.now()
    if weeks_back == 0:
        report_filename = f"weekly_report_{today.strftime('%Y-%m-%d')}.md"
    else:
        report_filename = f"weekly_report_{weeks_back}_weeks_ago_{today.strftime('%Y-%m-%d')}.md"

    weekly_report_path = Config.OUTPUT_DIR / report_filename
    weekly_report_path.write_text(weekly_report, encoding='utf-8')

    logger.info(f"Weekly report saved to: {weekly_report_path}")

    # Print report to console
    print("\n" + "=" * 80)
    print(weekly_report)
    print("=" * 80)
    print(f"\nReport saved to: {weekly_report_path}\n")


if __name__ == "__main__":
    main()
