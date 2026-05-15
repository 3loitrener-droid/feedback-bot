from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.routes import auth, employees, feedback, criteria, periods, summary, llm, export
from app.config import settings

log = structlog.get_logger()

app = FastAPI(
    title="Feedback Assistant API",
    description="Performance feedback management system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [auth.router, employees.router, feedback.router, criteria.router, periods.router, summary.router, llm.router, export.router]:
    app.include_router(router, prefix="/api")


@app.on_event("startup")
async def on_startup():
    import app.models  # ensure all models registered
    from app.db.session import engine
    from app.db.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed demo data if DB is empty
    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        if not result.scalar_one_or_none():
            from app.scripts.seed import run_seed
            await run_seed(db)
            log.info("seed_completed")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})
