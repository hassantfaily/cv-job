from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from models import Profile

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    from config import settings

    # Pull user info from the latest parsed CV profile
    result = await db.execute(select(Profile).order_by(desc(Profile.created_at)).limit(1))
    profile = result.scalar_one_or_none()
    s = (profile.structured or {}) if profile else {}
    name = s.get("name", "")

    return {
        "email": {
            "provider": settings.EMAIL_PROVIDER,
            "address": settings.EMAIL_ADDRESS,
            "display_name": settings.EMAIL_DISPLAY_NAME or name,
            "configured": bool(settings.EMAIL_ADDRESS and settings.EMAIL_PASSWORD),
        },
        "user": {
            "name": name,
            "email": s.get("email", ""),
            "phone": s.get("phone", ""),
            "location": s.get("location", ""),
            "linkedin_url": s.get("linkedin", ""),
            "github_url": s.get("github", ""),
            "source": "parsed from CV" if profile else "no CV uploaded yet",
        },
        "ai": {
            "provider": "OpenAI",
            "model": settings.OPENAI_MODEL,
            "configured": bool(settings.OPENAI_API_KEY),
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
