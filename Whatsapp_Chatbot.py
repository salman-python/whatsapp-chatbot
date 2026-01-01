import os
import logging
import random
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv


# Load API tokens and configuration from .env file
load_dotenv()

ACCESS_TOKEN = os.getenv("TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# WhatsApp API endpoint for sending messages
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

# ================= INITIALIZE FLASK APP =================
app = Flask(__name__)

# Configure logging to show timestamp, log level, and message
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Keep track of user states in memory
user_states = {}


# Keywords to detect user intent
INTENTS = {
    "greeting": ["hello", "hi", "hey"],
    "bye": ["bye", "goodbye"],
    "help": ["help", "commands", "menu"],
    "python": ["python", "coding", "programming"],
}

# Responses for greetings
GREETINGS = [
    "Hello! How can I help you?",
    "Hi there! What can I do for you?",
    "Hey! Need any help?"
]

# Islamic related information
ISLAMIC_INFO = {
    "namaz": "Namaz is an obligatory prayer performed five times daily.",
    "roza": "Roza (fasting) is observed during the month of Ramadan.",
    "zakat": "Zakat is a form of obligatory charity in Islam."
}

# Basic Python and Flask FAQs
PYTHON_FAQ = {
    "what is python": "Python is a popular programming language used for web development, AI, and automation.",
    "what is flask": "Flask is a lightweight Python web framework commonly used to build APIs."
}


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Verify WhatsApp webhook with the provided token."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info("Webhook verified successfully")
        return challenge, 200

    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    """Receive messages from WhatsApp and respond."""
    data = request.get_json()

    if not data or "entry" not in data:
        return jsonify({"status": "ignored"}), 200

    for entry in data["entry"]:
        for change in entry.get("changes", []):
            messages = change.get("value", {}).get("messages")
            if not messages:
                continue

            message = messages[0]
            sender = message.get("from")
            text = message.get("text", {}).get("body", "").lower()

            reply = handle_message(sender, text)
            send_message(sender, reply)

    return jsonify({"status": "ok"}), 200

# ================= CHATBOT LOGIC =================
def detect_intent(text):
    """Detect user intent based on predefined keywords."""
    for intent, keywords in INTENTS.items():
        for word in keywords:
            if word in text:
                return intent
    return None

def handle_message(sender, text):
    """Decide how to respond based on user input and state."""
    state = user_states.get(sender)
    intent = detect_intent(text)

    # Respond to greetings
    if intent == "greeting":
        return random.choice(GREETINGS)

    # Respond to Islamic greeting
    if "assalamoalaikum" in text or "a o a" in text:
        return "Wa Alaikum Assalam. How can I assist you?"

    # Show main menu/help
    if intent == "help" or text.startswith("/help"):
        return (
            "Main Menu:\n"
            "1. Python Help\n"
            "2. Islamic Info\n"
            "3. About Bot\n\n"
            "Reply with 1, 2, or 3"
        )

    # Handle menu selection
    if text == "1":
        return "You can ask me questions about Python or Flask."
    if text == "2":
        user_states[sender] = "ISLAMIC"
        return "You can ask about Namaz, Roza, or Zakat."
    if text == "3":
        return "I am a WhatsApp chatbot built using Flask and the WhatsApp Cloud API."

    # Respond to Islamic questions
    if state == "ISLAMIC":
        for topic, reply in ISLAMIC_INFO.items():
            if topic in text:
                return reply
        return "You can ask about Namaz, Roza, or Zakat."

    # Respond to Python FAQs
    for question, answer in PYTHON_FAQ.items():
        if question in text:
            return answer

    # Handle religion-related queries
    if "religion" in text:
        user_states[sender] = "ASK_ISLAMIC"
        return "I am Muslim. Would you like to know more about Islam? (yes/no)"

    if state == "ASK_ISLAMIC":
        user_states[sender] = None
        if text in ["yes", "y"]:
            return "Great! Type 'menu' to explore Islamic topics."
        return "No problem. Let me know if you need help with anything else."

    # Respond to goodbye
    if intent == "bye":
        return "Goodbye! Have a great day."

    # Default fallback response
    return (
        "I didn't understand that. You can try:\n"
        "- hello\n"
        "- menu\n"
        "- /help"
    )

# ================= SEND MESSAGE TO WHATSAPP =================
def send_message(to, text):
    """Send a message to the user via WhatsApp Cloud API."""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Message sent to {to}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message: {e}")

# ================= RUN THE APP =================
if __name__ == "__main__":
    app.run(port=5000, debug=True)
