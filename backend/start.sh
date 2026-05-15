#!/bin/bash

# FastAPI handles DB init on startup — no need to run it separately
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" &

python -m app.bot.main
