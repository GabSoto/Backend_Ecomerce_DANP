import math

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.address import Address
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.address import AddressOut
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderCreate, OrderItemOut, OrderOut, OrderSummaryOut

VALID_TRANSITIONS = {
    "pending": ["paid", "cancelled"],
    "paid": ["processing", "cancelled"],
    "processing": ["shipped"],
    "shipped": ["delivered"],
    "delivered": [],
    "cancelled": [],
}


def _address_to_out(addr: Address) -> AddressOut:
    return AddressOut(
        id=addr.id,
        street=addr.street,
        city=addr.city,
        state=addr.state,
        zip_code=addr.zip_code,
        is_default=addr.is_default,
        created_at=addr.created_at,
    )


def _order_to_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        status=order.status,
        shipping_address=_address_to_out(order.shipping_address),
        subtotal=order.subtotal,
        taxes=order.taxes,
        shipping_cost=order.shipping_cost,
        total=order.total,
        items=[
            OrderItemOut(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in order.items
        ],
        created_at=order.created_at,
    )


def checkout(db: Session, user: User, data: OrderCreate) -> OrderOut:
    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not cart_items:
        raise BadRequestError("Cart is empty")

    address = db.query(Address).filter(
        Address.id == data.shipping_address_id, Address.user_id == user.id
    ).first()
    if not address:
        raise NotFoundError("Shipping address not found")

    for ci in cart_items:
        product = db.query(Product).with_for_update().filter(Product.id == ci.product_id).first()
        if product.stock < ci.quantity:
            raise ConflictError(
                f"Insufficient stock for product '{product.name}'",
                error_code="INSUFFICIENT_STOCK",
            )

    subtotal = 0.0
    order_items_data = []
    for ci in cart_items:
        product = ci.product
        item_subtotal = round(product.price * ci.quantity, 2)
        subtotal += item_subtotal
        order_items_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": ci.quantity,
            "unit_price": product.price,
            "subtotal": item_subtotal,
        })

    taxes = round(subtotal * settings.TAX_RATE, 2)
    shipping_cost = settings.SHIPPING_COST
    total = round(subtotal + taxes + shipping_cost, 2)

    order = Order(
        user_id=user.id,
        status="pending",
        shipping_address_id=data.shipping_address_id,
        subtotal=subtotal,
        taxes=taxes,
        shipping_cost=shipping_cost,
        total=total,
    )
    db.add(order)
    db.flush()

    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"],
        )
        db.add(order_item)
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock -= item_data["quantity"]

    db.query(CartItem).filter(CartItem.user_id == user.id).delete()
    db.commit()
    db.refresh(order)
    return _order_to_out(order)


def list_orders(
    db: Session,
    user: User,
    page: int = 1,
    size: int = 20,
    status: str | None = None,
) -> PaginatedResponse:
    query = db.query(Order).filter(Order.user_id == user.id)
    if status:
        query = query.filter(Order.status == status)
    total = query.count()
    pages = max(1, math.ceil(total / size))
    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return PaginatedResponse(
        items=[
            OrderSummaryOut(
                id=o.id,
                status=o.status,
                total=o.total,
                items_count=len(o.items),
                created_at=o.created_at,
            )
            for o in orders
        ],
        page=page,
        size=size,
        total=total,
        pages=pages,
    )


def get_order(db: Session, order_id: str, user: User) -> OrderOut:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise NotFoundError("Order not found")
    return _order_to_out(order)


def cancel_order(db: Session, order_id: str, user: User) -> OrderOut:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise NotFoundError("Order not found")
    if order.status not in ("pending", "paid"):
        raise ConflictError(f"Cannot cancel order in '{order.status}' status")
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock += item.quantity
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return _order_to_out(order)


def update_order_status(db: Session, order_id: str, user: User, new_status: str) -> OrderOut:
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise NotFoundError("Order not found")
    valid_next = VALID_TRANSITIONS.get(order.status, [])
    if new_status not in valid_next:
        raise ConflictError(
            f"Invalid transition from '{order.status}' to '{new_status}'"
        )
    order.status = new_status
    db.commit()
    db.refresh(order)
    return _order_to_out(order)
