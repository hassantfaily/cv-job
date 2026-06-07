"""
Job search agent — scrapes multiple sources.
LinkedIn + Indeed use the browser service (Playwright).
RemoteOK and others use HTTP APIs.
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re

async def search_remoteok(query: str, limit: int = 20) -> List[Dict]:
    """RemoteOK has a public JSON API."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                "https://remoteok.com/api",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            data = r.json()
            for item in data[1:]:  # first item is metadata
                if not isinstance(item, dict):
                    continue
                title = item.get("position", "")
                if query.lower() not in title.lower() and query.lower() not in item.get("tags", []):
                    continue
                jobs.append({
                    "title": title,
                    "company": item.get("company", ""),
                    "location": "Remote",
                    "description": BeautifulSoup(item.get("description", ""), "html.parser").get_text(),
                    "source": "remoteok",
                    "source_url": item.get("url", ""),
                    "source_id": str(item.get("id", "")),
                    "job_type": "remote",
                    "salary_range": item.get("salary", ""),
                    "raw_data": item,
                })
                if len(jobs) >= limit:
                    break
    except Exception as e:
        print(f"RemoteOK error: {e}")
    return jobs


async def search_arbeitnow(query: str, location: str = "", limit: int = 20) -> List[Dict]:
    """Arbeitnow has a public job board API."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                "https://www.arbeitnow.com/api/job-board-api",
                params={"search": query, "location": location},
                headers={"User-Agent": "Mozilla/5.0"},
            )
            data = r.json()
            for item in data.get("data", [])[:limit]:
                jobs.append({
                    "title": item.get("title", ""),
                    "company": item.get("company_name", ""),
                    "location": item.get("location", ""),
                    "description": BeautifulSoup(item.get("description", ""), "html.parser").get_text(),
                    "source": "arbeitnow",
                    "source_url": item.get("url", ""),
                    "source_id": item.get("slug", ""),
                    "job_type": "remote" if item.get("remote") else "onsite",
                    "raw_data": item,
                })
    except Exception as e:
        print(f"Arbeitnow error: {e}")
    return jobs


async def search_github_jobs_workaround(query: str, limit: int = 20) -> List[Dict]:
    """Search jobs via TheMuseAPI (free, no auth needed for basic)."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                "https://www.themuse.com/api/public/jobs",
                params={"descending": "true", "page": 1, "level": ""},
                headers={"User-Agent": "Mozilla/5.0"},
            )
            data = r.json()
            for item in data.get("results", [])[:limit]:
                title = item.get("name", "")
                if query.lower() not in title.lower():
                    continue
                company = item.get("company", {}).get("name", "")
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": ", ".join([l.get("name", "") for l in item.get("locations", [])]),
                    "description": BeautifulSoup(item.get("contents", ""), "html.parser").get_text(),
                    "source": "themuse",
                    "source_url": item.get("refs", {}).get("landing_page", ""),
                    "source_id": str(item.get("id", "")),
                    "raw_data": item,
                })
    except Exception as e:
        print(f"TheMuse error: {e}")
    return jobs


def extract_hr_email(text: str) -> Optional[str]:
    """Try to extract a contact email from job description."""
    if not text:
        return None
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    emails = re.findall(pattern, text)
    for email in emails:
        if any(kw in email.lower() for kw in ["hr", "recruit", "talent", "career", "job", "hiring", "people"]):
            return email
    return emails[0] if emails else None
