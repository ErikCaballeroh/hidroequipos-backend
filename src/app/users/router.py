from fastapi import APIRouter, Response, status

from app.core.auth import authenticate_response, clear_access_cookie
from app.users.dependencies import CurrentUser, DbSession
from app.users.schemas import LoginRequest, LoginResponse, UserCreate, UserResponse, UserUpdate
from app.users import service

router = APIRouter()


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: DbSession, response: Response):
    user = await service.create_user(db, data)
    return authenticate_response(user, response)


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: DbSession, response: Response):
    user = await service.login_user(db, data)
    return authenticate_response(user, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    clear_access_cookie(response)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return current_user


@router.patch("/{user_uuid}", response_model=UserResponse)
async def update_user(user_uuid: str, data: UserUpdate, db: DbSession):
    return await service.update_user(db, user_uuid, data)


@router.delete("/{user_uuid}", response_model=UserResponse)
async def soft_delete_user(user_uuid: str, db: DbSession):
    return await service.soft_delete_user(db, user_uuid)
