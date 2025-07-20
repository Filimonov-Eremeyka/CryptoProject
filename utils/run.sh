#!/bin/bash

# Скрипт запуска Binance WebSocket коннектора
# Использование: ./run.sh [SYMBOL] [INTERVAL]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция логирования
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 не найден. Установите Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Найден Python $PYTHON_VERSION"
}

# Установка зависимостей
install_deps() {
    log_info "Проверка зависимостей..."
    
    if [ ! -d "venv" ]; then
        log_info "Создание виртуального окружения..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    log_info "Установка зависимостей..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_info "Зависимости установлены"
}

# Создание директорий
create_dirs() {
    mkdir -p logs data
    log_info "Директории созданы"
}

# Установка переменных окружения
set_env() {
    export SYMBOL=${1:-btcusdt}
    export INTERVAL=${2:-1m}
    
    log_info "Настройки:"
    log_info "  Символ: $SYMBOL"
    log_info "  Интервал: $INTERVAL"
}

# Запуск приложения
run_app() {
    log_info "Запуск Binance WebSocket коннектора..."
    log_info "Для остановки нажмите Ctrl+C"
    echo
    
    source venv/bin/activate
    python3 main.py
}

# Основная функция
main() {
    log_info "=== Binance WebSocket Connector ==="
    
    check_python
    install_deps
    create_dirs
    set_env "$@"
    run_app
}

# Обработка сигналов
trap 'echo -e "\n${YELLOW}Остановка сервиса...${NC}"; exit 0' INT TERM

# Запуск
main "$@"