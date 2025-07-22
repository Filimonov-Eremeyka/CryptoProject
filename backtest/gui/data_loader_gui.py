# SECTION 0: Импорты
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from data_loader import get_liquid_tickers, fetch_ohlcv, save

# SECTION 1: класс GUI
class LoaderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Binance History Loader")
        self.geometry("400x350")

        # ликвидные тикеры
        self.tickers = get_liquid_tickers()
        self.symbol_var = tk.StringVar()
        ttk.Label(self, text="Symbol").pack(pady=5)
        ttk.Combobox(self, textvariable=self.symbol_var, values=self.tickers).pack()

        # таймфреймы
        self.tf_var = tk.StringVar(value="1m")
        ttk.Label(self, text="Timeframe").pack()
        ttk.Combobox(
            self,
            textvariable=self.tf_var,
            values=["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        ).pack()

        # даты
        ttk.Label(self, text="Start date").pack()
        self.start_cal = ttk.Entry(self)
        self.start_cal.insert(0, (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d"))
        self.start_cal.pack()

        ttk.Label(self, text="End date").pack()
        self.end_cal = ttk.Entry(self)
        self.end_cal.insert(0, datetime.utcnow().strftime("%Y-%m-%d"))
        self.end_cal.pack()

        # кнопка
        ttk.Button(self, text="Download", command=self.download).pack(pady=20)

    def download(self):
        symbol = self.symbol_var.get()
        tf = self.tf_var.get()
        start = datetime.strptime(self.start_cal.get(), "%Y-%m-%d")
        end = datetime.strptime(self.end_cal.get(), "%Y-%m-%d")
        df = fetch_ohlcv(symbol, tf, start, end)
        save(df, symbol, tf, start, end)

if __name__ == "__main__":
    LoaderGUI().mainloop()