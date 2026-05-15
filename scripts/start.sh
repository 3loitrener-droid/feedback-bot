#!/bin/bash
set -e

echo "=== Feedback Assistant — запуск ==="

# Проверяем наличие .env
if [ ! -f .env ]; then
  echo "ERROR: Файл .env не найден."
  echo "Скопируй .env.example в .env и заполни переменные:"
  echo "  cp .env.example .env"
  exit 1
fi

# Проверяем обязательные переменные
source .env
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
  echo "WARN: TELEGRAM_BOT_TOKEN не настроен — бот не запустится"
fi
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
  echo "WARN: ANTHROPIC_API_KEY не настроен — LLM-анализ недоступен"
fi

echo ""
echo "Запускаем через Docker Compose..."
docker compose up --build -d

echo ""
echo "=== Готово ==="
echo "API:     http://localhost:8000/api/docs"
echo "Web:     http://localhost:3000"
echo "Логи:    docker compose logs -f"
echo ""
echo "Демо-аккаунты (после инициализации БД):"
echo "  Manager: alexey@company.com"
echo "  HRBP:    maria@company.com"
echo "  Admin:   dmitry@company.com"
