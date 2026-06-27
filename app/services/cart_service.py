from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemOut, CartItemUpdate, CartOut


def _cart_item_to_out(item: CartItem) -> CartItemOut:
    return CartItemOut(
        id=item.id,
        product_id=item.product_id,
        product_name=item.product.name,
        product_image_url=item.product.image_url,
        unit_price=item.product.price,
        quantity=item.quantity,
        subtotal=round(item.product.price * item.quantity, 2),
        added_at=item.added_at,
    )


def get_cart(db: Session, user: User) -> CartOut:
    items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    cart_items = [_cart_item_to_out(i) for i in items]
    subtotal = round(sum(i.subtotal for i in cart_items), 2)
    return CartOut(
        items=cart_items,
        items_count=len(cart_items),
        subtotal=subtotal,
    )


def add_item(db: Session, user: User, data: CartItemCreate) -> CartItemOut:
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise NotFoundError("Product not found")
    if data.quantity > product.stock:
        raise ConflictError(f"Requested quantity exceeds available stock ({product.stock})")
    existing = db.query(CartItem).filter(
        CartItem.user_id == user.id, CartItem.product_id == data.product_id
    ).first()
    if existing:
        new_qty = existing.quantity + data.quantity
        if new_qty > product.stock:
            raise ConflictError(f"Total quantity would exceed available stock ({product.stock})")
        existing.quantity = new_qty
        db.commit()
        db.refresh(existing)
        return _cart_item_to_out(existing)
    item = CartItem(
        user_id=user.id,
        product_id=data.product_id,
        quantity=data.quantity,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _cart_item_to_out(item)


def update_item(db: Session, item_id: str, user: User, data: CartItemUpdate) -> CartItemOut:
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not item:
        raise NotFoundError("Cart item not found")
    if data.quantity > item.product.stock:
        raise ConflictError(f"Requested quantity exceeds available stock ({item.product.stock})")
    item.quantity = data.quantity
    db.commit()
    db.refresh(item)
    return _cart_item_to_out(item)


def delete_item(db: Session, item_id: str, user: User) -> None:
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not item:
        raise NotFoundError("Cart item not found")
    db.delete(item)
    db.commit()


def clear_cart(db: Session, user: User) -> None:
    db.query(CartItem).filter(CartItem.user_id == user.id).delete()
    db.commit()
