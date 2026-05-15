#!/bin/bash

# Bot must connect to the same port uvicorn listens on
export API_URL="http://localhost:${PORT:-8000}"

uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
UVICORN_PID=$!

python -m app.bot.main &
BOT_PID=$!

wait $UVICORN_PID $BOT_PID
