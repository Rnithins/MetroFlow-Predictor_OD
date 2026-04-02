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
    database = get_database()
    ensure_indexes(database)
    seed_database(database)
    try:
        yield
    finally:
        close_mongo_connection()


app = FastAPI(title=settings.app_name, version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


app.include_router(api_router, prefix=settings.api_prefix)
