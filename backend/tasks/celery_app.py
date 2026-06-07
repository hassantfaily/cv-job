from celery import Celery
from config import settings
import asyncio

celery = Celery("jobbot", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery.task(bind=True, name="tasks.parse_cv")
def parse_cv_task(self, file_path: str, profile_id: str):
    from agents.cv_parser import parse_cv
    from database import AsyncSessionLocal
    from models import Profile
    from sqlalchemy import select
    import uuid

    async def _run():
        result = parse_cv(file_path)
        async with AsyncSessionLocal() as db:
            stmt = select(Profile).where(Profile.id == uuid.UUID(profile_id))
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row:
                row.raw_text = result["raw_text"]
                row.structured = result["structured"]
                await db.commit()
        return result

    return run_async(_run())


@celery.task(bind=True, name="tasks.apply_job")
def apply_job_task(self, application_id: str):
    from database import AsyncSessionLocal
    from models import Application, Job, Profile
    from agents.customizer import customize_for_job, generate_cv_pdf, generate_cover_letter_pdf
    from agents.email_sender import send_application_email
    from sqlalchemy import select
    import uuid

    async def _run():
        async with AsyncSessionLocal() as db:
            stmt = select(Application).where(Application.id == uuid.UUID(application_id))
            app = (await db.execute(stmt)).scalar_one_or_none()
            if not app:
                return

            job_stmt = select(Job).where(Job.id == app.job_id)
            job = (await db.execute(job_stmt)).scalar_one_or_none()

            profile_stmt = select(Profile).where(Profile.id == app.profile_id)
            profile = (await db.execute(profile_stmt)).scalar_one_or_none()

            if not job or not profile:
                app.status = "error"
                app.error = "Missing job or profile"
                await db.commit()
                return

            try:
                app.status = "customizing"
                await db.commit()

                customization = customize_for_job(
                    {"structured": profile.structured, "raw_text": profile.raw_text},
                    {"title": job.title, "company": job.company, "location": job.location,
                     "description": job.description, "requirements": job.requirements}
                )

                cv_path = generate_cv_pdf(
                    {"structured": profile.structured},
                    customization
                )
                cl_path = generate_cover_letter_pdf(
                    customization.get("cover_letter", ""),
                    {"structured": profile.structured},
                    {"company": job.company, "title": job.title}
                )

                app.custom_cv_path = cv_path
                app.cover_letter_path = cl_path
                app.custom_cv_text = customization.get("cover_letter", "")
                app.cover_letter_text = customization.get("cover_letter", "")
                app.subject = customization.get("email_subject", f"Application – {job.title}")
                await db.commit()

                if app.method == "email" and app.email_to:
                    app.status = "sending"
                    await db.commit()
                    await send_application_email(
                        to_email=app.email_to,
                        subject=app.subject,
                        body=customization.get("email_body", ""),
                        cv_path=cv_path,
                        cover_letter_path=cl_path,
                    )
                    from datetime import datetime, timezone
                    app.email_sent_at = datetime.now(timezone.utc)
                    app.status = "sent"
                elif app.method == "portal" and job.portal_url:
                    s = profile.structured or {}
                    name = s.get("name", "")
                    parts = name.split()
                    user_info = {
                        "first_name": s.get("first_name") or (parts[0] if parts else ""),
                        "last_name": s.get("last_name") or (" ".join(parts[1:]) if len(parts) > 1 else ""),
                        "email": s.get("email", ""),
                        "phone": s.get("phone", ""),
                        "location": s.get("location", ""),
                        "linkedin": s.get("linkedin", ""),
                        "github": s.get("github", ""),
                        "website": s.get("website", ""),
                    }
                    import httpx as _httpx
                    async with _httpx.AsyncClient(timeout=120) as hc:
                        await hc.post(
                            f"{settings.BROWSER_SERVICE_URL}/portal/apply",
                            json={
                                "portal_url": job.portal_url,
                                "cv_path": cv_path,
                                "cover_letter_path": cl_path,
                                "cover_letter_text": customization.get("cover_letter", ""),
                                "job_title": job.title,
                                "create_account": True,
                                "user_info": user_info,
                            },
                        )
                    from datetime import datetime, timezone
                    app.portal_applied_at = datetime.now(timezone.utc)
                    app.status = "portal_pending"
                else:
                    app.status = "ready"
                await db.commit()

            except Exception as e:
                app.status = "error"
                app.error = str(e)
                await db.commit()
                raise

    run_async(_run())


@celery.task(bind=True, name="tasks.search_jobs")
def search_jobs_task(self, query: str, location: str, sources: list, search_run_id: str):
    from database import AsyncSessionLocal
    from models import Job, SearchRun
    from agents.job_searcher import (
        search_remoteok, search_arbeitnow, search_github_jobs_workaround, extract_hr_email
    )
    from sqlalchemy import select
    import uuid
    from datetime import datetime, timezone

    async def _run():
        all_jobs = []
        if "remoteok" in sources:
            all_jobs += await search_remoteok(query)
        if "arbeitnow" in sources:
            all_jobs += await search_arbeitnow(query, location)
        if "themuse" in sources:
            all_jobs += await search_github_jobs_workaround(query)

        async with AsyncSessionLocal() as db:
            saved = 0
            for j in all_jobs:
                if not j.get("source_url"):
                    continue
                existing = (await db.execute(
                    select(Job).where(Job.source_url == j["source_url"])
                )).scalar_one_or_none()
                if existing:
                    continue
                hr_email = extract_hr_email(j.get("description", ""))
                job = Job(
                    title=j["title"],
                    company=j["company"],
                    location=j.get("location", ""),
                    description=j.get("description", ""),
                    source=j["source"],
                    source_url=j["source_url"],
                    source_id=j.get("source_id"),
                    job_type=j.get("job_type"),
                    salary_range=j.get("salary_range"),
                    hr_email=hr_email,
                    raw_data=j.get("raw_data"),
                )
                db.add(job)
                saved += 1

            run_stmt = select(SearchRun).where(SearchRun.id == uuid.UUID(search_run_id))
            run = (await db.execute(run_stmt)).scalar_one_or_none()
            if run:
                run.jobs_found = saved
                run.status = "completed"
                run.finished_at = datetime.now(timezone.utc)

            await db.commit()
        return saved

    return run_async(_run())
