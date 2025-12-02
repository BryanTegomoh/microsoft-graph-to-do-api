"""Web-based chat interface for Microsoft To Do tasks with auto-shutdown."""

import json
import re
import threading
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from anthropic import Anthropic
from src.auth.graph_auth import GraphAuthenticator
from src.graph.todo_client import ToDoClient
from src.config import Config

# Global state
tasks = []
conversation_history = []
client = None
system_prompt = ""
last_activity = time.time()
IDLE_TIMEOUT = 60  # Shutdown after 60 seconds of no activity
server_instance = None


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


def fetch_url_content(url, max_chars=3000):
    """Fetch and extract text content from a URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Simple HTML to text extraction
        text = response.text
        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Decode HTML entities
        import html
        text = html.unescape(text)

        return text[:max_chars] + ("..." if len(text) > max_chars else "")
    except Exception as e:
        return f"Error fetching URL: {str(e)}"


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

    # Build context with full URL information
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
        # Include ALL URLs, not just first 2
        if urls:
            task_str += f"\n   URLs: " + "\n   ".join(urls)
        lines.append(task_str)

    task_context = "\n".join(lines)

    system_prompt = f"""You are a helpful assistant with access to the user's Microsoft To Do task list.
You can help them find tasks, summarize their workload, identify patterns, and answer questions.

Here is the user's complete task list ({len(tasks)} tasks):

{task_context}

CRITICAL INSTRUCTIONS FOR RESPONSES:
1. When listing tasks that have URLs, ALWAYS include the full URL on its own line so users can click it
2. Format URLs like this:
   Task #18: 3 quick applications: fellowship, grant, and RFP
   URL: https://example.com/job-posting

3. Be concise but ALWAYS show URLs when they exist for relevant tasks
4. Reference specific task numbers when relevant
5. You can suggest tasks to prioritize, delete, or group together

When the user asks you to fetch, read, or summarize content from a URL, respond with:
[FETCH_URL: <the url>]
The system will fetch the content and you'll receive it in the next message.
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
            background: linear-gradient(135deg, #0d9488 0%, #14b8a6 50%, #2dd4bf 100%);
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
            background: linear-gradient(135deg, #065f46 0%, #047857 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { opacity: 0.9; font-size: 14px; }
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
            background: #f0fdf4;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
        }
        .message.user { align-items: flex-end; }
        .message.assistant { align-items: flex-start; }
        .message-content {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 16px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .message-content a {
            color: #059669;
            text-decoration: underline;
            word-break: break-all;
        }
        .message-content a:hover {
            color: #047857;
            text-decoration: underline;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.user .message-content a {
            color: #d1fae5;
            text-decoration: underline;
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
            border-top: 1px solid #d1fae5;
            display: flex;
            gap: 10px;
        }
        #userInput {
            flex: 1;
            padding: 15px;
            border: 2px solid #a7f3d0;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        #userInput:focus { border-color: #10b981; }
        #sendBtn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        #sendBtn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(16, 185, 129, 0.4);
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
            background: #10b981;
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
            background: #ecfdf5;
        }
        .suggestion {
            padding: 8px 16px;
            background: white;
            border: 1px solid #a7f3d0;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .suggestion:hover {
            background: #10b981;
            color: white;
            border-color: #10b981;
        }
        .status-bar {
            background: #d1fae5;
            padding: 5px 20px;
            font-size: 11px;
            color: #065f46;
            text-align: center;
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
            <span class="suggestion" onclick="askQuestion('What are my high priority tasks? Show URLs')">High priority tasks</span>
            <span class="suggestion" onclick="askQuestion('Show AI-related tasks with their URLs')">AI-related tasks</span>
            <span class="suggestion" onclick="askQuestion('What are my oldest tasks?')">Oldest tasks</span>
            <span class="suggestion" onclick="askQuestion('Show job application tasks with URLs')">Job applications</span>
            <span class="suggestion" onclick="askQuestion('What should I focus on today?')">Today's focus</span>
        </div>
        <div class="chat-area" id="chatArea">
            <div class="message assistant">
                <div class="message-content">Hi! I have access to your Microsoft To Do tasks. Ask me anything - like finding tasks on specific topics, identifying priorities, or suggesting what to work on.

I'll show you clickable URLs for any relevant tasks. You can also ask me to fetch and summarize content from any link!</div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Ask about your tasks..." onkeypress="if(event.key==='Enter')sendMessage()">
            <button id="sendBtn" onclick="sendMessage()">Send</button>
        </div>
        <div class="status-bar">
            Server auto-closes when you close this tab. Just close the browser when done.
        </div>
    </div>

    <script>
        // Heartbeat to keep server alive while tab is open
        setInterval(() => {
            fetch('/heartbeat').catch(() => {});
        }, 30000);

        // Notify server when page is closing
        window.addEventListener('beforeunload', () => {
            navigator.sendBeacon('/shutdown');
        });

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

        function linkifyText(text) {
            // Convert URLs to clickable links - improved regex
            const urlRegex = /(https?:\/\/[^\s<>"')\]]+)/g;
            return text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            const chatArea = document.getElementById('chatArea');
            const sendBtn = document.getElementById('sendBtn');

            // Add user message (with linkified URLs)
            const userDiv = document.createElement('div');
            userDiv.className = 'message user';
            userDiv.innerHTML = '<div class="message-content">' + linkifyText(escapeHtml(message)) + '</div>';
            chatArea.appendChild(userDiv);

            input.value = '';
            sendBtn.disabled = true;

            // Add typing indicator
            const typingId = 'typing-' + Date.now();
            chatArea.innerHTML += '<div class="message assistant" id="' + typingId + '"><div class="typing"><span></span><span></span><span></span></div></div>';
            chatArea.scrollTop = chatArea.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                const data = await response.json();

                // Remove typing indicator
                document.getElementById(typingId).remove();

                // Add response with clickable links
                const assistantDiv = document.createElement('div');
                assistantDiv.className = 'message assistant';
                assistantDiv.innerHTML = '<div class="message-content">' + linkifyText(escapeHtml(data.response)) + '</div>';
                chatArea.appendChild(assistantDiv);
            } catch (error) {
                document.getElementById(typingId).remove();
                chatArea.innerHTML += '<div class="message assistant"><div class="message-content">Error: ' + error.message + '</div></div>';
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
        global last_activity
        last_activity = time.time()

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
        elif self.path == '/heartbeat':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'ok')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global conversation_history, last_activity, server_instance
        last_activity = time.time()

        if self.path == '/shutdown':
            self.send_response(200)
            self.end_headers()
            # Trigger shutdown in background
            threading.Thread(target=self._delayed_shutdown, daemon=True).start()
            return

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
                    max_tokens=2048,
                    system=system_prompt,
                    messages=conversation_history
                )
                assistant_message = response.content[0].text

                # Check if AI wants to fetch a URL
                fetch_match = re.search(r'\[FETCH_URL:\s*(https?://[^\]]+)\]', assistant_message)
                if fetch_match:
                    url_to_fetch = fetch_match.group(1).strip()
                    # Fetch the URL content
                    url_content = fetch_url_content(url_to_fetch)

                    # Add the fetch request to history
                    conversation_history.append({"role": "assistant", "content": assistant_message})

                    # Add URL content as user message
                    conversation_history.append({
                        "role": "user",
                        "content": f"Here is the content from {url_to_fetch}:\n\n{url_content}\n\nPlease summarize or answer questions about this content."
                    })

                    # Get AI's response about the content
                    response2 = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2048,
                        system=system_prompt,
                        messages=conversation_history
                    )
                    assistant_message = response2.content[0].text

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

    def _delayed_shutdown(self):
        """Shutdown server after a brief delay."""
        time.sleep(1)
        if server_instance:
            print("\nBrowser closed. Shutting down server...")
            server_instance.shutdown()

    def log_message(self, format, *args):
        pass  # Suppress default logging


def idle_monitor():
    """Monitor for idle timeout and shutdown if no activity."""
    global last_activity, server_instance
    while True:
        time.sleep(10)
        idle_time = time.time() - last_activity
        if idle_time > IDLE_TIMEOUT:
            print(f"\nNo activity for {IDLE_TIMEOUT}s. Shutting down...")
            if server_instance:
                server_instance.shutdown()
            break


def main():
    global client, server_instance

    print("=" * 50)
    print("TO DO TASK CHAT - Web Interface")
    print("=" * 50)

    # Initialize Anthropic client
    client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    # Load tasks
    task_count = load_tasks()

    # Start idle monitor thread
    monitor_thread = threading.Thread(target=idle_monitor, daemon=True)
    monitor_thread.start()

    # Start server
    port = 8080
    server_instance = HTTPServer(('localhost', port), ChatHandler)
    print(f"\nServer running at: http://localhost:{port}")
    print(f"Auto-shutdown after {IDLE_TIMEOUT}s of inactivity or when browser closes.")
    print("Press Ctrl+C to stop manually.\n")

    # Open browser automatically
    import webbrowser
    webbrowser.open(f'http://localhost:{port}')

    try:
        server_instance.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nServer stopped. Goodbye!")


if __name__ == "__main__":
    main()
