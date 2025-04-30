
import requests
import pandas as pd
import ta
import time
import threading
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters

app = Flask(__name__)

BOT_TOKEN = '8051801199:AAEIDOsCF45Zw0FVZJK6PHMKkYnFeZaveKo'
CHAT_ID = '6333148344'
bot = Bot(token=BOT_TOKEN)

stable_coins = [
    'USDT', 'USDC', 'BUSD', 'TUSD', 'FDUSD', 'DAI', 'USDSB', 'USD', 'EURS',
    'PAX', 'USDP', 'GUSD', 'SUSD', 'LUSD', 'HUSD', 'MIM', 'UST', 'FRAX',
    'XAUT', 'XSGD', 'CUSD', 'NUSD', 'USDX'
]

@app.route('/')
def home():
    return "RSI Bot Aktif"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return 'ok'

def get_usdt_symbols():
    try:
        data = requests.get("https://api.binance.com/api/v3/exchangeInfo").json()
        return [
            s['symbol'] for s in data['symbols']
            if s['symbol'].endswith('USDT') and s['baseAsset'] not in stable_coins
        ]
    except Exception as e:
        print("Sembol alma hatası:", e)
        return []

def get_klines(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    df = pd.DataFrame(requests.get(url).json())
    df.columns = ['time','open','high','low','close','volume','close_time','quote_asset_volume','number_of_trades','taker_buy_base','taker_buy_quote','ignore']
    df['close'] = df['close'].astype(float)
    return df

def calculate_rsi(df, period=14):
    rsi = ta.momentum.RSIIndicator(close=df['close'], window=period)
    df['rsi'] = rsi.rsi()
    return df

def send_telegram_message(msg):
    bot.send_message(chat_id=CHAT_ID, text=msg)

def handle_message(update, context):
    text = update.message.text.strip().lower()
    print(f"Gelen mesaj: {text}")  # Log için
    if text == "arda_botu_test_ediyor":
        context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Bot çalışıyor.")

def rsi_bot():
    symbols = get_usdt_symbols()

    while True:
        try:
            for symbol in symbols:
                df_5m = calculate_rsi(get_klines(symbol, '5m'))
                df_15m = calculate_rsi(get_klines(symbol, '15m'))
                df_1h = calculate_rsi(get_klines(symbol, '1h'))
                df_4h = calculate_rsi(get_klines(symbol, '4h'))

                rsi_5m = df_5m['rsi'].iloc[-1]
                rsi_15m = df_15m['rsi'].iloc[-1]
                rsi_1h = df_1h['rsi'].iloc[-1]
                rsi_4h = df_4h['rsi'].iloc[-1]
                last_price = df_5m['close'].iloc[-1]
                rsi_avg = (rsi_5m + rsi_15m + rsi_1h + rsi_4h) / 4

                if rsi_5m > 90 or rsi_15m > 90 or rsi_avg > 85:
                    msg = (
                        f"💰: {symbol}\n"
                        f"🔔: High🔴🔴 RSI Alert +85 \n"
                        f" RSI 5minute: {rsi_5m:.2f}\n"
                        f" RSI 15minute: {rsi_15m:.2f}\n"
                        f" RSI 1hour: {rsi_1h:.2f}\n"
                        f" RSI 4hour: {rsi_4h:.2f}\n"
                        f" Last Price: {last_price:.5f}\n"
                        f" ScalpingPA"
                    )
                    send_telegram_message(msg)
                time.sleep(0.1)
            time.sleep(60)
        except Exception as e:
            print("Bot hatası:", e)
            time.sleep(60)

from telegram.ext import CallbackContext
dp = Dispatcher(bot, None, workers=0)
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

if __name__ == "__main__":
    threading.Thread(target=rsi_bot).start()
    app.run(host='0.0.0.0', port=8080)
