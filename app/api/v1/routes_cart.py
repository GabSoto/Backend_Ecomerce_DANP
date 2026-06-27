from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemOut, CartItemUpdate, CartOut
from app.schemas.common import ErrorResponse
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["cart"])

AUTH = {401: {"model": ErrorResponse, "description": "Token inválido o expirado"}}
NOT_FOUND = {401: {"model": ErrorResponse}, 404: {"model": ErrorResponse, "description": "Producto o item no encontrado"}}
CONFLICT = {401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse, "description": "Cantidad excede stock disponible"}}


@router.get(
    "",
    response_model=CartOut,
    summary="Obtener carrito",
    description="Devuelve los items del carrito del usuario con totales calculados al vuelo (precio actual del producto).",
    responses=AUTH,
)
def get_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return cart_service.get_cart(db, user)


@router.post(
    "/items",
    response_model=CartItemOut,
    status_code=201,
    summary="Agregar item al carrito",
    description="Agrega un producto al carrito. Si ya existe, increments la cantidad. Valida contra stock disponible.",
    responses=CONFLICT,
)
def add_item(
    data: CartItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return cart_service.add_item(db, user, data)


@router.put(
    "/items/{item_id}",
    response_model=CartItemOut,
    summary="Actualizar cantidad de item",
    description="Actualiza la cantidad de un item del carrito. Valida contra stock disponible.",
    responses=CONFLICT,
)
def update_item(
    item_id: str,
    data: CartItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return cart_service.update_item(db, item_id, user, data)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Eliminar item del carrito",
    description="Elimina un item específico del carrito.",
    responses=NOT_FOUND,
)
def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart_service.delete_item(db, item_id, user)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Vaciar carrito",
    description="Elimina todos los items del carrito del usuario.",
    responses=AUTH,
)
def clear_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart_service.clear_cart(db, user)