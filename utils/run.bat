@echo off
rem === Binance WebSocket Connector (Windows) ===

rem 1. Проверяем Python
where python >nul 2>&1 || (
  echo [ERROR] Python 3.x not found. Install from https://python.org/
  pause & exit /b 1
)

for /f "tokens=2 delims=. " %%v in ('python -c "import sys; print(sys.version)"') do (
  if %%v lss 3 (
    echo [ERROR] Python 3.8+ required
    pause & exit /b 1
  )
)

rem 2. Виртуальное окружение
if not exist ".venv\Scripts\activate.bat" (
  echo [INFO] Creating venv...
  python -m venv .venv
)

call .venv\Scripts\activate.bat

rem 3. Зависимости
echo [INFO] Installing requirements...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

rem 4. Параметры (по желанию меняй)
set "SYMBOL=btcusdt"
set "INTERVAL=1m"

rem 5. Запуск
echo [INFO] Starting connector...
python main.py
