# SECTION 0: импорты
import os
from datetime import datetime, timedelta
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tkinter as tk
from tkinter import ttk, filedialog
from tkcalendar import DateEntry


# SECTION 1: чтение parquet
def load_parquet(file_path):
    import pandas as pd
    df = pd.read_parquet(file_path)
    # убеждаемся, что время datetime
    if "open_time" in df.columns:
        df["open_time"] = pd.to_datetime(df["open_time"])
    else:
        df["open_time"] = pd.to_datetime(df.iloc[:, 0])
    return df.sort_values("open_time")


# SECTION 2: извлечение периода из имени файла
def parse_period(file_path):
    """
    Ожидаем формат: SYMBOL_TF_YYYYMMDD_YYYYMMDD.parquet
    Возвращает (start_dt, end_dt)
    """
    parts = Path(file_path).stem.split("_")
    if len(parts) < 4:
        return None, None
    try:
        start = datetime.strptime(parts[-2], "%Y%m%d")
        end = datetime.strptime(parts[-1], "%Y%m%d")
        return start, end
    except ValueError:
        return None, None


# SECTION 3: GUI
class VisualizerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plotly Chart Viewer")
        self.geometry("420x300")

        # выбор каталога
        self.dir_var = tk.StringVar()
        ttk.Label(self, text="Data folder:").pack(pady=4)
        dir_frame = ttk.Frame(self)
        dir_frame.pack()
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=40).pack(side=tk.LEFT, padx=2)
        ttk.Button(dir_frame, text="...", command=self.choose_dir).pack(side=tk.LEFT)

        # выбор файла
        self.file_var = tk.StringVar()
        ttk.Label(self, text="Parquet file:").pack(pady=4)
        file_frame = ttk.Frame(self)
        file_frame.pack()
        self.file_combo = ttk.Combobox(file_frame, textvariable=self.file_var, width=50)
        self.file_combo.pack(padx=2)

        # даты (ограничены диапазоном файла)
        self.start_date = DateEntry(self, date_pattern="yyyy-mm-dd")
        self.end_date   = DateEntry(self, date_pattern="yyyy-mm-dd")
        ttk.Label(self, text="Start").pack()
        self.start_date.pack()
        ttk.Label(self, text="End").pack()
        self.end_date.pack()

        ttk.Button(self, text="Show chart", command=self.show_chart).pack(pady=10)

        # инициализируем
        self.dir_var.set("data/history")
        self.refresh_files()

    def choose_dir(self):
        folder = filedialog.askdirectory(initialdir=self.dir_var.get())
        if folder:
            self.dir_var.set(folder)
            self.refresh_files()

    def refresh_files(self):
        folder = Path(self.dir_var.get())
        files = [f.name for f in folder.glob("*.parquet")]
        self.file_combo["values"] = files
        if files:
            self.file_combo.current(0)
            self.on_file_select()

    def on_file_select(self, *args):
        file_path = Path(self.dir_var.get()) / self.file_var.get()
        start, end = parse_period(file_path)
        if start and end:
            self.start_date.set_date(start)
            self.end_date.set_date(end)
            self.start_date.config(mindate=start, maxdate=end)
            self.end_date.config(mindate=start, maxdate=end)

    def show_chart(self):
        file_path = Path(self.dir_var.get()) / self.file_var.get()
        df = load_parquet(file_path)

        # фильтрация по выбранному диапазону
        mask = (df["open_time"] >= pd.to_datetime(self.start_date.get_date())) & \
               (df["open_time"] <= pd.to_datetime(self.end_date.get_date()))
        df = df.loc[mask]

        if df.empty:
            tk.messagebox.showwarning("No data", "Выбранный диапазон пуст.")
            return

        # Plotly-chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.05,
                            subplot_titles=("Candlestick", "Volume"),
                            row_heights=[0.7, 0.3])

        fig.add_trace(go.Candlestick(
            x=df["open_time"],
            open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            name="OHLC"
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            x=df["open_time"], y=df["volume"],
            name="Volume", marker_color="rgba(0,150,255,0.5)"
        ), row=2, col=1)

        fig.update_layout(title=self.file_var.get(), xaxis_rangeslider_visible=False)
        fig.show()


if __name__ == "__main__":
    VisualizerGUI().mainloop()