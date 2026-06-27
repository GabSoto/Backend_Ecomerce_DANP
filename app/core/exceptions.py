class NotFoundError(Exception):
    def __init__(self, detail: str = "Resource not found", error_code: str | None = None):
        self.detail = detail
        self.error_code = error_code


class ConflictError(Exception):
    def __init__(self, detail: str = "Resource conflict", error_code: str | None = None):
        self.detail = detail
        self.error_code = error_code


class InsufficientStockError(Exception):
    def __init__(self, detail: str = "Insufficient stock", product_id: str | None = None):
        self.detail = detail
        self.error_code = "INSUFFICIENT_STOCK"
        self.product_id = product_id


class InvalidTransitionError(Exception):
    def __init__(self, detail: str = "Invalid status transition", error_code: str | None = None):
        self.detail = detail
        self.error_code = error_code or "INVALID_TRANSITION"


class UnauthorizedError(Exception):
    def __init__(self, detail: str = "Unauthorized", error_code: str | None = None):
        self.detail = detail
        self.error_code = error_code


class BadRequestError(Exception):
    def __init__(self, detail: str = "Bad request", error_code: str | None = None):
        self.detail = detail
        self.error_code = error_code
