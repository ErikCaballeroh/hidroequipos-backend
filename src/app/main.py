from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exception_handlers import register_generic_exception_handler
from app.users.exception_handlers import register_user_exception_handlers
from app.users.router import router as users_router

app = FastAPI(title="Hidroequipos")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_user_exception_handlers(app)
register_generic_exception_handler(app)


@app.get("/health", tags=["health"])
def root():
    return {"status": "ok"}


app.include_router(users_router, prefix="/api/v1/users", tags=["usuarios"])
