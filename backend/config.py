from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://jobbot:changeme@postgres:5432/jobbot"
    REDIS_URL: str = "redis://redis:6379/0"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.5-mini-2026-03-17"
    SECRET_KEY: str = "change-this-secret"

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
