#!/bin/bash
# Локальный запуск без Docker (для разработки)
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Создан .env — заполни его перед запуском"
fi

# Запускаем только инфраструктуру через Docker
echo "Поднимаем PostgreSQL и Redis..."
docker compose up postgres redis -d

sleep 2

# Backend
echo "Запускаем backend..."
cd backend
pip install -r requirements.txt -q
export $(cat ../.env | grep -v '^#' | xargs) 2>/dev/null || true
export DATABASE_URL="postgresql+asyncpg://feedback:feedback_secret@localhost:5432/feedback_bot"
export REDIS_URL="redis://localhost:6379/0"
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Frontend
echo "Запускаем frontend..."
cd frontend
npm install -q
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=== Dev-сервер запущен ==="
echo "API:  http://localhost:8000/api/docs"
echo "Web:  http://localhost:3000"
echo ""
echo "Ctrl+C для остановки"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
