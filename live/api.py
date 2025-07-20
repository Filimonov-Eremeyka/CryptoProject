from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import time

def create_app(connector) -> FastAPI:
    """Создание FastAPI приложения с инжекцией коннектора"""
    
    app = FastAPI(
        title="Binance WebSocket Connector API",
        description="High-performance real-time crypto data API for MetaTrader 5",
        version="1.0.0"
    )
    
    @app.get("/")
    async def root():
        """Информация об API"""
        return {
            "service": "Binance WebSocket Connector",
            "version": "1.0.0",
            "status": "running" if connector.is_running else "stopped",
            "symbol": connector.config.SYMBOL.upper(),
            "interval": connector.config.INTERVAL,
            "endpoints": {
                "ohlcv": "/ohlcv",
                "health": "/health",
                "status": "/status"
            }
        }
    
    @app.get("/ohlcv")
    async def get_ohlcv():
        """
        Получение последних OHLCV данных
        Оптимизированный endpoint для MQL5 WebRequest
        """
        try:
            candle = connector.get_latest_candle()
            
            if not candle:
                raise HTTPException(
                    status_code=404, 
                    detail="No data available yet"
                )
            
            # Упрощенный формат для максимальной скорости парсинга в MQL5
            response_data = {
                "timestamp": candle["timestamp"],
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "volume": candle["volume"],
                "is_closed": candle["is_closed"],
                "server_time": int(time.time() * 1000)  # время сервера для измерения задержки
            }
            
            return JSONResponse(
                content=response_data,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "Access-Control-Allow-Origin": "*"
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/ohlcv/csv")
    async def get_ohlcv_csv():
        """
        Получение OHLCV данных в CSV формате
        Альтернативный endpoint для простого парсинга
        """
        try:
            candle = connector.get_latest_candle()
            
            if not candle:
                raise HTTPException(
                    status_code=404, 
                    detail="No data available yet"
                )
            
            # CSV строка: timestamp,open,high,low,close,volume
            csv_data = f"{candle['timestamp']},{candle['open']},{candle['high']},{candle['low']},{candle['close']},{candle['volume']}"
            
            return JSONResponse(
                content={"csv": csv_data},
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Access-Control-Allow-Origin": "*"
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        """Проверка здоровья сервиса"""
        candle = connector.get_latest_candle()
        current_time = int(time.time() * 1000)
        
        # Проверяем актуальность данных (не старше 2 минут)
        data_age = None
        is_data_fresh = False
        
        if candle:
            data_age = current_time - candle["timestamp"]
            is_data_fresh = data_age < 120000  # 2 минуты в миллисекундах
        
        status = "healthy" if (connector.is_running and is_data_fresh) else "unhealthy"
        
        return {
            "status": status,
            "websocket_connected": connector.is_running,
            "last_data_timestamp": candle["timestamp"] if candle else None,
            "data_age_ms": data_age,
            "is_data_fresh": is_data_fresh,
            "reconnect_count": connector.reconnect_count,
            "server_time": current_time
        }
    
    @app.get("/status")
    async def get_status():
        """Подробная информация о статусе коннектора"""
        candle = connector.get_latest_candle()
        
        return {
            "connector": {
                "running": connector.is_running,
                "reconnect_count": connector.reconnect_count,
                "symbol": connector.config.SYMBOL.upper(),
                "interval": connector.config.INTERVAL
            },
            "latest_candle": {
                "available": candle is not None,
                "data": candle if candle else None
            },
            "config": {
                "file_output": connector.config.ENABLE_FILE_OUTPUT,
                "output_file": connector.config.OUTPUT_FILE,
                "output_format": connector.config.OUTPUT_FORMAT
            },
            "server_time": int(time.time() * 1000)
        }
    
    @app.get("/ping")
    async def ping():
        """Быстрый ping endpoint для измерения задержки"""
        return {
            "pong": int(time.time() * 1000)
        }
    
    return app