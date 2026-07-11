from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.stock.exceptions import ProductNotFoundError, SupplierEmailNotFoundError

def register_stock_exception_handlers(app):
    @app.exception_handler(ProductNotFoundError)
    async def product_not_found_handler(request: Request, exc: ProductNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Producto no encontrado."},
        )

    @app.exception_handler(SupplierEmailNotFoundError)
    async def supplier_email_not_found_handler(request: Request, exc: SupplierEmailNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "El proveedor del producto no tiene un correo configurado."},
        )
