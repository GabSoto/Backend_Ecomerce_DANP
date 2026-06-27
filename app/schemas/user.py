from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.profile import ProfileOut


class UserOut(BaseModel):
    id: str = Field(..., description="UUID del usuario")
    name: str = Field(..., description="Nombre completo")
    email: str = Field(..., description="Email del usuario")
    created_at: datetime = Field(..., description="Fecha de registro")

    model_config = {"from_attributes": True}


class UserWithProfileOut(BaseModel):
    id: str = Field(..., description="UUID del usuario")
    name: str = Field(..., description="Nombre completo")
    email: str = Field(..., description="Email del usuario")
    created_at: datetime = Field(..., description="Fecha de registro")
    profile: ProfileOut | None = Field(None, description="Perfil personal del usuario (o null si no existe)")

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = Field(None, description="Nuevo nombre del usuario")
    email: EmailStr | None = Field(None, description="Nuevo email (debe ser único)")


class PasswordUpdate(BaseModel):
    current_password: str = Field(..., description="Contraseña actual en texto plano")
    new_password: str = Field(..., description="Nueva contraseña (mínimo 8 caracteres)")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
