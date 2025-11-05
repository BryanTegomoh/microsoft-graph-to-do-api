# Microsoft To Do AI Assistant

A personal productivity tool I built to manage information overload. Connects [Microsoft To Do](https://todo.microsoft.com) with AI to automatically analyze articles and tasks I save, prioritize what matters, and send me daily briefings on what to focus on.

## What It Does

- Fetches my tasks from [Microsoft To Do](https://todo.microsoft.com) via [Microsoft Graph API](https://learn.microsoft.com/en-us/graph/api/resources/todo-overview)
- Analyzes task content and extracts URLs for additional context
- Uses AI ([Claude](https://anthropic.com/claude), [GPT-4](https://openai.com/gpt-4), [Gemini](https://deepmind.google/technologies/gemini/), or [Grok](https://x.ai/)) to evaluate priority and suggest actions
- Generates daily email briefs with actionable insights
- Updates task priorities back to Microsoft To Do
- Runs automatically on my schedule
- All processing happens locally - only AI analysis calls external APIs

## Example Output

```
Top Priority Tasks

1. Review Q4 budget report (Priority: 92/100)
   Summary: Budget review requires approval before Friday deadline
   Why it matters: Critical for stakeholder meeting next week
   Next action: Schedule review with finance team

2. Respond to client proposal (Priority: 85/100)
   Summary: Client awaiting feedback on project scope and timeline
   Why it matters: Opportunity to close $50K contract
   Next action: Draft response addressing their three key questions

3. Read AI research paper (Priority: 78/100)
   Summary: New paper on transformer architectures from DeepMind
   Why it matters: Relevant to current project implementation
   Next action: Read and summarize key findings
```

## Quick Start

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Microsoft account](https://account.microsoft.com) with To Do
- [Azure app registration](https://portal.azure.com) for Graph API access
- API key from [Anthropic](https://console.anthropic.com/), [OpenAI](https://platform.openai.com/api-keys), [Google](https://makersuite.google.com/app/apikey), or [xAI](https://console.x.ai/)

### Installation

```bash
git clone <your-repo-url>
cd microsoft-graph-to-do-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`
2. Configure your credentials:

```env
# Microsoft Graph API
CLIENT_ID=your_client_id
TENANT_ID=consumers  # For personal accounts

# AI Provider
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key

# Email (optional)
EMAIL_FROM=your@email.com
EMAIL_TO=your@email.com
EMAIL_PASSWORD=your_app_password
```

### Run

```bash
python main.py
```

First run requires device code authentication (one-time setup, token cached for 90 days).

## Features

- **Smart Prioritization**: 5-factor weighted algorithm combining AI analysis, deadlines, recency, importance, and category
- **Multi-AI Support**: Works with [Anthropic Claude](https://anthropic.com/claude), [OpenAI GPT-4](https://openai.com/gpt-4), [Google Gemini](https://deepmind.google/technologies/gemini/), or [xAI Grok](https://x.ai/)
- **Email Summaries**: HTML-formatted daily briefs with insights and recommendations
- **URL Analysis**: Extracts and analyzes web content linked in tasks
- **Automation Ready**: Compatible with [Windows Task Scheduler](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page) or cron

## Configuration

Key `.env` options:

- `AI_PROVIDER` - Which AI service to use (anthropic/openai/google/xai)
- `ENABLE_TASK_UPDATES` - Update priorities in Microsoft To Do (true/false)
- `SEND_EMAIL_BRIEF` - Email daily summaries (true/false)
- `LOG_LEVEL` - Logging detail (INFO/DEBUG/WARNING)

## Project Structure

```
src/
├── auth/       # Microsoft Graph authentication
├── graph/      # To Do API client
├── fetch/      # URL content extraction
├── llm/        # AI analysis (multi-provider)
├── rules/      # Priority ranking algorithm
├── writers/    # Email and report generation
└── utils/      # Logging utilities
```

## Azure Setup

1. Go to [Azure Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Register new application
3. Set account type to "Personal Microsoft accounts only"
4. Enable "Allow public client flows" in Authentication
5. Add [Microsoft Graph](https://learn.microsoft.com/en-us/graph/api/resources/todo-overview) delegated permission: `Tasks.ReadWrite`
6. Copy Client ID to `.env`

## AI Provider Setup

**[Anthropic Claude](https://anthropic.com/claude)**
- Get key: [console.anthropic.com](https://console.anthropic.com/)
- Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

**[OpenAI GPT](https://openai.com/gpt-4)**
- Get key: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Add to `.env`: `OPENAI_API_KEY=sk-...`

**[Google Gemini](https://deepmind.google/technologies/gemini/)**
- Get key: [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
- Add to `.env`: `GOOGLE_API_KEY=...`

**[xAI Grok](https://x.ai/)**
- Get key: [console.x.ai](https://console.x.ai/)
- Add to `.env`: `XAI_API_KEY=xai-...`

## Customization

**Priority Weights**: Edit `src/rules/priority_ranker.py`
**Email Template**: Edit `src/writers/email_sender.py`
**AI Prompts**: Edit `src/llm/ai_analyzer.py`

## License

MIT License - see [LICENSE](LICENSE)
