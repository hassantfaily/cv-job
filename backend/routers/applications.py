from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from models import Application, Job, Profile
from tasks.celery_app import apply_job_task
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter(prefix="/api/applications", tags=["applications"])


class ApplyRequest(BaseModel):
    job_id: str
    profile_id: str
    method: str = "email"
    hr_email: Optional[str] = None


@router.post("")
async def create_application(req: ApplyRequest, db: AsyncSession = Depends(get_db)):
    app = Application(
        job_id=uuid.UUID(req.job_id),
        profile_id=uuid.UUID(req.profile_id),
        method=req.method,
        email_to=req.hr_email,
        status="pending",
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)

    task = apply_job_task.delay(str(app.id))
    app.task_id = task.id
    await db.commit()

    return {"application_id": str(app.id), "task_id": task.id, "status": "pending"}


@router.post("/bulk")
async def bulk_apply(
    job_ids: list[str],
    profile_id: str,
    method: str = "email",
    db: AsyncSession = Depends(get_db),
):
    results = []
    for job_id in job_ids:
        job_result = await db.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
        job = job_result.scalar_one_or_none()
        if not job:
            continue
        app = Application(
            job_id=uuid.UUID(job_id),
            profile_id=uuid.UUID(profile_id),
            method=method,
            email_to=job.hr_email,
            status="pending",
        )
        db.add(app)
        await db.commit()
        await db.refresh(app)
        task = apply_job_task.delay(str(app.id))
        app.task_id = task.id
        await db.commit()
        results.append({"job_id": job_id, "application_id": str(app.id)})
    return results


@router.get("")
async def list_applications(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Application, Job).join(Job, Application.job_id == Job.id).order_by(
        desc(Application.created_at)
    )
    if status:
        stmt = stmt.where(Application.status == status)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": str(a.id),
            "status": a.status,
            "method": a.method,
            "email_to": a.email_to,
            "subject": a.subject,
            "email_sent_at": a.email_sent_at,
            "created_at": a.created_at,
            "job": {"id": str(j.id), "title": j.title, "company": j.company, "location": j.location},
        }
        for a, j in rows
    ]


@router.get("/{app_id}")
async def get_application(app_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Application).where(Application.id == uuid.UUID(app_id)))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404)
    return {
        "id": str(app.id), "status": app.status, "method": app.method,
        "cover_letter_text": app.cover_letter_text, "subject": app.subject,
        "email_to": app.email_to, "error": app.error, "task_id": app.task_id,
        "email_sent_at": app.email_sent_at, "created_at": app.created_at,
    }


@router.get("/{app_id}/cv")
async def download_cv(app_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Application).where(Application.id == uuid.UUID(app_id)))
    app = result.scalar_one_or_none()
    if not app or not app.custom_cv_path:
        raise HTTPException(404)
    return FileResponse(app.custom_cv_path, media_type="application/pdf")


@router.get("/{app_id}/cover-letter")
async def download_cover_letter(app_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Application).where(Application.id == uuid.UUID(app_id)))
    app = result.scalar_one_or_none()
    if not app or not app.cover_letter_path:
        raise HTTPException(404)
    return FileResponse(app.cover_letter_path, media_type="application/pdf")


@router.get("/stats/summary")
async def stats(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    result = await db.execute(
        select(Application.status, func.count(Application.id).label("count"))
        .group_by(Application.status)
    )
    rows = result.all()
    return {r.status: r.count for r in rows}
