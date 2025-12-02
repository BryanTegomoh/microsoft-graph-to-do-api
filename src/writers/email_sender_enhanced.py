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
            stale_items = ""
            for t in stale_tasks:
                title = escape(t.get('title', '')[:55])
                if len(t.get('title', '')) > 55:
                    title += '...'
                stale_items += f"<li><span class='badge badge-warning'>{t['age_days']}d old</span> {title}</li>"
            stale_html = f"""
            <div class="section alert-section">
                <h3>Stale Tasks Alert</h3>
                <p><strong>{stale_count} tasks</strong> are 30+ days old and may need attention</p>
                <ul>{stale_items}</ul>
            </div>
            """

        # Build high priority tasks section
        high_priority_html = ""
        high_priority_count = high_priority.get('high_priority_count', 0)
        if high_priority_count > 0:
            hp_tasks = high_priority.get('high_priority_tasks', [])[:8]
            hp_items = ""
            for t in hp_tasks:
                score_str = f"{t['priority_score']:.0f}" if t.get('priority_score', 0) > 0 else "HIGH"
                title_text = t.get('title', '')
                truncated_title = escape(title_text[:50] + ('...' if len(title_text) > 50 else ''))
                due_str = f" <span style='color:#6b7280;font-size:12px;'>Due: {t.get('due_date', '')}</span>" if t.get('due_date') else ""
                hp_items += f"<li><span class='badge badge-danger'>{score_str}</span> {truncated_title}{due_str}</li>"
            high_priority_html = f"""
            <div class="section priority-section">
                <h3>High Priority Tasks</h3>
                <p><strong>{high_priority_count} tasks</strong> require immediate attention</p>
                <ul>{hp_items}</ul>
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
                truncated_title = escape(title_text[:45] + ('...' if len(title_text) > 45 else ''))
                reason_text = escape(t.get('reason', ''))
                del_items += f"<li>{truncated_title} <span style='color:#6b7280;font-size:12px;font-style:italic;'>- {reason_text}</span></li>"
            past_due = deletable.get('past_due_count', 0)
            very_old = deletable.get('very_old_count', 0)
            expired = deletable.get('expired_event_count', 0)
            deletable_html = f"""
            <div class="section cleanup-section">
                <h3>Tasks Safe to Delete</h3>
                <p><strong>{deletable_count} tasks</strong> may be safe to remove</p>
                <p style="font-size:13px;color:#4b5563;margin-bottom:12px;">
                    <span class="badge badge-danger">{past_due} past due</span>
                    <span class="badge badge-warning">{very_old} very old</span>
                    <span class="badge badge-success">{expired} expired</span>
                </p>
                <ul>{del_items}</ul>
            </div>
            """

        # Build domains section
        domains_html = ""
        top_domains = domains.get('top_domains', [])[:6]
        if top_domains:
            domain_rows = ""
            for d in top_domains:
                domain_rows += f"<tr><td>{escape(d['domain'])}</td><td style='text-align:right;font-weight:600;color:#065f46;'>{d['count']}</td></tr>"
            domains_html = f"""
            <div class="section table-section">
                <h3>Research Sources</h3>
                <p><strong>{domains.get('total_urls', 0)}</strong> URLs from <strong>{domains.get('unique_domains', 0)}</strong> unique domains</p>
                <table>
                    <tr><th>Domain</th><th style="text-align:right;">Tasks</th></tr>
                    {domain_rows}
                </table>
            </div>
            """

        # Build lists section
        lists_html = ""
        top_lists = lists.get('top_lists', [])[:5]
        if top_lists:
            list_rows = ""
            for l in top_lists:
                list_rows += f"<tr><td>{escape(l['list'])}</td><td style='text-align:right;font-weight:600;color:#065f46;'>{l['count']}</td></tr>"
            lists_html = f"""
            <div class="section table-section">
                <h3>Tasks by List</h3>
                <table>
                    <tr><th>List</th><th style="text-align:right;">Count</th></tr>
                    {list_rows}
                </table>
            </div>
            """

        # Build recommendations section
        recs_html = ""
        if recommendations:
            rec_items = ""
            for rec in recommendations[:3]:
                priority_class = {"high": "high", "medium": "medium"}.get(rec.get('priority', ''), '')
                rec_items += f"""
                <div class="rec-card {priority_class}">
                    <strong>{escape(rec['action'])}</strong>
                    <p>{escape(rec['details'])}</p>
                </div>
                """
            recs_html = f"""
            <div class="section">
                <h3>Action Recommendations</h3>
                {rec_items}
            </div>
            """

        # Velocity section
        velocity_html = ""
        if velocity.get('trend_direction') and velocity.get('trend_direction') != 'unknown':
            trend_icon = {"increasing": "+", "decreasing": "-", "stable": "="}.get(velocity.get('trend_direction', ''), '')
            days_clear = f"<br><span style='font-size:10px;opacity:0.8;'>{velocity['days_to_clear']}d to clear</span>" if velocity.get('days_to_clear') else ""
            velocity_html = f"""
            <div class="stat-card velocity">
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

        # Get current date for header
        from datetime import datetime
        report_date = datetime.now().strftime("%B %d, %Y")

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            max-width: 680px;
            margin: 0 auto;
            padding: 0;
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        }}
        .email-wrapper {{
            padding: 30px 20px;
        }}
        .container {{
            background-color: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(5, 150, 105, 0.15);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #065f46 0%, #047857 50%, #059669 100%);
            color: white;
            padding: 35px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0 0 8px 0;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .header .subtitle {{
            color: rgba(255,255,255,0.9);
            font-size: 15px;
            margin: 0;
        }}
        .header .date-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            margin-top: 15px;
            backdrop-filter: blur(10px);
        }}
        .content {{
            padding: 30px;
        }}
        .stat-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 25px;
        }}
        .stat-card {{
            flex: 1;
            min-width: 140px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 20px 16px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }}
        .stat-card.secondary {{
            background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
            box-shadow: 0 4px 15px rgba(20, 184, 166, 0.3);
        }}
        .stat-card.tertiary {{
            background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%);
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
        }}
        .stat-card.velocity {{
            background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 100%);
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: 700;
            margin: 5px 0;
            line-height: 1;
        }}
        .stat-label {{
            font-size: 11px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }}
        .section {{
            background-color: #f9fafb;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 16px;
            border: 1px solid #e5e7eb;
        }}
        .section h3 {{
            color: #065f46;
            margin: 0 0 12px 0;
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section p {{
            margin: 0 0 10px 0;
            color: #4b5563;
            font-size: 14px;
        }}
        .section ul {{
            margin: 12px 0 0 0;
            padding-left: 0;
            list-style: none;
        }}
        .section ul li {{
            padding: 10px 12px;
            background: white;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 14px;
            border-left: 3px solid #10b981;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .alert-section {{
            background: linear-gradient(135deg, #fef3c7 0%, #fef9c3 100%);
            border: 1px solid #fcd34d;
        }}
        .alert-section h3 {{
            color: #92400e;
        }}
        .alert-section ul li {{
            border-left-color: #f59e0b;
            background: #fffbeb;
        }}
        .priority-section {{
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
            border: 1px solid #fca5a5;
        }}
        .priority-section h3 {{
            color: #991b1b;
        }}
        .priority-section ul li {{
            border-left-color: #ef4444;
            background: #fff5f5;
        }}
        .cleanup-section {{
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            border: 1px solid #6ee7b7;
        }}
        .cleanup-section h3 {{
            color: #065f46;
        }}
        .cleanup-section ul li {{
            border-left-color: #10b981;
            background: #ecfdf5;
        }}
        .table-section table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 12px;
            font-size: 14px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .table-section th {{
            background: #065f46;
            color: white;
            text-align: left;
            padding: 12px 15px;
            font-weight: 500;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .table-section td {{
            padding: 12px 15px;
            background: white;
            border-bottom: 1px solid #e5e7eb;
        }}
        .table-section tr:last-child td {{
            border-bottom: none;
        }}
        .table-section tr:hover td {{
            background: #f0fdf4;
        }}
        .rec-card {{
            background: white;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 10px;
            border-left: 4px solid #10b981;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .rec-card.high {{
            border-left-color: #ef4444;
            background: linear-gradient(90deg, #fff5f5 0%, white 100%);
        }}
        .rec-card.medium {{
            border-left-color: #f59e0b;
            background: linear-gradient(90deg, #fffbeb 0%, white 100%);
        }}
        .rec-card strong {{
            color: #1f2937;
            font-size: 14px;
        }}
        .rec-card p {{
            margin: 6px 0 0 0;
            font-size: 13px;
            color: #6b7280;
        }}
        .expand-section {{
            background: #f0fdf4;
            border: 1px solid #a7f3d0;
            border-radius: 12px;
            margin-top: 20px;
        }}
        .expand-section summary {{
            cursor: pointer;
            padding: 16px 20px;
            font-weight: 600;
            color: #065f46;
            font-size: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .expand-section summary:hover {{
            background: #ecfdf5;
            border-radius: 12px;
        }}
        .report-content {{
            padding: 20px;
            background: white;
            border-top: 1px solid #d1fae5;
            line-height: 1.7;
            font-size: 14px;
        }}
        .report-content h1 {{
            font-size: 18px;
            color: #065f46;
            margin: 25px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #10b981;
        }}
        .report-content h2 {{
            font-size: 16px;
            color: #047857;
            margin: 20px 0 10px 0;
        }}
        .report-content h3 {{
            font-size: 14px;
            color: #059669;
            margin: 16px 0 8px 0;
        }}
        .report-content p {{
            margin: 10px 0;
            color: #374151;
        }}
        .report-content ul, .report-content ol {{
            margin: 12px 0;
            padding-left: 24px;
        }}
        .report-content li {{
            margin: 6px 0;
            color: #4b5563;
        }}
        .report-content strong {{
            color: #1f2937;
        }}
        .report-content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 13px;
        }}
        .report-content th {{
            background: #ecfdf5;
            color: #065f46;
            text-align: left;
            padding: 10px 12px;
            font-weight: 600;
            border: 1px solid #d1fae5;
        }}
        .report-content td {{
            padding: 10px 12px;
            border: 1px solid #e5e7eb;
        }}
        .footer {{
            background: #f9fafb;
            padding: 25px 30px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }}
        .footer p {{
            margin: 0;
            color: #6b7280;
            font-size: 13px;
        }}
        .footer .brand {{
            color: #065f46;
            font-weight: 600;
        }}
        .footer .tagline {{
            margin-top: 8px;
            font-size: 11px;
            color: #9ca3af;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-danger {{
            background: #fee2e2;
            color: #dc2626;
        }}
        .badge-warning {{
            background: #fef3c7;
            color: #d97706;
        }}
        .badge-success {{
            background: #d1fae5;
            color: #059669;
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="container">
            <div class="header">
                <h1>Weekly Task Analytics</h1>
                <p class="subtitle">Your productivity insights at a glance</p>
                <div class="date-badge">{week_stats.get('week_start', 'Week')} - {week_stats.get('week_end', 'Today')}</div>
            </div>

            <div class="content">
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Tasks</div>
                        <div class="stat-number">{week_stats.get('total_tasks', 0)}</div>
                    </div>
                    <div class="stat-card secondary">
                        <div class="stat-label">Net Change</div>
                        <div class="stat-number">{week_stats.get('net_change', 0):+d}</div>
                    </div>
                    <div class="stat-card tertiary">
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

                <details class="expand-section">
                    <summary>View Full Detailed Report</summary>
                    <div class="report-content">
                        {rendered_markdown}
                    </div>
                </details>
            </div>

            <div class="footer">
                <p>Generated by <span class="brand">To Do AI Task Manager</span></p>
                <p class="tagline">Powered by AI - Automated Weekly Analytics</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
        return html
