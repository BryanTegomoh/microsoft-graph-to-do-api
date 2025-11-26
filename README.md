# Microsoft To Do AI Assistant

I built this because my Microsoft To Do was becoming a black hole. Every time I found an interesting article about AI in healthcare, a research paper, or just something I wanted to read later, I'd throw it in To Do. Problem is, everthing just piled up and I never knew what to actually focus on.

This tool connects Microsoft To Do with AI (Claude, GPT-4, Gemini, or Grok) to automatically analyze everything, figure out what matters, and send me a daily brief of what to actually pay attention to. Been running it daily since Nov 5, 2025.

## What It Actually Does

1. Pulls all your tasks from Microsoft To Do
2. If tasks have URLs, fetches and reads the content (first URL only to avoid rate limits)
3. Sends everything to AI to analyze priority and suggest actions
4. Ranks tasks using weighted scoring: 40% AI analysis, 25% deadline urgency, 15% recency, 10% importance flags, 10% category
5. Generates a daily markdown brief organized into "Focus Today" (priority ≥80), "This Week" (≥60), and "Later"
6. Optionally emails you the brief and updates importance flags back in Microsoft To Do

Currently processing ~58 tasks across 3 lists. Turns out most of mine end up in the "Later" bucket - this is more of a research reading list than an urgent task manager for me.

## Real Example Output

From my actual tasks:

```
🎯 Focus Today

1. Review healthcare AI startup applications (Priority: 87/100)
   Summary: 3 potential co-founder candidates interested in medical AI
   Why it matters: Time-sensitive - they're evaluating other opportunities
   Next action: Schedule intro calls this week

📅 This Week

2. Read CDC autism-vaccine study (Priority: 72/100)
   Summary: New research on vaccine safety and developmental outcomes
   Why it matters: Relevant for current healthcare research project
   Next action: Review methodology and data sources

📌 Later (42 more tasks)

Research backlog, articles to read, things to explore when I have time...
```

The output is pretty emoji-heavy but whatever, it works.

## Quick Start

### What You Need

- Python 3.8+
- Microsoft account with To Do
- Azure app registration (free, takes 5 minutes)
- API key from Anthropic, OpenAI, Google, or xAI

### Install

```bash
git clone <your-repo-url>
cd microsoft-graph-to-do-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

Copy `.env.example` to `.env` and add your credentials:

```env
# Microsoft Graph API (see Azure Setup below)
CLIENT_ID=your_client_id
TENANT_ID=consumers  # Important: use "consumers" for personal Microsoft accounts

# Pick one AI provider
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Email yourself the daily brief
SEND_EMAIL_BRIEF=false  # Set to true if you want emails
EMAIL_FROM=your@email.com
EMAIL_TO=your@email.com
EMAIL_PASSWORD=your_app_password

# Optional: Update task priorities in To Do
ENABLE_TASK_UPDATES=false  # Conservative default - won't mess with your tasks
```

### Run

```bash
python main.py
```

First run requires device code authentication (one-time, token cached for 90 days). Just follow the prompts.

## Azure Setup (The Authentication Struggle)

This took me about 16 minutes to figure out the first time, so here's what actually works:

1. Go to [Azure Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Click "New registration"
3. Name it whatever you want
4. **Important**: Set account type to "Personal Microsoft accounts only"
5. Skip the redirect URI
6. After creation, go to Authentication → Enable "Allow public client flows"
7. Go to API permissions → Add permission → Microsoft Graph → Delegated → `Tasks.ReadWrite`
8. Copy the Client ID to your `.env`

**Gotcha**: Don't use `offline_access` scope - it's reserved and will error out. Just use `Tasks.ReadWrite` and the device code flow handles the rest.

**Another gotcha**: Use `TENANT_ID=consumers`, not `common` or your actual tenant ID. Personal Microsoft accounts need the `/consumers` endpoint.

## AI Provider Setup

Supports four providers because I kept switching between them:

**Anthropic Claude** (what I use most)
- Get key: https://console.anthropic.com/
- Add to `.env`: `AI_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=sk-ant-...`

**OpenAI GPT-4**
- Get key: https://platform.openai.com/api-keys
- Add to `.env`: `AI_PROVIDER=openai` and `OPENAI_API_KEY=sk-...`

**Google Gemini**
- Get key: https://makersuite.google.com/app/apikey
- Add to `.env`: `AI_PROVIDER=google` and `GOOGLE_API_KEY=...`

**xAI Grok** (added Nov 5, 2025)
- Get key: https://console.x.ai/
- Add to `.env`: `AI_PROVIDER=xai` and `XAI_API_KEY=xai-...`

Switching providers is just changing `AI_PROVIDER` in your .env.

## Features & Design Decisions

**Smart Prioritization**: 5-factor weighted algorithm. AI gets 40% weight (the most), deadlines get 25%, recency 15%, importance flags 10%, category 10%. This is opinionated but works for me.

**URL Analysis**: Fetches web content from links in your tasks. Only grabs the first URL per task to avoid rate limits. Content gets truncated to 3000 characters before sending to AI (token limits).

**Conservative Defaults**: `ENABLE_TASK_UPDATES` and `SEND_EMAIL_BRIEF` are both `false` by default. This won't mess with your To Do or spam you unless you explicitly enable features.

**Caching**: 24-hour cache for fetched URLs (`CACHE_ENABLED=true`). Won't hammer the same article URL repeatedly.

**Graceful Failures**: If AI fails, it just assigns default priority 50 and keeps going.

**Email Briefs**: HTML emails with priority badges. Spent way too much time on the styling tbh.

## Automation

This is built to run daily. I use Windows Task Scheduler:

```bash
# See setup_scheduler.bat for the full setup
# Basically: Run main.py daily at 6 AM, generates brief + optional email
```

Works fine with cron on Linux/Mac too, just schedule `python main.py`.

## Limitations

- Only fetches first URL per task (didn't want to get rate limited)
- Auth token expires after 90 days, just re-auth when it happens
- Mostly tested on Windows

## My Use Case

I'm researching the intersection of AI and healthcare, so my To Do is full of:
- Research papers on medical AI
- Healthcare datasets and benchmarks
- Career transition articles (tech → healthcare)
- Co-founder search notes
- CDC studies, clinical trials, etc.

Helps me triage whats worth reading vs what can wait. If you use To Do for actual urgent tasks this might not be as useful - mine is basically a reading list.

## Project Structure

```
src/
├── auth/       # Microsoft Graph device code authentication
├── graph/      # To Do API client (fetch tasks, update priorities)
├── fetch/      # URL content extraction (BeautifulSoup + requests)
├── llm/        # AI analysis (multi-provider abstraction)
├── rules/      # Priority ranking algorithm (5-factor weighted)
├── writers/    # Email and markdown report generation
└── utils/      # Logging utilities
```

## Config Options

Check `.env.example` for the full list. Main ones are `AI_PROVIDER`, `ENABLE_TASK_UPDATES`, `SEND_EMAIL_BRIEF`.

## License

MIT
