from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

load_dotenv()

class Settings(BaseSettings):
    # App
    app_name: str = Field(default="Task Manager", validation_alias="APP_NAME")
    app_description: str = Field(default="My graduation project", validation_alias="APP_DESCRIPTION")
    app_version: str = Field(default="1.0", validation_alias="APP_VERSION")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    
    # Database
    postgres_user: str = Field(..., validation_alias="POSTGRES_USER")
    postgres_password: str = Field(..., validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., validation_alias="POSTGRES_DB")
    database_url: str = Field(..., validation_alias="DATABASE_URL")
    test_database_url: str = Field(default=None, validation_alias="TEST_DATABASE_URL")
    
    
    # JWT
    jwt_secret_key: str = Field(..., validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Redis 
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_url: str = Field(default=None, validation_alias="REDIS_URL")
    
    # Celery
    celery_broker_url: str = Field(..., env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")

    celery_database_url: str = Field(..., env="CELERY_DATABASE_URL")


    # GigaChat
    gigachat_credentials: str = Field(..., env="GIGACHAT_CREDENTIALS")
    gigachat_scope: str = Field(default="GIGACHAT_API_PERS", env="GIGACHAT_SCOPE")
    gigachat_model: str = Field(default="GigaChat", env="GIGACHAT_MODEL")
    gigachat_temperature: float = Field(default=0.1, env="GIGACHAT_TEMPERATURE")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


    


settings = Settings()