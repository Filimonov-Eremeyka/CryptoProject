# SECTION 1: imports
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import argparse
import sys
import os
from pathlib import Path
import threading
from utils.data_utils import csv_to_parquet, resample

# SECTION 2: parse_cli()
def parse_cli():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Конвертер CSV в Parquet с ресэмплингом')
    parser.add_argument('--file', type=str, help='Путь к CSV файлу')
    parser.add_argument('--tf', nargs='+', choices=['5m', '15m', '1h'], 
                       help='Таймфреймы для создания (5m, 15m, 1h)')
    return parser.parse_args()

# SECTION 3: run_cli(file, tfs)
def run_cli(file, tfs):
    """Запуск в режиме CLI"""
    try:
        # Проверяем существование файла
        if not os.path.exists(file):
            print(f"Ошибка: файл {file} не найден")
            return False
        
        # Конвертируем CSV в Parquet
        print("Конвертация CSV в Parquet...")
        parquet_path = csv_to_parquet(file)
        
        # Извлекаем символ из имени файла
        filename = Path(file).stem
        symbol = filename.replace('_1m', '')
        
        # Ресэмплинг для каждого таймфрейма
        print("Создание дополнительных таймфреймов...")
        for tf in tfs:
            resample(symbol, tf)
        
        print("Конвертация завершена успешно!")
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

# SECTION 4: run_gui()
def run_gui():
    """Запуск GUI интерфейса"""
    
    class ConverterGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("CSV → Parquet Конвертер")
            self.root.geometry("500x400")
            
            # Переменные
            self.selected_file = tk.StringVar()
            self.tf_vars = {
                '5m': tk.BooleanVar(value=True),
                '15m': tk.BooleanVar(value=True), 
                '1h': tk.BooleanVar(value=True)
            }
            
            self.create_widgets()
        
        def create_widgets(self):
            # Заголовок
            title_label = tk.Label(self.root, text="CSV → Parquet Конвертер", 
                                 font=("Arial", 16, "bold"))
            title_label.pack(pady=10)
            
            # Выбор файла
            file_frame = tk.Frame(self.root)
            file_frame.pack(pady=10, padx=20, fill='x')
            
            tk.Label(file_frame, text="Выберите CSV файл:", font=("Arial", 10)).pack(anchor='w')
            
            file_select_frame = tk.Frame(file_frame)
            file_select_frame.pack(fill='x', pady=5)
            
            self.file_entry = tk.Entry(file_select_frame, textvariable=self.selected_file, 
                                     state='readonly', font=("Arial", 9))
            self.file_entry.pack(side='left', fill='x', expand=True)
            
            tk.Button(file_select_frame, text="Обзор...", 
                     command=self.select_file).pack(side='right', padx=(5, 0))
            
            # Выбор таймфреймов
            tf_frame = tk.LabelFrame(self.root, text="Создать таймфреймы:", 
                                   font=("Arial", 10, "bold"))
            tf_frame.pack(pady=20, padx=20, fill='x')
            
            for tf in ['5m', '15m', '1h']:
                cb = tk.Checkbutton(tf_frame, text=f"{tf} (ресэмпл из 1m)", 
                                  variable=self.tf_vars[tf], font=("Arial", 9))
                cb.pack(anchor='w', padx=10, pady=2)
            
            # Кнопка конвертации
            self.convert_btn = tk.Button(self.root, text="Конвертировать", 
                                       command=self.start_conversion, 
                                       font=("Arial", 12, "bold"),
                                       bg="#4CAF50", fg="white", 
                                       state='disabled')
            self.convert_btn.pack(pady=20)
            
            # Прогресс бар
            self.progress = ttk.Progressbar(self.root, mode='indeterminate')
            self.progress.pack(pady=10, padx=20, fill='x')
            
            # Лог
            log_frame = tk.Frame(self.root)
            log_frame.pack(pady=10, padx=20, fill='both', expand=True)
            
            tk.Label(log_frame, text="Лог выполнения:", font=("Arial", 10)).pack(anchor='w')
            
            self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 9))
            scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
            self.log_text.config(yscrollcommand=scrollbar.set)
            
            self.log_text.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')
        
        def select_file(self):
            """Выбор CSV файла"""
            file_path = filedialog.askopenfilename(
                title="Выберите CSV файл",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir="C:/CryptoProject/backtest/data/history"
            )
            
            if file_path:
                self.selected_file.set(file_path)
                self.convert_btn.config(state='normal')
                self.log(f"Выбран файл: {file_path}")
        
        def log(self, message):
            """Добавление сообщения в лог"""
            self.log_text.insert('end', message + '\n')
            self.log_text.see('end')
            self.root.update_idletasks()
        
        def start_conversion(self):
            """Запуск конвертации в отдельном потоке"""
            if not self.selected_file.get():
                messagebox.showerror("Ошибка", "Выберите файл для конвертации")
                return
            
            # Получаем выбранные таймфреймы
            selected_tfs = [tf for tf, var in self.tf_vars.items() if var.get()]
            
            if not selected_tfs:
                messagebox.showerror("Ошибка", "Выберите хотя бы один таймфрейм")
                return
            
            # Запускаем в отдельном потоке
            self.convert_btn.config(state='disabled')
            self.progress.start()
            
            thread = threading.Thread(target=self.convert_file, args=(selected_tfs,))
            thread.daemon = True
            thread.start()
        
        def convert_file(self, selected_tfs):
            """Конвертация файла"""
            try:
                file_path = self.selected_file.get()
                self.log("Начинаем конвертацию...")
                
                # Конвертируем CSV в Parquet
                self.log("Конвертация CSV → Parquet...")
                parquet_path = csv_to_parquet(file_path)
                self.log(f"✓ Создан: {parquet_path}")
                
                # Извлекаем символ из имени файла
                filename = Path(file_path).stem
                symbol = filename.replace('_1m', '')
                
                # Ресэмплинг для каждого таймфрейма
                self.log("Создание дополнительных таймфреймов...")
                for tf in selected_tfs:
                    self.log(f"Обработка {tf}...")
                    resample(symbol, tf)
                    self.log(f"✓ Создан: {symbol}_{tf}.parquet")
                
                self.log("🎉 Конвертация завершена успешно!")
                messagebox.showinfo("Готово", "Конвертация завершена успешно!")
                
            except Exception as e:
                error_msg = f"Ошибка: {str(e)}"
                self.log(error_msg)
                messagebox.showerror("Ошибка", error_msg)
            
            finally:
                self.progress.stop()
                self.convert_btn.config(state='normal')
    
    # Создаем и запускаем GUI
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()

# SECTION 5: main()
def main():
    """Главная функция"""
    args = parse_cli()
    
    # Если указаны аргументы командной строки - запускаем CLI
    if args.file and args.tf:
        success = run_cli(args.file, args.tf)
        sys.exit(0 if success else 1)
    
    # Иначе запускаем GUI
    run_gui()

if __name__ == "__main__":
    main()