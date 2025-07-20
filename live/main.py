import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Optional
import csv
import io

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from config import Config

class BinanceConnector:
    """Высокопроизводительный коннектор к Binance WebSocket API"""
    
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        self.websocket = None
        self.latest_candle: Optional[Dict] = None
        self.is_running = False
        self.reconnect_count = 0
        
        # Настройка логирования
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Буферы для оптимизации записи
        self.write_buffer = io.StringIO()
        
    def setup_logging(self):
        """Настройка системы логирования"""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    async def connect(self) -> bool:
        """Подключение к WebSocket"""
        try:
            self.logger.info(f"Подключение к {self.config.get_ws_url()}")
            
            # Настройки для минимальной задержки
            self.websocket = await websockets.connect(
    self.config.get_ws_url(),
    ping_interval=self.config.PING_INTERVAL,
    ping_timeout=self.config.PING_TIMEOUT,
    max_size=2**20,  # 1MB буфер
    compression=None,
)

            
            self.logger.info("WebSocket подключение установлено")
            self.reconnect_count = 0
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка подключения: {e}")
            return False
    
    def parse_kline_data(self, message: Dict) -> Optional[Dict]:
        """Парсинг данных свечи из WebSocket сообщения"""
        try:
            if 'k' not in message:
                return None
                
            kline = message['k']
            
            # Извлекаем только необходимые данные
            candle_data = {
                'timestamp': int(kline['t']),  # время открытия свечи
                'datetime': datetime.fromtimestamp(int(kline['t']) / 1000).isoformat(),
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v']),
                'is_closed': kline['x'],  # завершена ли свеча
                'symbol': kline['s'],
                'interval': kline['i']
            }
            
            return candle_data
            
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Ошибка парсинга данных: {e}")
            return None
    
    def write_to_file(self, candle_data: Dict):
        """Быстрая запись данных в файл"""
        if not self.config.ENABLE_FILE_OUTPUT:
            return
            
        try:
            if self.config.OUTPUT_FORMAT == 'json':
                # JSON формат для MQL5
                with open(self.config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(candle_data, f, separators=(',', ':'))
                    
            elif self.config.OUTPUT_FORMAT == 'csv':
                # CSV формат
                with open(self.config.OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        candle_data['timestamp'],
                        candle_data['open'],
                        candle_data['high'],
                        candle_data['low'],
                        candle_data['close'],
                        candle_data['volume']
                    ])
                    
        except IOError as e:
            self.logger.error(f"Ошибка записи в файл: {e}")
    
    async def handle_message(self, message: str):
        """Обработка входящего сообщения"""
        try:
            # Быстрый парсинг JSON
            data = json.loads(message)
            
            # Парсинг данных свечи
            candle_data = self.parse_kline_data(data)
            if not candle_data:
                return
            
            # Обновляем последние данные в памяти
            self.latest_candle = candle_data
            
            # Запись в файл (асинхронно)
            if self.config.ENABLE_FILE_OUTPUT:
                asyncio.create_task(asyncio.to_thread(self.write_to_file, candle_data))
            
            # Логируем только завершенные свечи для уменьшения спама
            if candle_data['is_closed']:
                self.logger.info(
                    f"Новая свеча {candle_data['symbol']}: "
                    f"O={candle_data['open']:.8f} H={candle_data['high']:.8f} "
                    f"L={candle_data['low']:.8f} C={candle_data['close']:.8f} "
                    f"V={candle_data['volume']:.2f}"
                )
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def listen(self):
        """Основной цикл прослушивания WebSocket"""
        try:
            async for message in self.websocket:
                if not self.is_running:
                    break
                await self.handle_message(message)
                
        except ConnectionClosed:
            self.logger.warning("WebSocket соединение закрыто")
        except WebSocketException as e:
            self.logger.error(f"Ошибка WebSocket: {e}")
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка: {e}")
    
    async def reconnect(self) -> bool:
        """Логика переподключения"""
        while self.reconnect_count < self.config.MAX_RECONNECT_ATTEMPTS:
            self.reconnect_count += 1
            self.logger.info(f"Попытка переподключения {self.reconnect_count}/{self.config.MAX_RECONNECT_ATTEMPTS}")
            
            await asyncio.sleep(self.config.RECONNECT_DELAY)
            
            if await self.connect():
                return True
                
        self.logger.error("Превышен лимит попыток переподключения")
        return False
    
    async def run(self):
        """Главный цикл работы коннектора"""
        self.is_running = True
        self.logger.info(f"Запуск коннектора для {self.config.SYMBOL.upper()}, интервал {self.config.INTERVAL}")
        
        while self.is_running:
            # Подключение
            if not await self.connect():
                if not await self.reconnect():
                    break
                continue
            
            # Прослушивание
            try:
                await self.listen()
            except Exception as e:
                self.logger.error(f"Ошибка в основном цикле: {e}")
            
            # Переподключение при обрыве
            if self.is_running:
                self.logger.info("Соединение потеряно, переподключение...")
                if not await self.reconnect():
                    break
    
    def stop(self):
        """Остановка коннектора"""
        self.logger.info("Остановка коннектора...")
        self.is_running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
    
    def get_latest_candle(self) -> Optional[Dict]:
        """Получение последних данных свечи"""
        return self.latest_candle


async def main():
    """Главная функция"""
    connector = BinanceConnector()
    
    # Обработка сигналов для корректного завершения
    def signal_handler(signum, frame):
        print("\nПолучен сигнал завершения...")
        connector.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Запуск HTTP сервера (если включен)
        if connector.config.ENABLE_HTTP_SERVER:
            from api import create_app
            app = create_app(connector)
            
            # Запуск сервера в отдельной задаче
            import uvicorn
            server_config = uvicorn.Config(
                app=app,
                host=connector.config.HTTP_HOST,
                port=connector.config.HTTP_PORT,
                log_level="warning"
            )
            server = uvicorn.Server(server_config)
            server_task = asyncio.create_task(server.serve())
            
            # Запуск коннектора
            connector_task = asyncio.create_task(connector.run())
            
            # Ожидание завершения любой задачи
            await asyncio.gather(connector_task, server_task, return_exceptions=True)
        else:
            # Только коннектор
            await connector.run()
            
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
    finally:
        connector.stop()


if __name__ == "__main__":
    asyncio.run(main())