# SECTION 0: импорты
import os
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry

# ---------- логирование ----------
from colorlog import ColoredFormatter

LOG_LEVEL = logging.DEBUG
LOGFILE = Path(__file__).with_suffix('.log')

formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    reset=True, log_colors={'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 'ERROR': 'red'}
)

console = logging.StreamHandler()
console.setFormatter(formatter)

file_hdl = logging.FileHandler(LOGFILE, encoding='utf-8')
file_hdl.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logging.basicConfig(level=LOG_LEVEL, handlers=[console, file_hdl])
log = logging.getLogger("Visualizer")

# ---------- SECTION 1 ----------
def load_parquet(file_path: Path) -> pd.DataFrame:
    log.debug("Читаю %s", file_path)
    df = pd.read_parquet(file_path)

    if "open_time" in df.columns:
        df["open_time"] = pd.to_datetime(df["open_time"])
    else:
        df["open_time"] = pd.to_datetime(df.iloc[:, 0])

    df = df.sort_values("open_time").reset_index(drop=True)
    log.debug("Загружено строк: %d", len(df))
    return df

# ---------- SECTION 2 ----------
def parse_period(file_path: Path):
    parts = file_path.stem.split("_")
    if len(parts) < 4:
        return None, None
    try:
        start = datetime.strptime(parts[-2], "%Y%m%d")
        end   = datetime.strptime(parts[-1], "%Y%m%d")
        return start, end
    except ValueError:
        return None, None

# ---------- SECTION 3 ----------
class VisualizerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plotly Chart Viewer")
        self.geometry("420x300")

        # выбор каталога
        self.dir_var = tk.StringVar(value="data/history")
        ttk.Label(self, text="Data folder:").pack(pady=4)
        dir_frame = ttk.Frame(self); dir_frame.pack()
        ttk.Entry(dir_frame, textvariable=self.dir_var, width=40).pack(side=tk.LEFT, padx=2)
        ttk.Button(dir_frame, text="...", command=self.choose_dir).pack(side=tk.LEFT)

        # выбор файла
        self.file_var = tk.StringVar()
        ttk.Label(self, text="Parquet file:").pack(pady=4)
        file_frame = ttk.Frame(self); file_frame.pack()
        self.file_combo = ttk.Combobox(file_frame, textvariable=self.file_var, width=50)
        self.file_combo.pack(padx=2)
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_select)

        # даты
        self.start_date = DateEntry(self, date_pattern="yyyy-mm-dd")
        self.end_date   = DateEntry(self, date_pattern="yyyy-mm-dd")
        ttk.Label(self, text="Start").pack(); self.start_date.pack()
        ttk.Label(self, text="End").pack();   self.end_date.pack()

        ttk.Button(self, text="Show chart", command=self.show_chart).pack(pady=10)

        self.refresh_files()
        log.info("GUI запущен")

    def choose_dir(self):
        folder = filedialog.askdirectory(initialdir=self.dir_var.get())
        if folder:
            self.dir_var.set(folder)
            log.info("Выбрана папка: %s", folder)
            self.refresh_files()

    def refresh_files(self):
        folder = Path(self.dir_var.get())
        if not folder.exists():
            log.error("Папка не существует: %s", folder)
            return
        files = list(folder.glob("*.parquet"))
        log.debug("Найдено parquet: %d", len(files))
        self.file_combo["values"] = [f.name for f in files]
        if files:
            self.file_combo.current(0)
            self.on_file_select()
        else:
            log.warning("В папке %s нет *.parquet", folder)

    def on_file_select(self, *_):
        file_path = Path(self.dir_var.get()) / self.file_var.get()
        start, end = parse_period(file_path)
        if start and end:
            self.start_date.set_date(start)
            self.end_date.set_date(end)
            self.start_date.config(mindate=start, maxdate=end)
            self.end_date.config(mindate=start, maxdate=end)
            log.debug("Диапазон из имени файла: %s — %s", start.date(), end.date())

    def show_chart(self):
        file_path = Path(self.dir_var.get()) / self.file_var.get()
        if not file_path.exists():
            log.error("Файл не найден: %s", file_path)
            messagebox.showerror("File not found", str(file_path))
            return

        try:
            df = load_parquet(file_path)
            mask = (
                df["open_time"] >= pd.to_datetime(self.start_date.get_date())
            ) & (
                df["open_time"] <= pd.to_datetime(self.end_date.get_date())
            )
            df = df.loc[mask]

            if df.empty:
                log.warning("После фильтрации данных нет")
                messagebox.showwarning("No data", "Выбранный диапазон пуст.")
                return

            log.info("Строю график из %d баров", len(df))

            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=("Candlestick", "Volume"),
                row_heights=[0.7, 0.3]
            )
            fig.update_yaxes(fixedrange=False)   # ← добавлено
            fig.update_xaxes(fixedrange=False)   # ← добавлено
            fig.add_trace(
                go.Candlestick(
                    x=df["open_time"],
                    open=df["open"], high=df["high"],
                    low=df["low"], close=df["close"],
                    name="OHLC"
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Bar(
                    x=df["open_time"], y=df["volume"],
                    name="Volume", marker_color="rgba(0,150,255,0.5)"
                ),
                row=2, col=1
            )
            fig.update_layout(title=self.file_var.get(), xaxis_rangeslider_visible=False)
            fig.show()

        except Exception as e:
            log.exception("Ошибка при построении графика: %s", e)
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    VisualizerGUI().mainloop()