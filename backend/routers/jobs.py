from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from models import Job, SearchRun
from tasks.celery_app import search_jobs_task
from pydantic import BaseModel
from typing import List, Optional
import uuid

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class SearchRequest(BaseModel):
    query: str
    location: Optional[str] = ""
    sources: List[str] = ["remoteok", "arbeitnow", "themuse"]


@router.post("/search")
async def start_search(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    run = SearchRun(query=req.query, location=req.location, sources=req.sources)
    db.add(run)
    await db.commit()
    await db.refresh(run)

    task = search_jobs_task.delay(req.query, req.location, req.sources, str(run.id))
    return {"search_run_id": str(run.id), "task_id": task.id}


@router.get("/search/{run_id}")
async def get_search_status(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchRun).where(SearchRun.id == uuid.UUID(run_id)))
    run = result.scalar_one_or_none()
    if not run:
        return {"status": "not_found"}
    return {"status": run.status, "jobs_found": run.jobs_found, "finished_at": run.finished_at}


@router.get("")
async def list_jobs(
    q: Optional[str] = None,
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Job).order_by(desc(Job.created_at))
    if q:
        stmt = stmt.where(Job.title.ilike(f"%{q}%") | Job.company.ilike(f"%{q}%"))
    if source:
        stmt = stmt.where(Job.source == source)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "source": j.source,
            "source_url": j.source_url,
            "salary_range": j.salary_range,
            "job_type": j.job_type,
            "hr_email": j.hr_email,
            "status": j.status,
            "created_at": j.created_at,
        }
        for j in jobs
    ]


@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        return {"error": "Not found"}
    return {
        "id": str(job.id), "title": job.title, "company": job.company,
        "location": job.location, "description": job.description,
        "requirements": job.requirements, "source": job.source,
        "source_url": job.source_url, "hr_email": job.hr_email,
        "portal_url": job.portal_url, "salary_range": job.salary_range,
        "job_type": job.job_type, "status": job.status,
    }
