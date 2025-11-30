"""Enhanced email notification sender with Quick Actions and Weekly Digest."""

import logging
import smtplib
from html import escape
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter

import markdown

from src.config import Config

logger = logging.getLogger(__name__)


class EmailSenderEnhanced:
    """Sends enhanced email notifications with Quick Actions and insights."""

    def __init__(self):
        """Initialize the email sender."""
        self.smtp_server = Config.EMAIL_SMTP_SERVER
        self.smtp_port = Config.EMAIL_SMTP_PORT
        self.from_email = Config.EMAIL_FROM
        self.to_email = Config.EMAIL_TO
        self.password = Config.EMAIL_PASSWORD

    def send_daily_brief(self, brief_path: str, top_tasks: List[Dict]) -> bool:
        """
        Send enhanced daily brief via email with Morning Insight and Quick Actions.

        Args:
            brief_path: Path to the markdown brief file.
            top_tasks: List of top priority tasks.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Read the brief content
            with open(brief_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🎯 Your Daily Task Brief - {datetime.now().strftime('%B %d, %Y')}"
            msg['From'] = self.from_email
            msg['To'] = self.to_email

            # Create plain text version
            text_content = self._create_text_version(top_tasks, markdown_content)

            # Create HTML version with enhancements
            html_content = self._create_html_version_enhanced(top_tasks, markdown_content)

            # Attach both versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            logger.info(f"Sending enhanced email to {self.to_email}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)

            logger.info("Enhanced email sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_weekly_digest(self, weekly_report_path: str, week_stats: Dict) -> bool:
        """
        Send weekly digest email.

        Args:
            weekly_report_path: Path to weekly report markdown file.
            week_stats: Dictionary with weekly statistics.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Read the weekly report content
            with open(weekly_report_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📊 Your Weekly Task Analytics - {datetime.now().strftime('%B %d, %Y')}"
            msg['From'] = self.from_email
            msg['To'] = self.to_email

            # Create HTML version
            html_content = self._create_weekly_digest_html(markdown_content, week_stats)

            # Create plain text version
            text_content = markdown_content

            # Attach both versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            logger.info(f"Sending weekly digest to {self.to_email}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)

            logger.info("Weekly digest sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send weekly digest: {e}")
            return False

    def _generate_morning_insight(self, top_tasks: List[Dict]) -> str:
        """
        Generate a smart morning insight based on task analysis.

        Args:
            top_tasks: List of top priority tasks.

        Returns:
            Morning insight message string.
        """
        if not top_tasks:
            return "Your task list is clear - great time to plan ahead or tackle long-term projects!"

        total_tasks = len(top_tasks)
        high_priority = sum(1 for t in top_tasks if t['priority_score'] >= 80)
        avg_score = sum(t['priority_score'] for t in top_tasks) / total_tasks if total_tasks > 0 else 0

        # Collect categories
        categories = [t['analysis'].get('category', 'other') for t in top_tasks[:10]]
        category_counts = Counter(categories)
        top_category = category_counts.most_common(1)[0][0] if category_counts else "tasks"

        # Generate contextual insights
        if high_priority >= 5:
            return f"High-urgency day ahead with {high_priority} critical tasks. Focus on {top_category} items first and consider time-blocking."
        elif high_priority >= 2:
            return f"You have {high_priority} high-priority tasks today, primarily {top_category} work. Start with these while you're fresh!"
        elif avg_score < 60:
            return f"Light priority load today ({total_tasks} {top_category} tasks). Perfect opportunity for deep work or clearing your reading backlog."
        elif top_category == "apply":
            return f"{category_counts['apply']} job applications on your list. Set aside focused time this morning to complete them while at your peak."
        elif top_category == "contact":
            return f"{category_counts['contact']} networking/outreach tasks today. Morning is ideal for reaching out when people check their inboxes!"
        elif top_category == "research":
            return f"Research-focused day with {total_tasks} items. Consider batching similar topics and setting time limits to avoid rabbit holes."
        else:
            return f"{total_tasks} tasks across {len(category_counts)} categories. Prioritize {top_category} work and tackle high-value items first."

    def _create_text_version(self, top_tasks: List[Dict], full_content: str) -> str:
        """Create plain text email version with morning insight."""
        lines = []
        lines.append(f"Daily Task Brief - {datetime.now().strftime('%B %d, %Y')}")
        lines.append("=" * 60)
        lines.append("")

        # Add morning insight
        insight = self._generate_morning_insight(top_tasks)
        lines.append("MORNING INSIGHT")
        lines.append(insight)
        lines.append("")
        lines.append("=" * 60)
        lines.append("")
        lines.append("TOP PRIORITIES FOR TODAY")
        lines.append("")

        for i, item in enumerate(top_tasks[:10], 1):
            task = item['task']
            analysis = item['analysis']
            score = item['priority_score']

            lines.append(f"{i}. [{score:.1f}] {task['title']}")
            lines.append(f"   Summary: {analysis.get('summary', 'N/A')}")
            lines.append(f"   Action: {analysis.get('suggested_action', 'N/A')}")
            lines.append(f"   Time: {analysis.get('estimated_time_minutes', 'N/A')} minutes")
            lines.append("")

        lines.append("-" * 60)
        lines.append("")
        lines.append("Have a productive day!")
        lines.append("")
        lines.append("---")
        lines.append("Generated by Microsoft To Do AI Task Manager")

        return "\n".join(lines)

    def _create_html_version_enhanced(self, top_tasks: List[Dict], markdown_content: str) -> str:
        """Create enhanced HTML email with Morning Insight and Quick Actions."""
        # Generate morning insight
        morning_insight = self._generate_morning_insight(top_tasks)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .insight-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .insight-box h3 {{
            margin-top: 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .insight-box p {{
            margin: 10px 0 0 0;
            font-size: 18px;
            font-weight: 500;
            line-height: 1.5;
        }}
        .task {{
            background-color: #f8f9fa;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }}
        .task-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        .task-score {{
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .task-score.high {{
            background-color: #e74c3c;
        }}
        .task-score.medium {{
            background-color: #f39c12;
        }}
        .task-score.low {{
            background-color: #27ae60;
        }}
        .task-detail {{
            margin: 5px 0;
            padding-left: 10px;
        }}
        .task-detail strong {{
            color: #555;
        }}
        .quick-actions {{
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #ddd;
        }}
        .action-btn {{
            display: inline-block;
            padding: 6px 12px;
            margin: 4px 4px 4px 0;
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            text-decoration: none;
            color: #333;
            font-size: 13px;
        }}
        .action-btn.complete {{
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }}
        .action-btn.snooze {{
            background-color: #fff3cd;
            border-color: #ffeaa7;
            color: #856404;
        }}
        .action-btn.priority {{
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #777;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Your Daily Task Brief</h1>
        <p style="color: #777; font-size: 14px;">{datetime.now().strftime('%A, %B %d, %Y')}</p>

        <div class="insight-box">
            <h3>☀️ Morning Insight</h3>
            <p>{morning_insight}</p>
        </div>

        <h2>Top Priorities for Today</h2>
"""

        for i, item in enumerate(top_tasks[:10], 1):
            task = item['task']
            analysis = item['analysis']
            score = item['priority_score']
            task_id = task.get('id', '')
            list_id = task.get('listId', '')

            # Determine score class
            score_class = "high" if score >= 80 else "medium" if score >= 60 else "low"

            html += f"""
        <div class="task">
            <div class="task-title">
                {i}. <span class="task-score {score_class}">{score:.1f}</span> {task['title']}
            </div>
            <div class="task-detail"><strong>Summary:</strong> {analysis.get('summary', 'N/A')}</div>
            <div class="task-detail"><strong>Next Action:</strong> {analysis.get('suggested_action', 'N/A')}</div>
            <div class="task-detail"><strong>Estimated Time:</strong> {analysis.get('estimated_time_minutes', 'N/A')} minutes</div>
"""

            # Add "Why it matters" if available
            why_it_matters = analysis.get('why_it_matters')
            if why_it_matters:
                html += f"""
            <div class="task-detail" style="background-color: #e8f5e9; padding: 8px; border-left: 3px solid #4caf50; margin: 8px 0;">
                <strong>💡 Why this matters:</strong> {why_it_matters}
            </div>
"""

            # Add due date if available
            if task.get('due_date'):
                html += f"""
            <div class="task-detail"><strong>Due:</strong> {task['due_date']}</div>
"""

            # Add tags if available
            tags = analysis.get('tags', [])
            if tags:
                html += f"""
            <div class="task-detail"><strong>Tags:</strong> {', '.join(tags[:5])}</div>
"""

            # Add URLs if available
            urls = task.get('urls', [])
            if urls:
                html += """
            <div class="task-detail"><strong>Links:</strong><br>
"""
                for url in urls[:3]:
                    html += f"""
                <a href="{url}" style="color: #3498db; text-decoration: none; display: block; margin: 3px 0;">{url[:60]}{'...' if len(url) > 60 else ''}</a>
"""
                html += """
            </div>
"""

            # Add Quick Actions with web link that opens To Do
            # Use Microsoft's official web URL which works in all email clients
            # On mobile, this will prompt to open in the To Do app if installed
            todo_web_url = f"https://to-do.microsoft.com/tasks/id/{task_id}/details"

            html += f"""
            <div class="quick-actions">
                <strong style="font-size: 12px; color: #777;">Quick Action:</strong><br>
                <a href="{todo_web_url}" class="action-btn" style="text-decoration: none;" title="Open in Microsoft To Do">📱 Open in To Do</a>
            </div>
"""

            html += """
        </div>
"""

        html += """
        <div class="footer">
            <p>📊 Full detailed brief is available in your output folder</p>
            <p style="margin-top: 15px;">
                <em>Generated by Microsoft To Do AI Task Manager</em><br>
                Powered by AI • Automated Daily
            </p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def _create_weekly_digest_html(self, markdown_content: str, week_stats: Dict) -> str:
        """Create HTML version of weekly digest email with rich formatting."""
        import re

        # Parse sections from markdown for better formatting
        stale_count = week_stats.get('stale_count', 0)
        velocity = week_stats.get('velocity', {})
        domains = week_stats.get('url_domains', {})
        lists = week_stats.get('list_breakdown', {})
        recommendations = week_stats.get('recommendations', [])
        deletable = week_stats.get('deletable_tasks', {})
        high_priority = week_stats.get('high_priority_tasks', {})

        # Build stale tasks section
        stale_html = ""
        if stale_count > 0:
            stale_tasks = week_stats.get('stale_tasks', [])[:5]
            stale_items = "".join([f"<li><span style='color:#e74c3c;'>[{t['age_days']}d]</span> {escape(t.get('title', '')[:60])}...</li>" for t in stale_tasks])
            stale_html = f"""
            <div class="section alert-section">
                <h3>⚠️ Stale Tasks Alert</h3>
                <p><strong>{stale_count} tasks</strong> are 30+ days old</p>
                <ul style="margin: 10px 0; padding-left: 20px;">{stale_items}</ul>
            </div>
            """

        # Build high priority tasks section
        high_priority_html = ""
        high_priority_count = high_priority.get('high_priority_count', 0)
        if high_priority_count > 0:
            hp_tasks = high_priority.get('high_priority_tasks', [])[:8]
            hp_items = ""
            for t in hp_tasks:
                score_str = f"[{t['priority_score']:.0f}]" if t.get('priority_score', 0) > 0 else "[HIGH]"
                title_text = t.get('title', '')
                truncated_title = title_text[:55] + ('...' if len(title_text) > 55 else '')
                due_str = f" <span style='color:#666;font-size:12px;'>(Due: {escape(str(t.get('due_date', '')))})</span>" if t.get('due_date') else ""
                hp_items += f"<li><span style='color:#e74c3c;font-weight:bold;'>{score_str}</span> {escape(truncated_title)}{due_str}</li>"
            high_priority_html = f"""
            <div class="section" style="background-color:#fff5f5; border:1px solid #fed7d7;">
                <h3>🔥 High Priority Tasks</h3>
                <p><strong>{high_priority_count} tasks</strong> require immediate attention</p>
                <ul style="margin: 10px 0; padding-left: 20px;">{hp_items}</ul>
            </div>
            """

        # Build deletable tasks section
        deletable_html = ""
        deletable_count = deletable.get('deletable_count', 0)
        if deletable_count > 0:
            del_tasks = deletable.get('deletable_tasks', [])[:8]
            del_items = ""
            for t in del_tasks:
                title_text = t.get('title', '')
                truncated_title = title_text[:50] + ('...' if len(title_text) > 50 else '')
                reason_text = escape(t.get('reason', ''))
                del_items += f"<li>{escape(truncated_title)} <span style='color:#666;font-size:12px;font-style:italic;'>— {reason_text}</span></li>"
            past_due = deletable.get('past_due_count', 0)
            very_old = deletable.get('very_old_count', 0)
            expired = deletable.get('expired_event_count', 0)
            deletable_html = f"""
            <div class="section" style="background-color:#f0fff4; border:1px solid #c6f6d5;">
                <h3>🗑️ Tasks Safe to Delete</h3>
                <p><strong>{deletable_count} tasks</strong> may be safe to remove:</p>
                <p style="font-size:13px;color:#666;">Past due: {past_due} | Very old: {very_old} | Expired events: {expired}</p>
                <ul style="margin: 10px 0; padding-left: 20px;">{del_items}</ul>
            </div>
            """

        # Build domains section
        domains_html = ""
        top_domains = domains.get('top_domains', [])[:6]
        if top_domains:
            domain_rows = "".join([f"<tr><td>{d['domain']}</td><td style='text-align:right;'><strong>{d['count']}</strong></td></tr>" for d in top_domains])
            domains_html = f"""
            <div class="section">
                <h3>🔗 Research Sources</h3>
                <p><strong>{domains.get('total_urls', 0)}</strong> URLs from <strong>{domains.get('unique_domains', 0)}</strong> domains</p>
                <table style="width:100%; border-collapse:collapse; margin:10px 0;">
                    <tr style="background:#f8f9fa;"><th style="text-align:left; padding:8px;">Domain</th><th style="text-align:right; padding:8px;">Tasks</th></tr>
                    {domain_rows}
                </table>
            </div>
            """

        # Build lists section
        lists_html = ""
        top_lists = lists.get('top_lists', [])[:5]
        if top_lists:
            list_rows = "".join([f"<tr><td>{l['list']}</td><td style='text-align:right;'><strong>{l['count']}</strong></td></tr>" for l in top_lists])
            lists_html = f"""
            <div class="section">
                <h3>📋 Tasks by List</h3>
                <table style="width:100%; border-collapse:collapse; margin:10px 0;">
                    <tr style="background:#f8f9fa;"><th style="text-align:left; padding:8px;">List</th><th style="text-align:right; padding:8px;">Count</th></tr>
                    {list_rows}
                </table>
            </div>
            """

        # Build recommendations section
        recs_html = ""
        if recommendations:
            rec_items = ""
            for rec in recommendations[:3]:
                priority_color = {"high": "#e74c3c", "medium": "#f39c12", "low": "#3498db"}.get(rec.get('priority', ''), '#777')
                rec_items += f"""
                <div style="background:#fff; border-left:4px solid {priority_color}; padding:12px; margin:10px 0; border-radius:4px;">
                    <strong>{rec['action']}</strong>
                    <p style="margin:5px 0 0; font-size:13px; color:#666;">{rec['details']}</p>
                </div>
                """
            recs_html = f"""
            <div class="section">
                <h3>💡 Action Recommendations</h3>
                {rec_items}
            </div>
            """

        # Velocity section
        velocity_html = ""
        if velocity.get('trend_direction') and velocity.get('trend_direction') != 'unknown':
            trend_icon = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}.get(velocity.get('trend_direction', ''), '')
            days_clear = f"<br><span style='font-size:12px;'>Est. {velocity['days_to_clear']} days to clear</span>" if velocity.get('days_to_clear') else ""
            velocity_html = f"""
            <div class="stat-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
                <div class="stat-label">Velocity {trend_icon}</div>
                <div class="stat-number">{velocity.get('avg_daily_change', 0):+.1f}</div>
                <div class="stat-label">tasks/day{days_clear}</div>
            </div>
            """

        # Convert markdown to HTML for the full report section
        rendered_markdown = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'nl2br']
        )

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f0f2f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a2e;
            border-bottom: 3px solid #4361ee;
            padding-bottom: 15px;
            margin-bottom: 5px;
        }}
        h2 {{
            color: #1a1a2e;
            margin-top: 30px;
            font-size: 18px;
        }}
        h3 {{
            color: #4361ee;
            margin: 0 0 10px 0;
            font-size: 16px;
        }}
        .subtitle {{
            color: #777;
            margin-bottom: 25px;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            margin: 8px 0;
        }}
        .stat-label {{
            font-size: 12px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .section {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .alert-section {{
            background-color: #fff5f5;
            border: 1px solid #fed7d7;
        }}
        table {{
            font-size: 14px;
        }}
        table td, table th {{
            padding: 8px;
            border-bottom: 1px solid #eee;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #777;
            font-size: 13px;
        }}
        .report-content h1 {{
            font-size: 20px;
            color: #1a1a2e;
            margin: 20px 0 10px 0;
            border-bottom: 2px solid #4361ee;
            padding-bottom: 8px;
        }}
        .report-content h2 {{
            font-size: 17px;
            color: #4361ee;
            margin: 18px 0 8px 0;
        }}
        .report-content h3 {{
            font-size: 15px;
            color: #555;
            margin: 15px 0 6px 0;
        }}
        .report-content p {{
            margin: 8px 0;
        }}
        .report-content ul, .report-content ol {{
            margin: 10px 0;
            padding-left: 25px;
        }}
        .report-content li {{
            margin: 5px 0;
        }}
        .report-content strong {{
            color: #333;
        }}
        .report-content code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 13px;
        }}
        .report-content pre {{
            background-color: #f4f4f4;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        .report-content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        .report-content table th {{
            background-color: #f8f9fa;
            text-align: left;
            font-weight: 600;
        }}
        .report-content table td, .report-content table th {{
            padding: 10px;
            border: 1px solid #e0e0e0;
        }}
        .report-content hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Weekly Task Analytics</h1>
        <p class="subtitle">{week_stats.get('week_start', 'Week')} to {week_stats.get('week_end', 'Today')}</p>

        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Total Tasks</div>
                <div class="stat-number">{week_stats.get('total_tasks', 0)}</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="stat-label">Net Change</div>
                <div class="stat-number">{week_stats.get('net_change', 0):+d}</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="stat-label">Avg Priority</div>
                <div class="stat-number">{week_stats.get('avg_priority', 0):.0f}</div>
            </div>
            {velocity_html}
        </div>

        {stale_html}
        {high_priority_html}
        {deletable_html}
        {domains_html}
        {lists_html}
        {recs_html}

        <div class="section">
            <h3>📈 Full Report</h3>
            <details>
                <summary style="cursor:pointer; color:#4361ee; font-weight:500;">Click to expand detailed report</summary>
                <div class="report-content" style="margin-top: 15px; line-height: 1.6; background: #fff; padding: 20px; border-radius: 8px; font-size: 14px;">
                    {rendered_markdown}
                </div>
            </details>
        </div>

        <div class="footer">
            <p>Generated by <strong>To Do AI Task Manager</strong></p>
            <p style="font-size: 11px; color: #aaa;">Weekly Analytics Report</p>
        </div>
    </div>
</body>
</html>
"""
        return html
