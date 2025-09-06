from telebot import types
from shared import bot, t, get_lang, get_user_type

# ===================== منوی Admin =====================
def send_admin_menu(message):
    lang = get_lang(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton(t(lang, "menu.admin.fund_performance")),
        types.KeyboardButton(t(lang, "menu.admin.investor_list")),
        types.KeyboardButton(t(lang, "menu.admin.investor_stats"))
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, t(lang, "menu.choose_option"), reply_markup=markup)

# ===================== منوی User =====================
def send_user_menu(message):
    lang = get_lang(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton(t(lang, "menu.fund_performance")),
        types.KeyboardButton(t(lang, "menu.account")),
        types.KeyboardButton(t(lang, "menu.investment")),
        types.KeyboardButton(t(lang, "menu.support")),
        types.KeyboardButton(t(lang, "menu.faq"))
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, t(lang, "menu.choose_option"), reply_markup=markup)

# ===================== زیرمنوی User =====================
def send_user_submenu(chat_id):
    lang = get_lang(chat_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton("1"),
        types.KeyboardButton("2"),
        types.KeyboardButton("3"),
        types.KeyboardButton(t(lang, "back.message"))
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, t(lang, "submenu.choose_option_user"), reply_markup=markup)

# ===================== زیرمنوی Admin =====================
def send_admin_submenu(chat_id):
    lang = get_lang(chat_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton("4"),
        types.KeyboardButton("5"),
        types.KeyboardButton("6"),
        types.KeyboardButton(t(lang, "back.message"))
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, t(lang, "submenu.choose_option_admin"), reply_markup=markup)

# ===================== ثبت هندلرها =====================
def register_handlers():
    @bot.message_handler(func=lambda m: m.text in [
        t(get_lang(m.chat.id), "menu.admin.fund_performance"),
        t(get_lang(m.chat.id), "menu.admin.investor_list"),
        t(get_lang(m.chat.id), "menu.admin.investor_stats"),
        t(get_lang(m.chat.id), "menu.fund_performance"),
        t(get_lang(m.chat.id), "menu.account"),
        t(get_lang(m.chat.id), "menu.investment"),
        t(get_lang(m.chat.id), "menu.support"),
        t(get_lang(m.chat.id), "menu.faq")
    ])
    def handle_main_choice(message):
        chat_id = message.chat.id
        if get_user_type(chat_id) == "admin":
            send_admin_submenu(chat_id)
        else:
            send_user_submenu(chat_id)

    @bot.message_handler(func=lambda m: m.text in ["1","2","3","4","5","6"])
    def handle_submenu_choice(message):
        chat_id = message.chat.id
        lang = get_lang(chat_id)
        bot.send_message(chat_id, t(lang, "submenu.selected", choice=message.text))

    @bot.message_handler(func=lambda m: m.text == t(get_lang(m.chat.id), "back.message"))
    def handle_back(message):
        chat_id = message.chat.id
        if get_user_type(chat_id) == "admin":
            send_admin_menu(message)
        else:
            send_user_menu(message)
