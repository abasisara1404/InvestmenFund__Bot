import os
import json
from dotenv import load_dotenv
import telebot

# ------------------ بارگذاری توکن و ساخت ربات ------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ------------------ بارگذاری ترجمه‌ها ------------------
def load_properties(lang):
    props = {}
    filename = os.path.join("messages", f"{lang}.properties")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    props[key.strip()] = value.strip()
    return props

translations = {lang: load_properties(lang) for lang in ["fa","en","de","ru"]}

def t(lang, key, **kwargs):
    text = translations.get(lang, {}).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text

# ------------------ وضعیت کاربران ------------------
user_languages = {}  # chat_id -> زبان فعلی

users_file = "users.json"
if os.path.exists(users_file):
    with open(users_file, "r", encoding="utf-8") as f:
        users_data = json.load(f)
else:
    users_data = {}

def get_user_type(chat_id):
    return users_data.get(str(chat_id), {}).get("type", "user")

def get_lang(chat_id):
    return user_languages.get(str(chat_id), "fa")

def save_users():
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)
