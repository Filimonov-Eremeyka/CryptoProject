# SECTION 0: Импорт
import pandas as pd
from pathlib import Path

# SECTION 1: Конвертация CSV → Parquet
def csv_to_parquet(csv_path: str) -> str:
    """
    Конвертирует CSV-файл в Parquet.

    Args:
        csv_path (str): путь к исходному CSV.

    Returns:
        str: путь к созданному Parquet-файлу.
    """
    df = pd.read_csv(csv_path)
    parquet_path = str(Path(csv_path).with_suffix('.parquet'))
    df.to_parquet(parquet_path, index=False)
    print(f"Конвертирован: {csv_path} → {parquet_path}")
    return parquet_path


# SECTION 2: Ресэмплинг 1m → старшие таймфреймы
def resample(symbol: str, tf: str) -> str:
    """
    Ресэмплирует 1-минутный Parquet в заданный таймфрейм.

    Args:
        symbol (str): символ, например 'SOLUSDTUSDT'.
        tf (str): целевой таймфрейм ('5m', '15m', '30m', '1h', '4h', '1d').

    Returns:
        str: путь к созданному Parquet-файлу.
    """
    # путь к исходному 1-минутному файлу
    base_path = Path("data/history")
    src = base_path / f"{symbol}_1m.parquet"
    if not src.exists():
        raise FileNotFoundError(src)

    df = pd.read_parquet(src)

    # убеждаемся, что индекс — datetime
    if 'open_time' in df.columns:
        df['open_time'] = pd.to_datetime(df['open_time'])
        df = df.set_index('open_time')

    # словарь таймфреймов
    tf_map = {
        '5m': '5T',
        '15m': '15T',
        '30m': '30T',
        '1h': '1H',
        '4h': '4H',
        '1d': '1D',
    }
    if tf not in tf_map:
        raise ValueError(f"Неподдерживаемый таймфрейм: {tf}")

    # правила агрегации OHLCV
    agg = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
    }

    resampled = (
        df[list(agg.keys())]
        .resample(tf_map[tf])
        .agg(agg)
        .dropna()
        .reset_index()
    )

    dst = base_path / f"{symbol}_{tf}.parquet"
    resampled.to_parquet(dst, index=False)
    print(f"Создан файл: {dst}")
    return str(dst)