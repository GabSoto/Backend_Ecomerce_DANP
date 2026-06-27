from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductStockUpdate,
    ProductUpdate,
)
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])

WRITE_ERRORS = {
    401: {"model": ErrorResponse, "description": "Token inválido o expirado"},
    404: {"model": ErrorResponse, "description": "Producto o categoría no encontrado"},
    409: {"model": ErrorResponse, "description": "Stock insuficiente o producto referenciado en órdenes"},
}


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="Listar productos",
    description=(
        "Lista paginada de productos con filtros combinables: categoría, texto, rango de precio y disponibilidad.\n\n"
        "**No requiere autenticación.**"
    ),
)
def list_products(
    page: int = Query(default=1, ge=1, description="Número de página (>= 1)"),
    size: int = Query(default=20, ge=1, le=100, description="Tamaño de página (1-100)"),
    category_id: str | None = Query(None, description="Filtrar por UUID de categoría"),
    q: str | None = Query(None, description="Texto de búsqueda en nombre/descripción"),
    min_price: float | None = Query(None, ge=0, description="Precio mínimo"),
    max_price: float | None = Query(None, ge=0, description="Precio máximo"),
    in_stock: bool | None = Query(None, description="true → solo productos con stock > 0"),
    db: Session = Depends(get_db),
):
    return product_service.list_products(
        db, page=page, size=size, category_id=category_id, q=q,
        min_price=min_price, max_price=max_price, in_stock=in_stock,
    )


@router.get(
    "/{product_id}",
    response_model=ProductOut,
    summary="Obtener producto por ID",
    description="Devuelve un producto específico. **No requiere autenticación.**",
    responses={404: {"model": ErrorResponse, "description": "Producto no encontrado"}},
)
def get_product(product_id: str, db: Session = Depends(get_db)):
    return product_service.get_product_out(db, product_id)


@router.post(
    "",
    response_model=ProductOut,
    status_code=201,
    summary="Crear producto",
    description="Crea un nuevo producto. Requiere autenticación.",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse, "description": "Categoría no encontrada"}},
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return product_service.create_product(db, data)


@router.put(
    "/{product_id}",
    response_model=ProductOut,
    summary="Actualizar producto",
    description="Actualiza los campos de un producto. Requiere autenticación.",
    responses=WRITE_ERRORS,
)
def update_product(
    product_id: str,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return product_service.update_product(db, product_id, data)


@router.patch(
    "/{product_id}/stock",
    response_model=ProductOut,
    summary="Ajustar stock de producto",
    description="Ajusta el stock mediante un delta (positivo o negativo). El stock resultante no puede ser negativo.",
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        409: {"model": ErrorResponse, "description": "El stock resultante sería negativo"},
    },
)
def update_stock(
    product_id: str,
    data: ProductStockUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return product_service.update_stock(db, product_id, data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Eliminar producto",
    description="Elimina un producto. No se puede borrar si aparece en order_items (integridad histórica).",
    responses=WRITE_ERRORS,
)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    product_service.delete_product(db, product_id)