from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])

AUTH = {401: {"model": ErrorResponse, "description": "Token inválido o expirado"}}


@router.post(
    "",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout — crear orden",
    description=(
        "Opera como checkout transaccional: lee el carrito, valida stock, crea la orden con order_items "
        "(precio congelado), descuenta stock y vacía el carrito. Si cualquier paso falla, rollback completo."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Carrito vacío"},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Dirección de envío no encontrada"},
        409: {"model": ErrorResponse, "description": "Stock insuficiente para uno o más productos"},
    },
)
def checkout(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return order_service.checkout(db, user, data)


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="Listar órdenes",
    description="Lista paginada de órdenes del usuario autenticado. Filtrable por estado.",
    responses=AUTH,
)
def list_orders(
    page: int = Query(default=1, ge=1, description="Número de página (>= 1)"),
    size: int = Query(default=20, ge=1, le=100, description="Tamaño de página (1-100)"),
    status: str | None = Query(None, description="Filtrar por estado: pending, paid, processing, shipped, delivered, cancelled"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return order_service.list_orders(db, user, page=page, size=size, status=status)


@router.get(
    "/{order_id}",
    response_model=OrderOut,
    summary="Obtener orden por ID",
    description="Devuelve una orden con sus order_items completos.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse, "description": "Orden no encontrada"}},
)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return order_service.get_order(db, order_id, user)


@router.patch(
    "/{order_id}/cancel",
    response_model=OrderOut,
    summary="Cancelar orden",
    description=(
        "Cancela una orden en estado `pending` o `paid`. Repone el stock de los productos involucrados. "
        "No se puede cancelar una orden `shipped` o `delivered`."
    ),
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Orden no encontrada"},
        409: {"model": ErrorResponse, "description": "No se puede cancelar en el estado actual"},
    },
)
def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return order_service.cancel_order(db, order_id, user)


@router.patch(
    "/{order_id}/status",
    response_model=OrderOut,
    summary="Actualizar estado de orden",
    description=(
        "Actualiza el estado de la orden respetando las transiciones válidas:\n\n"
        "`pending → paid → processing → shipped → delivered`\n\n"
        "No se permiten saltos arbitrarios."
    ),
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Orden no encontrada"},
        409: {"model": ErrorResponse, "description": "Transición inválida"},
    },
)
def update_status(
    order_id: str,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return order_service.update_order_status(db, order_id, user, data.status)