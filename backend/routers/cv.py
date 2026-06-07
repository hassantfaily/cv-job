from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Profile
from tasks.celery_app import parse_cv_task
import shutil
import os
import uuid

router = APIRouter(prefix="/api/cv", tags=["cv"])

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_cv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    file_id = uuid.uuid4().hex
    filename = f"{file_id}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    profile = Profile(file_path=filepath)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    task = parse_cv_task.delay(filepath, str(profile.id))

    return {"profile_id": str(profile.id), "task_id": task.id, "status": "parsing"}


@router.get("/profile/{profile_id}")
async def get_profile(profile_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).where(Profile.id == uuid.UUID(profile_id)))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found")
    return {
        "id": str(profile.id),
        "structured": profile.structured,
        "file_path": profile.file_path,
        "created_at": profile.created_at,
    }


@router.get("/profiles")
async def list_profiles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).order_by(Profile.created_at.desc()))
    profiles = result.scalars().all()
    return [{"id": str(p.id), "name": (p.structured or {}).get("name", "Unknown"),
             "created_at": p.created_at} for p in profiles]
