
import requests
from binance.client import Client
import time
import ta
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

client = Client()

WEBHOOK_URL = "https://web-production-7810.up.railway.app//"

def get_symbols():
    exchange_info = client.get_exchange_info()
    usdt_pairs = [s['symbol'] for s in exchange_info['symbols']
                  if s['symbol'].endswith('USDT') and s['status'] == 'TRADING' and not s['symbol'].endswith('BUSDUSDT')]
    return usdt_pairs

def get_klines(symbol):
    try:
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=100)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['close'] = pd.to_numeric(df['close'])
        return df
    except:
        return None

def analyze(symbol):
    df = get_klines(symbol)
    if df is None or len(df) < 50:
        return

    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['ma200'] = df['close'].rolling(window=200).mean()

    latest = df.iloc[-1]

    if latest['rsi'] < 30 and latest['macd'] > latest['macd_signal'] and latest['close'] > latest['ma200']:
        send_signal(symbol, "شراء", latest['close'])

def send_signal(symbol, direction, entry):
    target = round(entry * 1.03, 4)
    stop = round(entry * 0.97, 4)
    data = {
        "symbol": symbol,
        "direction": direction,
        "entry": round(entry, 4),
        "target": target,
        "stop": stop
    }
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        print(f"Sent signal for {symbol} - Response: {response.status_code}")
    except Exception as e:
        print(f"Failed to send signal for {symbol} - {e}")

def run():
    symbols = get_symbols()
    for symbol in symbols:
        analyze(symbol)

if __name__ == "__main__":
    while True:
        print("Checking market...")
        run()
        time.sleep(60)
