from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.users.exceptions import (
    BranchNotFoundError,
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
    InvalidCurrentPasswordError,
)


def register_user_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(request: Request, exc: UserNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(UsernameAlreadyExistsError)
    async def username_exists_handler(request: Request, exc: UsernameAlreadyExistsError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(BranchNotFoundError)
    async def branch_not_found_handler(request: Request, exc: BranchNotFoundError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(InvalidCurrentPasswordError)
    async def invalid_current_password_handler(request: Request, exc: InvalidCurrentPasswordError):
        return JSONResponse(status_code=403, content={"detail": str(exc)})
