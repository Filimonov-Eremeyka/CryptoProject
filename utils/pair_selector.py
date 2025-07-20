"""
Pair Selector — утилита для выбора ликвидных фьючерс‑пар Binance.

Файл разбит на нумерованные секции.  Если понадобится добавлять
новую логику, вставляем, например, `SECTION 2.1` между 2 и 3 —
и оба будем точно знать, где править.
"""

# SECTION 1: Импорты и константы
# ------------------------------------------------------------
from __future__ import annotations

import ccxt
from typing import Dict, List, Tuple

EXCHANGE_ID          = "binance"
DEFAULT_TYPE         = "future"        # USDⓈ‑M фьючи
MIN_VOLUME_USDT      = 1_000_000       # ликвидность ≥ 1 млн USDT
MAX_MIN_NOTIONAL     = 10              # minNotional ≤ 10 USDT
TOP_N                = 30              # сколько пар в итоге вернуть

# SECTION 2: Подключение к бирже и загрузка рынков
# ------------------------------------------------------------

def _connect_exchange() -> ccxt.Exchange:
    """Создаём объект ccxt для Binance USDⓈ‑M Futures."""
    return ccxt.binance({"options": {"defaultType": DEFAULT_TYPE}})


def _load_futures_markets(ex: ccxt.Exchange) -> Dict[str, dict]:
    """Возвращает словарь только активных USDT‑фьючерсов."""
    markets = ex.load_markets()
    return {
        s: m for s, m in markets.items()
        if m.get("active") and m.get("contract") and m.get("quote") == "USDT" and m.get("type") == "swap"     
    }

# SECTION 3: Фильтр по ликвидности
# ------------------------------------------------------------

def _filter_by_liquidity(
    ex: ccxt.Exchange,
    futures: Dict[str, dict],
    min_volume: float,
    max_min_notional: float,
) -> List[Tuple[str, float]]:
    """Отбирает пары, удовлетворяющие условиям ликвидности."""
    tickers = ex.fetch_tickers(list(futures))
    selected: List[Tuple[str, float]] = []
    for symbol, market in futures.items():
        vol = tickers[symbol]["quoteVolume"]
        min_notional = market["limits"]["cost"]["min"]
        if vol >= min_volume and min_notional <= max_min_notional:
            selected.append((symbol, vol))
    return selected

# SECTION 4: Сортировка и финальный список пар
# ------------------------------------------------------------

def select_pairs(top_n: int = TOP_N) -> List[str]:
    """Главная функция: возвращает TOP‑N пар по объёму."""
    ex       = _connect_exchange()
    futures  = _load_futures_markets(ex)
    filtered = _filter_by_liquidity(ex, futures, MIN_VOLUME_USDT, MAX_MIN_NOTIONAL)

    # сортировка по объёму убыв.
    top = sorted(filtered, key=lambda x: x[1], reverse=True)[:top_n]
    return [sym for sym, _ in top]

# SECTION 5: CLI‑точка входа
# ------------------------------------------------------------
if __name__ == "__main__":
    pairs = select_pairs()
    print(f"\nВыбрано {len(pairs)} пар:\n{pairs}\n")
