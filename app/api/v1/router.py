from fastapi import APIRouter

from app.api.v1.routes_auth import router as auth_router
from app.api.v1.routes_users import router as users_router
from app.api.v1.routes_addresses import router as addresses_router
from app.api.v1.routes_categories import router as categories_router
from app.api.v1.routes_products import router as products_router
from app.api.v1.routes_cart import router as cart_router
from app.api.v1.routes_orders import router as orders_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(addresses_router)
router.include_router(categories_router)
router.include_router(products_router)
router.include_router(cart_router)
router.include_router(orders_router)
