from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL : str
    JWT_SECRET : str
    JWT_ALGORITHM : str
    REDIS_HOST:str = 'localhost'
    REDIS_PORT:int = 6379
    RATE_WINDOW:int = 60
    RATE_LIMIT:int = 100
    model_config = SettingsConfigDict(
        env_file = ".env",
        extra='ignore'
    )

Config = Settings()