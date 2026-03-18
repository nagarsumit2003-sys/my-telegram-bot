import requests
import time
import os

GROQ_KEY = os.environ.get("GROQ_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
BOT_NAME = "Buddy"

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
conversation = {}

def get_updates(offset=None):
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    res = requests.get(f"{BASE_URL}/getUpdates", params=params)
    return res.json()

def send_message(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

def reset_conversation(chat_id):
    conversation[chat_id] = [
        {
            "role": "system",
            "content": f"Tera naam {BOT_NAME} hai. Tu ek smart aur friendly AI assistant hai. Hindi aur English dono mein baat karta hai. Chhote aur clear jawab deta hai."
        }
    ]

def ask_groq(chat_id, user_message):
    if chat_id not in conversation:
        reset_conversation(chat_id)
    conversation[chat_id].append({"role": "user", "content": user_message})
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}"},
        json={"model": "llama-3.1-8b-instant", "messages": conversation[chat_id]}
    )
    reply = res.json()['choices'][0]['message']['content']
    conversation[chat_id].append({"role": "assistant", "content": reply})
    return reply

def handle_message(chat_id, text):
    if text == "/start":
        reset_conversation(chat_id)
        send_message(chat_id, f"Namaste! Main {BOT_NAME} hoon 🤖\n\n/help - Commands\n/clear - Reset")
    elif text == "/help":
        send_message(chat_id, f"Main {BOT_NAME} hoon:\n\n✅ Kisi bhi sawaal ka jawab\n✅ Hindi aur English\n✅ Conversation yaad rakhta hoon\n\n/clear — Nayi baat shuru karo")
    elif text == "/clear":
        reset_conversation(chat_id)
        send_message(chat_id, "✅ Conversation clear ho gayi!")
    elif text:
        reply = ask_groq(chat_id, text)
        send_message(chat_id, reply)

print("Purane messages clear ho rahe hain...")
old = get_updates()
if old.get("result"):
    last_id = old["result"][-1]["update_id"]
    get_updates(offset=last_id + 1)

print(f"{BOT_NAME} chal raha hai 🚀")
offset = None

while True:
    updates = get_updates(offset)
    for update in updates.get("result", []):
        offset = update["update_id"] + 1
        msg = update.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "")
        if chat_id and text:
            handle_message(chat_id, text)
    time.sleep(1)        pdf_text = read_pdf(document["file_id"])
        if pdf_text:
            reply = ask_groq(chat_id, f"Yeh PDF hai:\n\n{pdf_text}\n\nIska summary do aur main points batao.")
            send_reply(chat_id, reply)
        else:
            send_message(chat_id, "PDF padh nahi paya.")

    elif text == "/start":
        reset_conversation(chat_id)
        send_message(chat_id, f"Namaste! Main {BOT_NAME} hoon 🤖\n\nMujhe bhejo:\n💬 Message\n🖼️ Image\n🎤 Voice message\n📄 PDF\n\n/help — Commands dekhne ke liye")

    elif text == "/help":
        send_message(chat_id, f"Main {BOT_NAME} hoon:\n\n✅ Text chat\n✅ Image samajhna 🖼️\n✅ Voice message 🎤\n✅ PDF padhna 📄\n✅ Reminder ⏰\n\n/voice on — Voice reply on\n/voice off — Voice reply off\n/remind 10 meeting — 10 min mein reminder\n/clear — Conversation reset")

    elif text == "/clear":
        reset_conversation(chat_id)
        send_message(chat_id, "✅ Conversation clear ho gayi!")

    elif text == "/voice on":
        voice_mode[chat_id] = True
        send_message(chat_id, "🔊 Voice mode ON — ab main bolke reply karunga!")

    elif text == "/voice off":
        voice_mode[chat_id] = False
        send_message(chat_id, "🔇 Voice mode OFF — ab text mein reply karunga.")

    elif text and text.startswith("/remind"):
        parts = text.split(" ", 2)
        if len(parts) >= 3:
            try:
                minutes = int(parts[1])
                reminder_text = parts[2]
                set_reminder(chat_id, minutes, reminder_text)
                send_message(chat_id, f"⏰ Reminder set! {minutes} minute mein yaad dilaaunga: {reminder_text}")
            except:
                send_message(chat_id, "Format: /remind 10 meeting karna hai")
        else:
            send_message(chat_id, "Format: /remind 10 meeting karna hai")

    elif text:
        reply = ask_groq(chat_id, text)
        send_reply(chat_id, reply)

print("Purane messages clear ho rahe hain...")
old = get_updates()
if old.get("result"):
    last_id = old["result"][-1]["update_id"]
    get_updates(offset=last_id + 1)

print(f"{BOT_NAME} chal raha hai 🚀")
offset = None

while True:
    updates = get_updates(offset)
    for update in updates.get("result", []):
        offset = update["update_id"] + 1
        msg = update.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        if chat_id:
            handle_message(chat_id, update)
    time.sleep(1)
