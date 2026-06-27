from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.address import AddressOut


class OrderCreate(BaseModel):
    shipping_address_id: str = Field(..., description="UUID de la dirección de envío")


class OrderStatusUpdate(BaseModel):
    status: Literal["paid", "processing", "shipped", "delivered"] = Field(
        ..., description="Nuevo estado de la orden"
    )


class OrderItemOut(BaseModel):
    id: str = Field(..., description="UUID del item")
    product_id: str = Field(..., description="UUID del producto")
    product_name: str = Field(..., description="Nombre del producto (snapshot)")
    quantity: int = Field(..., description="Cantidad comprada")
    unit_price: float = Field(..., description="Precio congelado al momento de la compra")
    subtotal: float = Field(..., description="quantity * unit_price")

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str = Field(..., description="UUID de la orden")
    status: str = Field(..., description="Estado actual de la orden")
    shipping_address: AddressOut = Field(..., description="Dirección de envío")
    subtotal: float = Field(..., description="Subtotal de productos")
    taxes: float = Field(..., description="Impuestos calculados")
    shipping_cost: float = Field(..., description="Costo de envío")
    total: float = Field(..., description="Total a pagar")
    items: list[OrderItemOut] = Field(..., description="Items de la orden")
    created_at: datetime = Field(..., description="Fecha de creación")

    model_config = {"from_attributes": True}


class OrderSummaryOut(BaseModel):
    id: str = Field(..., description="UUID de la orden")
    status: str = Field(..., description="Estado actual")
    total: float = Field(..., description="Total a pagar")
    items_count: int = Field(..., description="Número de items")
    created_at: datetime = Field(..., description="Fecha de creación")

    model_config = {"from_attributes": True}
