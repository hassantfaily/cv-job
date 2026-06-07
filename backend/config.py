from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://jobbot:changeme@postgres:5432/jobbot"
    REDIS_URL: str = "redis://redis:6379/0"
    ANTHROPIC_API_KEY: str = ""
    SECRET_KEY: str = "change-this-secret"

    USER_FIRST_NAME: str = ""
    USER_LAST_NAME: str = ""
    USER_PHONE: str = ""
    USER_LOCATION: str = ""
    USER_LINKEDIN_URL: str = ""
    USER_GITHUB_URL: str = ""
    USER_WEBSITE: str = ""

    EMAIL_PROVIDER: str = "gmail"
    EMAIL_ADDRESS: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_DISPLAY_NAME: str = ""
    ICLOUD_EMAIL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587

    BROWSER_SERVICE_URL: str = "http://browser:8001"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
