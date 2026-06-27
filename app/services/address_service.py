from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.address import Address
from app.models.order import Order
from app.models.user import User
from app.schemas.address import AddressCreate, AddressUpdate


def _ensure_unique_default(db: Session, user_id: str, exclude_id: str | None = None) -> None:
    query = db.query(Address).filter(Address.user_id == user_id, Address.is_default == True)
    if exclude_id:
        query = query.filter(Address.id != exclude_id)
    for addr in query.all():
        addr.is_default = False


def list_addresses(db: Session, user: User) -> list[Address]:
    return db.query(Address).filter(Address.user_id == user.id).order_by(Address.created_at.desc()).all()


def get_address(db: Session, address_id: str, user: User) -> Address:
    addr = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not addr:
        raise NotFoundError("Address not found")
    return addr


def create_address(db: Session, user: User, data: AddressCreate) -> Address:
    user_addresses = db.query(Address).filter(Address.user_id == user.id).count()
    is_default = data.is_default or user_addresses == 0
    if is_default:
        _ensure_unique_default(db, user.id)
    addr = Address(
        user_id=user.id,
        street=data.street,
        city=data.city,
        state=data.state,
        zip_code=data.zip_code,
        is_default=is_default,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


def update_address(db: Session, address_id: str, user: User, data: AddressUpdate) -> Address:
    addr = get_address(db, address_id, user)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(addr, key, value)
    db.commit()
    db.refresh(addr)
    return addr


def delete_address(db: Session, address_id: str, user: User) -> None:
    addr = get_address(db, address_id, user)
    order_using = db.query(Order).filter(Order.shipping_address_id == address_id).first()
    if order_using:
        raise ConflictError("Cannot delete address that is in use by an order")
    db.delete(addr)
    db.commit()


def set_default_address(db: Session, address_id: str, user: User) -> Address:
    addr = get_address(db, address_id, user)
    _ensure_unique_default(db, user.id, exclude_id=address_id)
    addr.is_default = True
    db.commit()
    db.refresh(addr)
    return addr
