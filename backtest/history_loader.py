# -*- coding: utf-8 -*-
"""history_loader.py

SECTION 0:  Импорты и константы
--------------------------------
Сюда собираем все внешние зависимости и значения по умолчанию, 
чтобы их легко было найти и изменить. Никакой логики здесь нет.
"""

# SECTION 0: imports & constants ---------------------------------------------
import argparse
import csv
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple

import ccxt

# Биржа и тип рынка (см. pair_selector)
EXCHANGE_ID = "binance"
DEFAULT_TYPE = "future"  # USD‑M perpetual

# Пара и тайм‑фрейм по умолчанию
DEFAULT_PAIR = "SOL/USDT:USDT"
DEFAULT_TIMEFRAME = "1m"  # можно 1m,5m,15m,...

# Сколько дней истории тянуть, если не задали явно
DEFAULT_DAYS_BACK = 90

# Куда складывать CSV‑файлы
DATA_DIR = Path("data/history")

# SECTION 1:   Парсим аргументы CLI ------------------------------------------

def _parse_args() -> argparse.Namespace:
    """Командная строка.

    Примеры:
    ---------
    
    Получить 90 дней 1‑минутных свечей SOLUSDT и сохранить их в data/history:

    ```powershell
    python backtest\history_loader.py \
        --symbol "SOL/USDT:USDT" --timeframe 1m --days 90
    ```

    Получить с конкретной даты до сейчас:

    ```powershell
    python backtest\history_loader.py --since 2024-01-01
    ```
    """
    p = argparse.ArgumentParser(description="Загрузка исторических свечей из Binance")
    p.add_argument("--symbol", default=DEFAULT_PAIR, help="Торговая пара (ccxt формат)")
    p.add_argument("--timeframe", default=DEFAULT_TIMEFRAME, help="TF: 1m,5m,1h…")
    p.add_argument("--days", type=int, default=DEFAULT_DAYS_BACK, help="Сколько дней назад (игнорируется, если задан --since)")
    p.add_argument("--since", help="Дата начала (YYYY-MM-DD), берёт верх над --days")
    p.add_argument("--dest", default=str(DATA_DIR), help="Каталог для CSV‑файлов")
    return p.parse_args()

# SECTION 2:   Подключение к бирже -------------------------------------------

def _connect_exchange() -> ccxt.Exchange:
    ex = getattr(ccxt, EXCHANGE_ID)({"options": {"defaultType": DEFAULT_TYPE}})
    # Можем добавить apiKey/secret позже, но для истории они не нужны.
    ex.rateLimit = max(250, ex.rateLimit)  # подстраховка
    return ex

# SECTION 3:   Грузим свечи порциями ----------------------------------------

def _fetch_ohlcv(
    ex: ccxt.Exchange,
    symbol: str,
    timeframe: str,
    since_ts: int,
) -> List[List]:
    """Возвращает список свечей [timestamp, open, high, low, close, volume]."""
    limit = ex.safe_integer(ex.timeframes, timeframe) or 1000  # Binance даёт 1500, но 1000 — безопасно
    all_candles: List[List] = []
    ms = since_ts
    while True:
        batch = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=ms, limit=limit)
        if not batch:
            break
        all_candles.extend(batch)
        if len(batch) < limit:
            break  # дошли до конца
        ms = batch[-1][0] + ex.parse_timeframe(timeframe) * 1000  # следующий блок
    return all_candles

# SECTION 4 ─ скачиваем свечи по чанкам и пишем CSV
from tqdm import tqdm                     # NEW

def _download_klines(ex, symbol, tf, since_ms, out_path):
    CHUNK = 1000           # макс. 1000 свечей за раз
    all_rows = []
    pbar = tqdm(desc=f"{symbol} {tf}", unit="bars")   # NEW

    while True:
        ohlcv = ex.fetch_ohlcv(symbol, tf, since_ms, CHUNK)
        if not ohlcv:
            break
        all_rows.extend(ohlcv)
        since_ms = ohlcv[-1][0] + 1          # +1 мс, чтобы не дублировать
        pbar.update(len(ohlcv))              # NEW
    pbar.close()                             # NEW

    header = "timestamp,open,high,low,close,volume\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        for t, o, h, l, c, v in all_rows:
            f.write(f"{t},{o},{h},{l},{c},{v}\n")


# SECTION 5:   Главная точка входа ------------------------------------------

def main() -> None:
    args = _parse_args()

    # Вычисляем начало периода
    if args.since:
        since_dt = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        since_dt = datetime.now(timezone.utc) - timedelta(days=args.days)
    since_ts = int(since_dt.timestamp() * 1000)

    ex = _connect_exchange()
    print(f"Подключено к {ex.id}, загружаем {args.symbol} ({args.timeframe}) c {since_dt:%Y-%m-%d}…")

    candles = _fetch_ohlcv(ex, args.symbol, args.timeframe, since_ts)

    dest_file = Path(args.dest) / f"{args.symbol.replace('/', '').replace(':', '')}_{args.timeframe}.csv"
    _save_csv(candles, dest_file)


if __name__ == "__main__":
    main()
