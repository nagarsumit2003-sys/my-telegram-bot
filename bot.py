import requests
import time
import os
import base64
import threading
import fitz
from gtts import gTTS
from io import BytesIO

GROQ_KEY = os.environ.get("GROQ_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
BOT_NAME = "Buddy"

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
conversation = {}
voice_mode = {}

def get_updates(offset=None):
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    res = requests.get(f"{BASE_URL}/getUpdates", params=params)
    return res.json()

def send_message(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

def send_voice(chat_id, text):
    tts = gTTS(text=text, lang='hi')
    audio = BytesIO()
    tts.write_to_fp(audio)
    audio.seek(0)
    requests.post(f"{BASE_URL}/sendVoice", data={"chat_id": chat_id}, files={"voice": ("voice.mp3", audio, "audio/mpeg")})

def send_reply(chat_id, text):
    if voice_mode.get(chat_id, False):
        send_voice(chat_id, text)
    else:
        send_message(chat_id, text)

def reset_conversation(chat_id):
    conversation[chat_id] = [
        {
            "role": "system",
            "content": f"Tera naam {BOT_NAME} hai. Tu ek smart aur friendly AI assistant hai. Hindi aur English dono mein baat karta hai. Chhote aur clear jawab deta hai."
        }
    ]

def get_file_url(file_id):
    file_info = requests.get(f"{BASE_URL}/getFile?file_id={file_id}").json()
    file_path = file_info["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

def get_image_base64(file_id):
    image_data = requests.get(get_file_url(file_id)).content
    return base64.b64encode(image_data).decode("utf-8")

def transcribe_voice(file_id):
    audio_data = requests.get(get_file_url(file_id)).content
    res = requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {GROQ_KEY}"},
        files={"file": ("audio.ogg", audio_data, "audio/ogg")},
        data={"model": "whisper-large-v3"}
    )
    return res.json().get("text", "")

def read_pdf(file_id):
    pdf_data = requests.get(get_file_url(file_id)).content
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text[:3000]

def ask_groq_image(base64_image, caption=""):
    prompt = caption if caption else "Is image mein kya hai? Detail mein batao."
    res = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}"},
        json={
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]
        }
    )
    return res.json()['choices'][0]['message']['content']

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

def set_reminder(chat_id, minutes, reminder_text):
    def remind():
        time.sleep(minutes * 60)
        send_message(chat_id, f"⏰ Reminder: {reminder_text}")
    t = threading.Thread(target=remind)
    t.daemon = True
    t.start()

def handle_message(chat_id, update):
    msg = update.get("message", {})
    text = msg.get("text", "")
    photo = msg.get("photo")
    voice = msg.get("voice")
    audio = msg.get("audio")
    document = msg.get("document")
    caption = msg.get("caption", "")

    if photo:
        send_message(chat_id, "Image dekh raha hoon... 🔍")
        b64 = get_image_base64(photo[-1]["file_id"])
        reply = ask_groq_image(b64, caption)
        send_reply(chat_id, reply)

    elif voice or audio:
        send_message(chat_id, "Awaaz sun raha hoon... 🎤")
        file_id = (voice or audio)["file_id"]
        transcribed = transcribe_voice(file_id)
        if transcribed:
            send_message(chat_id, f"🗣️ Tune kaha: {transcribed}")
            reply = ask_groq(chat_id, transcribed)
            send_reply(chat_id, reply)
        else:
            send_message(chat_id, "Awaaz samajh nahi aai, dobara bhejo.")

    elif document and document.get("mime_type") == "application/pdf":
        send_message(chat_id, "PDF padh raha hoon... 📄")
        pdf_text = read_pdf(document["file_id"])
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
