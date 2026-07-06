from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_auth
from app.core.response import success_response
from app.database.session import get_db
from app.models.entities import User
from app.schemas.domain import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await AuthService(db).register(data)
    return success_response(user.model_dump(), "User registered successfully")


@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    tokens = await AuthService(db).login(data.email, data.password)
    return success_response(tokens.model_dump(), "Login successful")


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    tokens = await AuthService(db).refresh(refresh_token)
    return success_response(tokens.model_dump(), "Token refreshed")


@router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    return success_response(UserResponse.model_validate(user).model_dump())
