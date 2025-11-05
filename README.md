# Microsoft To Do AI Assistant

An intelligent task management tool that connects Microsoft To Do with AI to automatically analyze, prioritize, and organize your tasks.

## What It Does

- Fetches tasks from Microsoft To Do via Graph API
- Analyzes task content and extracts URLs for additional context
- Uses AI (Claude, GPT-4, or Gemini) to evaluate priority and suggest actions
- Generates daily email briefs with actionable insights
- Updates task priorities back to Microsoft To Do
- Runs automatically on a schedule

## Quick Start

### Prerequisites

- Python 3.8+
- Microsoft account with To Do
- Azure app registration for Graph API access
- API key from Anthropic, OpenAI, or Google

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
- **Multi-AI Support**: Works with Anthropic Claude, OpenAI GPT-4, or Google Gemini
- **Email Summaries**: HTML-formatted daily briefs with insights and recommendations
- **URL Analysis**: Extracts and analyzes web content linked in tasks
- **Automation Ready**: Compatible with Windows Task Scheduler or cron

## Configuration

Key `.env` options:

- `AI_PROVIDER` - Which AI service to use (anthropic/openai/google)
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

1. Go to [Azure Portal](https://portal.azure.com)
2. Register new application
3. Set account type to "Personal Microsoft accounts only"
4. Enable "Allow public client flows" in Authentication
5. Add Microsoft Graph delegated permission: `Tasks.ReadWrite`
6. Copy Client ID to `.env`

## AI Provider Setup

**Anthropic Claude**
- Get key: https://console.anthropic.com/
- Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

**OpenAI GPT**
- Get key: https://platform.openai.com/api-keys
- Add to `.env`: `OPENAI_API_KEY=sk-...`

**Google Gemini**
- Get key: https://makersuite.google.com/app/apikey
- Add to `.env`: `GOOGLE_API_KEY=...`

## Customization

**Priority Weights**: Edit `src/rules/priority_ranker.py`
**Email Template**: Edit `src/writers/email_sender.py`
**AI Prompts**: Edit `src/llm/ai_analyzer.py`

## License

MIT License - see [LICENSE](LICENSE)
