import os
import logging
import random
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# ================= LOAD ENV VARIABLES =================
load_dotenv()

ACCESS_TOKEN = os.getenv("TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

# ================= APP SETUP =================
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# In-memory user state
user_states = {}

# ================= INTENTS & DATA =================
INTENTS = {
    "greeting": ["hello", "hi", "hey"],
    "bye": ["bye", "goodbye"],
    "help": ["help", "commands", "menu"],
    "python": ["python", "coding", "programming"],
}

GREETINGS = [
    "Hello 👋 How can I help you?",
    "Hi there 😊 What can I do for you?",
    "Hey! Need any help?"
]

ISLAMIC_INFO = {
    "namaz": "🕌 Namaz is an obligatory prayer performed 5 times daily.",
    "roza": "🌙 Roza (fasting) is mandatory during Ramadan.",
    "zakat": "💰 Zakat is a compulsory charity in Islam."
}

PYTHON_FAQ = {
    "what is python": "🐍 Python is a popular programming language used for web, AI, and automation.",
    "what is flask": "⚙️ Flask is a lightweight Python web framework used to build APIs."
}

# ================= WEBHOOK VERIFICATION =================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info("Webhook verified successfully")
        return challenge, 200

    return "Verification failed", 403


# ================= RECEIVE WHATSAPP MESSAGES =================
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
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
    for intent, keywords in INTENTS.items():
        for word in keywords:
            if word in text:
                return intent
    return None


def handle_message(sender, text):
    state = user_states.get(sender)
    intent = detect_intent(text)

    # Greeting
    if intent == "greeting":
        return random.choice(GREETINGS)

    # Islamic greeting
    if "assalamoalaikum" in text or "a o a" in text:
        return "Wa Alaikum Assalam 😊 How can I help you?"

    # Menu / Help
    if intent == "help" or text.startswith("/help"):
        return (
            "📋 *Main Menu*\n"
            "1️⃣ Python Help\n"
            "2️⃣ Islamic Info\n"
            "3️⃣ About Bot\n\n"
            "Reply with 1, 2, or 3"
        )

    # Menu selection
    if text == "1":
        return "🐍 Ask me about Python or Flask."
    if text == "2":
        user_states[sender] = "ISLAMIC"
        return "🕌 Ask about Namaz, Roza, or Zakat."
    if text == "3":
        return "🤖 I am a WhatsApp chatbot built using Flask & WhatsApp Cloud API."

    # Islamic state
    if state == "ISLAMIC":
        for topic, reply in ISLAMIC_INFO.items():
            if topic in text:
                return reply
        return "You can ask about Namaz, Roza, or Zakat."

    # Python FAQs
    for question, answer in PYTHON_FAQ.items():
        if question in text:
            return answer

    # Religion question
    if "religion" in text:
        user_states[sender] = "ASK_ISLAMIC"
        return "I'm Muslim, Alhamdulillah ☪️ Would you like Islamic information? (yes/no)"

    if state == "ASK_ISLAMIC":
        user_states[sender] = None
        if text in ["yes", "y"]:
            return "Great! Type *menu* to explore Islamic topics."
        return "No problem 😊 Let me know if you need help."

    # Bye
    if intent == "bye":
        return "Goodbye 👋 Have a great day!"

    # Fallback
    return (
        "🤖 I didn't understand that.\n\n"
        "Try:\n"
        "• hello\n"
        "• menu\n"
        "• /help"
    )


# ================= SEND MESSAGE =================
def send_message(to, text):
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
        response = requests.post(
            WHATSAPP_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logging.info(f"Message sent to {to}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message: {e}")


# ================= RUN APP =================
if __name__ == "__main__":
    app.run(port=5000, debug=True)
