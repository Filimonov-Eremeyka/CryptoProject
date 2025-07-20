import pandas as pd
import os
from pathlib import Path

def csv_to_parquet(csv_path):
    """
    Конвертирует CSV файл в Parquet формат.
    
    Args:
        csv_path (str): Путь к CSV файлу
    
    Returns:
        str: Путь к созданному Parquet файлу
    """
    # Читаем CSV
    df = pd.read_csv(csv_path)
    
    # Создаем путь для parquet файла
    parquet_path = csv_path.replace('.csv', '.parquet')
    
    # Сохраняем в parquet
    df.to_parquet(parquet_path, index=False)
    
    print(f"Конвертирован: {csv_path} -> {parquet_path}")
    return parquet_path

def resample(symbol, tf):
    """
    Ресэмплирует данные 1m в указанный таймфрейм.
    
    Args:
        symbol (str): Символ (например, 'SOLUSDTUSDT')
        tf (str): Таймфрейм ('5m', '15m', '1h')
    
    Returns:
        str: Путь к созданному файлу
    """
    # Путь к исходному файлу 1m
    base_path = Path("backtest/data/history")
    input_path = base_path / f"{symbol}_1m.parquet"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Файл {input_path} не найден")
    
    # Читаем данные
    df = pd.read_parquet(input_path)
    
    # ИСПРАВЛЕНИЕ: Правильно обрабатываем timestamp
    if 'timestamp' in df.columns:
        # Если timestamp в миллисекундах, конвертируем в datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
    else:
        # Если первая колонка - timestamp (альтернативный случай)
        timestamp_col = df.columns[0]
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        df.set_index(timestamp_col, inplace=True)
    
    # Мапинг таймфреймов для pandas
    tf_mapping = {
        '5m': '5T',
        '15m': '15T', 
        '1h': '1H'
    }
    
    if tf not in tf_mapping:
        raise ValueError(f"Неподдерживаемый таймфрейм: {tf}")
    
    # Ресэмплинг OHLCV данных
    ohlc_agg = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    
    # Находим колонки для агрегации
    agg_dict = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'open' in col_lower:
            agg_dict[col] = 'first'
        elif 'high' in col_lower:
            agg_dict[col] = 'max'
        elif 'low' in col_lower:
            agg_dict[col] = 'min'
        elif 'close' in col_lower:
            agg_dict[col] = 'last'
        elif 'volume' in col_lower:
            agg_dict[col] = 'sum'
        else:
            agg_dict[col] = 'last'  # для остальных колонок
    
    # Выполняем ресэмплинг
    resampled_df = df.resample(tf_mapping[tf]).agg(agg_dict)
    
    # Убираем NaN строки
    resampled_df = resampled_df.dropna()
    
    # Сохраняем результат
    output_path = base_path / f"{symbol}_{tf}.parquet"
    resampled_df.reset_index().to_parquet(output_path, index=False)
    
    print(f"Создан файл: {output_path}")
    return str(output_path)