from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    EMAIL_ADDRESS: str = ""
    EMAIL_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
