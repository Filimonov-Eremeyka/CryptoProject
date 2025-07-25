# indicators/polus_x.py
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Tuple

# ----------------- вспомогательные функции -----------------
def _find_volume_minimum(df: pd.DataFrame, center: int) -> int:
    """Возвращает индекс локального минимума объёма или -1."""
    if center <= 0 or center >= len(df) - 1:
        return -1
    vol = df['volume'].values
    if vol[center - 1] > vol[center] < vol[center + 1]:
        return center
    return -1

# ----------------- основной класс -----------------
class PolusX:
    """
    Класс-обёртка для индикатора PolusX.
    Принимает DataFrame с колонками:
    open, high, low, close, volume (и open_time как индекс или колонка)
    """
    def __init__(self,
                 use_tick_volume: bool = True,
                 show_lines: bool = True,
                 ind1: bool = True,
                 ind2: bool = True,
                 ind3: bool = True):
        self.use_tick_volume = use_tick_volume
        self.show_lines = show_lines
        self.ind1 = ind1
        self.ind2 = ind2
        self.ind3 = ind3

    # ---------- индикатор-1 ----------
    def _calc_ind1(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        high = df['high'].values
        low = df['low'].values
        vol = df['volume' if not self.use_tick_volume else 'tick_volume'].values

        max_arr = np.zeros(len(df)) * np.nan
        min_arr = np.zeros(len(df)) * np.nan

        max_val = min_val = 0
        last_dj = 0
        for i in range(len(df)):
            if np.isnan(max_val) or max_val == 0:
                max_val = high[i]
                min_val = low[i]
                continue

            local_dj = _find_volume_minimum(df, i)
            if local_dj != -1:
                last_dj = local_dj

            if high[i] >= max_val and last_dj < len(df):
                min_val = low[last_dj]

            if i < len(df) - 1 and df['close'].iat[i + 1] < min_val and last_dj < len(df):
                max_val = high[i + 1]
                min_val = low[last_dj]

            if i < len(df) - 1 and high[i + 1] >= max_val:
                max_val = high[i + 1]

            max_arr[i] = max_val if self.show_lines else np.nan
            min_arr[i] = min_val

        return max_arr, min_arr

    # ---------- индикатор-2 ----------
    def _calc_ind2(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        high = df['high'].values
        low = df['low'].values
        vol = df['volume' if not self.use_tick_volume else 'tick_volume'].values

        max_arr = np.zeros(len(df)) * np.nan
        min_arr = np.zeros(len(df)) * np.nan

        max2 = min2 = 0
        dj = 0
        for i in range(len(df)):
            if np.isnan(max2) or max2 == 0:
                max2 = high[i]
                min2 = low[i]
                continue

            if i > 0 and i < len(df) - 1:
                if vol[i - 1] > vol[i] < vol[i + 1]:
                    dj = i

            if low[i] <= min2 and dj < len(df):
                max2 = high[dj]

            if i < len(df) - 1 and df['close'].iat[i + 1] > max2 and dj < len(df):
                min2 = low[i + 1]
                max2 = high[dj]

            if i < len(df) - 1 and low[i + 1] <= min2:
                min2 = low[i + 1]

            max_arr[i] = max2
            min_arr[i] = min2 if self.show_lines else np.nan

        return max_arr, min_arr

    # ---------- индикатор-3 ----------
    def _calc_ind3(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        vol = df['volume' if not self.use_tick_volume else 'tick_volume'].values

        max3_arr = np.zeros(len(df)) * np.nan
        min3_arr = np.zeros(len(df)) * np.nan
        cl_arr = np.zeros(len(df)) * np.nan

        for i in range(1, len(df) - 1):
            if vol[i - 1] > vol[i] < vol[i + 1]:
                max3_arr[i] = high[i]
                min3_arr[i] = low[i]
                cl_arr[i] = close[i - 1]

        return max3_arr, min3_arr, cl_arr

    # ---------- публичный метод ----------
    def add_to_figure(self, df: pd.DataFrame, fig, row=1, col=1):
        """Добавляет все включённые линии в существующий subplot."""
        if self.ind1:
            high1, min1 = self._calc_ind1(df)
            fig.add_trace(go.Scatter(
                x=df['open_time'], y=high1,
                line=dict(color='limegreen', width=1, dash='dot'),
                name='PolusHigh'), row=row, col=col)
            fig.add_trace(go.Scatter(
                x=df['open_time'], y=min1,
                line=dict(color='red', width=2),
                name='PolusMin'), row=row, col=col)

        if self.ind2:
            max2, min2 = self._calc_ind2(df)
            fig.add_trace(go.Scatter(
                x=df['open_time'], y=max2,
                line=dict(color='aqua', width=2),
                name='PolusMax'), row=row, col=col)
            if self.show_lines:
                fig.add_trace(go.Scatter(
                    x=df['open_time'], y=min2,
                    line=dict(color='magenta', width=1, dash='dot'),
                    name='PolusLow'), row=row, col=col)

        if self.ind3:
            max3, min3, cl = self._calc_ind3(df)
            fig.add_trace(go.Scatter(
                x=df['open_time'], y=max3,
                line=dict(color='steelblue', width=1),
                name='PolusUp'), row=row, col=col)
            fig.add_trace(go.Scatter(
                x=df['open_time'], y=min3,
                line=dict(color='orangered', width=1),
                name='PolusDn'), row=row, col=col)
            fig.add_trace(go.Scatter(
                x=df['open_time'], y=cl,
                line=dict(color='gold', width=1),
                name='PAnvar'), row=row, col=col)