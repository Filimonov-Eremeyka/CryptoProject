# CryptoProject
# Binance WebSocket High-Performance Connector

Высокопроизводительный коннектор для получения реальных рыночных данных с Binance WebSocket API с минимальной задержкой для интеграции с MetaTrader 5.

## 🚀 Особенности

- **Минимальная задержка** (<100ms при оптимальном расположении сервера)
- **Автоматическое переподключение** при обрыве соединения
- **Два способа интеграции**: файловый вывод и HTTP API
- **Оптимизация для MT5**: простые форматы JSON/CSV для MQL5
- **Мониторинг состояния** через HTTP endpoints
- **Docker поддержка** для простого развертывания

## 📁 Структура проекта

```
binance-connector/
├── config.py          # Конфигурация
├── main.py            # Основная логика WebSocket
├── api.py             # FastAPI HTTP сервер
├── requirements.txt   # Python зависимости
├── Dockerfile         # Docker образ
├── docker-compose.yml # Docker Compose
├── run.sh            # Скрипт запуска
└── README.md         # Документация
```

## ⚡ Быстрый старт

### Способ 1: Python (рекомендуется для разработки)

```bash
# Клонирование и переход в директорию
git clone <repository-url>
cd binance-connector

# Запуск с автоматической установкой
chmod +x run.sh
./run.sh btcusdt 1m
```

### Способ 2: Docker (рекомендуется для продакшна)

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Способ 3: Ручная установка

```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск
python main.py
```

## 🔧 Конфигурация

Основные настройки в `config.py`:

```python
# Торговая пара и интервал
SYMBOL = "btcusdt"      # или через переменную окружения
INTERVAL = "1m"         # 1s, 1m, 3m, 5m, 15m, 30m, 1h, etc.

# Файловый вывод
ENABLE_FILE_OUTPUT = True
OUTPUT_FILE = "ohlcv_data.json"
OUTPUT_FORMAT = "json"  # "json" или "csv"

# HTTP сервер
ENABLE_HTTP_SERVER = True
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8888

