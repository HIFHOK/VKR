from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file='.env', extra='ignore')
    
    APP_NAME: str = "Accounting Subsystem"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin123"
    POSTGRES_DB: str = "accounting_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    PROMETHEUS_URL: str = "http://prometheus:9090"
    API_V1_PREFIX: str = "/api/v1"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()