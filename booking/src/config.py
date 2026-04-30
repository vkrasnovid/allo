from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://allo:allo_dev_pass@localhost:5432/allo"
    redis_url: str = "redis://:allo_redis_pass@localhost:6379/0"
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "allo_admin"
    s3_secret_key: str = "allo_minio_pass"
    port: int = 8003

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
