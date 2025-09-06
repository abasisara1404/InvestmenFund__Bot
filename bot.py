# bot.py
from shared import bot, user_languages, user_types, t, user_current_menu
import main_menu
import json
from telebot import types

# =================== Load Users ===================
with open("users.json", "r", encoding="utf-8") as f:
    users = json.load(f)
    for u in users:
        user_types[u["chat_id"]] = u.get("type", "user")

# =================== Load Menu ===================
main_menu.load_menu_json()

# =================== Start Command ===================
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    # اگر کاربر جدید است، پیش‌فرض یوزر
    if chat_id not in user_types:
        user_types[chat_id] = "user"
    # انتخاب زبان
    lang_buttons = [
        types.InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        types.InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    ]
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*lang_buttons)
    bot.send_message(chat_id, "Choose your language / زبان خود را انتخاب کنید:", reply_markup=markup)

# =================== Language Selection ===================
@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def set_language(call):
    lang = call.data.split("_")[1]
    chat_id = call.message.chat.id
    user_languages[chat_id] = lang
    # ارسال منوی اصلی بر اساس نوع کاربر
    main_menu.send_main_menu(chat_id, user_types.get(chat_id, "user"))

# =================== Handle Menu Buttons ===================
@bot.message_handler(func=lambda m: True)
def handle_buttons(message):
    chat_id = message.chat.id
    lang = user_languages.get(chat_id, "fa")
    text = message.text
    options = user_current_menu.get(chat_id, [])

    # دکمه Back
    if text == t(lang, "back.message"):
        # برگشت به منوی اصلی
        main_menu.send_main_menu(chat_id, user_types.get(chat_id, "user"))
        return

    # پیدا کردن کلید متناظر با لیبل
    key_match = None
    for key in options:
        if text == t(lang, key):
            key_match = key
            break
    if not key_match:
        bot.send_message(chat_id, "Invalid option or not allowed.")
        return

    # اگر زیرمنو دارد
    main_menu.send_sub_menu(chat_id, key_match)

# =================== Start Polling ===================
bot.infinity_polling()
