"""Web-based chat interface for Microsoft To Do tasks."""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from anthropic import Anthropic
from src.auth.graph_auth import GraphAuthenticator
from src.graph.todo_client import ToDoClient
from src.config import Config

# Global state
tasks = []
conversation_history = []
client = None
system_prompt = ""


def sanitize_text(text):
    """Remove problematic Unicode characters."""
    if not text:
        return text
    replacements = {
        '\u2011': '-', '\u2013': '-', '\u2014': '-',
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2026': '...', '\u2192': '->', '\u2022': '*',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def load_tasks():
    """Load all tasks from Microsoft To Do."""
    global tasks, system_prompt
    print("Loading tasks from Microsoft To Do...")
    auth = GraphAuthenticator()
    token = auth.get_access_token()
    todo_client = ToDoClient(token)

    raw_tasks = todo_client.get_all_tasks()
    tasks = [todo_client.parse_task_metadata(t) for t in raw_tasks]
    print(f"Loaded {len(tasks)} tasks.")

    # Build context
    lines = []
    for i, task in enumerate(tasks, 1):
        title = sanitize_text(task.get("title", "Untitled"))
        list_name = sanitize_text(task.get("list_name", "Unknown"))
        due_date = task.get("due_date", "")
        importance = task.get("importance", "normal")
        urls = task.get("urls", [])

        task_str = f"{i}. [{list_name}] {title}"
        if due_date:
            task_str += f" (Due: {due_date})"
        if importance == "high":
            task_str += " [HIGH PRIORITY]"
        if urls:
            task_str += f" | URLs: {', '.join(urls[:2])}"
        lines.append(task_str)

    task_context = "\n".join(lines)

    system_prompt = f"""You are a helpful assistant with access to the user's Microsoft To Do task list.
You can help them find tasks, summarize their workload, identify patterns, and answer questions.

Here is the user's complete task list ({len(tasks)} tasks):

{task_context}

When answering:
- Be concise and helpful
- Reference specific task numbers when relevant
- If asked about topics, search through task titles and URLs
- You can suggest tasks to prioritize, delete, or group together
"""
    return len(tasks)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>To Do Task Chat</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 800px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 90vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { opacity: 0.8; font-size: 14px; }
        .task-count {
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
            font-size: 13px;
        }
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
        }
        .message.user { align-items: flex-end; }
        .message.assistant { align-items: flex-start; }
        .message-content {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 16px;
            line-height: 1.5;
            white-space: pre-wrap;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.assistant .message-content {
            background: white;
            color: #333;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        #userInput {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        #userInput:focus { border-color: #667eea; }
        #sendBtn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        #sendBtn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        #sendBtn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .typing {
            display: flex;
            gap: 5px;
            padding: 15px;
        }
        .typing span {
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        .typing span:nth-child(1) { animation-delay: -0.32s; }
        .typing span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        .suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 10px 20px;
            background: #f8f9fa;
        }
        .suggestion {
            padding: 8px 16px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .suggestion:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Task Chat</h1>
            <p>Ask questions about your Microsoft To Do tasks</p>
            <div class="task-count" id="taskCount">Loading tasks...</div>
        </div>
        <div class="suggestions">
            <span class="suggestion" onclick="askQuestion('What are my high priority tasks?')">High priority tasks</span>
            <span class="suggestion" onclick="askQuestion('Do I have any tasks about AI?')">AI-related tasks</span>
            <span class="suggestion" onclick="askQuestion('What are my oldest tasks?')">Oldest tasks</span>
            <span class="suggestion" onclick="askQuestion('Show tasks with job applications')">Job applications</span>
            <span class="suggestion" onclick="askQuestion('What should I focus on today?')">Today\\'s focus</span>
        </div>
        <div class="chat-area" id="chatArea">
            <div class="message assistant">
                <div class="message-content">Hi! I have access to your Microsoft To Do tasks. Ask me anything - like finding tasks on specific topics, identifying priorities, or suggesting what to work on.</div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Ask about your tasks..." onkeypress="if(event.key==='Enter')sendMessage()">
            <button id="sendBtn" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        // Load task count on page load
        fetch('/status')
            .then(r => r.json())
            .then(data => {
                document.getElementById('taskCount').textContent = data.task_count + ' tasks loaded';
            });

        function askQuestion(q) {
            document.getElementById('userInput').value = q;
            sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            const chatArea = document.getElementById('chatArea');
            const sendBtn = document.getElementById('sendBtn');

            // Add user message
            chatArea.innerHTML += `<div class="message user"><div class="message-content">${escapeHtml(message)}</div></div>`;
            input.value = '';
            sendBtn.disabled = true;

            // Add typing indicator
            const typingId = 'typing-' + Date.now();
            chatArea.innerHTML += `<div class="message assistant" id="${typingId}"><div class="typing"><span></span><span></span><span></span></div></div>`;
            chatArea.scrollTop = chatArea.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                const data = await response.json();

                // Remove typing indicator and add response
                document.getElementById(typingId).remove();
                chatArea.innerHTML += `<div class="message assistant"><div class="message-content">${escapeHtml(data.response)}</div></div>`;
            } catch (error) {
                document.getElementById(typingId).remove();
                chatArea.innerHTML += `<div class="message assistant"><div class="message-content">Error: ${error.message}</div></div>`;
            }

            sendBtn.disabled = false;
            chatArea.scrollTop = chatArea.scrollHeight;
            input.focus();
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""


class ChatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'task_count': len(tasks)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global conversation_history
        if self.path == '/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            user_message = data.get('message', '')

            # Add to history
            conversation_history.append({"role": "user", "content": user_message})

            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=conversation_history
                )
                assistant_message = response.content[0].text
                conversation_history.append({"role": "assistant", "content": assistant_message})

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'response': assistant_message}).encode())
            except Exception as e:
                conversation_history.pop()  # Remove failed message
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress default logging


def main():
    global client

    print("=" * 50)
    print("TO DO TASK CHAT - Web Interface")
    print("=" * 50)

    # Initialize Anthropic client
    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    # Load tasks
    task_count = load_tasks()

    # Start server
    port = 8080
    server = HTTPServer(('localhost', port), ChatHandler)
    print(f"\nServer running at: http://localhost:{port}")
    print("Open this URL in your browser to chat with your tasks.")
    print("Press Ctrl+C to stop.\n")

    # Open browser automatically
    import webbrowser
    webbrowser.open(f'http://localhost:{port}')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
