from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.users.exceptions import (
    BranchNotFoundError,
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from app.users.models import Usuario
from app.users.schemas import LoginRequest, UserCreate, UserUpdate


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def get_user(db: AsyncSession, user_uuid: str) -> Usuario:
    result = await db.execute(
        select(Usuario).where(
            Usuario.uuid == user_uuid,
            Usuario.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError(user_uuid)
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> Usuario | None:
    result = await db.execute(
        select(Usuario).where(
            Usuario.username == username,
            Usuario.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def branch_exists(db: AsyncSession, branch_id: str) -> bool:
    result = await db.execute(
        text("SELECT 1 FROM public.sucursales WHERE id = :branch_id LIMIT 1"),
        {"branch_id": branch_id},
    )
    return result.first() is not None


async def create_user(db: AsyncSession, data: UserCreate) -> Usuario:
    existing = await get_user_by_username(db, data.username)
    if existing:
        raise UsernameAlreadyExistsError(data.username)

    if not await branch_exists(db, data.branch_id):
        raise BranchNotFoundError(data.branch_id)

    user = Usuario(
        uuid=str(uuid4()),
        branch_id=data.branch_id,
        nombre=data.nombre,
        username=data.username,
        password_hash=await hash_password(data.password),
        rol=data.rol,
        activo=1,
        created_at=now_iso(),
        updated_at=now_iso(),
        deleted_at=None,
        synced_at=None,
    )
    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise

    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, data: LoginRequest) -> Usuario:
    user = await get_user_by_username(db, data.username)
    if user is None or user.activo != 1:
        raise InvalidCredentialsError()
    if not await verify_password(data.password, user.password_hash):
        raise InvalidCredentialsError()
    return user


async def update_user(db: AsyncSession, user_uuid: str, data: UserUpdate) -> Usuario:
    user = await get_user(db, user_uuid)

    if data.branch_id is not None:
        user.branch_id = data.branch_id
    if data.nombre is not None:
        user.nombre = data.nombre
    if data.username is not None:
        existing = await get_user_by_username(db, data.username)
        if existing and existing.uuid != user.uuid:
            raise UsernameAlreadyExistsError(data.username)
        user.username = data.username
    if data.rol is not None:
        user.rol = data.rol
    if data.password is not None:
        user.password_hash = hash_password(data.password)

    user.updated_at = now_iso()

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise

    await db.refresh(user)
    return user


async def soft_delete_user(db: AsyncSession, user_uuid: str) -> Usuario:
    user = await get_user(db, user_uuid)
    user.activo = 0
    user.deleted_at = now_iso()
    user.updated_at = now_iso()

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise

    await db.refresh(user)
    return user
