from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_access_token
from app.core.config import settings
from app.core.database import get_db
from app.users import service
from app.users.exceptions import UserNotFoundError
from app.users.models import Usuario

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(request: Request, db: DbSession) -> Usuario:
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
        )

    try:
        payload = decode_access_token(token)
        user_uuid = payload.get("sub")
        if not user_uuid:
            raise ValueError("Missing sub")
        return await service.get_user(db, str(user_uuid))
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada",
        )


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def require_role(required_role: str):
    async def _require_role(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.rol != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado"
            )
        return current_user

    return _require_role
