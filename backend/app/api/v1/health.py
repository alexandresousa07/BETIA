from fastapi import APIRouter

from app.core.response import success_response
from app.config.settings import get_settings

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("")
async def health_check():
    return success_response({
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
    })
