# shared.py
import os
import json
from dotenv import load_dotenv
import telebot
from telebot import types

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ------------------ ترجمه‌ها ------------------
def load_properties(lang):
    props = {}
    filename = os.path.join("messages", f"{lang}.properties")
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

# ------------------ کاربران ------------------
user_languages = {}  # chat_id -> lang
user_types = {}      # chat_id -> "user" / "admin"
user_current_menu = {} # chat_id -> لیست کلیدهای منو فعلی
