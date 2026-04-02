import feedparser
import requests
import os
import json
from datetime import datetime

# === ТВОИ НАСТРОЙКИ (замени на свои!) ===
TELEGRAM_TOKEN = 8511804869:AAEea2v-4g2xtoOSLE5qpMk6ITOcbMPsIcc
TELEGRAM_CHANNEL =   @zakony_rf_prosto_bot  # например @prostye_zakony_rf
GROQ_API_KEY = # GROQ_API_KEY будет взят из секретов GitHub
LAST_CHECK_FILE = "last_check.json"

RSS_URL = "http://publication.pravo.gov.ru/api/rss?pageSize=200"

def load_last_check():
    if os.path.exists(LAST_CHECK_FILE):
        with open(LAST_CHECK_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("last_pub_date")
    return None

def save_last_check(pub_date):
    with open(LAST_CHECK_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_pub_date": pub_date}, f)

def get_simple_explanation(title, description, link):
    prompt = f"""Закон: {title}
Короткое описание: {description}
Ссылка: {link}

Объясни простым языком для обычного человека (как бабушке или другу):
1. Что это меняет в жизни?
2. Кому это важно?
3. К чему это может привести?
Текст должен быть весёлым, понятным, без канцелярита. Максимум 350-400 символов."""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 600
        }
    )
    return response.json()["choices"][0]["message"]["content"]

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHANNEL,
        "text": text,
        "parse_mode": "HTML"
    })

# Главная работа
feed = feedparser.parse(RSS_URL)
last_pub = load_last_check()
new_items = []

for entry in feed.entries:
    pub_date = entry.published
    if last_pub and pub_date <= last_pub:
        continue

    title = entry.title
    description = entry.get("description", "")[:500]
    link = entry.link

    explanation = get_simple_explanation(title, description, link)

    message = f"🆕 <b>Новый закон / законопроект</b>\n\n" \
              f"<b>{title}</b>\n\n" \
              f"{explanation}\n\n" \
              f"📖 Полный текст: {link}"

    send_to_telegram(message)
    new_items.append(pub_date)

if new_items:
    save_last_check(max(new_items))
    print(f"Отправлено {len(new_items)} новых законов")
else:
    print("Пока новых законов нет")
