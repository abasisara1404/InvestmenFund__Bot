# =================== Import Libraries ===================
import telebot
from telebot import types
import requests
import mplfinance as mpf
import pandas as pd
from io import BytesIO
import json
import os
import matplotlib
from dotenv import load_dotenv

matplotlib.use('Agg')
import matplotlib.pyplot as plt

# =================== Initialize Bot ===================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# =================== Load Translations ===================
def load_properties(lang):
    props = {}
    filename = os.path.join("messages", f"{lang}.properties")
    with open(filename, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()
    return props

# داینامیک خواندن تمام زبان‌ها از پوشه messages
translations = {}
messages_dir = "messages"
for filename in os.listdir(messages_dir):
    if filename.endswith(".properties"):
        lang = filename.split(".")[0]
        translations[lang] = load_properties(lang)

def t(lang, key, **kwargs):
    text = translations.get(lang, {}).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text

# =================== Load Coins & Timeframes ===================
with open("coins.json", "r", encoding="utf-8") as f:
    coins = json.load(f)

with open("timeframes.json", "r", encoding="utf-8") as f:
    timeframes = json.load(f)

# =================== User States ===================
user_languages = {}
open_timeframes = {}
last_message_id = {}

def get_lang(chat_id):
    return user_languages.get(chat_id, "fa")

def safe_edit_message_markup(chat_id, message_id, new_markup):
    try:
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=new_markup)
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise e

# =================== Start Command ===================
@bot.message_handler(commands=['start'])
def start(message):
    # ساخت دکمه‌های زبان داینامیک
    lang_buttons = []
    flags = {"fa":"🇮🇷", "en":"🇬🇧", "de":"🇩🇪", "ru":"🇷🇺"}
    for lang in translations.keys():
        flag = flags.get(lang,"")
        lang_buttons.append(types.InlineKeyboardButton(f"{flag} {lang}", callback_data=f"lang_{lang}"))
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*lang_buttons)
    bot.send_message(message.chat.id, "Choose your language / زبان خود را انتخاب کنید:", reply_markup=markup)

# =================== Set Language Callback ===================
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    lang = call.data.split("_", 1)[1]
    user_languages[call.message.chat.id] = lang
    send_coin_menu(call.message.chat.id)
    send_main_menu(call.message)

# =================== Coin Menu (Inline) ===================
def send_coin_menu(chat_id):
    lang = get_lang(chat_id)
    markup = types.InlineKeyboardMarkup()
    columns = 3
    for i in range(0, len(coins), columns):
        row = []
        for coin in coins[i:i+columns]:
            btn_text = f"🔽 {coin['emoji']} {coin['name']}" if open_timeframes.get(chat_id) == coin['id'] else f"▶️ {coin['emoji']} {coin['name']}"
            row.append(types.InlineKeyboardButton(btn_text, callback_data=coin['id']))
        markup.row(*row)
        for coin in coins[i:i+columns]:
            if open_timeframes.get(chat_id) == coin['id']:
                tf_row = [types.InlineKeyboardButton(f"🟦 {tf['label']}", callback_data=f"tf_{coin['id']}_{tf['value']}") for tf in timeframes]
                markup.row(*tf_row)
    if chat_id in last_message_id:
        safe_edit_message_markup(chat_id, last_message_id[chat_id], markup)
    else:
        msg = bot.send_message(chat_id, t(lang, "start.select_coin"), reply_markup=markup)
        last_message_id[chat_id] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data in [c["id"] for c in coins])
def coin_selected(call):
    chat_id = call.message.chat.id
    coin_id = call.data
    open_timeframes[chat_id] = None if open_timeframes.get(chat_id) == coin_id else coin_id
    send_coin_menu(chat_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tf_"))
def timeframe_selected(call):
    chat_id = call.message.chat.id
    _, coin_id, tf = call.data.split("_", 2)
    send_price_and_chart(chat_id, coin_id, tf)

# =================== Price Chart ===================
def send_price_and_chart(chat_id, coin_id, interval="1d"):
    coin = next((c for c in coins if c['id']==coin_id), None)
    if not coin:
        bot.send_message(chat_id, "Coin not found!")
        return
    symbol = coin["symbol"]
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": 96}
    data = requests.get(url, params=params).json()
    df = pd.DataFrame(data, columns=[
        "Open time","Open","High","Low","Close","Volume",
        "Close time","Quote asset volume","Number of trades",
        "Taker buy base asset volume","Taker buy quote asset volume","Ignore"
    ])
    df["Open time"] = pd.to_datetime(df["Open time"], unit='ms')
    for col in ["Open","High","Low","Close","Volume"]:
        df[col] = df[col].astype(float)
    df.set_index("Open time", inplace=True)
    last_price = df["Close"].iloc[-1]
    bot.send_message(chat_id, f"💰 {coin['name']} Price: {last_price:,.2f} USD")
    buf = BytesIO()
    mpf.plot(df, type='candle', style='charles', volume=True,
             title=f"{coin['name']} - {interval} Chart",
             ylabel="Price (USDT)", savefig=buf)
    buf.seek(0)
    bot.send_photo(chat_id, buf)
    buf.close()

# =================== Reply Keyboard Menu ===================
def send_main_menu(message):
    lang = get_lang(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    menu_buttons = [
        t(lang, "menu.fund_performance"),
        t(lang, "menu.account"),
        t(lang, "menu.investment"),
        t(lang, "menu.investment_status"),
        t(lang, "menu.referral"),
        t(lang, "menu.support"),
        t(lang, "menu.faq")
    ]

    buttons = [types.KeyboardButton(btn) for btn in menu_buttons]
    markup.add(*buttons)
    bot.send_message(message.chat.id, t(lang, "menu.choose_option"), reply_markup=markup)

@bot.message_handler(commands=['menu'])
def handle_menu_command(message):
    send_main_menu(message)

# =================== Main Menu Selection ===================
@bot.message_handler(func=lambda m: m.text in [
    t(get_lang(m.chat.id), "menu.fund_performance"),
    t(get_lang(m.chat.id), "menu.account"),
    t(get_lang(m.chat.id), "menu.investment"),
    t(get_lang(m.chat.id), "menu.investment_status"),
    t(get_lang(m.chat.id), "menu.referral"),
    t(get_lang(m.chat.id), "menu.support"),
    t(get_lang(m.chat.id), "menu.faq")
])
def handle_main_choice(message):
    chat_id = message.chat.id
    lang = get_lang(chat_id)
    selected = message.text

    # پیام کوتاه هنگام باز کردن زیرمنو
    opening_msg = bot.send_message(chat_id, t(lang, "submenu.opening"))

    # ساخت زیرمنو
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    sub_buttons = [
        types.KeyboardButton("1"),
        types.KeyboardButton("2"),
        types.KeyboardButton("3"),
        types.KeyboardButton(t(lang, "back.message"))
    ]
    markup.add(*sub_buttons)

    # نمایش زیرمنو
    bot.send_message(chat_id, t(lang, "submenu.choose_option", choice=selected), reply_markup=markup)

    # حذف پیام "در حال باز کردن زیرمنو..."
    try:
        bot.delete_message(chat_id, opening_msg.message_id)
    except:
        pass

    # نمایش زیرمنوی inline کوین‌ها همزمان
    send_coin_menu(chat_id)

@bot.message_handler(func=lambda m: m.text == t(get_lang(m.chat.id), "back.message"))
def handle_back(message):
    chat_id = message.chat.id
    lang = get_lang(chat_id)
    bot.send_message(chat_id, t(lang, "back.message"), reply_markup=types.ReplyKeyboardRemove())
    send_main_menu(message)

@bot.message_handler(func=lambda m: m.text in ["1","2","3"])
def handle_submenu_choice(message):
    chat_id = message.chat.id
    lang = get_lang(chat_id)
    bot.send_message(chat_id, t(lang, "submenu.selected", choice=message.text))

# =================== Run Bot ===================
bot.infinity_polling()
