from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.security import create_access_token
from src.models.schemas import AuthToken, LoginRequest, RegisterRequest
from src.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=AuthToken, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthToken:
    user = await register_user(db, email=body.email, username=body.username, password=body.password)
    token = create_access_token(user_id=user.id, role=user.role.value)
    return AuthToken(access_token=token)


@router.post("/login", response_model=AuthToken)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthToken:
    user = await authenticate_user(db, identifier=body.identifier, password=body.password)
    token = create_access_token(user_id=user.id, role=user.role.value)
    return AuthToken(access_token=token)
