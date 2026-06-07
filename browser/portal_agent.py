"""
Portal agent: uses Playwright to apply on company portals.
Handles account creation, form filling, and CV upload.
"""
from playwright.async_api import async_playwright, Page
from tenacity import retry, stop_after_attempt, wait_fixed
from config import settings
import asyncio
import os

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


async def get_browser():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    )
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
    )
    return pw, browser, context


async def search_linkedin_jobs(query: str, location: str = "", limit: int = 20) -> list:
    """Scrape LinkedIn public job listings (no login needed for basic search)."""
    pw, browser, context = await get_browser()
    jobs = []
    try:
        page = await context.new_page()
        url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}&f_TPR=r86400"
        await page.goto(url, timeout=30000)
        await page.wait_for_selector(".jobs-search__results-list", timeout=15000)

        items = await page.query_selector_all(".jobs-search__results-list > li")
        for item in items[:limit]:
            try:
                title_el = await item.query_selector(".base-search-card__title")
                company_el = await item.query_selector(".base-search-card__subtitle")
                location_el = await item.query_selector(".job-search-card__location")
                link_el = await item.query_selector("a.base-card__full-link")

                title = await title_el.inner_text() if title_el else ""
                company = await company_el.inner_text() if company_el else ""
                loc = await location_el.inner_text() if location_el else ""
                href = await link_el.get_attribute("href") if link_el else ""

                jobs.append({
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": loc.strip(),
                    "source": "linkedin",
                    "source_url": href.split("?")[0] if href else "",
                    "description": "",
                })
            except Exception:
                continue
    finally:
        await browser.close()
        await pw.stop()
    return jobs


async def get_linkedin_job_details(url: str) -> dict:
    pw, browser, context = await get_browser()
    try:
        page = await context.new_page()
        await page.goto(url, timeout=30000)
        await page.wait_for_selector(".show-more-less-html", timeout=10000)
        desc_el = await page.query_selector(".show-more-less-html")
        description = await desc_el.inner_text() if desc_el else ""
        return {"description": description.strip()}
    except Exception:
        return {}
    finally:
        await browser.close()
        await pw.stop()


async def apply_on_portal(
    portal_url: str,
    cv_path: str,
    cover_letter_path: str,
    cover_letter_text: str,
    job_title: str,
) -> dict:
    """
    Generic portal application handler.
    Detects common ATS platforms and applies.
    """
    pw, browser, context = await get_browser()
    result = {"success": False, "message": ""}
    try:
        page = await context.new_page()
        await page.goto(portal_url, timeout=30000)
        await asyncio.sleep(2)

        url = page.url.lower()

        if "greenhouse.io" in url or "boards.greenhouse" in url:
            result = await _apply_greenhouse(page, cv_path, cover_letter_text)
        elif "lever.co" in url:
            result = await _apply_lever(page, cv_path, cover_letter_text)
        elif "workday" in url:
            result = await _apply_workday(page, cv_path, cover_letter_path)
        elif "myworkdayjobs" in url:
            result = await _apply_workday(page, cv_path, cover_letter_path)
        else:
            result = await _apply_generic(page, cv_path, cover_letter_text, job_title)

    except Exception as e:
        result = {"success": False, "message": str(e)}
    finally:
        await browser.close()
        await pw.stop()
    return result


async def _fill_common_fields(page: Page, cover_letter_text: str):
    """Fill name, email, phone in any form."""
    field_map = {
        "first.name|first_name|firstname": settings.USER_FIRST_NAME,
        "last.name|last_name|lastname": settings.USER_LAST_NAME,
        "email": settings.EMAIL_ADDRESS,
        "phone|telephone": settings.USER_PHONE,
        "linkedin": settings.USER_LINKEDIN_URL,
        "cover.letter|coverletter|cover_letter": cover_letter_text,
    }
    inputs = await page.query_selector_all("input, textarea")
    for inp in inputs:
        name = (await inp.get_attribute("name") or "").lower()
        placeholder = (await inp.get_attribute("placeholder") or "").lower()
        id_attr = (await inp.get_attribute("id") or "").lower()
        combined = f"{name} {placeholder} {id_attr}"

        for pattern, value in field_map.items():
            if any(p in combined for p in pattern.split("|")) and value:
                try:
                    await inp.fill(value)
                except Exception:
                    pass
                break


async def _apply_greenhouse(page: Page, cv_path: str, cover_letter_text: str) -> dict:
    await _fill_common_fields(page, cover_letter_text)
    file_inputs = await page.query_selector_all("input[type='file']")
    if file_inputs and cv_path and os.path.exists(cv_path):
        await file_inputs[0].set_input_files(cv_path)
    submit = await page.query_selector("input[type='submit'], button[type='submit']")
    if submit:
        await submit.click()
        await asyncio.sleep(3)
        return {"success": True, "message": "Submitted via Greenhouse"}
    return {"success": False, "message": "No submit button found"}


async def _apply_lever(page: Page, cv_path: str, cover_letter_text: str) -> dict:
    await _fill_common_fields(page, cover_letter_text)
    file_inputs = await page.query_selector_all("input[type='file']")
    if file_inputs and cv_path and os.path.exists(cv_path):
        await file_inputs[0].set_input_files(cv_path)
    submit = await page.query_selector("button[type='submit']")
    if submit:
        await submit.click()
        await asyncio.sleep(3)
        return {"success": True, "message": "Submitted via Lever"}
    return {"success": False, "message": "No submit button found"}


async def _apply_workday(page: Page, cv_path: str, cover_letter_path: str) -> dict:
    await asyncio.sleep(2)
    file_inputs = await page.query_selector_all("input[type='file']")
    if file_inputs and cv_path and os.path.exists(cv_path):
        await file_inputs[0].set_input_files(cv_path)
        if len(file_inputs) > 1 and cover_letter_path and os.path.exists(cover_letter_path):
            await file_inputs[1].set_input_files(cover_letter_path)
    return {"success": False, "message": "Workday requires manual steps — CV uploaded"}


async def _apply_generic(page: Page, cv_path: str, cover_letter_text: str, job_title: str) -> dict:
    await _fill_common_fields(page, cover_letter_text)
    file_inputs = await page.query_selector_all("input[type='file']")
    if file_inputs and cv_path and os.path.exists(cv_path):
        await file_inputs[0].set_input_files(cv_path)
    submit = await page.query_selector(
        "button[type='submit'], input[type='submit'], button:has-text('Apply'), button:has-text('Submit')"
    )
    if submit:
        await submit.click()
        await asyncio.sleep(3)
        return {"success": True, "message": "Submitted via generic form"}
    return {"success": False, "message": "Could not find submit — manual review needed"}


async def create_account_and_apply(
    portal_url: str,
    cv_path: str,
    cover_letter_text: str,
) -> dict:
    """
    Auto-create account if portal requires login, then apply.
    Uses the user's email as the account email.
    """
    pw, browser, context = await get_browser()
    result = {"success": False, "message": ""}
    try:
        page = await context.new_page()
        await page.goto(portal_url, timeout=30000)

        sign_up = await page.query_selector(
            "a:has-text('Sign up'), a:has-text('Register'), a:has-text('Create account'), "
            "button:has-text('Sign up'), button:has-text('Register')"
        )
        if sign_up:
            await sign_up.click()
            await asyncio.sleep(2)
            await _fill_common_fields(page, cover_letter_text)
            password_inputs = await page.query_selector_all("input[type='password']")
            generated_pwd = f"Jobbot@{settings.USER_FIRST_NAME}2024!"
            for pwd_input in password_inputs:
                await pwd_input.fill(generated_pwd)
            submit = await page.query_selector("button[type='submit'], input[type='submit']")
            if submit:
                await submit.click()
                await asyncio.sleep(3)
                result = {"success": True, "message": f"Account created. Password: {generated_pwd}"}
        else:
            result = {"success": False, "message": "No signup form detected"}
    except Exception as e:
        result = {"success": False, "message": str(e)}
    finally:
        await browser.close()
        await pw.stop()
    return result
