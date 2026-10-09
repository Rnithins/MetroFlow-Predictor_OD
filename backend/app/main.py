from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.db.mongo import close_mongo_connection, get_database
from app.services.bootstrap import ensure_indexes, seed_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    import logging

    logger = logging.getLogger("uvicorn.error")
    try:
        database = get_database()
        ensure_indexes(database)
        seed_database(database)
        logger.info("MetroFlowNet database initialized and seeded successfully.")
    except Exception as exc:
        logger.warning(f"Database bootstrap warning: {exc}")

    try:
        yield
    finally:
        close_mongo_connection()


app = FastAPI(title="MetroFlowNet - OD Passenger Flow Predictor API", version="2.0.0", lifespan=lifespan)

configured_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
allow_all = "*" in configured_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else configured_origins,
    allow_origin_regex=None if allow_all else r"https://.*\.onrender\.com",
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "MetroFlowNet API"}


# Include routes under prefix (e.g. /api/v1) and at root level
app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(api_router)


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
