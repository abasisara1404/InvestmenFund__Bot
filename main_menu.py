# main_menu.py
from shared import bot, t, user_languages, user_types, user_current_menu, types
import json

menu_data = {}

def load_menu_json():
    global menu_data
    with open("menu.json", "r", encoding="utf-8") as f:
        menu_data = json.load(f)

def get_user_type(chat_id):
    return user_types.get(chat_id, "user")

def send_main_menu(chat_id, u_type=None):
    if not u_type:
        u_type = get_user_type(chat_id)
    main_items = menu_data[u_type]["main"]
    options = [item["key"] for item in main_items]
    user_current_menu[chat_id] = options
    lang = user_languages.get(chat_id, "fa")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = [types.KeyboardButton(t(lang, key)) for key in options]
    markup.add(*buttons)
    bot.send_message(chat_id, t(lang, "menu.choose_option"), reply_markup=markup)

def send_sub_menu(chat_id, parent_key):
    u_type = get_user_type(chat_id)
    lang = user_languages.get(chat_id, "fa")
    # پیدا کردن زیرمنو
    for item in menu_data[u_type]["main"]:
        if item["key"] == parent_key:
            options = item.get("submenu", [])
            user_current_menu[chat_id] = options
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            buttons = [types.KeyboardButton(t(lang, key)) for key in options]
            markup.add(*buttons)
            bot.send_message(chat_id, t(lang, "submenu.choose_option", choice=t(lang,parent_key)), reply_markup=markup)
            return
