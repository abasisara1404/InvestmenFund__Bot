from telebot import types
from io import BytesIO
import pandas as pd
import mplfinance as mpf
import requests
from shared import bot, t, get_lang

coins = []
timeframes = []

open_timeframes = {}
last_message_id = {}

def safe_edit_message_markup(chat_id, message_id, new_markup):
    try:
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=new_markup)
    except Exception as e:
        if "message is not modified" not in str(e):
            raise e

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

def register_handlers():
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
