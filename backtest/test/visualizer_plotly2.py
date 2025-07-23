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
        self.geometry("450x400")

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

        # новые опции для интерактивности
        self.options_frame = ttk.LabelFrame(self, text="Chart Options", padding=10)
        self.options_frame.pack(pady=10, padx=10, fill="x")

        # ---------- блок настроек PolusX ----------
        polus_frame = ttk.LabelFrame(self, text="PolusX Indicator", padding=10)
        polus_frame.pack(pady=5, padx=10, fill="x")

        self.polus_ind1 = tk.BooleanVar(value=True)
        self.polus_ind2 = tk.BooleanVar(value=True)
        self.polus_ind3 = tk.BooleanVar(value=True)
        self.polus_lines = tk.BooleanVar(value=True)

        ttk.Checkbutton(polus_frame, text="IND1 (min/max)", variable=self.polus_ind1).pack(anchor="w")
        ttk.Checkbutton(polus_frame, text="IND2 (max/min)", variable=self.polus_ind2).pack(anchor="w")
        ttk.Checkbutton(polus_frame, text="IND3 (up/dn/anvar)", variable=self.polus_ind3).pack(anchor="w")
        ttk.Checkbutton(polus_frame, text="Show helper lines", variable=self.polus_lines).pack(anchor="w")
        
        # режим перетаскивания
        self.dragmode_var = tk.StringVar(value="pan")
        ttk.Label(self.options_frame, text="Default mode:").pack(anchor="w")
        dragmode_frame = ttk.Frame(self.options_frame)
        dragmode_frame.pack(anchor="w")
        ttk.Radiobutton(dragmode_frame, text="Pan", variable=self.dragmode_var, value="pan").pack(side=tk.LEFT)
        ttk.Radiobutton(dragmode_frame, text="Zoom", variable=self.dragmode_var, value="zoom").pack(side=tk.LEFT)
        ttk.Radiobutton(dragmode_frame, text="Select", variable=self.dragmode_var, value="select").pack(side=tk.LEFT)
        
        # дополнительные опции
        self.scroll_zoom_var = tk.BooleanVar(value=True)
        self.crossfilter_var = tk.BooleanVar(value=False)
        self.auto_scale_var = tk.BooleanVar(value=True)  # новая опция!
        
        ttk.Checkbutton(self.options_frame, text="Enable scroll zoom", variable=self.scroll_zoom_var).pack(anchor="w")
        ttk.Checkbutton(self.options_frame, text="Crossfilter enabled", variable=self.crossfilter_var).pack(anchor="w")
        ttk.Checkbutton(self.options_frame, text="Auto-scale Y axis (растягивание)", variable=self.auto_scale_var).pack(anchor="w")

        # кнопки
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Show chart", command=self.show_chart).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Show in browser", command=lambda: self.show_chart(browser=True)).pack(side=tk.LEFT, padx=5)

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

    def create_figure(self, df):
        """Создает и настраивает фигуру Plotly"""
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("Candlestick", "Volume"),
            row_heights=[0.7, 0.3]
        )
        
        # основной график - свечи
        fig.add_trace(
            go.Candlestick(
                x=df["open_time"],
                open=df["open"], 
                high=df["high"],
                low=df["low"], 
                close=df["close"],
                name="OHLC",
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4444'
            ),
            row=1, col=1
        )
        
        # объемы
        colors = ['#ff4444' if close < open else '#00ff88' for close, open in zip(df["close"], df["open"])]
        fig.add_trace(
            go.Bar(
                x=df["open_time"], 
                y=df["volume"],
                name="Volume", 
                marker_color=colors,
                opacity=0.6
            ),
            row=2, col=1
        )
        
        # --- добавляем PolusX ---
        from indicators.polus_x import PolusX
        polus = PolusX(
            use_tick_volume=False,                       # всегда реальный объём
            show_lines=self.polus_lines.get(),
            ind1=self.polus_ind1.get(),
            ind2=self.polus_ind2.get(),
            ind3=self.polus_ind3.get()
        )
        polus.add_to_figure(df, fig, row=1, col=1)

        # настройка осей и интерактивности
        fig.update_layout(
            title=self.file_var.get(),
            xaxis_rangeslider_visible=False,
            dragmode=self.dragmode_var.get(),
            hovermode='x unified',
            template='plotly_dark',
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # КЛЮЧЕВЫЕ НАСТРОЙКИ для растягивания масштаба:
        fig.update_xaxes(
            fixedrange=False,
            autorange=True if self.auto_scale_var.get() else False
        )
        
        if self.auto_scale_var.get():
            # Для автоматического растягивания Y при зуме X
            fig.update_yaxes(
                fixedrange=False, 
                autorange=True,
                scaleanchor=None,  # не привязывать к другим осям
                scaleratio=None,   # свободное соотношение
                automargin=True    # автоотступы
            )
        else:
            # Фиксированный диапазон Y
            fig.update_yaxes(
                fixedrange=False,
                autorange=False
            )
        
        # синхронизация осей X между подграфиками
        if self.crossfilter_var.get():
            fig.update_xaxes(matches='x')
        
        return fig

    def get_config(self):
        """Возвращает конфигурацию для Plotly"""
        config = {
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d'],
            'scrollZoom': self.scroll_zoom_var.get(),  # зум колесиком мыши
            'doubleClick': 'autosize',  # двойной клик = автомасштаб
            'showAxisDragHandles': True,  # ручки для перетаскивания осей
            'showAxisRangeEntryBoxes': True,  # поля ввода диапазона
            # КЛЮЧЕВАЯ настройка для растягивания:
            'responsive': True,  # адаптивный размер
            'editable': True,    # возможность редактировать
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'chart_{self.file_var.get()}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'height': 800,
                'width': 1200,
                'scale': 2
            }
        }
        return config

    def show_chart(self, browser=False):
        file_path = Path(self.dir_var.get()) / self.file_var.get()
        if not file_path.exists():
            log.error("Файл не найден: %s", file_path)
            messagebox.showerror("File not found", str(file_path))
            return

        try:
            df = load_parquet(file_path)
            
            # фильтрация по датам
            start_date = pd.to_datetime(self.start_date.get_date())
            end_date = pd.to_datetime(self.end_date.get_date()) + pd.Timedelta(days=1)
            
            mask = (df["open_time"] >= start_date) & (df["open_time"] < end_date)
            df = df.loc[mask]

            if df.empty:
                log.warning("После фильтрации данных нет")
                messagebox.showwarning("No data", "Выбранный диапазон пуст.")
                return

            log.info("Строю график из %d баров в режиме %s", len(df), self.dragmode_var.get())

            fig = self.create_figure(df)
            config = self.get_config()
            
            if browser:
                # показать в браузере с полным функционалом
                fig.show(config=config, renderer='browser')
            else:
                # показать в дефолтном рендерере
                fig.show(config=config)

        except Exception as e:
            log.exception("Ошибка при построении графика: %s", e)
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    VisualizerGUI().mainloop()