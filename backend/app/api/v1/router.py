from fastapi import APIRouter

from app.api.v1 import ai, auth, competitions, health, matches, odds, recommendations, training

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(competitions.router)
api_router.include_router(matches.router)
api_router.include_router(recommendations.router)
api_router.include_router(ai.router)
api_router.include_router(odds.router)
api_router.include_router(training.router)
