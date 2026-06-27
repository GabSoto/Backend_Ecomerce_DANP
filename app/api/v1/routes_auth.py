from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import ErrorResponse
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

COMMON_ERROR = {401: {"model": ErrorResponse}, 409: {"model": ErrorResponse}}


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
    summary="Registrar nuevo usuario",
    description="Crea un nuevo usuario. El email debe ser único; si ya existe devuelve 409.",
    responses={409: {"model": ErrorResponse, "description": "Email ya registrado"}},
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return auth_service.register(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Autentica al usuario con email y contraseña. Devuelve access_token y refresh_token.",
    responses={401: {"model": ErrorResponse, "description": "Credenciales inválidas"}},
)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login(db, data.email, data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token",
    description="Intercambia un refresh_token válido por un nuevo access_token.",
    responses={401: {"model": ErrorResponse, "description": "Refresh token inválido o expirado"}},
)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_token(db, data.refresh_token)