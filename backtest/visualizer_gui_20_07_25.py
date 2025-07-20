"""
GUI интерфейс для визуализации криптовалютных данных.

Функциональность:
- Выбор символа и таймфрейма
- Настройка диапазона дат
- Предварительный просмотр и сохранение графиков
- Интеграция с модулем visualizer.py

Автор: Crypto Trading System
Дата: 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont
import os
import threading
from datetime import datetime, timedelta
from typing import List, Optional
import logging

# Импорт нашего модуля визуализации
try:
    from visualizer import CandlestickVisualizer
except ImportError:
    print("Ошибка: Модуль visualizer.py не найден!")
    exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VisualizationGUI:
    """GUI для визуализации криптовалютных данных."""

    def __init__(self, root: tk.Tk):
        """
        Инициализация GUI.

        Args:
            root: Корневое окно Tkinter
        """
        self.root = root
        self.visualizer = CandlestickVisualizer()

        # Настройка окна
        self.root.title("Crypto Data Visualizer")
        self.root.geometry("600x700")
        self.root.resizable(True, True)

        # Переменные для хранения настроек
        self.symbol_var = tk.StringVar(value="SOLUSDTUSDT")
        self.timeframe_var = tk.StringVar(value="1h")
        self.use_date_range_var = tk.BooleanVar(value=False)
        self.days_back_var = tk.IntVar(value=7)

        # Создаем интерфейс
        self.create_widgets()

        # Сканируем доступные файлы при запуске
        self.refresh_available_files()

    def create_widgets(self):
        """Создание элементов интерфейса."""
        # Основная рамка
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Настройка растяжения
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Заголовок
        title_label = ttk.Label(main_frame, text="Визуализация криптовалютных данных",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Секция выбора данных
        data_frame = ttk.LabelFrame(
            main_frame, text="Выбор данных", padding="10")
        data_frame.grid(row=1, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=(0, 10))
        data_frame.columnconfigure(1, weight=1)

        # Выбор символа
        ttk.Label(data_frame, text="Символ:").grid(
            row=0, column=0, sticky=tk.W, pady=2)
        self.symbol_combobox = ttk.Combobox(data_frame, textvariable=self.symbol_var,
                                            width=20, state="readonly")
        self.symbol_combobox.grid(row=0, column=1, sticky=(
            tk.W, tk.E), pady=2, padx=(10, 0))

        # Выбор таймфрейма
        ttk.Label(data_frame, text="Таймфрейм:").grid(
            row=1, column=0, sticky=tk.W, pady=2)
        self.timeframe_combobox = ttk.Combobox(data_frame, textvariable=self.timeframe_var,
                                               values=["1m", "5m", "15m",
                                                       "30m", "1h", "4h", "1d"],
                                               width=20, state="readonly")
        self.timeframe_combobox.grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))

        # Кнопка обновления списка файлов
        refresh_button = ttk.Button(data_frame, text="Обновить список",
                                    command=self.refresh_available_files)
        refresh_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Секция настройки времени
        time_frame = ttk.LabelFrame(
            main_frame, text="Настройки времени", padding="10")
        time_frame.grid(row=2, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=(0, 10))
        time_frame.columnconfigure(1, weight=1)

        # Радио кнопки для выбора режима
        ttk.Radiobutton(time_frame, text="Последние N дней",
                        variable=self.use_date_range_var, value=False).grid(row=0, column=0, sticky=tk.W)

        # Поле для количества дней
        days_frame = ttk.Frame(time_frame)
        days_frame.grid(row=1, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=5)
        ttk.Label(days_frame, text="Количество дней:").pack(side=tk.LEFT)
        days_spinbox = ttk.Spinbox(days_frame, from_=1, to=365, width=10,
                                   textvariable=self.days_back_var)
        days_spinbox.pack(side=tk.LEFT, padx=(10, 0))

        # Радио кнопка для диапазона дат
        ttk.Radiobutton(time_frame, text="Диапазон дат",
                        variable=self.use_date_range_var, value=True).grid(row=2, column=0, sticky=tk.W, pady=(10, 0))

        # Поля для выбора дат
        date_frame = ttk.Frame(time_frame)
        date_frame.grid(row=3, column=0, columnspan=2,
                        sticky=(tk.W, tk.E), pady=5)

        ttk.Label(date_frame, text="С:").pack(side=tk.LEFT)
        self.start_date_entry = ttk.Entry(date_frame, width=12)
        self.start_date_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.start_date_entry.insert(
            0, (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))

        ttk.Label(date_frame, text="До:").pack(side=tk.LEFT)
        self.end_date_entry = ttk.Entry(date_frame, width=12)
        self.end_date_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.end_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Секция настроек вывода
        output_frame = ttk.LabelFrame(
            main_frame, text="Настройки вывода", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2,
                          sticky=(tk.W, tk.E), pady=(0, 10))

        self.save_file_var = tk.BooleanVar(value=True)
        self.show_plot_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(output_frame, text="Сохранить в файл",
                        variable=self.save_file_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(output_frame, text="Показать график",
                        variable=self.show_plot_var).grid(row=0, column=1, sticky=tk.W)

        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        # Кнопка создания графика
        self.create_button = ttk.Button(button_frame, text="Создать график",
                                        command=self.create_visualization,
                                        style='Accent.TButton')
        self.create_button.pack(side=tk.LEFT, padx=(0, 10))

        # Кнопка открытия папки с графиками
        folder_button = ttk.Button(button_frame, text="Открыть папку с графиками",
                                   command=self.open_plots_folder)
        folder_button.pack(side=tk.LEFT, padx=(0, 10))

        # Кнопка закрытия
        close_button = ttk.Button(button_frame, text="Закрыть",
                                  command=self.root.quit)
        close_button.pack(side=tk.LEFT)

        # Прогресс бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                            maximum=100, length=400)
        self.progress_bar.grid(row=5, column=0, columnspan=2,
                               sticky=(tk.W, tk.E), pady=(10, 0))

        # Лог области
        log_frame = ttk.LabelFrame(main_frame, text="Лог", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(
            tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # Текстовое поле для лога
        self.log_text = tk.Text(log_frame, height=8, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Скроллбар для лога
        log_scrollbar = ttk.Scrollbar(
            log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # Настройка растяжения для log_frame
        main_frame.rowconfigure(6, weight=1)

    def refresh_available_files(self):
        """Обновление списка доступных файлов."""
        try:
            # Сканируем папку с данными
            data_path = self.visualizer.data_path
            if not os.path.exists(data_path):
                self.log_message("Папка с данными не найдена: " + data_path)
                return

            # Получаем список .parquet файлов
            files = [f for f in os.listdir(
                data_path) if f.endswith('.parquet')]

            # Извлекаем символы
            symbols = set()
            for file in files:
                try:
                    symbol = file.replace('.parquet', '').split('_')[0]
                    symbols.add(symbol)
                except:
                    continue

            # Обновляем combobox
            symbols_list = sorted(list(symbols))
            self.symbol_combobox['values'] = symbols_list

            if symbols_list and self.symbol_var.get() not in symbols_list:
                self.symbol_var.set(symbols_list[0])

            self.log_message(f"Найдено {len(symbols_list)} символов: {', '.join(symbols_list[:5])}" +
                             ("..." if len(symbols_list) > 5 else ""))

        except Exception as e:
            self.log_message(f"Ошибка при сканировании файлов: {str(e)}")

    def log_message(self, message: str):
        """Добавление сообщения в лог."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def create_visualization(self):
        """Создание визуализации в отдельном потоке."""
        # Блокируем кнопку на время выполнения
        self.create_button.config(state='disabled')
        self.progress_var.set(0)

        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self._create_visualization_thread)
        thread.daemon = True
        thread.start()

        def _create_visualization_thread(self):
            symbol = self.symbol_var.get()
            timeframes = [tf for tf,
                          var in self.timeframe_vars.items() if var.get()]
            indicators = [ind for ind,
                          var in self.indicator_vars.items() if var.get()]
            start = self.start_date.get()
            end = self.end_date.get()

        if not symbol:
            self.log_message("⛔ Укажите символ")
        return
        if not timeframes:
            self.log_message("⛔ Выберите хотя бы один таймфрейм")
            return
        if not indicators:
            self.log_message("⛔ Выберите хотя бы один индикатор")
            return

        self.log_message(
            f"🟡 Визуализация: {symbol}, TF={timeframes}, Индикаторы={indicators}")

        try:
            self.visualizer.visualize(
                symbol=symbol,
                timeframes=timeframes,
                indicators=indicators,
                start_date=start if start else None,
                end_date=end if end else None,
            )
            self.log_message("✅ Графики успешно созданы!")
        except Exception as e:
            self.log_message(f"❌ Ошибка при построении графика: {str(e)}")

    def open_plots_folder(self):
        folder = Path("visuals")
        if not folder.exists():
            self.log_message("⛔ Папка с графиками не найдена")
            return
        try:
            os.startfile(folder.resolve())
        except Exception as e:
            self.log_message(f"❌ Ошибка при открытии папки: {str(e)}")

    def log_message(self, message):
        self.log.config(state="normal")
        self.log.insert(tk.END, message + "\n")
        self.log.config(state="disabled")
        self.log.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizerGUI(root)
    root.mainloop()
