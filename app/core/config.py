from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


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
    redis_url: str = Field(default=None, validation_alias="REDIS_URL")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


    


settings = Settings()