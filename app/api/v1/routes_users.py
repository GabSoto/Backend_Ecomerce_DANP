from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.profile import ProfileOut, ProfileUpsert
from app.schemas.user import PasswordUpdate, UserOut, UserUpdate, UserWithProfileOut
from app.services import profile_service

router = APIRouter(prefix="/users", tags=["users"])

PROTECTED_ERROR = {
    401: {"model": ErrorResponse, "description": "Token inválido o expirado"},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
}


@router.get(
    "/me",
    response_model=UserWithProfileOut,
    summary="Obtener usuario actual",
    description="Devuelve el usuario autenticado con su perfil embebido (o null si no existe).",
    responses={401: {"model": ErrorResponse, "description": "Token inválido o expirado"}},
)
def get_me(user: User = Depends(get_current_user)):
    return UserWithProfileOut(
        id=user.id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        profile=ProfileOut.model_validate(user.profile) if user.profile else None,
    )


@router.patch(
    "/me",
    response_model=UserOut,
    summary="Actualizar datos del usuario",
    description="Actualiza nombre y/o email del usuario autenticado. El email debe seguir siendo único.",
    responses={
        401: {"model": ErrorResponse, "description": "Token inválido o expirado"},
        409: {"model": ErrorResponse, "description": "Email ya en uso"},
    },
)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.email is not None and data.email != user.email:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise ConflictError("Email already in use")
        user.email = data.email
    if data.name is not None:
        user.name = data.name
    db.commit()
    db.refresh(user)
    return user


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Cambiar contraseña",
    description="Requiere la contraseña actual. La nueva debe tener al menos 8 caracteres.",
    responses={
        400: {"model": ErrorResponse, "description": "Contraseña actual incorrecta"},
        401: {"model": ErrorResponse, "description": "Token inválido o expirado"},
    },
)
def update_password(
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, user.password_hash):
        raise NotFoundError("Current password does not match")
    user.password_hash = hash_password(data.new_password)
    db.commit()


@router.put(
    "/me/profile",
    response_model=ProfileOut,
    summary="Crear o actualizar perfil",
    description="Upsert del perfil del usuario. Si no existe lo crea, si existe lo actualiza.",
    responses={401: {"model": ErrorResponse, "description": "Token inválido o expirado"}},
)
def upsert_profile(
    data: ProfileUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return profile_service.upsert_profile(db, user, data)