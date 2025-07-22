# SECTION 0: Импорты и константы
import os, sys, time, logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import ccxt
import pandas as pd
from tqdm import tqdm

# SECTION 0.1: конфигурация логов
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/loader.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# SECTION 0.2: константы
DATA_DIR = Path("data/history")
EXCHANGE_ID = "binance"
MARKET_TYPE = "future"   # USDⓈ-M
# SECTION 1: Получение ликвидных тикеров
def get_liquid_tickers(top_n: int = 30) -> List[str]:
    ex = ccxt.binance({"options": {"defaultType": MARKET_TYPE}})
    markets = ex.load_markets()
    tickers = ex.fetch_tickers()

    records = []
    for symbol, m in markets.items():
        if not m.get("active") or m["type"] != MARKET_TYPE:
            continue
        quote = m["quote"]
        if quote != "USDT":
            continue
        t = tickers.get(symbol, {})
        quote_vol = float(t.get("quoteVolume", 0))
        min_notional = float(m.get("limits", {}).get("cost", {}).get("min", 0))
        records.append((symbol, quote_vol, min_notional))

    # фильтрация и сортировка
    records = [r for r in records if r[1] >= 1_000_000 and r[2] <= 10]
    records.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in records[:top_n]]
# SECTION 2: Загрузка OHLCV
def fetch_ohlcv(
    symbol: str,
    timeframe: str,
    since: datetime,
    until: datetime,
) -> pd.DataFrame:
    ex = ccxt.binance({"options": {"defaultType": MARKET_TYPE}})
    ex.rateLimit = max(250, ex.rateLimit)

    since_ms = int(since.timestamp() * 1000)
    until_ms = int(until.timestamp() * 1000)
    tf_sec = ex.parse_timeframe(timeframe)
    all_bars = []

    with tqdm(total=None, desc=f"{symbol} {timeframe}") as pbar:
        while since_ms < until_ms:
            batch = ex.fetch_ohlcv(
                symbol, timeframe=timeframe, since=since_ms, limit=1000
            )
            if not batch:
                break
            all_bars.extend(batch)
            since_ms = batch[-1][0] + tf_sec * 1000
            pbar.update(len(batch))
            time.sleep(ex.rateLimit / 1000)

    df = pd.DataFrame(
        all_bars,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trades",
            "taker_base",
            "taker_quote",
            "ignore",
        ],
    )
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df = df[df["open_time"] < until]  # обрезаем лишнее
    return df
# SECTION 3: Сохранение
def save(df: pd.DataFrame, symbol: str, timeframe: str, since: datetime, until: datetime):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    base = f"{symbol.replace('/', '').replace(':', '')}_{timeframe}_{since:%Y%m%d}_{until:%Y%m%d}"
    csv_path = DATA_DIR / f"{base}.csv"
    parquet_path = DATA_DIR / f"{base}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    logging.info("Saved %s rows to %s / %s", len(df), csv_path.name, parquet_path.name)
    