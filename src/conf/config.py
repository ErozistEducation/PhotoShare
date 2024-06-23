
# from pydantic import BaseSettings
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator, EmailStr


class Settings(BaseSettings):
    DB_URL: str = "postgresql+asyncpg://postgres:7703@localhost:5432/postgres_rest_app"
    SECRET_KEY_JWT: str = "secret_key"
    ALGORITHM: str = "HS256"
    MAIL_USERNAME: EmailStr = "user@meta.ua"
    MAIL_PASSWORD: str = "123456"
    MAIL_FROM: str = "user@meta.ua"
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.meta.ua"
    REDIS_DOMAIN: str = 'localhost'
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    CLOUDINARY_NAME: str = 'Untitled'
    CLOUDINARY_API_KEY: int = 797694525887882
    CLOUDINARY_API_SECRET: str = "secret"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()

    