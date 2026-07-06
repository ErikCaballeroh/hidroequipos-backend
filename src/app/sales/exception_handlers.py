from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.sales.exceptions import RangoFechasInvalidoError


def register_ventas_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RangoFechasInvalidoError)
    async def rango_fechas_invalido_handler(request: Request, exc: RangoFechasInvalidoError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})
