from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/settings", tags=["settings"])


class EmailSettings(BaseModel):
    provider: str
    address: str
    password: str
    display_name: str


class UserInfo(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    github_url: Optional[str] = ""
    website: Optional[str] = ""


@router.get("")
async def get_settings():
    from config import settings
    return {
        "email": {
            "provider": settings.EMAIL_PROVIDER,
            "address": settings.EMAIL_ADDRESS,
            "display_name": settings.EMAIL_DISPLAY_NAME,
            "configured": bool(settings.EMAIL_ADDRESS and settings.EMAIL_PASSWORD),
        },
        "user": {
            "first_name": settings.USER_FIRST_NAME,
            "last_name": settings.USER_LAST_NAME,
            "phone": settings.USER_PHONE,
            "location": settings.USER_LOCATION,
            "linkedin_url": settings.USER_LINKEDIN_URL,
        },
        "ai": {
            "model": "claude-sonnet-4-6",
            "configured": bool(settings.ANTHROPIC_API_KEY),
        },
    }


@router.post("/test-email")
async def test_email():
    from config import settings
    from agents.email_sender import send_application_email
    try:
        await send_application_email(
            to_email=settings.EMAIL_ADDRESS,
            subject="JobBot – Test Email",
            body="This is a test email from your JobBot system. Email sending is working correctly.",
            cv_path="",
            cover_letter_path="",
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
