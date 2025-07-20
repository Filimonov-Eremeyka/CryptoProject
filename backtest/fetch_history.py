import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные из .env, если он есть
load_dotenv()

# Читаем параметры из .env
SYMBOL = os.getenv("HIST_SYMBOL", "BTCUSDT")
INTERVAL = os.getenv("HIST_INTERVAL", "1m")
LIMIT = int(os.getenv("HIST_LIMIT", 1000))
OUTPUT_FILE = os.getenv("HIST_OUTPUT_FILE", f"{SYMBOL}_{INTERVAL}_history.csv")
MARKET_TYPE = os.getenv("HIST_MARKET_TYPE", "spot").lower()

# Выбор API URL по типу рынка
if MARKET_TYPE == "spot":
    BASE_URL = "https://api.binance.com/api/v3/klines"
elif MARKET_TYPE == "futures":
    BASE_URL = "https://fapi.binance.com/fapi/v1/klines"
else:
    raise ValueError(f"[ERROR] Недопустимый тип рынка: {MARKET_TYPE}. Используйте 'spot' или 'futures'.")

def fetch_klines(symbol: str, interval: str, limit: int = 1000):
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }
    print(f"[INFO] Отправляем запрос: {BASE_URL} c параметрами {params}")
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def save_to_csv(data, filename):
    df = pd.DataFrame(data, columns=[
        "Open time", "Open", "High", "Low", "Close", "Volume",
        "Close time", "Quote asset volume", "Number of trades",
        "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"
    ])
    df["Open time"] = pd.to_datetime(df["Open time"], unit='ms')
    df["Close time"] = pd.to_datetime(df["Close time"], unit='ms')
    df.to_csv(filename, index=False)
    print(f"[INFO] Данные сохранены в файл: {filename}")

def main():
    print(f"[INFO] Загрузка истории: SYMBOL={SYMBOL}, INTERVAL={INTERVAL}, MARKET={MARKET_TYPE}, LIMIT={LIMIT}")
    data = fetch_klines(SYMBOL, INTERVAL, LIMIT)
    save_to_csv(data, OUTPUT_FILE)

if __name__ == "__main__":
    main()
