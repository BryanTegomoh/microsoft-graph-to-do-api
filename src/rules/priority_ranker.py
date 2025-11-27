"""Priority ranking system for tasks."""

import logging
from typing import List, Dict
from datetime import datetime, timedelta
from dateutil import parser

logger = logging.getLogger(__name__)


class PriorityRanker:
    """Ranks and prioritizes tasks based on multiple factors."""

    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize the priority ranker.

        Args:
            weights: Custom weights for ranking factors.
        """
        # Default weights (must sum to 1.0)
        self.weights = weights or {
            "ai_priority": 0.40,      # AI-suggested priority
            "deadline_urgency": 0.25,  # Based on due date
            "recency": 0.15,           # How recently created
            "importance": 0.10,        # User-set importance
            "category": 0.10,          # Task category weight
        }

        # Validate weights
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total}, normalizing to 1.0")
            self.weights = {k: v / total for k, v in self.weights.items()}

    def calculate_priority_score(self, task: Dict, analysis: Dict) -> float:
        """
        Calculate overall priority score for a task.

        Args:
            task: Task metadata.
            analysis: AI analysis results.

        Returns:
            Priority score (0-100).
        """
        scores = {
            "ai_priority": self._score_ai_priority(analysis),
            "deadline_urgency": self._score_deadline_urgency(task),
            "recency": self._score_recency(task),
            "importance": self._score_importance(task),
            "category": self._score_category(analysis),
        }

        # Calculate weighted sum
        final_score = sum(
            scores[factor] * weight
            for factor, weight in self.weights.items()
        )

        logger.debug(f"Task '{task.get('title', 'Unknown')}' scores: {scores} -> {final_score:.2f}")
        return round(final_score, 2)

    def _score_ai_priority(self, analysis: Dict) -> float:
        """Score based on AI-suggested priority (0-100)."""
        return analysis.get("priority_score", 50)

    def _score_deadline_urgency(self, task: Dict) -> float:
        """
        Score based on deadline urgency (0-100).

        Logic:
        - Overdue: 100
        - Due today: 90
        - Due this week: 70
        - Due next week: 50
        - Due later: 30
        - No due date: 20
        """
        due_date_str = task.get("due_date")
        if not due_date_str:
            return 20  # No deadline = low urgency

        try:
            due_date = parser.parse(due_date_str)
            now = datetime.now(due_date.tzinfo or None)

            days_until_due = (due_date - now).days

            if days_until_due < 0:
                return 100  # Overdue
            elif days_until_due == 0:
                return 90   # Due today
            elif days_until_due <= 3:
                return 80   # Due in next 3 days
            elif days_until_due <= 7:
                return 70   # Due this week
            elif days_until_due <= 14:
                return 50   # Due next week
            elif days_until_due <= 30:
                return 35   # Due this month
            else:
                return 20   # Due later

        except Exception as e:
            logger.warning(f"Error parsing due date '{due_date_str}': {e}")
            return 20

    def _score_recency(self, task: Dict) -> float:
        """
        Score based on how recently the task was created (0-100).

        Newer tasks get higher scores (might be more relevant).
        """
        created_str = task.get("created_at")
        if not created_str:
            return 50  # Default

        try:
            created = parser.parse(created_str)
            now = datetime.now(created.tzinfo or None)

            days_old = (now - created).days

            if days_old == 0:
                return 100  # Created today
            elif days_old <= 3:
                return 80   # Created in last 3 days
            elif days_old <= 7:
                return 60   # Created this week
            elif days_old <= 30:
                return 40   # Created this month
            else:
                return 20   # Older

        except Exception as e:
            logger.warning(f"Error parsing created date '{created_str}': {e}")
            return 50

    def _score_importance(self, task: Dict) -> float:
        """
        Score based on user-set importance (0-100).

        Microsoft To Do importance levels: low, normal, high
        """
        importance = task.get("importance", "normal").lower()

        importance_map = {
            "high": 100,
            "normal": 50,
            "low": 25,
        }

        return importance_map.get(importance, 50)

    def _score_category(self, analysis: Dict) -> float:
        """
        Score based on task category (0-100).

        Some categories are inherently more urgent than others.
        """
        category = analysis.get("category", "other").lower()
        urgency_level = analysis.get("urgency_level", "medium").lower()

        # Base category scores
        category_scores = {
            "urgent": 95,
            "apply": 85,
            "contact": 80,
            "important": 80,
            "review": 65,
            "planning": 60,
            "research": 55,
            "reading": 40,
            "watch": 35,
            "routine": 30,
            "other": 50,
        }

        # Urgency multipliers
        urgency_multipliers = {
            "critical": 1.2,
            "high": 1.1,
            "medium": 1.0,
            "low": 0.8,
        }

        base_score = category_scores.get(category, 50)
        multiplier = urgency_multipliers.get(urgency_level, 1.0)

        return min(base_score * multiplier, 100)

    def rank_tasks(self, tasks_with_analysis: List[Dict]) -> List[Dict]:
        """
        Rank a list of tasks by priority.

        Args:
            tasks_with_analysis: List of dicts with 'task' and 'analysis' keys.

        Returns:
            Sorted list of tasks with priority scores, highest first.
        """
        logger.info(f"Ranking {len(tasks_with_analysis)} tasks")

        # Calculate scores
        for item in tasks_with_analysis:
            task = item["task"]
            analysis = item["analysis"]
            score = self.calculate_priority_score(task, analysis)
            item["priority_score"] = score

        # Sort by priority score (descending)
        ranked = sorted(
            tasks_with_analysis,
            key=lambda x: x["priority_score"],
            reverse=True
        )

        logger.info("Tasks ranked successfully")
        return ranked

    def categorize_by_timeframe(self, ranked_tasks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize ranked tasks into timeframes.

        Args:
            ranked_tasks: List of ranked tasks with scores.

        Returns:
            Dictionary with categorized tasks: today, this_week, later, waiting.
        """
        categorized = {
            "today": [],
            "this_week": [],
            "later": [],
            "waiting": [],
        }

        for item in ranked_tasks:
            task = item["task"]
            analysis = item["analysis"]
            score = item["priority_score"]

            # High priority or due today
            if score >= 80 or self._is_due_today(task):
                categorized["today"].append(item)
            # Medium-high priority or due this week
            elif score >= 60 or self._is_due_this_week(task):
                categorized["this_week"].append(item)
            # Waiting on something (from tags/category)
            elif "waiting" in analysis.get("tags", []) or "blocked" in analysis.get("tags", []):
                categorized["waiting"].append(item)
            # Everything else
            else:
                categorized["later"].append(item)

        # Log distribution
        for timeframe, items in categorized.items():
            logger.info(f"{timeframe}: {len(items)} tasks")

        return categorized

    def _is_due_today(self, task: Dict) -> bool:
        """Check if task is due today."""
        due_date_str = task.get("due_date")
        if not due_date_str:
            return False

        try:
            due_date = parser.parse(due_date_str)
            now = datetime.now(due_date.tzinfo or None)
            return due_date.date() == now.date()
        except Exception:
            return False

    def _is_due_this_week(self, task: Dict) -> bool:
        """Check if task is due this week."""
        due_date_str = task.get("due_date")
        if not due_date_str:
            return False

        try:
            due_date = parser.parse(due_date_str)
            now = datetime.now(due_date.tzinfo or None)
            days_until = (due_date - now).days
            return 0 <= days_until <= 7
        except Exception:
            return False
