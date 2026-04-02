from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.api.deps import get_current_user, get_db, require_admin
from app.schemas.flow import PredictionRequest, PredictionResponse, TrainRequest, TrainResponse
from app.services.prediction import build_prediction, run_training

router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse)
def predict(
    payload: PredictionRequest,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PredictionResponse:
    try:
        return build_prediction(db, payload, created_by=current_user["email"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/train", response_model=TrainResponse)
def train(
    payload: TrainRequest,
    _: dict = Depends(require_admin),
) -> TrainResponse:
    return run_training(payload)
