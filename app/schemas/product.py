from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., description="Nombre del producto")
    description: str | None = Field(None, description="Descripción del producto")
    price: float = Field(..., ge=0, description="Precio unitario (>= 0)")
    stock: int = Field(0, ge=0, description="Stock inicial disponible (>= 0)")
    image_url: str | None = Field(None, description="URL de la imagen del producto")
    category_id: str = Field(..., description="UUID de la categoría a la que pertenece")


class ProductUpdate(BaseModel):
    name: str | None = Field(None, description="Nombre del producto")
    description: str | None = Field(None, description="Descripción del producto")
    price: float | None = Field(None, ge=0, description="Precio unitario (>= 0)")
    image_url: str | None = Field(None, description="URL de la imagen del producto")
    category_id: str | None = Field(None, description="UUID de la categoría")


class ProductStockUpdate(BaseModel):
    delta: int = Field(..., description="Cambio de stock: positivo = ingreso, negativo = salida")


class ProductOut(BaseModel):
    id: str = Field(..., description="UUID del producto")
    name: str = Field(..., description="Nombre del producto")
    description: str | None = Field(None, description="Descripción del producto")
    price: float = Field(..., description="Precio unitario")
    stock: int = Field(..., description="Stock disponible")
    image_url: str | None = Field(None, description="URL de la imagen")
    category_id: str = Field(..., description="UUID de la categoría")
    category_name: str = Field(..., description="Nombre de la categoría (join)")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")

    model_config = {"from_attributes": True}
