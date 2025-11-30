"""Chat with your Microsoft To Do tasks using AI."""

import os
import sys
from anthropic import Anthropic
from src.auth.graph_auth import GraphAuthenticator
from src.graph.todo_client import ToDoClient
from src.config import Config


def load_tasks():
    """Load all tasks from Microsoft To Do."""
    print("Loading tasks from Microsoft To Do...")
    auth = GraphAuthenticator()
    token = auth.get_access_token()
    client = ToDoClient(token)

    raw_tasks = client.get_all_tasks()
    tasks = [client.parse_task_metadata(t) for t in raw_tasks]
    print(f"Loaded {len(tasks)} tasks.\n")
    return tasks


def sanitize_text(text):
    """Remove problematic Unicode characters for Windows console."""
    if not text:
        return text
    # Replace common problematic characters
    replacements = {
        '\u2011': '-',  # non-breaking hyphen
        '\u2013': '-',  # en dash
        '\u2014': '-',  # em dash
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
        '\u2026': '...',  # ellipsis
        '\u2192': '->',  # arrow
        '\u2022': '*',  # bullet
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Remove any remaining non-ASCII characters that might cause issues
    return text.encode('ascii', 'replace').decode('ascii')


def format_tasks_for_context(tasks):
    """Format tasks into a context string for the AI."""
    lines = []
    for i, task in enumerate(tasks, 1):
        title = sanitize_text(task.get("title", "Untitled"))
        list_name = sanitize_text(task.get("list_name", "Unknown List"))
        due_date = task.get("due_date", "No due date")
        created = task.get("created_at", "")[:10] if task.get("created_at") else "Unknown"
        importance = task.get("importance", "normal")
        urls = task.get("urls", [])
        body = sanitize_text(task.get("body", "")[:200]) if task.get("body") else ""

        task_str = f"{i}. [{list_name}] {title}"
        if due_date and due_date != "No due date":
            task_str += f" (Due: {due_date})"
        if importance == "high":
            task_str += " [HIGH PRIORITY]"
        if urls:
            task_str += f" | URLs: {', '.join(urls[:2])}"
        if body:
            task_str += f" | Notes: {body[:100]}..."

        lines.append(task_str)

    return "\n".join(lines)


def chat_with_tasks(tasks):
    """Interactive chat session with task context."""
    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    # Build context
    task_context = format_tasks_for_context(tasks)

    system_prompt = f"""You are a helpful assistant with access to the user's Microsoft To Do task list.
You can help them find tasks, summarize their workload, identify patterns, and answer questions about their tasks.

Here is the user's complete task list ({len(tasks)} tasks):

{task_context}

When answering:
- Be concise and helpful
- Reference specific task numbers when relevant
- If asked about topics, search through task titles, URLs, and notes
- You can suggest tasks to prioritize, delete, or group together
- If a task has a URL, mention it might have more context there
"""

    conversation_history = []

    print("=" * 60)
    print("TASK CHAT - Ask questions about your To Do list")
    print("=" * 60)
    print("Examples:")
    print("  - 'Do I have any tasks about AI in healthcare?'")
    print("  - 'What are my oldest tasks?'")
    print("  - 'Show me tasks related to job applications'")
    print("  - 'What should I focus on today?'")
    print("  - 'Are there any duplicate tasks?'")
    print("\nType 'quit' or 'exit' to end the session.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_input
        })

        try:
            # Call Claude
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                messages=conversation_history
            )

            assistant_message = response.content[0].text

            # Add assistant response to history
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            # Sanitize output for Windows console
            display_message = sanitize_text(assistant_message)
            print(f"\nAssistant: {display_message}\n")

        except Exception as e:
            print(f"\nError: {e}\n")
            # Remove failed user message from history
            conversation_history.pop()


def main():
    """Main entry point."""
    # Check for API key
    if not Config.ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)

    # Load tasks
    tasks = load_tasks()

    if not tasks:
        print("No tasks found!")
        sys.exit(1)

    # Start chat
    chat_with_tasks(tasks)


if __name__ == "__main__":
    main()
