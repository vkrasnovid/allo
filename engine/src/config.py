from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://:allo_redis_pass@localhost:6379/0"
    database_url: str = "postgresql+asyncpg://allo:allo_dev_pass@localhost:5432/allo"
    booking_api_url: str = "http://localhost:8003/api/v1"
    openclaw_api_url: str = "http://localhost:4000"
    openclaw_api_key: str = "test_openclaw_key"
    port: int = 8002

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
