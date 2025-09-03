
#bot = telebot.TeleBot("8033740923:AAGSLI6AQpa0nhq3w0gIlpWjDM6MAwTbdlU") 

# =================== Import Libraries ===================
import telebot
from telebot import types
import requests
import mplfinance as mpf
import pandas as pd
from io import BytesIO
import json
import os
import datetime
import matplotlib
import os
from dotenv import load_dotenv

# =================== Use Agg Backend ===================
# جلوگیری از هشدار GUI در matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# =================== Initialize Bot ===================
load_dotenv()  # بارگذاری متغیرهای محیطی از فایل .env
BOT_TOKEN = os.getenv("BOT_TOKEN")  # خواندن توکن
bot = telebot.TeleBot(BOT_TOKEN)

# =================== Load Translations ===================
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

# بارگذاری ترجمه‌ها
translations = {lang: load_properties(lang) for lang in ["fa","en","de","ru"]}

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
user_languages = {}       # chat_id -> lang
open_timeframes = {}      # chat_id -> coin_id یا None
last_message_id = {}      # chat_id -> message_id

def get_lang(chat_id):
    return user_languages.get(chat_id, "fa")

# =================== Safe Edit Message Markup ===================
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
    # دکمه‌های انتخاب زبان دو سطر دو ستون
    lang_buttons = [
        types.InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        types.InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    ]
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(*lang_buttons)
    bot.send_message(message.chat.id, "Choose your language / زبان خود را انتخاب کنید:", reply_markup=markup)

# =================== Set Language ===================
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    lang = call.data.split("_", 1)[1]
    user_languages[call.message.chat.id] = lang
    send_coin_menu(call.message.chat.id)

# =================== Send Coin Menu with ComboBox ===================
def send_coin_menu(chat_id):
    lang = get_lang(chat_id)
    markup = types.InlineKeyboardMarkup()
    columns = 3  # تعداد ستون کوین‌ها

    for i in range(0, len(coins), columns):
        row = []
        # ردیف کوین‌ها
        for coin in coins[i:i+columns]:
            if open_timeframes.get(chat_id) == coin['id']:
                btn_text = f"🔽 {coin['emoji']} {coin['name']}"  # زیرمنو باز
            else:
                btn_text = f"▶️ {coin['emoji']} {coin['name']}"  # زیرمنو بسته
            row.append(types.InlineKeyboardButton(btn_text, callback_data=coin['id']))
        markup.row(*row)

        # اضافه کردن زیرمنو تایم‌فریم جلوتر با 🟦
        for coin in coins[i:i+columns]:
            if open_timeframes.get(chat_id) == coin['id']:
                tf_row = [types.InlineKeyboardButton(f"🟦 {tf['label']}", callback_data=f"tf_{coin['id']}_{tf['value']}") for tf in timeframes]
                markup.row(*tf_row)

    if chat_id in last_message_id:
        safe_edit_message_markup(chat_id, last_message_id[chat_id], markup)
    else:
        msg = bot.send_message(chat_id, t(lang, "start.select_coin"), reply_markup=markup)
        last_message_id[chat_id] = msg.message_id

# =================== Coin Toggle Callback ===================
@bot.callback_query_handler(func=lambda call: call.data in [c["id"] for c in coins])
def coin_selected(call):
    chat_id = call.message.chat.id
    coin_id = call.data

    # toggle باز/بسته شدن زیرمنو
    if open_timeframes.get(chat_id) == coin_id:
        open_timeframes[chat_id] = None
    else:
        open_timeframes[chat_id] = coin_id

    send_coin_menu(chat_id)

# =================== Timeframe Callback ===================
@bot.callback_query_handler(func=lambda call: call.data.startswith("tf_"))
def timeframe_selected(call):
    chat_id = call.message.chat.id
    _, coin_id, tf = call.data.split("_", 2)
    send_price_and_chart(chat_id, coin_id, tf)

# =================== Send Candlestick Chart in-memory ===================
def send_price_and_chart(chat_id, coin_id, interval="1d"):
    coin = next((c for c in coins if c['id']==coin_id), None)
    if not coin:
        bot.send_message(chat_id, "Coin not found!")
        return

    symbol = coin["symbol"]
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": 96}
    data = requests.get(url, params=params).json()

    # ساخت DataFrame
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

    # ساخت چارت در حافظه بدون ذخیره فایل
    buf = BytesIO()
    mpf.plot(df, type='candle', style='charles', volume=True,
             title=f"{coin['name']} - {interval} Chart",
             ylabel="Price (USDT)", savefig=buf)
    buf.seek(0)
    bot.send_photo(chat_id, buf)
    buf.close()

# =================== Run Bot ===================
bot.infinity_polling()
