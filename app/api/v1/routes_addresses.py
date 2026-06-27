from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate
from app.schemas.common import ErrorResponse
from app.services import address_service

router = APIRouter(prefix="/addresses", tags=["addresses"])

PROTECTED = {
    401: {"model": ErrorResponse, "description": "Token inválido o expirado"},
    404: {"model": ErrorResponse, "description": "Dirección no encontrada o no pertenece al usuario"},
    409: {"model": ErrorResponse, "description": "No se puede eliminar: está referenciada por una orden"},
}


@router.get(
    "",
    response_model=list[AddressOut],
    summary="Listar direcciones",
    description="Devuelve todas las direcciones del usuario autenticado.",
    responses={401: {"model": ErrorResponse, "description": "Token inválido o expirado"}},
)
def list_addresses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return address_service.list_addresses(db, user)


@router.post(
    "",
    response_model=AddressOut,
    status_code=201,
    summary="Crear dirección",
    description="Crea una nueva dirección. Si es la primera, se marca automáticamente como default.",
    responses={401: {"model": ErrorResponse, "description": "Token inválido o expirado"}},
)
def create_address(
    data: AddressCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return address_service.create_address(db, user, data)


@router.get(
    "/{address_id}",
    response_model=AddressOut,
    summary="Obtener dirección por ID",
    description="Devuelve una dirección específica del usuario autenticado.",
    responses=PROTECTED,
)
def get_address(
    address_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return address_service.get_address(db, address_id, user)


@router.put(
    "/{address_id}",
    response_model=AddressOut,
    summary="Actualizar dirección",
    description="Actualiza los campos de una dirección existente.",
    responses=PROTECTED,
)
def update_address(
    address_id: str,
    data: AddressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return address_service.update_address(db, address_id, user, data)


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Eliminar dirección",
    description="Elimina una dirección. No se puede borrar si está referenciada por una orden.",
    responses=PROTECTED,
)
def delete_address(
    address_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    address_service.delete_address(db, address_id, user)


@router.patch(
    "/{address_id}/default",
    response_model=AddressOut,
    summary="Marcar dirección como default",
    description="Marca esta dirección como la principal. Desmarca las demás del usuario.",
    responses=PROTECTED,
)
def set_default(
    address_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return address_service.set_default_address(db, address_id, user)