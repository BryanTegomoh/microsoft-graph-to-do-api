# Microsoft To Do AI Assistant

I built this because my To Do list was out of control.

Every article, every research paper, every "read later" link, it all went into Microsoft To Do. And then just sat there. Hundreds of tasks, no idea what actually mattered.

So I built something to fix it. This connects To Do with AI (Claude, GPT-4, Gemini, or Grok) to analyze everything and tell me what to focus on. **Runs automatically every morning and emails me a prioritized brief.**

Been using it daily, and wanted to make it open source for busy professionals. 

## How It Works

1. Pulls all tasks from Microsoft To Do
2. Reads any URLs in your tasks (articles, papers, etc.)
3. AI analyzes everything and ranks by priority
4. Sends you a daily brief: what to focus on today, this week, and later
5. Cleans up duplicate URLs automatically
6. Weekly reports track your patterns and themes

That's it. No more staring at an overwhelming task list wondering where to start.

## What I Use It For

I'm researching AI in healthcare, so my To Do is full of:
- Research papers and clinical studies
- Healthcare AI articles and benchmarks
- Career stuff 
- Random interesting things I want to read later

This helps me figure out what's actually worth my time vs what can wait. If you use To Do for actual urgent work tasks, your mileage may vary, mine is basically a curated reading list.

## Quick Start

```bash
git clone https://github.com/yourusername/microsoft-graph-to-do-api
cd microsoft-graph-to-do-api
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python main.py
```

You'll need:
- Python 3.8+
- Microsoft account with To Do
- Azure app registration (free, 5 min setup)
- API key from Anthropic, OpenAI, Google, or xAI

See [SETUP.md](SETUP.md) for detailed instructions.

## Example Output

```
Focus Today

1. [87] Review healthcare AI startup applications
   Time-sensitive opportunity - schedule calls this week

2. [82] CDC data modernization report
   Directly relevant to current research

This Week

3. [71] Stanford LLM prompting techniques paper
   Good reference for prompt engineering

Later (40+ tasks)

Research backlog, articles to explore when I have time...
```

## Automation

I run this daily at 6 AM via Windows Task Scheduler. It generates the brief and emails it to me when I'm back from my morning workout. 

Works with cron on Linux/Mac too - just schedule `python main.py`.

## Project Structure

```
src/
├── auth/       # Microsoft Graph authentication
├── graph/      # To Do API client
├── fetch/      # URL content extraction
├── llm/        # AI analysis (multi-provider)
├── rules/      # Priority ranking algorithm
├── writers/    # Email and report generation
└── analytics/  # Weekly trends analysis
```

## License

MIT
