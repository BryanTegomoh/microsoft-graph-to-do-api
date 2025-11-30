"""Weekly trends and pattern analysis for tasks."""

import logging
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter, defaultdict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WeeklyTrendsAnalyzer:
    """Analyzes weekly patterns and trends from daily briefs."""

    def __init__(self, output_dir: Path, tasks: List[Dict] = None):
        """
        Initialize the weekly trends analyzer.

        Args:
            output_dir: Directory containing daily brief markdown files.
            tasks: Optional list of current tasks for live analysis.
        """
        self.output_dir = Path(output_dir)
        self.tasks = tasks or []

    def analyze_week(self, weeks_back: int = 0) -> Dict:
        """
        Analyze trends for a specific week.

        Args:
            weeks_back: How many weeks back to analyze (0 = current week, 1 = last week, etc.)

        Returns:
            Dictionary containing weekly analytics.
        """
        # Determine date range for the week
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday() + (weeks_back * 7))
        week_end = week_start + timedelta(days=6)

        logger.info(f"Analyzing week: {week_start.date()} to {week_end.date()}")

        # Find all daily briefs in this week
        daily_briefs = self._get_briefs_in_range(week_start, week_end)

        if not daily_briefs:
            logger.warning(f"No daily briefs found for week {week_start.date()} to {week_end.date()}")
            return self._get_empty_analytics(week_start, week_end)

        # Analyze the briefs
        analytics = {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "total_briefs": len(daily_briefs),
            "task_stats": self._analyze_task_stats(daily_briefs),
            "themes": self._extract_themes(daily_briefs),
            "priority_distribution": self._analyze_priority_distribution(daily_briefs),
            "category_breakdown": self._analyze_categories(daily_briefs),
            "completion_insights": self._analyze_completion_patterns(daily_briefs),
            "daily_breakdown": self._get_daily_breakdown(daily_briefs),
        }

        return analytics

    def _get_briefs_in_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get all daily briefs within a date range."""
        briefs = []
        current_date = start_date

        while current_date <= end_date:
            brief_path = self.output_dir / f"daily_brief_{current_date.strftime('%Y-%m-%d')}.md"
            if brief_path.exists():
                try:
                    content = brief_path.read_text(encoding='utf-8')
                    briefs.append({
                        "date": current_date.strftime('%Y-%m-%d'),
                        "path": brief_path,
                        "content": content
                    })
                except Exception as e:
                    logger.error(f"Error reading {brief_path}: {e}")

            current_date += timedelta(days=1)

        return briefs

    def _analyze_task_stats(self, briefs: List[Dict]) -> Dict:
        """Analyze task count statistics across the week."""
        stats = {
            "total_tasks_tracked": 0,
            "avg_tasks_per_day": 0,
            "focus_today_count": 0,
            "this_week_count": 0,
            "later_count": 0,
            "avg_focus_tasks": 0,
            "avg_weekly_tasks": 0,
        }

        focus_counts = []
        week_counts = []
        total_counts = []

        for brief in briefs:
            content = brief["content"]

            # Extract task counts from summary
            total_match = re.search(r'\*\*Total Tasks Analyzed:\*\*\s*(\d+)', content)
            focus_match = re.search(r'\*\*Focus Today:\*\*\s*(\d+)', content)
            week_match = re.search(r'\*\*This Week:\*\*\s*(\d+)', content)
            later_match = re.search(r'\*\*Later:\*\*\s*(\d+)', content)

            if total_match:
                total = int(total_match.group(1))
                total_counts.append(total)
                stats["total_tasks_tracked"] = max(stats["total_tasks_tracked"], total)

            if focus_match:
                focus_count = int(focus_match.group(1))
                focus_counts.append(focus_count)
                stats["focus_today_count"] += focus_count

            if week_match:
                week_count = int(week_match.group(1))
                week_counts.append(week_count)
                stats["this_week_count"] += week_count

            if later_match:
                later_count = int(later_match.group(1))
                stats["later_count"] = max(stats["later_count"], later_count)

        # Calculate averages
        if briefs:
            stats["avg_tasks_per_day"] = round(sum(total_counts) / len(briefs), 1) if total_counts else 0
            stats["avg_focus_tasks"] = round(sum(focus_counts) / len(briefs), 1) if focus_counts else 0
            stats["avg_weekly_tasks"] = round(sum(week_counts) / len(briefs), 1) if week_counts else 0

        return stats

    def _extract_themes(self, briefs: List[Dict]) -> Dict:
        """Extract and count recurring themes from task titles and descriptions."""
        # Keywords to track (healthcare/AI focus)
        theme_keywords = {
            "AI/Machine Learning": [r'\bAI\b', r'\bML\b', r'machine learning', r'deep learning', r'neural', r'LLM', r'GPT', r'Claude', r'Grok'],
            "Healthcare": [r'health', r'medical', r'clinical', r'patient', r'doctor', r'physician', r'CDC', r'FDA'],
            "Research": [r'research', r'paper', r'study', r'analysis', r'data', r'findings', r'publication'],
            "Career/Jobs": [r'application', r'job', r'position', r'researcher', r'co-founder', r'interview', r'apply'],
            "Vaccines/Immunology": [r'vaccine', r'autism', r'immunization', r'antibody', r'immunity'],
            "Regulation/Policy": [r'regulation', r'policy', r'compliance', r'framework', r'governance', r'risk'],
            "Startups/Entrepreneurship": [r'startup', r'co-founder', r'entrepreneur', r'venture', r'founder'],
            "Immigration": [r'USCIS', r'visa', r'green card', r'I-485', r'civil surgeon', r'immigration'],
        }

        theme_counts = Counter()
        theme_tasks = defaultdict(list)

        for brief in briefs:
            content = brief["content"]

            # Extract task titles (lines starting with ###)
            task_titles = re.findall(r'^###\s+\d+\.\s+(.+)$', content, re.MULTILINE)

            for title in task_titles:
                for theme, patterns in theme_keywords.items():
                    for pattern in patterns:
                        if re.search(pattern, title, re.IGNORECASE):
                            theme_counts[theme] += 1
                            if title not in theme_tasks[theme]:
                                theme_tasks[theme].append(title)
                            break  # Count each task only once per theme

        # Get top themes
        top_themes = theme_counts.most_common(5)

        return {
            "top_themes": [{"theme": theme, "count": count} for theme, count in top_themes],
            "theme_details": dict(theme_tasks),
            "total_themes_identified": len(theme_counts)
        }

    def _analyze_priority_distribution(self, briefs: List[Dict]) -> Dict:
        """Analyze distribution of priority scores."""
        priority_scores = []

        for brief in briefs:
            content = brief["content"]
            # Extract priority scores (format: "Priority Score:** 59.8/100")
            scores = re.findall(r'\*\*Priority Score:\*\*\s*(\d+\.?\d*)/100', content)
            priority_scores.extend([float(score) for score in scores])

        if not priority_scores:
            return {"avg_priority": 0, "high_priority_count": 0, "medium_priority_count": 0, "low_priority_count": 0}

        high_priority = [s for s in priority_scores if s >= 80]
        medium_priority = [s for s in priority_scores if 60 <= s < 80]
        low_priority = [s for s in priority_scores if s < 60]

        return {
            "avg_priority": round(sum(priority_scores) / len(priority_scores), 1),
            "high_priority_count": len(high_priority),
            "medium_priority_count": len(medium_priority),
            "low_priority_count": len(low_priority),
            "highest_score": max(priority_scores) if priority_scores else 0,
            "lowest_score": min(priority_scores) if priority_scores else 0,
        }

    def _analyze_categories(self, briefs: List[Dict]) -> Dict:
        """Analyze task categories from the briefs."""
        # This is a simplified version - in a real implementation,
        # you'd parse the actual category data from tasks
        category_keywords = {
            "apply": [r'\[APPLY\]', r'application', r'apply for'],
            "contact": [r'\[CONTACT\]', r'reach out', r'connect with', r'co-founder'],
            "research": [r'\[RESEARCH\]', r'research', r'investigate'],
            "reading": [r'\[READ\]', r'read', r'article', r'paper'],
            "review": [r'\[REVIEW\]', r'review', r'analyze'],
            "watch": [r'\[WATCH\]', r'watch', r'video', r'webinar'],
            "urgent": [r'\[URGENT\]', r'urgent', r'asap'],
        }

        category_counts = Counter()

        for brief in briefs:
            content = brief["content"]
            task_titles = re.findall(r'^###\s+\d+\.\s+(.+)$', content, re.MULTILINE)

            for title in task_titles:
                for category, patterns in category_keywords.items():
                    for pattern in patterns:
                        if re.search(pattern, title, re.IGNORECASE):
                            category_counts[category] += 1
                            break

        return {
            "categories": dict(category_counts),
            "top_category": category_counts.most_common(1)[0] if category_counts else ("none", 0)
        }

    def _analyze_completion_patterns(self, briefs: List[Dict]) -> Dict:
        """Analyze task completion patterns by comparing total task counts."""
        if len(briefs) < 2:
            return {
                "net_tasks_added": 0,
                "estimated_completion_rate": 0,
                "trend": "insufficient_data"
            }

        # Compare first and last brief
        first_brief = briefs[0]
        last_brief = briefs[-1]

        first_total = self._extract_total_tasks(first_brief["content"])
        last_total = self._extract_total_tasks(last_brief["content"])

        net_change = last_total - first_total

        # Estimate completion rate (simplified)
        # If tasks decreased, estimate that as completion
        estimated_completed = max(0, -net_change)

        return {
            "tasks_at_week_start": first_total,
            "tasks_at_week_end": last_total,
            "net_tasks_added": net_change,
            "estimated_completed": estimated_completed,
            "trend": "increasing" if net_change > 0 else "decreasing" if net_change < 0 else "stable"
        }

    def _extract_total_tasks(self, content: str) -> int:
        """Extract total task count from brief content."""
        match = re.search(r'\*\*Total Tasks Analyzed:\*\*\s*(\d+)', content)
        return int(match.group(1)) if match else 0

    def _get_daily_breakdown(self, briefs: List[Dict]) -> List[Dict]:
        """Get a breakdown of each day in the week."""
        breakdown = []

        for brief in briefs:
            content = brief["content"]
            total = self._extract_total_tasks(content)

            focus_match = re.search(r'\*\*Focus Today:\*\*\s*(\d+)', content)
            week_match = re.search(r'\*\*This Week:\*\*\s*(\d+)', content)

            breakdown.append({
                "date": brief["date"],
                "total_tasks": total,
                "focus_tasks": int(focus_match.group(1)) if focus_match else 0,
                "week_tasks": int(week_match.group(1)) if week_match else 0,
            })

        return breakdown

    def _get_empty_analytics(self, week_start: datetime, week_end: datetime) -> Dict:
        """Return empty analytics structure."""
        return {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "total_briefs": 0,
            "task_stats": {},
            "themes": {"top_themes": [], "theme_details": {}, "total_themes_identified": 0},
            "priority_distribution": {},
            "category_breakdown": {},
            "completion_insights": {},
            "daily_breakdown": [],
        }

    def _analyze_stale_tasks(self, days_threshold: int = 30) -> Dict:
        """
        Identify tasks that haven't been touched in X days.

        Args:
            days_threshold: Number of days to consider a task stale.

        Returns:
            Dictionary with stale task analysis.
        """
        if not self.tasks:
            return {"stale_count": 0, "stale_tasks": [], "oldest_task": None}

        now = datetime.now()
        stale_tasks = []

        for task in self.tasks:
            created_at = task.get("created_at")
            if created_at:
                try:
                    # Parse ISO format date
                    if isinstance(created_at, str):
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_date = created_date.replace(tzinfo=None)  # Make naive for comparison
                    else:
                        created_date = created_at

                    age_days = (now - created_date).days
                    if age_days >= days_threshold:
                        stale_tasks.append({
                            "title": task.get("title", "Unknown")[:80],
                            "age_days": age_days,
                            "list_name": task.get("list_name", "Unknown"),
                            "id": task.get("id"),
                        })
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error parsing date for task: {e}")

        # Sort by age (oldest first)
        stale_tasks.sort(key=lambda x: x["age_days"], reverse=True)

        return {
            "stale_count": len(stale_tasks),
            "stale_tasks": stale_tasks[:10],  # Top 10 oldest
            "oldest_task": stale_tasks[0] if stale_tasks else None,
            "avg_age_days": round(sum(t["age_days"] for t in stale_tasks) / len(stale_tasks), 1) if stale_tasks else 0,
        }

    def _analyze_url_domains(self) -> Dict:
        """
        Analyze which domains/sources tasks come from.

        Returns:
            Dictionary with domain frequency analysis.
        """
        if not self.tasks:
            return {"domain_counts": {}, "top_domains": [], "total_urls": 0}

        domain_counts = Counter()

        for task in self.tasks:
            urls = task.get("urls", [])
            for url in urls:
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc.lower()
                    # Clean up common prefixes
                    if domain.startswith("www."):
                        domain = domain[4:]
                    if domain:
                        domain_counts[domain] += 1
                except Exception:
                    pass

        top_domains = domain_counts.most_common(10)

        return {
            "domain_counts": dict(domain_counts),
            "top_domains": [{"domain": d, "count": c} for d, c in top_domains],
            "total_urls": sum(domain_counts.values()),
            "unique_domains": len(domain_counts),
        }

    def _analyze_lists(self) -> Dict:
        """
        Analyze task distribution across To Do lists.

        Returns:
            Dictionary with list-by-list breakdown.
        """
        if not self.tasks:
            return {"list_counts": {}, "top_lists": [], "total_lists": 0}

        list_counts = Counter()

        for task in self.tasks:
            list_name = task.get("list_name", "Unknown")
            list_counts[list_name] += 1

        sorted_lists = list_counts.most_common()

        return {
            "list_counts": dict(list_counts),
            "top_lists": [{"list": name, "count": count} for name, count in sorted_lists[:10]],
            "total_lists": len(list_counts),
            "largest_list": sorted_lists[0] if sorted_lists else ("None", 0),
        }

    def _calculate_velocity(self, briefs: List[Dict]) -> Dict:
        """
        Calculate task completion velocity and backlog projections.

        Returns:
            Dictionary with velocity metrics.
        """
        if len(briefs) < 2:
            return {
                "avg_daily_change": 0,
                "completion_rate": 0,
                "days_to_clear": None,
                "trend_direction": "unknown"
            }

        # Track daily changes
        daily_changes = []
        prev_total = None

        for brief in briefs:
            total = self._extract_total_tasks(brief["content"])
            if prev_total is not None:
                daily_changes.append(total - prev_total)
            prev_total = total

        if not daily_changes:
            return {
                "avg_daily_change": 0,
                "completion_rate": 0,
                "days_to_clear": None,
                "trend_direction": "unknown"
            }

        avg_change = sum(daily_changes) / len(daily_changes)

        # Calculate completion rate (negative change = completion)
        completions = [c for c in daily_changes if c < 0]
        avg_completion = abs(sum(completions) / len(completions)) if completions else 0

        # Project days to clear backlog
        current_total = prev_total or 0
        days_to_clear = None
        if avg_change < 0 and current_total > 0:
            days_to_clear = round(current_total / abs(avg_change))

        return {
            "avg_daily_change": round(avg_change, 1),
            "completion_rate": round(avg_completion, 1),
            "days_to_clear": days_to_clear,
            "trend_direction": "decreasing" if avg_change < -0.5 else "increasing" if avg_change > 0.5 else "stable",
            "current_backlog": current_total,
        }

    def _compare_themes_to_last_week(self, current_themes: Dict) -> Dict:
        """
        Compare this week's themes to last week.

        Returns:
            Dictionary showing theme changes.
        """
        # Get last week's briefs
        today = datetime.now()
        last_week_start = today - timedelta(days=today.weekday() + 7)
        last_week_end = last_week_start + timedelta(days=6)

        last_week_briefs = self._get_briefs_in_range(last_week_start, last_week_end)

        if not last_week_briefs:
            return {"comparison_available": False, "changes": []}

        last_week_themes = self._extract_themes(last_week_briefs)

        # Compare theme counts
        current_counts = {t["theme"]: t["count"] for t in current_themes.get("top_themes", [])}
        last_counts = {t["theme"]: t["count"] for t in last_week_themes.get("top_themes", [])}

        all_themes = set(current_counts.keys()) | set(last_counts.keys())

        changes = []
        for theme in all_themes:
            current = current_counts.get(theme, 0)
            last = last_counts.get(theme, 0)
            change = current - last
            if change != 0:
                changes.append({
                    "theme": theme,
                    "this_week": current,
                    "last_week": last,
                    "change": change,
                    "direction": "up" if change > 0 else "down"
                })

        # Sort by absolute change
        changes.sort(key=lambda x: abs(x["change"]), reverse=True)

        return {
            "comparison_available": True,
            "changes": changes[:5],  # Top 5 changes
            "trending_up": [c for c in changes if c["direction"] == "up"][:3],
            "trending_down": [c for c in changes if c["direction"] == "down"][:3],
        }

    def _generate_action_recommendations(self, analytics: Dict) -> List[Dict]:
        """
        Generate specific actionable recommendations.

        Returns:
            List of recommendation dictionaries.
        """
        recommendations = []

        # Stale tasks recommendation
        stale = analytics.get("stale_tasks", {})
        if stale.get("stale_count", 0) > 5:
            oldest = stale.get("stale_tasks", [])[:3]
            titles = [t["title"][:40] + "..." if len(t["title"]) > 40 else t["title"] for t in oldest]
            recommendations.append({
                "type": "cleanup",
                "priority": "medium",
                "action": f"Review {stale['stale_count']} stale tasks (30+ days old)",
                "details": f"Oldest: {', '.join(titles)}",
                "impact": "Reduce cognitive load and keep list relevant"
            })

        # High priority overload
        priority = analytics.get("priority_distribution", {})
        high_count = priority.get("high_priority_count", 0)
        if high_count > 10:
            recommendations.append({
                "type": "prioritization",
                "priority": "high",
                "action": f"Re-evaluate {high_count} high-priority tasks",
                "details": "Too many urgent items dilutes focus",
                "impact": "Better focus on truly critical items"
            })

        # Backlog growth
        velocity = analytics.get("velocity", {})
        if velocity.get("avg_daily_change", 0) > 3:
            recommendations.append({
                "type": "intake",
                "priority": "medium",
                "action": "Slow down task intake or increase completion rate",
                "details": f"Adding ~{velocity['avg_daily_change']:.1f} tasks/day net",
                "impact": "Prevent backlog from growing unmanageable"
            })

        # Domain concentration
        domains = analytics.get("url_domains", {})
        top_domains = domains.get("top_domains", [])
        if top_domains and top_domains[0]["count"] > 20:
            top = top_domains[0]
            recommendations.append({
                "type": "research",
                "priority": "low",
                "action": f"Consider batch-processing {top['domain']} content",
                "details": f"{top['count']} tasks from this source",
                "impact": "More efficient research workflow"
            })

        # List imbalance
        lists = analytics.get("list_breakdown", {})
        largest = lists.get("largest_list", ("", 0))
        if largest[1] > 100:
            recommendations.append({
                "type": "organization",
                "priority": "low",
                "action": f"Consider splitting '{largest[0]}' list",
                "details": f"{largest[1]} tasks in one list",
                "impact": "Better organization and faster navigation"
            })

        return recommendations

    def generate_weekly_report(self, weeks_back: int = 0) -> str:
        """
        Generate a formatted weekly report.

        Args:
            weeks_back: How many weeks back to analyze (0 = current week)

        Returns:
            Formatted markdown report string.
        """
        analytics = self.analyze_week(weeks_back)

        # Get briefs for velocity calculation
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday() + (weeks_back * 7))
        week_end = week_start + timedelta(days=6)
        briefs = self._get_briefs_in_range(week_start, week_end)

        # Add new analytics sections
        analytics["stale_tasks"] = self._analyze_stale_tasks()
        analytics["url_domains"] = self._analyze_url_domains()
        analytics["list_breakdown"] = self._analyze_lists()
        analytics["velocity"] = self._calculate_velocity(briefs)
        analytics["theme_comparison"] = self._compare_themes_to_last_week(analytics.get("themes", {}))
        analytics["recommendations"] = self._generate_action_recommendations(analytics)

        # Build the report
        report_lines = [
            f"# Weekly Task Analytics Report",
            f"",
            f"**Week:** {analytics['week_start']} to {analytics['week_end']}",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"---",
            f"",
            f"## Summary",
            f"",
        ]

        # Task statistics
        stats = analytics.get("task_stats", {})
        if stats:
            report_lines.extend([
                f"### Task Volume",
                f"- **Total Tasks Tracked:** {stats.get('total_tasks_tracked', 0)}",
                f"- **Average Tasks per Day:** {stats.get('avg_tasks_per_day', 0)}",
                f"- **Average Focus Tasks:** {stats.get('avg_focus_tasks', 0)}/day",
                f"- **Average Weekly Tasks:** {stats.get('avg_weekly_tasks', 0)}/day",
                f"- **Tasks in 'Later' Bucket:** {stats.get('later_count', 0)}",
                f"",
            ])

        # Velocity metrics (NEW)
        velocity = analytics.get("velocity", {})
        if velocity and velocity.get("trend_direction") != "unknown":
            report_lines.extend([
                f"### Completion Velocity",
                f"- **Daily Change:** {velocity.get('avg_daily_change', 0):+.1f} tasks/day",
                f"- **Avg Completion Rate:** {velocity.get('completion_rate', 0):.1f} tasks/day",
                f"- **Current Backlog:** {velocity.get('current_backlog', 0)} tasks",
                f"- **Trend:** {velocity.get('trend_direction', 'unknown').title()}",
            ])
            if velocity.get("days_to_clear"):
                report_lines.append(f"- **Est. Days to Clear:** {velocity['days_to_clear']} days (at current rate)")
            report_lines.append("")

        # Completion patterns
        completion = analytics.get("completion_insights", {})
        if completion:
            report_lines.extend([
                f"### Completion Insights",
                f"- **Tasks at Week Start:** {completion.get('tasks_at_week_start', 0)}",
                f"- **Tasks at Week End:** {completion.get('tasks_at_week_end', 0)}",
                f"- **Net Change:** {completion.get('net_tasks_added', 0):+d} tasks",
                f"- **Estimated Completed:** {completion.get('estimated_completed', 0)} tasks",
                f"- **Trend:** {completion.get('trend', 'unknown').title()}",
                f"",
            ])

        # Priority distribution
        priority = analytics.get("priority_distribution", {})
        if priority:
            report_lines.extend([
                f"### Priority Distribution",
                f"- **Average Priority Score:** {priority.get('avg_priority', 0)}/100",
                f"- **High Priority (80+):** {priority.get('high_priority_count', 0)} tasks",
                f"- **Medium Priority (60-79):** {priority.get('medium_priority_count', 0)} tasks",
                f"- **Low Priority (<60):** {priority.get('low_priority_count', 0)} tasks",
                f"",
            ])

        # Stale Tasks Alert (NEW)
        stale = analytics.get("stale_tasks", {})
        if stale.get("stale_count", 0) > 0:
            report_lines.extend([
                f"## Stale Tasks Alert",
                f"",
                f"**{stale['stale_count']} tasks** are 30+ days old (avg age: {stale.get('avg_age_days', 0)} days)",
                f"",
                f"**Oldest tasks to review:**",
                f"",
            ])
            for task in stale.get("stale_tasks", [])[:5]:
                report_lines.append(f"- [{task['age_days']} days] {task['title']}")
            report_lines.append("")

        # URL Domain Analysis (NEW)
        domains = analytics.get("url_domains", {})
        if domains.get("total_urls", 0) > 0:
            report_lines.extend([
                f"## Research Sources",
                f"",
                f"**{domains['total_urls']} URLs** from **{domains['unique_domains']} domains**",
                f"",
                f"| Domain | Tasks |",
                f"|--------|-------|",
            ])
            for d in domains.get("top_domains", [])[:8]:
                report_lines.append(f"| {d['domain']} | {d['count']} |")
            report_lines.append("")

        # List Breakdown (NEW)
        lists = analytics.get("list_breakdown", {})
        if lists.get("total_lists", 0) > 0:
            report_lines.extend([
                f"## Tasks by List",
                f"",
                f"| List | Count |",
                f"|------|-------|",
            ])
            for lst in lists.get("top_lists", []):
                report_lines.append(f"| {lst['list']} | {lst['count']} |")
            report_lines.append("")

        # Top themes with week-over-week comparison
        themes = analytics.get("themes", {})
        top_themes = themes.get("top_themes", [])
        theme_comparison = analytics.get("theme_comparison", {})

        if top_themes:
            report_lines.extend([
                f"## Trending Themes",
                f"",
            ])
            for i, theme_data in enumerate(top_themes, 1):
                theme = theme_data.get("theme", "Unknown")
                count = theme_data.get("count", 0)
                report_lines.append(f"{i}. **{theme}** - {count} tasks")

            # Week-over-week comparison (NEW)
            if theme_comparison.get("comparison_available"):
                trending_up = theme_comparison.get("trending_up", [])
                trending_down = theme_comparison.get("trending_down", [])

                if trending_up or trending_down:
                    report_lines.extend(["", "**Week-over-Week Changes:**"])
                    for t in trending_up:
                        report_lines.append(f"- {t['theme']}: +{t['change']} tasks")
                    for t in trending_down:
                        report_lines.append(f"- {t['theme']}: {t['change']} tasks")

            report_lines.append("")

        # Category breakdown
        categories = analytics.get("category_breakdown", {})
        category_dict = categories.get("categories", {})
        if category_dict:
            report_lines.extend([
                f"## Category Breakdown",
                f"",
            ])
            sorted_categories = sorted(category_dict.items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_categories:
                report_lines.append(f"- **{category.title()}:** {count} tasks")

            report_lines.append("")

        # Daily breakdown
        daily = analytics.get("daily_breakdown", [])
        if daily:
            report_lines.extend([
                f"## Daily Breakdown",
                f"",
                f"| Date | Total Tasks | Focus | This Week |",
                f"|------|-------------|-------|-----------|",
            ])
            for day in daily:
                report_lines.append(
                    f"| {day['date']} | {day['total_tasks']} | {day['focus_tasks']} | {day['week_tasks']} |"
                )

            report_lines.append("")

        # Action Recommendations (NEW)
        recommendations = analytics.get("recommendations", [])
        if recommendations:
            report_lines.extend([
                f"---",
                f"",
                f"## Action Recommendations",
                f"",
            ])
            for rec in recommendations:
                priority_emoji = {"high": "!!", "medium": "!", "low": ""}
                emoji = priority_emoji.get(rec.get("priority", ""), "")
                report_lines.extend([
                    f"### {emoji} {rec['action']}",
                    f"- **Type:** {rec['type'].title()}",
                    f"- **Details:** {rec['details']}",
                    f"- **Impact:** {rec['impact']}",
                    f"",
                ])

        # Add insights section
        report_lines.extend([
            f"---",
            f"",
            f"## Key Insights",
            f"",
        ])

        # Generate insights based on data
        insights = self._generate_insights(analytics)
        for insight in insights:
            report_lines.append(f"- {insight}")

        report_lines.append("")
        report_lines.append(f"*Generated by Microsoft To Do AI Task Manager - Weekly Analytics*")

        return "\n".join(report_lines)

    def _generate_insights(self, analytics: Dict) -> List[str]:
        """Generate key insights from the analytics data."""
        insights = []

        # Task volume insights
        stats = analytics.get("task_stats", {})
        total = stats.get("total_tasks_tracked", 0)
        later_count = stats.get("later_count", 0)
        if later_count > 0 and total > 0:
            later_pct = (later_count / total) * 100
            if later_pct > 80:
                insights.append(f"**Research backlog heavy:** {later_pct:.0f}% of tasks are in 'Later' - consider archiving low-value items")

        # Completion insights
        completion = analytics.get("completion_insights", {})
        net_change = completion.get("net_tasks_added", 0)
        if net_change > 5:
            insights.append(f"**High intake week:** Added {net_change} net tasks - you're capturing a lot of new items")
        elif net_change < -5:
            insights.append(f"**Progress week:** Completed {-net_change} net tasks - great job clearing the backlog!")

        # Theme insights
        themes = analytics.get("themes", {})
        top_themes = themes.get("top_themes", [])
        if top_themes:
            top_theme = top_themes[0]
            insights.append(f"**Top focus area:** {top_theme['theme']} is trending ({top_theme['count']} tasks this week)")

        # Priority insights
        priority = analytics.get("priority_distribution", {})
        high_count = priority.get("high_priority_count", 0)
        if high_count == 0:
            insights.append("**No urgent items:** You have no high-priority (80+) tasks - good time for deep work on research")
        elif high_count > 10:
            insights.append(f"**High urgency load:** {high_count} high-priority tasks - consider time-blocking for these")

        # Focus task insights
        avg_focus = stats.get("avg_focus_tasks", 0)
        if avg_focus < 1:
            insights.append("**Low daily focus:** Most tasks are below priority threshold - consider adjusting priorities or deadlines")

        return insights
