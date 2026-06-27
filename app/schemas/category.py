from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., description="Nombre único de la categoría")
    description: str | None = Field(None, description="Descripción de la categoría")
    image_url: str | None = Field(None, description="URL de la imagen")


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, description="Nombre único de la categoría")
    description: str | None = Field(None, description="Descripción de la categoría")
    image_url: str | None = Field(None, description="URL de la imagen")


class CategoryOut(BaseModel):
    id: str = Field(..., description="UUID de la categoría")
    name: str = Field(..., description="Nombre de la categoría")
    description: str | None = Field(None, description="Descripción de la categoría")
    image_url: str | None = Field(None, description="URL de la imagen")
    created_at: datetime = Field(..., description="Fecha de creación")

    model_config = {"from_attributes": True}
