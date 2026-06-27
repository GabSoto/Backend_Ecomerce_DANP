from datetime import datetime

from pydantic import BaseModel, Field


class ProfileUpsert(BaseModel):
    first_name: str = Field(..., description="Nombre")
    last_name: str = Field(..., description="Apellidos")
    phone_number: str | None = Field(None, description="Número de teléfono")
    avatar_url: str | None = Field(None, description="URL del avatar")


class ProfileOut(BaseModel):
    id: str = Field(..., description="UUID del perfil")
    first_name: str = Field(..., description="Nombre")
    last_name: str = Field(..., description="Apellidos")
    phone_number: str | None = Field(None, description="Número de teléfono")
    avatar_url: str | None = Field(None, description="URL del avatar")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")

    model_config = {"from_attributes": True}
