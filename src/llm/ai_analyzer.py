"""AI-powered task analysis using multiple LLM providers."""

import logging
import json
from typing import Dict, Optional, List
from abc import ABC, abstractmethod

from src.config import Config

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def analyze_task(self, task_data: Dict, content: Optional[str] = None) -> Dict:
        """Analyze a task and return insights."""
        pass


class AnthropicProvider(AIProvider):
    """Anthropic Claude AI provider."""

    def __init__(self):
        """Initialize Anthropic provider."""
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            self.model = Config.ANTHROPIC_MODEL
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def analyze_task(self, task_data: Dict, content: Optional[str] = None) -> Dict:
        """Analyze a task using Claude."""
        prompt = self._build_analysis_prompt(task_data, content)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            return self._get_fallback_analysis()

    def _build_analysis_prompt(self, task_data: Dict, content: Optional[str]) -> str:
        """Build the analysis prompt."""
        prompt = f"""Analyze this task and provide structured insights in JSON format.

Task Title: {task_data.get('title', 'No title')}
Task Description: {task_data.get('body', 'No description')}
Due Date: {task_data.get('due_date', 'Not set')}
Current Importance: {task_data.get('importance', 'normal')}
Status: {task_data.get('status', 'notStarted')}
"""

        if content:
            # Truncate content to avoid token limits
            truncated_content = content[:3000] + "..." if len(content) > 3000 else content
            prompt += f"\n\nLinked Content:\n{truncated_content}\n"

        prompt += """
Please analyze this task and provide the following in valid JSON format:

{
  "summary": "One-sentence summary of what this task is about",
  "priority_score": <number 0-100, where 100 is highest priority>,
  "priority_reasoning": "Brief explanation of the priority score",
  "estimated_time_minutes": <estimated time to complete in minutes>,
  "tags": ["topic1", "topic2", "topic3"],
  "category": "one of: urgent, important, routine, research, reading, planning, other",
  "urgency_level": "one of: critical, high, medium, low",
  "suggested_action": "Next action to take (imperative form)",
  "key_insights": ["insight1", "insight2", "insight3"],
  "why_it_matters": "One sentence explaining why this task matters"
}

Respond ONLY with the JSON object, no additional text.
"""
        return prompt

    def _parse_response(self, response_text: str) -> Dict:
        """Parse the AI response."""
        try:
            # Try to extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in response")
                return self._get_fallback_analysis()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return self._get_fallback_analysis()

    def _get_fallback_analysis(self, task_data: Dict = None) -> Dict:
        """Return fallback analysis when AI fails."""
        title = task_data.get('title', 'Unknown task') if task_data else 'Unknown task'
        return {
            "summary": f"Review and complete: {title[:80]}",
            "priority_score": 50,
            "priority_reasoning": "AI analysis unavailable - default priority assigned",
            "estimated_time_minutes": 30,
            "tags": ["untagged"],
            "category": "other",
            "urgency_level": "medium",
            "suggested_action": f"Review this task and determine next steps",
            "key_insights": ["Task requires review", "No additional analysis available"],
            "why_it_matters": "This task needs attention"
        }


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self):
        """Initialize OpenAI provider."""
        try:
            import openai
            self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            self.model = Config.OPENAI_MODEL
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def analyze_task(self, task_data: Dict, content: Optional[str] = None) -> Dict:
        """Analyze a task using GPT."""
        prompt = self._build_analysis_prompt(task_data, content)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a task analysis expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1024
            )

            response_text = response.choices[0].message.content
            return self._parse_response(response_text)

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return self._get_fallback_analysis()

    def _build_analysis_prompt(self, task_data: Dict, content: Optional[str]) -> str:
        """Build the analysis prompt (same as Anthropic)."""
        return AnthropicProvider._build_analysis_prompt(self, task_data, content)

    def _parse_response(self, response_text: str) -> Dict:
        """Parse the AI response (same as Anthropic)."""
        return AnthropicProvider._parse_response(self, response_text)

    def _get_fallback_analysis(self) -> Dict:
        """Return fallback analysis (same as Anthropic)."""
        return AnthropicProvider._get_fallback_analysis(self)


class GoogleProvider(AIProvider):
    """Google Gemini provider."""

    def __init__(self):
        """Initialize Google provider."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel(Config.GOOGLE_MODEL)
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")

    def analyze_task(self, task_data: Dict, content: Optional[str] = None) -> Dict:
        """Analyze a task using Gemini."""
        prompt = self._build_analysis_prompt(task_data, content)

        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)

        except Exception as e:
            logger.error(f"Error calling Google API: {e}")
            return self._get_fallback_analysis()

    def _build_analysis_prompt(self, task_data: Dict, content: Optional[str]) -> str:
        """Build the analysis prompt (same as Anthropic)."""
        return AnthropicProvider._build_analysis_prompt(self, task_data, content)

    def _parse_response(self, response_text: str) -> Dict:
        """Parse the AI response (same as Anthropic)."""
        return AnthropicProvider._parse_response(self, response_text)

    def _get_fallback_analysis(self) -> Dict:
        """Return fallback analysis (same as Anthropic)."""
        return AnthropicProvider._get_fallback_analysis(self)


class TaskAnalyzer:
    """Main task analyzer that uses configured AI provider."""

    def __init__(self):
        """Initialize the task analyzer."""
        provider_name = Config.AI_PROVIDER.lower()

        if provider_name == "anthropic":
            self.provider = AnthropicProvider()
        elif provider_name == "openai":
            self.provider = OpenAIProvider()
        elif provider_name == "google":
            self.provider = GoogleProvider()
        else:
            raise ValueError(f"Unsupported AI provider: {provider_name}")

        logger.info(f"Initialized TaskAnalyzer with {provider_name} provider")

    def analyze_task(self, task_data: Dict, content: Optional[str] = None) -> Dict:
        """
        Analyze a task and return AI-generated insights.

        Args:
            task_data: Task metadata dictionary.
            content: Optional web content associated with the task.

        Returns:
            Analysis results dictionary.
        """
        logger.info(f"Analyzing task: {task_data.get('title', 'Unknown')}")
        return self.provider.analyze_task(task_data, content)

    def batch_analyze_tasks(self, tasks_with_content: List[tuple]) -> List[Dict]:
        """
        Analyze multiple tasks.

        Args:
            tasks_with_content: List of (task_data, content) tuples.

        Returns:
            List of analysis results.
        """
        results = []
        for task_data, content in tasks_with_content:
            analysis = self.analyze_task(task_data, content)
            results.append({
                "task": task_data,
                "analysis": analysis
            })
        return results
