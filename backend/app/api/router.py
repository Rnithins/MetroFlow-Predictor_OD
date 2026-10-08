from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    admin,
    auth,
    dashboard,
    dispatch,
    gtfs,
    historical,
    networks,
    od_matrix,
    predict,
    profile,
    routes_nav,
    simulation,
    stations,
    upload,
    data_sources,
)

api_router = APIRouter()


@api_router.get("/")
def read_root():
    return {"status": "online", "message": "MetroFlowNet Passenger Flow Predictor API"}


api_router.include_router(auth.router)
api_router.include_router(stations.router)
api_router.include_router(dashboard.router)
api_router.include_router(historical.router)
api_router.include_router(profile.router)
api_router.include_router(predict.router)
api_router.include_router(upload.router)
api_router.include_router(od_matrix.router)
api_router.include_router(routes_nav.router)
api_router.include_router(admin.router)
api_router.include_router(networks.router, prefix="/networks")
api_router.include_router(simulation.router, prefix="/simulation")
api_router.include_router(dispatch.router, prefix="/dispatch")
api_router.include_router(gtfs.router, prefix="/gtfs")
api_router.include_router(data_sources.router, prefix="/data-sources")
