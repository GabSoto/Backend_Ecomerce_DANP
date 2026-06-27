from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    InsufficientStockError,
    InvalidTransitionError,
    NotFoundError,
    UnauthorizedError,
)

TAGS_METADATA = [
    {"name": "Auth", "description": "Registro, login y renovación de tokens JWT."},
    {"name": "Users", "description": "Perfil de usuario, datos de cuenta y perfil personal."},
    {"name": "Addresses", "description": "Gestión de direcciones de envío del usuario autenticado."},
    {"name": "Categories", "description": "Catálogo de categorías de producto. Las lecturas son públicas."},
    {"name": "Products", "description": "Catálogo de productos con filtros, paginación y gestión de stock. Las lecturas son públicas."},
    {"name": "Cart", "description": "Carrito de compra del usuario autenticado."},
    {"name": "Orders", "description": "Checkout, listado, seguimiento y cancelación de pedidos."},
]

app = FastAPI(
    title="E-commerce API",
    summary="Backend de e-commerce con FastAPI: autenticación JWT, catálogo, carrito y pedidos.",
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "Soporte API", "email": "test@example.com"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.exception_handler(NotFoundError)
def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


@app.exception_handler(ConflictError)
def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(
        status_code=409,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


@app.exception_handler(InsufficientStockError)
def insufficient_stock_handler(request: Request, exc: InsufficientStockError):
    return JSONResponse(
        status_code=409,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


@app.exception_handler(InvalidTransitionError)
def invalid_transition_handler(request: Request, exc: InvalidTransitionError):
    return JSONResponse(
        status_code=409,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


@app.exception_handler(UnauthorizedError)
def unauthorized_handler(request: Request, exc: UnauthorizedError):
    return JSONResponse(
        status_code=401,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


@app.exception_handler(BadRequestError)
def bad_request_handler(request: Request, exc: BadRequestError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )
