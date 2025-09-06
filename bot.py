import json
from shared import bot, user_languages, get_user_type
import main_menu
import coin_menu
import telebot

# ------------------ بارگذاری coins و timeframes ------------------
with open("coins.json", "r", encoding="utf-8") as f:
    coins_data = json.load(f)
with open("timeframes.json", "r", encoding="utf-8") as f:
    timeframes_data = json.load(f)

coin_menu.coins.extend(coins_data)
coin_menu.timeframes.extend(timeframes_data)

# ------------------ ثبت هندلرها ------------------
main_menu.register_handlers()
coin_menu.register_handlers()

# ------------------ هندلر /start ------------------
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = str(message.chat.id)
    lang_buttons = [
        telebot.types.InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
        telebot.types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        telebot.types.InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
        telebot.types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    ]
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(*lang_buttons)
    bot.send_message(chat_id, "Choose your language / زبان خود را انتخاب کنید:", reply_markup=markup)

# ------------------ انتخاب زبان ------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    chat_id = str(call.message.chat.id)
    lang = call.data.split("_")[1]
    user_languages[chat_id] = lang

    # نمایش منو بر اساس نوع کاربر
    if get_user_type(chat_id) == "admin":
        main_menu.send_admin_menu(call.message)
    else:
        main_menu.send_user_menu(call.message)

# ------------------ هندلر تست Chat ID ------------------
@bot.message_handler(commands=['myid'])
def myid(message):
    chat_id = str(message.chat.id)
    user_type = get_user_type(chat_id)
    lang = user_languages.get(chat_id, "fa")
    bot.send_message(chat_id, f"Your Chat ID: {chat_id}\nUser Type: {user_type}\nCurrent Lang: {lang}")

# ------------------ حذف session قبلی ------------------
bot.delete_webhook()  # ⚡ این خط جلوی خطای 409 را می‌گیرد

# ------------------ اجرای ربات ------------------
bot.infinity_polling()
