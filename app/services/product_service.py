import math

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.common import PaginatedResponse
from app.schemas.product import ProductCreate, ProductOut, ProductStockUpdate, ProductUpdate


def _product_to_out(product: Product) -> ProductOut:
    return ProductOut(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        image_url=product.image_url,
        category_id=product.category_id,
        category_name=product.category.name if product.category else "",
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def list_products(
    db: Session,
    page: int = 1,
    size: int = 20,
    category_id: str | None = None,
    q: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
) -> PaginatedResponse:
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if q:
        query = query.filter(
            or_(Product.name.ilike(f"%{q}%"), Product.description.ilike(f"%{q}%"))
        )
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock:
        query = query.filter(Product.stock > 0)
    total = query.count()
    pages = max(1, math.ceil(total / size))
    products = query.offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(
        items=[_product_to_out(p) for p in products],
        page=page,
        size=size,
        total=total,
        pages=pages,
    )


def get_product(db: Session, product_id: str) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product not found")
    return product


def get_product_out(db: Session, product_id: str) -> ProductOut:
    return _product_to_out(get_product(db, product_id))


def create_product(db: Session, data: ProductCreate) -> ProductOut:
    cat = db.query(Category).filter(Category.id == data.category_id).first()
    if not cat:
        raise NotFoundError("Category not found")
    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        stock=data.stock,
        image_url=data.image_url,
        category_id=data.category_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return _product_to_out(product)


def update_product(db: Session, product_id: str, data: ProductUpdate) -> ProductOut:
    product = get_product(db, product_id)
    update_data = data.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        cat = db.query(Category).filter(Category.id == data.category_id).first()
        if not cat:
            raise NotFoundError("Category not found")
    for key, value in update_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return _product_to_out(product)


def update_stock(db: Session, product_id: str, data: ProductStockUpdate) -> ProductOut:
    product = get_product(db, product_id)
    new_stock = product.stock + data.delta
    if new_stock < 0:
        raise ConflictError("Insufficient stock", error_code="INSUFFICIENT_STOCK")
    product.stock = new_stock
    db.commit()
    db.refresh(product)
    return _product_to_out(product)


def delete_product(db: Session, product_id: str) -> None:
    product = get_product(db, product_id)
    order_ref = db.query(OrderItem).filter(OrderItem.product_id == product_id).first()
    if order_ref:
        raise ConflictError(
            "Cannot delete product referenced in orders; set stock=0 instead"
        )
    db.delete(product)
    db.commit()
