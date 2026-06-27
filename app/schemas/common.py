from pydantic import BaseModel, Field


class PaginatedResponse(BaseModel):
    items: list = Field(..., description="Lista de elementos de la página actual")
    page: int = Field(..., description="Número de página actual")
    size: int = Field(..., description="Tamaño de página solicitado")
    total: int = Field(..., description="Total de elementos")
    pages: int = Field(..., description="Total de páginas")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Mensaje legible del error")
    error_code: str | None = Field(None, description="Código de error opcional (ej. INSUFFICIENT_STOCK)")
