from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.deps import get_current_user, get_db
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/categories", tags=["categories"])

WRITE_ERRORS = {
    401: {"model": ErrorResponse, "description": "Token inválido o expirado"},
    404: {"model": ErrorResponse, "description": "Categoría no encontrada"},
    409: {"model": ErrorResponse, "description": "Nombre duplicado o no se puede eliminar (tiene productos)"},
}


@router.get(
    "",
    response_model=list[CategoryOut],
    summary="Listar categorías",
    description="Devuelve todas las categorías ordenadas por nombre. **No requiere autenticación.**",
)
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.get(
    "/{category_id}",
    response_model=CategoryOut,
    summary="Obtener categoría por ID",
    description="Devuelve una categoría específica. **No requiere autenticación.**",
    responses={404: {"model": ErrorResponse, "description": "Categoría no encontrada"}},
)
def get_category(category_id: str, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise NotFoundError("Category not found")
    return cat


@router.post(
    "",
    response_model=CategoryOut,
    status_code=201,
    summary="Crear categoría",
    description="Crea una nueva categoría. El nombre debe ser único. Requiere autenticación.",
    responses={401: {"model": ErrorResponse}, 409: {"model": ErrorResponse, "description": "Nombre duplicado"}},
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    existing = db.query(Category).filter(Category.name == data.name).first()
    if existing:
        raise ConflictError("Category name already exists")
    cat = Category(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put(
    "/{category_id}",
    response_model=CategoryOut,
    summary="Actualizar categoría",
    description="Actualiza los campos de una categoría existente. Requiere autenticación.",
    responses=WRITE_ERRORS,
)
def update_category(
    category_id: str,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise NotFoundError("Category not found")
    if data.name is not None and data.name != cat.name:
        existing = db.query(Category).filter(Category.name == data.name).first()
        if existing:
            raise ConflictError("Category name already exists")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cat, key, value)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Eliminar categoría",
    description="Elimina una categoría. No se puede borrar si tiene productos asociados.",
    responses=WRITE_ERRORS,
)
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise NotFoundError("Category not found")
    has_products = db.query(Product).filter(Product.category_id == category_id).first()
    if has_products:
        raise ConflictError("Cannot delete category with associated products")
    db.delete(cat)
    db.commit()