from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


async def internal_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Ocurrió un error interno"})


def register_generic_exception_handler(app: FastAPI) -> None:
    app.add_exception_handler(Exception, internal_error_handler)
