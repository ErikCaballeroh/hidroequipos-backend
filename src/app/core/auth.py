from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Response

from app.core.config import settings
from app.users.schemas import LoginResponse, UserResponse


def create_access_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def set_access_cookie(response: Response, token: str) -> None:
    # For development the cookie may be insecure; in production force secure flag.
    secure_flag = settings.auth_cookie_secure or (
        settings.environment != "development")

    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=secure_flag,
        samesite=settings.auth_cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


def clear_access_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.auth_cookie_name, path="/")


def authenticate_response(user, response: Response) -> LoginResponse:
    token = create_access_token(subject=user.uuid, claims={
        "username": user.username,
        "branch_id": user.branch_id,
        "rol": user.rol,
    })
    set_access_cookie(response, token)
    return LoginResponse(user=UserResponse.model_validate(user), authenticated=True)
