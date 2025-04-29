import requests
import pandas as pd
import ta
import time
import threading
from flask import Flask
from telegram import Bot

app = Flask(__name__)

@app.route('/')
def home():
    return ""

BOT_TOKEN = '8051801199:AAEIDOsCF45Zw0FVZJK6PHMKkYnFeZaveKo'
CHAT_ID = '6333148344'

stable_coins = [
    'USDT', 'USDC', 'BUSD', 'TUSD', 'FDUSD', 'DAI', 'USDSB', 'USD', 'EURS',
    'PAX', 'USDP', 'GUSD', 'SUSD', 'LUSD', 'HUSD', 'MIM', 'UST', 'FRAX',
    'XAUT', 'XSGD', 'CUSD', 'NUSD', 'USDX'
]

def get_usdt_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if 'symbols' not in data:
            print("Binance API yanıtında 'symbols' anahtarı yok. Geriye boş liste dönülüyor.")
            return []

        symbols = []
        for s in data['symbols']:
            symbol = s['symbol']
            base = s['baseAsset']
            if symbol.endswith('USDT') and base not in stable_coins:
                symbols.append(symbol)
        return symbols

    except Exception as e:
        print(f"Binance API bağlantı hatası: {e}")
        return []

def get_klines(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)
    df.columns = ['time', 'open', 'high', 'low', 'close', 'volume',
                  'close_time', 'quote_asset_volume', 'number_of_trades',
                  'taker_buy_base', 'taker_buy_quote', 'ignore']
    df['close'] = df['close'].astype(float)
    return df

def calculate_rsi(df, period=12):
    rsi = ta.momentum.RSIIndicator(close=df['close'], window=period)
    df['rsi'] = rsi.rsi()
    return df

def send_telegram_message(message):
    bot = Bot(token=BOT_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)

def rsi_bot():
    send_telegram_message("✅ RSI Bot başlatıldı ve çalışıyor.")
    
    symbols = get_usdt_symbols()

    while True:
        try:
            for symbol in symbols:
                df_5m = get_klines(symbol, '5m')
                df_15m = get_klines(symbol, '15m')
                df_1h = get_klines(symbol, '1h')
                df_4h = get_klines(symbol, '4h')

                df_5m = calculate_rsi(df_5m)
                df_15m = calculate_rsi(df_15m)
                df_1h = calculate_rsi(df_1h)
                df_4h = calculate_rsi(df_4h)

                rsi_5m = df_5m['rsi'].iloc[-1]
                rsi_15m = df_15m['rsi'].iloc[-1]
                rsi_1h = df_1h['rsi'].iloc[-1]
                rsi_4h = df_4h['rsi'].iloc[-1]
                last_price = df_5m['close'].iloc[-1]

                rsi_avg = (rsi_5m + rsi_15m + rsi_1h + rsi_4h) / 4

                if rsi_5m > 90 or rsi_15m > 90 or rsi_avg > 85:
                    message = (
                        f"💰: {symbol}\n"
                        f"🔔: High🔴🔴 RSI Alert +85 \n"
                        f" RSI 5minute: {rsi_5m:.2f}\n"
                        f" RSI 15minute: {rsi_15m:.2f}\n"
                        f" RSI 1hour: {rsi_1h:.2f}\n"
                        f" RSI 4hour: {rsi_4h:.2f}\n"
                        f" Last Price: {last_price:.5f}\n"
                        f" ScalpingPA"
                    )
                    send_telegram_message(message)

                time.sleep(1)

            time.sleep(60)

        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=rsi_bot).start()
    app.run(host='0.0.0.0', port=8080)
