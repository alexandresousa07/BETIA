from fastapi import APIRouter

from app.core.response import success_response
from app.ml.prediction.predictors import ALL_PREDICTORS, MARKET_DEFINITIONS

router = APIRouter(prefix="/ai", tags=["AI Models"])


@router.get("/models")
async def list_models():
    models = [
        {"name": p.name, "weight": p.weight, "type": p.__class__.__name__}
        for p in ALL_PREDICTORS
    ]
    return success_response(models)


@router.get("/markets")
async def list_markets():
    markets = [
        {"key": key, **value} for key, value in MARKET_DEFINITIONS.items()
    ]
    return success_response(markets)
