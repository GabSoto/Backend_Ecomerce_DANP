from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TAX_RATE: float = 0.18
    SHIPPING_COST: float = 5.99

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
