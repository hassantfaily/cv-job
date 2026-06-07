from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import portal_agent

app = FastAPI(title="JobBot Browser Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LinkedInSearchRequest(BaseModel):
    query: str
    location: str = ""
    limit: int = 20


class UserInfo(BaseModel):
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""


class PortalApplyRequest(BaseModel):
    portal_url: str
    cv_path: str
    cover_letter_path: str = ""
    cover_letter_text: str = ""
    job_title: str = ""
    create_account: bool = False
    user_info: UserInfo = UserInfo()


class JobDetailRequest(BaseModel):
    url: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/linkedin/search")
async def linkedin_search(req: LinkedInSearchRequest):
    jobs = await portal_agent.search_linkedin_jobs(req.query, req.location, req.limit)
    return {"jobs": jobs, "count": len(jobs)}


@app.post("/linkedin/job-details")
async def linkedin_job_details(req: JobDetailRequest):
    details = await portal_agent.get_linkedin_job_details(req.url)
    return details


@app.post("/portal/apply")
async def portal_apply(req: PortalApplyRequest):
    user_info = req.user_info.model_dump()

    if req.create_account:
        result = await portal_agent.create_account_and_apply(
            req.portal_url, req.cv_path, req.cover_letter_text, user_info
        )
        if result["success"]:
            apply_result = await portal_agent.apply_on_portal(
                req.portal_url, req.cv_path, req.cover_letter_path,
                req.cover_letter_text, req.job_title, user_info
            )
            return {"account": result, "application": apply_result}
        return {"account": result, "application": None}

    result = await portal_agent.apply_on_portal(
        req.portal_url, req.cv_path, req.cover_letter_path,
        req.cover_letter_text, req.job_title, user_info
    )
    return result
