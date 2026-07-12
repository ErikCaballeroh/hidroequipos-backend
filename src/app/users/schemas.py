from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    branch_id: str
    nombre: str = Field(..., min_length=1, max_length=120)
    username: str = Field(..., min_length=3, max_length=50,
                          pattern=r"^[a-zA-Z0-9_.-]+$")
    rol: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        if v.islower() or v.isupper() or v.isnumeric():
            raise ValueError(
                "La contraseña debe incluir letras y números y mezcla de mayúsculas/minúsculas")
        return v


class UserUpdate(BaseModel):
    branch_id: str | None = None
    nombre: str | None = None
    username: str | None = Field(
        None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    rol: str | None = None
    password: str | None = Field(None, min_length=8)

    @field_validator("password")
    @classmethod
    def check_password_strength_optional(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.islower() or v.isupper() or v.isnumeric():
            raise ValueError(
                "La contraseña debe incluir letras y números y mezcla de mayúsculas/minúsculas")
        return v


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    uuid: str
    activo: int
    created_at: str
    updated_at: str
    deleted_at: str | None = None
    synced_at: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user: UserResponse
    authenticated: bool = True


class UserUpdateMe(BaseModel):
    nombre: str | None = None
    username: str | None = Field(
        None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    current_password: str
    new_password: str | None = Field(None, min_length=8)

    @field_validator("new_password")
    @classmethod
    def check_password_strength_optional(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.islower() or v.isupper() or v.isnumeric():
            raise ValueError(
                "La contraseña debe incluir letras y números y mezcla de mayúsculas/minúsculas")
        return v
