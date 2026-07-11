from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    frontend_origin: str = "http://localhost:3000"
    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    auth_cookie_name: str = "access_token"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    )
    resend_api_key: str | None = None
    resend_from_email: str = "inventario@tu-dominio.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
