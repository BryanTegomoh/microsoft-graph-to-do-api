# Microsoft To Do AI Task Manager

An intelligent task management system that automatically analyzes, ranks, and prioritizes your Microsoft To Do tasks using AI. Get personalized daily email briefs with smart insights, URL content analysis, and actionable recommendations powered by Anthropic Claude, OpenAI GPT, or Google Gemini.

## Features

- **Microsoft Graph Integration**: Seamlessly sync with Microsoft To Do (supports personal Microsoft accounts)
- **Multi-AI Provider Support**: Choose between Anthropic Claude, OpenAI GPT, or Google Gemini
- **Email Briefs**: Receive beautiful HTML email summaries twice daily with:
  - Personalized "Why it matters to you" insights
  - Clickable URLs extracted from tasks
  - Priority scores and actionable next steps
  - Smart categorization (Urgent, Important, Routine, etc.)
- **URL Content Extraction**: Automatically fetch and analyze web content from task URLs
- **Smart Prioritization**: AI-powered ranking based on multiple factors:
  - AI-suggested priority (40%)
  - Deadline urgency (25%)
  - Task recency (15%)
  - User-set importance (10%)
  - Task category (10%)
- **Task Updates**: Optionally write priority updates back to Microsoft To Do
- **Zero-Touch Automation**: Set it up once, get daily briefs automatically via Windows Task Scheduler
- **Flexible Architecture**: Easy to extend and customize

## Architecture

```
microsoft-graph-to-do-api/
├── src/
│   ├── auth/           # Microsoft Graph authentication
│   ├── graph/          # To Do API client
│   ├── fetch/          # Web content extraction
│   ├── llm/            # AI provider integrations
│   ├── rules/          # Priority ranking logic
│   ├── writers/        # Output generators
│   └── utils/          # Utilities and logging
├── main.py             # Main orchestration script
├── requirements.txt    # Python dependencies
└── .env                # Configuration (you create this)
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Microsoft account with To Do access
- Azure app registration (for Microsoft Graph API)
- API key for your chosen AI provider

### 2. Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Click "New registration"
3. Name: "To Do AI Manager" (or your choice)
4. Supported account types: "Personal Microsoft accounts only" (for personal To Do accounts)
5. Click "Register"
6. Note your **Application (client) ID**
7. Go to "Authentication":
   - Enable "Allow public client flows" (required for device code flow)
8. Go to "API permissions":
   - Add permission → Microsoft Graph → Delegated permissions
   - Add: `Tasks.ReadWrite` (to read and update tasks)
   - Note: No admin consent needed for personal accounts

### 3. Installation

```bash
# Clone the repository
git clone https://github.com/BryanTegomoh/microsoft-graph-to-do-api.git
cd microsoft-graph-to-do-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
# Microsoft Graph API
CLIENT_ID=your_azure_app_client_id
TENANT_ID=consumers  # Use "consumers" for personal Microsoft accounts

# Microsoft Graph Scopes
GRAPH_SCOPES=Tasks.ReadWrite

# AI Provider (choose one: anthropic, openai, google)
AI_PROVIDER=anthropic

# AI API Keys (uncomment the one you use)
ANTHROPIC_API_KEY=your_anthropic_api_key
# OPENAI_API_KEY=your_openai_api_key
# GOOGLE_API_KEY=your_google_api_key

# Email Settings (for daily briefs)
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password  # Create at https://myaccount.google.com/apppasswords
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

# Application Settings
LOG_LEVEL=INFO
ENABLE_TASK_UPDATES=true
SEND_EMAIL_BRIEF=true
GENERATE_MARKDOWN_BRIEF=true
```

### 5. Test Configuration

```bash
# Test your configuration
python test_config.py

# Test email sending
python test_email.py
```

### 6. First Run

```bash
python main.py
```

On first run, you'll be prompted to authenticate with Microsoft using device code flow:
1. A URL and code will be displayed in the terminal
2. Open the URL in your browser
3. Enter the code
4. Sign in with your Microsoft account
5. Your authentication token will be cached for 90 days

## Usage Examples

### Basic Run

```bash
python main.py
```

This will:
1. Fetch all incomplete tasks from Microsoft To Do
2. Extract URLs and fetch web content
3. Analyze tasks with AI (using your chosen provider)
4. Generate a daily brief in `output/daily_brief_YYYY-MM-DD.md`
5. Send an HTML email brief to your inbox (if enabled)
6. Update task importance in Microsoft To Do (if enabled)

### Automated Twice-Daily Briefs (Windows)

Run the setup script to create scheduled tasks for 8 AM and 2 PM:

```bash
setup_automation_twice_daily.bat
```

This creates two Windows Task Scheduler tasks that run automatically every day.

### Custom Prioritization Weights

Edit [src/rules/priority_ranker.py](src/rules/priority_ranker.py#L16) to adjust ranking weights:

```python
self.weights = {
    "ai_priority": 0.40,      # AI-suggested priority
    "deadline_urgency": 0.25,  # Based on due date
    "recency": 0.15,           # How recently created
    "importance": 0.10,        # User-set importance
    "category": 0.10,          # Task category weight
}
```

## Output

### Email Brief
You'll receive an HTML email with:
- Task summary and priority breakdown
- Top 3 tasks to focus on today
- Each task includes:
  - Priority score (0-100)
  - AI-generated summary
  - Personalized "Why it matters to you" insight
  - Clickable URLs (if available)
  - Suggested next action
  - Estimated time to complete

### Markdown Brief
Daily briefs are also saved in `output/daily_brief_YYYY-MM-DD.md` with complete task analysis.

## Customization

### Adjust Schedule

Edit the batch files or Task Scheduler times:
- Morning brief: Default 8:00 AM
- Afternoon brief: Default 2:00 PM

### Email Format

Customize the HTML template in [src/writers/email_sender.py](src/writers/email_sender.py)

### Priority Weights

Modify ranking weights in [src/rules/priority_ranker.py](src/rules/priority_ranker.py)

### AI Prompts

Edit the analysis prompt in [src/llm/ai_analyzer.py](src/llm/ai_analyzer.py) to change how tasks are analyzed

## AI Provider Setup

### Anthropic Claude

1. Get API key: https://console.anthropic.com/
2. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
3. Set `AI_PROVIDER=anthropic`

### OpenAI GPT

1. Get API key: https://platform.openai.com/api-keys
2. Add to `.env`: `OPENAI_API_KEY=sk-...`
3. Set `AI_PROVIDER=openai`

### Google Gemini

1. Get API key: https://makersuite.google.com/app/apikey
2. Add to `.env`: `GOOGLE_API_KEY=...`
3. Set `AI_PROVIDER=google`

## Troubleshooting

### Authentication Issues

**Problem**: "AADSTS9002331: Application is configured for use by Microsoft Account users only"

**Solution**: Set `TENANT_ID=consumers` in `.env` and enable "Allow public client flows" in Azure Portal

**Problem**: "Failed to obtain access token"

**Solutions**:
- Verify your `CLIENT_ID` in `.env`
- Ensure `TENANT_ID=consumers` for personal accounts
- Delete `token_cache.json` and re-authenticate
- Check that "Allow public client flows" is enabled in Azure

### Email Issues

**Problem**: Email fails to send

**Solutions**:
- For Gmail: Use an App Password, not your regular password
  - Create at: https://myaccount.google.com/apppasswords
- Enable 2-Factor Authentication on your Google account
- Verify `EMAIL_FROM`, `EMAIL_TO`, and `EMAIL_PASSWORD` in `.env`
- Test with: `python test_email.py`

### AI Provider Errors

**Problem**: AI analysis fails

**Solutions**:
- Verify API key is correct in `.env`
- Check API quota/billing
- Review logs in `task_manager.log`
- System falls back to default priority scoring if AI fails

## Project Structure

```
microsoft-graph-to-do-api/
├── src/
│   ├── auth/              # Microsoft Graph authentication (device code flow)
│   ├── graph/             # To Do API client
│   ├── fetch/             # Web content extraction
│   ├── llm/               # AI provider integrations (Anthropic, OpenAI, Google)
│   ├── rules/             # Priority ranking logic
│   ├── writers/           # Email sender, brief generator, task updater
│   └── utils/             # Logging configuration
├── main.py                # Main orchestration script
├── test_config.py         # Configuration validator
├── test_email.py          # Email testing utility
├── requirements.txt       # Python dependencies
├── run_daily.bat          # Windows run script
├── setup_automation_twice_daily.bat  # Task Scheduler setup
└── .env                   # Your configuration (create from .env.example)
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Roadmap

- [x] Email notifications with HTML briefs
- [x] Personalized AI insights
- [x] Twice-daily automation
- [ ] Web UI dashboard
- [ ] Calendar integration
- [ ] Slack notifications
- [ ] Mobile app companion

## Support

- Issues: https://github.com/BryanTegomoh/microsoft-graph-to-do-api/issues
- Documentation: See this README
- Microsoft Graph API: https://learn.microsoft.com/en-us/graph/api/resources/todo-overview

---

Built with Python, Microsoft Graph API, and AI.
