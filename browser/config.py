from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_FIRST_NAME: str = ""
    USER_LAST_NAME: str = ""
    USER_PHONE: str = ""
    USER_LOCATION: str = ""
    USER_LINKEDIN_URL: str = ""
    EMAIL_ADDRESS: str = ""
    EMAIL_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
