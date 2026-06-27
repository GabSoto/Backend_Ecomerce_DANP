from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(..., description="Nombre completo del usuario")
    email: EmailStr = Field(..., description="Email único del usuario")
    password: str = Field(..., description="Contraseña (mínimo 8 caracteres)")

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Email registrado del usuario")
    password: str = Field(..., description="Contraseña en texto plano")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token JWT obtenido al hacer login")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT de acceso (corta duración)")
    refresh_token: str = Field(..., description="JWT de refresco (larga duración)")
    token_type: str = Field("bearer", description="Tipo de token")
