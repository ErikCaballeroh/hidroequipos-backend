from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.sales.exceptions import InvalidDateRangeError


def register_sales_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidDateRangeError)
    async def invalid_date_range_handler(
        request: Request, exc: InvalidDateRangeError
    ):
        return JSONResponse(status_code=400, content={"detail": str(exc)})
