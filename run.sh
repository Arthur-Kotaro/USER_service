#!/bin/bash
# run.sh — Запуск User Service

cd "$(dirname "$0")"

# Проверяем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "Creating virtual environment for User Service..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Проверяем, установлены ли зависимости
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies for User Service..."
    pip install -r requirements.txt
fi

echo "🚀 Starting User Service on port 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
