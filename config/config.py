import os
from typing import Optional
from dotenv import load_dotenv

# Загружаем .env переменные в окружение
load_dotenv()

class Config:
    """Конфигурация для Binance WebSocket коннектора"""

    # Тип рынка: spot или futures
    MARKET_TYPE = os.getenv("MARKET_TYPE", "spot")

    # WebSocket настройки
    BINANCE_WS_URL_SPOT = "wss://stream.binance.com:9443/ws"
    BINANCE_WS_URL_FUTURES = "wss://fstream.binance.com/ws"
    SYMBOL = os.getenv("SYMBOL", "btcusdt")  # торговая пара
    INTERVAL = os.getenv("INTERVAL", "1m")   # интервал свечей

    # Настройки переподключения
    RECONNECT_DELAY = 5  # секунд между попытками переподключения
    MAX_RECONNECT_ATTEMPTS = 10  # максимум попыток
    PING_INTERVAL = 20  # интервал пинга в секундах
    PING_TIMEOUT = 10   # таймаут пинга

    # Файловый вывод
    ENABLE_FILE_OUTPUT = True
    OUTPUT_FILE = "ohlcv_data.json"  # или .csv
    OUTPUT_FORMAT = "json"  # "json" или "csv"

    # HTTP API сервер
    ENABLE_HTTP_SERVER = True
    HTTP_HOST = "127.0.0.1"
    HTTP_PORT = int(os.getenv("API_PORT", 8888))

    # Логирование
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
    LOG_FILE = "binance_connector.log"

    # Производительность
    BUFFER_SIZE = 1024 * 16  # размер буфера WebSocket
    WRITE_BUFFER_SIZE = 1024 * 8  # буфер записи в файл

    @classmethod
    def get_ws_url(cls) -> str:
        """Генерирует URL для WebSocket подключения"""
        base_url = (
            cls.BINANCE_WS_URL_FUTURES
            if cls.MARKET_TYPE.lower() == "futures"
            else cls.BINANCE_WS_URL_SPOT
        )
        stream_name = f"{cls.SYMBOL.lower()}@kline_{cls.INTERVAL}"
        return f"{base_url}/{stream_name}"

    @classmethod
    def validate(cls) -> bool:
        """Валидация конфигурации"""
        valid_intervals = [
            '1s', '1m', '3m', '5m', '15m', '30m', '1h',
            '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'
        ]
        if cls.INTERVAL not in valid_intervals:
            raise ValueError(
                f"Недопустимый интервал: {cls.INTERVAL}. "
                f"Доступные: {valid_intervals}"
            )

        if cls.OUTPUT_FORMAT not in ['json', 'csv']:
            raise ValueError(
                f"Недопустимый формат вывода: {cls.OUTPUT_FORMAT}"
            )

        return True
