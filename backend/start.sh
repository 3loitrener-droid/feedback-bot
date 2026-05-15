#!/bin/bash
set -e

cd /app

# Run DB migrations / create tables
python -c "
import asyncio
from app.db.session import engine
from app.db.base import Base
import app.models

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(init())
"

# Start FastAPI in background
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" &

# Start Telegram bot in foreground (keeps container alive)
python -m app.bot.main
