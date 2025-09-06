from shared import bot, t, user_languages
from telebot import types

coins = [
    {"id": "BTC", "name": "Bitcoin", "emoji": "₿"},
    {"id": "ETH", "name": "Ethereum", "emoji": "Ξ"},
    {"id": "DOGE", "name": "Dogecoin", "emoji": "Ð"}
]

def send_coin_menu(chat_id):
    lang = user_languages.get(chat_id, "fa")
    markup = types.InlineKeyboardMarkup()
    for coin in coins:
        btn_text = f"{coin['emoji']} {coin['name']}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=coin["id"]))
    bot.send_message(chat_id, t(lang, "start.select_coin"), reply_markup=markup)

def register_handlers():
    @bot.callback_query_handler(func=lambda call: call.data in [c["id"] for c in coins])
    def coin_selected(call):
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id, f"Selected coin: {call.data}")
