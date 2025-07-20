#!/usr/bin/env python3
"""
live/connector.py
=================
Веб‑коннектор к Binance Futures (USDT‑M).

Каждый крупный логический блок размечен *секциями* (SECTION X), чтобы
проще ссылаться при обсуждениях. Нумерация плавающая: если появится новый
код между 2 и 3, мы назовём его 2.1, 2.2 и т.д.
"""

# === SECTION 1: Импорты стандартных и сторонних библиотек ==========
import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict

import websockets  # pip install websockets

# === SECTION 2: Загрузка конфигурации ==============================
@dataclass
class Config:
    symbol: str = os.getenv("SYMBOL", "BTCUSDT")
    interval: str = os.getenv("INTERVAL", "1m")
    ws_url: str = "wss://fstream.binance.com/stream"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


def load_config() -> Config:
    """Читает переменные окружения / .env (позже расширим)."""
    return Config()


# === SECTION 3: Настройка логгера ==================================
logger = logging.getLogger("connector")


def setup_logger(level: str) -> None:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=getattr(logging, level.upper(), logging.INFO),
    )


# === SECTION 4: Формирование URL подписки ==========================

def build_stream_url(cfg: Config) -> str:
    """Возвращает полный WS‑URL для подписки на свечи."""
    stream_name = f"{cfg.symbol.lower()}@kline_{cfg.interval}"
    return f"{cfg.ws_url}?streams={stream_name}"


# === SECTION 5: Обработка входящих сообщений =======================
async def handle_message(msg: Dict[str, Any]) -> None:
    """Пока просто выводим цену закрытия в лог."""
    kline = msg.get("k", {})
    if kline.get("x"):  # свеча завершена
        close_price = float(kline["c"])
        logger.info("Close %.2f", close_price)


# === SECTION 6: Основной цикл WebSocket ============================
async def stream_loop(cfg: Config) -> None:
    url = build_stream_url(cfg)
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                logger.info("Подключено к %s", url)
                async for raw in ws:
                    data = json.loads(raw)
                    await handle_message(data.get("data", {}))
        except Exception as exc:  # noqa: BLE001
            logger.warning("WS error: %s. Переподключаюсь через 5 сек", exc)
            await asyncio.sleep(5)


# === SECTION 7: Точка входа ========================================
async def main() -> None:
    cfg = load_config()
    setup_logger(cfg.log_level)
    await stream_loop(cfg)


if __name__ == "__main__":  # SECTION 7.1
    asyncio.run(main())
