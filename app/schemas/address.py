from datetime import datetime

from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    street: str = Field(..., description="Calle y número")
    city: str = Field(..., description="Ciudad")
    state: str = Field(..., description="Provincia o estado")
    zip_code: str = Field(..., description="Código postal")
    is_default: bool = Field(False, description="Marcar como dirección principal")


class AddressUpdate(BaseModel):
    street: str | None = Field(None, description="Calle y número")
    city: str | None = Field(None, description="Ciudad")
    state: str | None = Field(None, description="Provincia o estado")
    zip_code: str | None = Field(None, description="Código postal")


class AddressOut(BaseModel):
    id: str = Field(..., description="UUID de la dirección")
    street: str = Field(..., description="Calle y número")
    city: str = Field(..., description="Ciudad")
    state: str = Field(..., description="Provincia o estado")
    zip_code: str = Field(..., description="Código postal")
    is_default: bool = Field(..., description="Indica si es la dirección principal")
    created_at: datetime = Field(..., description="Fecha de creación")

    model_config = {"from_attributes": True}
