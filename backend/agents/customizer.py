from openai import OpenAI
import json
from config import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER
import os
import uuid

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def customize_for_job(profile: dict, job: dict) -> dict:
    """Generate a tailored CV and cover letter for a specific job."""
    structured = profile.get("structured", {})

    prompt = f"""You are a professional CV writer and career coach. Your job is to tailor a candidate's CV and write a compelling cover letter for a specific job.

CANDIDATE PROFILE:
{json.dumps(structured, indent=2)}

JOB DETAILS:
Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Description: {job.get('description', '')}
Requirements: {job.get('requirements', '')}

INSTRUCTIONS:
1. Rewrite the candidate's summary to directly address this role.
2. Reorder and rephrase experience bullet points to highlight the most relevant achievements.
3. Emphasize relevant skills.
4. Write a personalized cover letter (3-4 paragraphs) that:
   - Opens with genuine enthusiasm (NOT "I am writing to apply")
   - Shows you understand the company and role
   - Links 2-3 specific achievements to the job requirements
   - Ends with confident call to action
   - Sounds 100% human — no AI tells, no generic phrases
   - Uses the candidate's real name and real experience
   - DO NOT mention AI, automation, or that this was generated

Return ONLY valid JSON:
{{
  "custom_summary": "rewritten summary targeting this role",
  "relevant_skills": ["skill1", "skill2"],
  "experience_highlights": [
    {{
      "title": "Job Title",
      "company": "Company",
      "start_date": "date",
      "end_date": "date",
      "achievements": ["tailored bullet 1", "tailored bullet 2"]
    }}
  ],
  "cover_letter": "full cover letter text with \\n for newlines",
  "email_subject": "Application for [Job Title] – [Candidate Name]",
  "email_body": "professional email body (2-3 sentences) to attach CV and cover letter, sounds human"
}}"""

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def _get_user_info(structured: dict) -> dict:
    """Extract personal info from parsed CV structured data."""
    name = structured.get("name", "")
    first = structured.get("first_name") or (name.split()[0] if name else "")
    last = structured.get("last_name") or (" ".join(name.split()[1:]) if name and len(name.split()) > 1 else "")
    return {
        "name": name,
        "first_name": first,
        "last_name": last,
        "email": structured.get("email", settings.EMAIL_ADDRESS),
        "phone": structured.get("phone", ""),
        "location": structured.get("location", ""),
        "linkedin": structured.get("linkedin", ""),
        "github": structured.get("github", ""),
        "website": structured.get("website", ""),
    }


def generate_cv_pdf(profile: dict, customization: dict, output_dir: str = "/app/generated") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"cv_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(output_dir, filename)

    structured = profile.get("structured", {})
    user = _get_user_info(structured)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    name_style = ParagraphStyle("name", fontSize=22, fontName="Helvetica-Bold",
                                 textColor=colors.HexColor("#1a1a2e"), spaceAfter=4, alignment=TA_CENTER)
    contact_style = ParagraphStyle("contact", fontSize=9, fontName="Helvetica",
                                    textColor=colors.HexColor("#555555"), spaceAfter=12, alignment=TA_CENTER)
    section_style = ParagraphStyle("section", fontSize=11, fontName="Helvetica-Bold",
                                    textColor=colors.HexColor("#1a1a2e"), spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("body", fontSize=9.5, fontName="Helvetica", leading=14, spaceAfter=4)
    bullet_style = ParagraphStyle("bullet", fontSize=9.5, fontName="Helvetica",
                                   leading=14, leftIndent=12, spaceAfter=2)
    job_title_style = ParagraphStyle("job_title", fontSize=10, fontName="Helvetica-Bold", spaceAfter=0)
    job_meta_style = ParagraphStyle("job_meta", fontSize=9, fontName="Helvetica",
                                     textColor=colors.HexColor("#666666"), spaceAfter=4)

    story = []
    story.append(Paragraph(user["name"], name_style))

    contacts = [c for c in [user["email"], user["phone"], user["location"], user["linkedin"]] if c]
    story.append(Paragraph(" · ".join(contacts), contact_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 6))

    summary = customization.get("custom_summary") or structured.get("summary", "")
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 4))
        story.append(Paragraph(summary, body_style))

    skills = customization.get("relevant_skills") or structured.get("skills", [])
    if skills:
        story.append(Paragraph("SKILLS", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 4))
        story.append(Paragraph(" · ".join(skills), body_style))

    experience = customization.get("experience_highlights") or structured.get("experience", [])
    if experience:
        story.append(Paragraph("EXPERIENCE", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 4))
        for exp in experience:
            story.append(Paragraph(f"{exp.get('title', '')} — {exp.get('company', '')}", job_title_style))
            story.append(Paragraph(f"{exp.get('start_date', '')} – {exp.get('end_date', '')}", job_meta_style))
            for bullet in exp.get("achievements", []):
                story.append(Paragraph(f"• {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    for edu in structured.get("education", []):
        story.append(Paragraph("EDUCATION", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"{edu.get('degree')} — {edu.get('institution')}", job_title_style))
        meta = f"{edu.get('start_date', '')} – {edu.get('end_date', '')}"
        if edu.get("gpa"):
            meta += f" | GPA: {edu['gpa']}"
        story.append(Paragraph(meta, job_meta_style))

    languages = structured.get("languages", [])
    if languages:
        story.append(Paragraph("LANGUAGES", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 4))
        story.append(Paragraph(" · ".join([f"{l['language']} ({l['level']})" for l in languages]), body_style))

    doc.build(story)
    return filepath


def generate_cover_letter_pdf(cover_letter_text: str, profile: dict,
                               job: dict, output_dir: str = "/app/generated") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"cl_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(output_dir, filename)

    structured = profile.get("structured", {})
    user = _get_user_info(structured)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=2.5*cm, leftMargin=2.5*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)

    header_style = ParagraphStyle("header", fontSize=13, fontName="Helvetica-Bold",
                                   textColor=colors.HexColor("#1a1a2e"), spaceAfter=4)
    meta_style = ParagraphStyle("meta", fontSize=9, fontName="Helvetica",
                                 textColor=colors.HexColor("#666666"), spaceAfter=16)
    body_style = ParagraphStyle("body", fontSize=10.5, fontName="Helvetica", leading=16, spaceAfter=12)

    story = []
    story.append(Paragraph(user["name"], header_style))
    contacts = " · ".join(filter(None, [user["email"], user["phone"], user["location"]]))
    story.append(Paragraph(contacts, meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 20))

    from datetime import datetime
    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), body_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Hiring Team<br/>{job.get('company', '')}", body_style))
    story.append(Spacer(1, 8))

    for paragraph in cover_letter_text.split("\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), body_style))

    story.append(Spacer(1, 20))
    story.append(Paragraph("Sincerely,", body_style))
    story.append(Paragraph(f"<b>{user['name']}</b>", body_style))

    doc.build(story)
    return filepath
