"""
Модуль визуализации исторических данных криптовалютных пар.

Функциональность:
- Загрузка данных из .parquet файлов
- Построение свечных графиков (OHLC/Candlestick)
- Сохранение графиков в PNG
- Поддержка различных таймфреймов
- Готовность к расширению индикаторами

Автор: Crypto Trading System
Дата: 2025
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import numpy as np

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CandlestickVisualizer:
    """Класс для визуализации свечных графиков криптовалютных пар."""
    
    def __init__(self, data_path: str = "backtest/data/history/", output_path: str = "backtest/plots/"):
        """
        Инициализация визуализатора.
        
        Args:
            data_path: Путь к директории с .parquet файлами
            output_path: Путь для сохранения PNG файлов
        """
        self.data_path = data_path
        self.output_path = output_path
        
        # Создаем директорию для сохранения графиков если её нет
        os.makedirs(output_path, exist_ok=True)
        
        # Настройка стиля matplotlib
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        
    def load_data(self, symbol: str, timeframe: str, 
                  start_date: Optional[datetime] = None, 
                  end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Загрузка данных из .parquet файла.
        
        Args:
            symbol: Символ пары (например, 'SOLUSDTUSDT')
            timeframe: Таймфрейм (например, '1m', '5m', '15m', '1h')
            start_date: Дата начала (опционально)
            end_date: Дата окончания (опционально)
            
        Returns:
            DataFrame с историческими данными
        """
        filename = f"{symbol}_{timeframe}.parquet"
        filepath = os.path.join(self.data_path, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        
        try:
            # Загружаем данные
            df = pd.read_parquet(filepath)
            logger.info(f"Загружено {len(df)} записей из {filename}")
            
            # Проверяем наличие необходимых колонок
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Отсутствуют обязательные колонки: {missing_columns}")
            
            # Преобразуем timestamp в datetime
            if df['timestamp'].dtype == 'object':
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            elif df['timestamp'].dtype in ['int64', 'float64']:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Сортируем по времени
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Фильтруем по датам если указаны
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
            
            # Проверяем достаточность данных
            if len(df) < 2:
                raise ValueError(f"Недостаточно данных для построения графика: {len(df)} записей")
            
            logger.info(f"Данные после фильтрации: {len(df)} записей")
            logger.info(f"Период: {df['timestamp'].min()} - {df['timestamp'].max()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных из {filepath}: {str(e)}")
            raise
    
    def create_candlestick_chart(self, df: pd.DataFrame, symbol: str, timeframe: str,
                               title: Optional[str] = None, figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
        """
        Создание свечного графика.
        
        Args:
            df: DataFrame с данными OHLC
            symbol: Символ пары
            timeframe: Таймфрейм
            title: Заголовок графика (опционально)
            figsize: Размер фигуры
            
        Returns:
            Figure объект matplotlib
        """
        # Создаем фигуру и оси
        fig, ax = plt.subplots(figsize=figsize)
        
        # Определяем цвета для свечей
        up_color = '#00ff00'    # Зеленый для растущих свечей
        down_color = '#ff0000'  # Красный для падающих свечей
        
        # Рассчитываем ширину свечи в зависимости от таймфрейма
        timeframe_minutes = self._get_timeframe_minutes(timeframe)
        candle_width = pd.Timedelta(minutes=timeframe_minutes * 0.8)
        
        # Отрисовываем свечи
        for i, row in df.iterrows():
            timestamp = row['timestamp']
            open_price = row['open']
            high_price = row['high']
            low_price = row['low']
            close_price = row['close']
            
            # Определяем цвет свечи
            color = up_color if close_price >= open_price else down_color
            
            # Рисуем тень (high-low line)
            ax.plot([timestamp, timestamp], [low_price, high_price], 
                   color=color, linewidth=1, alpha=0.8)
            
            # Рисуем тело свечи
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            if body_height > 0:  # Избегаем нулевой высоты
                rect = Rectangle((timestamp - candle_width/2, body_bottom),
                               candle_width, body_height,
                               facecolor=color, edgecolor=color, alpha=0.8)
                ax.add_patch(rect)
            else:
                # Для доджи (open == close) рисуем тонкую линию
                ax.plot([timestamp - candle_width/2, timestamp + candle_width/2],
                       [open_price, open_price], color=color, linewidth=2)
        
        # Настройка осей
        ax.set_xlabel('Время', fontsize=12)
        ax.set_ylabel('Цена (USDT)', fontsize=12)
        
        # Форматирование оси времени
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, len(df) // 20)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Заголовок
        if not title:
            start_date = df['timestamp'].min().strftime('%Y-%m-%d %H:%M')
            end_date = df['timestamp'].max().strftime('%Y-%m-%d %H:%M')
            title = f"{symbol} - {timeframe} | {start_date} - {end_date}"
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Сетка
        ax.grid(True, alpha=0.3)
        
        # Статистика в углу
        self._add_stats_box(ax, df)
        
        # Подгонка макета
        plt.tight_layout()
        
        return fig
    
    def _get_timeframe_minutes(self, timeframe: str) -> int:
        """Получение количества минут для таймфрейма."""
        timeframe_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
        return timeframe_map.get(timeframe, 1)
    
    def _add_stats_box(self, ax: plt.Axes, df: pd.DataFrame):
        """Добавление статистики на график."""
        # Рассчитываем основные статистики
        current_price = df['close'].iloc[-1]
        high_price = df['high'].max()
        low_price = df['low'].min()
        volume_avg = df['volume'].mean()
        
        # Изменение цены
        price_change = current_price - df['close'].iloc[0]
        price_change_pct = (price_change / df['close'].iloc[0]) * 100
        
        # Текст со статистикой
        stats_text = f"""Текущая цена: ${current_price:.4f}
Максимум: ${high_price:.4f}
Минимум: ${low_price:.4f}
Изменение: {price_change:+.4f} ({price_change_pct:+.2f}%)
Средний объем: {volume_avg:.0f}"""
        
        # Добавляем текстовое поле
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='lightgray', alpha=0.8), fontsize=9)
    
    def save_chart(self, fig: plt.Figure, symbol: str, timeframe: str, 
                   suffix: str = "") -> str:
        """
        Сохранение графика в PNG файл.
        
        Args:
            fig: Figure объект matplotlib
            symbol: Символ пары
            timeframe: Таймфрейм
            suffix: Дополнительный суффикс для имени файла
            
        Returns:
            Путь к сохраненному файлу
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{timeframe}{suffix}_{timestamp}.png"
        filepath = os.path.join(self.output_path, filename)
        
        try:
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"График сохранен: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Ошибка при сохранении графика: {str(e)}")
            raise
    
    def visualize(self, symbol: str, timeframe: str, 
                  start_date: Optional[datetime] = None, 
                  end_date: Optional[datetime] = None,
                  save_to_file: bool = True, 
                  show_plot: bool = True,
                  title: Optional[str] = None) -> Optional[str]:
        """
        Основная функция для визуализации данных.
        
        Args:
            symbol: Символ пары
            timeframe: Таймфрейм
            start_date: Дата начала
            end_date: Дата окончания
            save_to_file: Сохранять ли файл
            show_plot: Отображать ли график
            title: Заголовок графика
            
        Returns:
            Путь к сохраненному файлу или None
        """
        try:
            # Загружаем данные
            df = self.load_data(symbol, timeframe, start_date, end_date)
            
            # Создаем график
            fig = self.create_candlestick_chart(df, symbol, timeframe, title)
            
            # Сохраняем файл
            filepath = None
            if save_to_file:
                filepath = self.save_chart(fig, symbol, timeframe)
            
            # Отображаем график
            if show_plot:
                plt.show()
            else:
                plt.close(fig)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Ошибка при визуализации {symbol}_{timeframe}: {str(e)}")
            return None

# Удобные функции для быстрого использования
def quick_visualize(symbol: str, timeframe: str, days_back: int = 7) -> Optional[str]:
    """
    Быстрая визуализация последних N дней.
    
    Args:
        symbol: Символ пары
        timeframe: Таймфрейм
        days_back: Количество дней назад
        
    Returns:
        Путь к сохраненному файлу
    """
    visualizer = CandlestickVisualizer()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    return visualizer.visualize(symbol, timeframe, start_date, end_date)

def batch_visualize(symbols: List[str], timeframes: List[str], 
                   days_back: int = 7) -> List[str]:
    """
    Пакетная визуализация нескольких пар и таймфреймов.
    
    Args:
        symbols: Список символов
        timeframes: Список таймфреймов
        days_back: Количество дней назад
        
    Returns:
        Список путей к сохраненным файлам
    """
    visualizer = CandlestickVisualizer()
    results = []
    
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                filepath = quick_visualize(symbol, timeframe, days_back)
                if filepath:
                    results.append(filepath)
            except Exception as e:
                logger.error(f"Ошибка при обработке {symbol}_{timeframe}: {str(e)}")
                continue
    
    return results

if __name__ == "__main__":
    # Пример использования
    visualizer = CandlestickVisualizer()
    
    # Визуализация SOLUSDTUSDT за последние 3 дня
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        filepath = visualizer.visualize(
            symbol="SOLUSDTUSDT",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date,
            save_to_file=True,
            show_plot=True
        )
        
        if filepath:
            print(f"График сохранен: {filepath}")
        else:
            print("Ошибка при создании графика")
            
    except Exception as e:
        print(f"Ошибка: {str(e)}")