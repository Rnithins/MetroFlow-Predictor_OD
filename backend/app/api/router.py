from fastapi import APIRouter

from app.api.routes import admin, auth, dashboard, historical, predict, profile, stations

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(stations.router)
api_router.include_router(dashboard.router)
api_router.include_router(historical.router)
api_router.include_router(profile.router)
api_router.include_router(predict.router)
api_router.include_router(admin.router)
