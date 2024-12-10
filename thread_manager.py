import json
import time
import uuid
import requests

# Load master context from a file
def load_master_context():
    with open("master_context.json", "r") as file:
        return json.load(file)

# Save master context to a file (if updates are needed)
def save_master_context(context):
    with open("master_context.json", "w") as file:
        json.dump(context, file)
class CodeInterpreterSessionManager:
    def __init__(self):
        self.session_info = {}
        self.api_url = "https://api.openai.com/v1/chat/completions"  # Replace with actual URL
        self.api_key = "YOUR_OPENAI_API_KEY"  # Replace with your API key

    # Check if an active session exists
    def is_session_active(self, user_id):
        session = self.session_info.get(user_id)
        if session and (time.time() - session['start_time'] < 3600):
            return True
        return False

    # Start a new session if none is active
    def get_thread_id(self, user_id):
        if not self.is_session_active(user_id):
            self.session_info[user_id] = {
                "thread_id": str(uuid.uuid4()),
                "start_time": time.time()
            }
        return self.session_info[user_id]['thread_id']

    # Send a request to the Assistant API
    def assistant_api_request(self, user_id, user_message, context):
        thread_id = self.get_thread_id(user_id)
        payload = {
            "thread_id": thread_id,
            "messages": [
                {"role": "system", "content": str(context)},  # Injected context from master
                {"role": "user", "content": user_message}
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.api_url, headers=headers, json=payload)
        return response.json()

# Usage
manager = CodeInterpreterSessionManager()
user_id = "user123"

# Load master context and send a message with minimal new threads
master_context = load_master_context()
response = manager.assistant_api_request(user_id, "Can you analyze the recent sales data?", master_context)

print(response['choices'][0]['message']['content'])
