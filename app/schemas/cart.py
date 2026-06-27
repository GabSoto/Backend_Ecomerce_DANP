from datetime import datetime

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    product_id: str = Field(..., description="UUID del producto a agregar")
    quantity: int = Field(1, ge=1, description="Cantidad a agregar (>= 1)")


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, description="Nueva cantidad del item (>= 1)")


class CartItemOut(BaseModel):
    id: str = Field(..., description="UUID del item de carrito")
    product_id: str = Field(..., description="UUID del producto")
    product_name: str = Field(..., description="Nombre del producto")
    product_image_url: str | None = Field(None, description="URL de la imagen del producto")
    unit_price: float = Field(..., description="Precio unitario ACTUAL del producto")
    quantity: int = Field(..., description="Cantidad en el carrito")
    subtotal: float = Field(..., description="unit_price * quantity")
    added_at: datetime = Field(..., description="Fecha de adición")

    model_config = {"from_attributes": True}


class CartOut(BaseModel):
    items: list[CartItemOut] = Field(..., description="Items del carrito")
    items_count: int = Field(..., description="Número total de items")
    subtotal: float = Field(..., description="Suma de todos los subtotales")
