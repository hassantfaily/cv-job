import anthropic
import json
from config import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os
import uuid

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

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

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip().rstrip("```")

    return json.loads(text)


def generate_cv_pdf(profile: dict, customization: dict, output_dir: str = "/app/generated") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"cv_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(output_dir, filename)

    structured = profile.get("structured", {})
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle("name", fontSize=22, fontName="Helvetica-Bold",
                                 textColor=colors.HexColor("#1a1a2e"), spaceAfter=4, alignment=TA_CENTER)
    contact_style = ParagraphStyle("contact", fontSize=9, fontName="Helvetica",
                                    textColor=colors.HexColor("#555555"), spaceAfter=12, alignment=TA_CENTER)
    section_style = ParagraphStyle("section", fontSize=11, fontName="Helvetica-Bold",
                                    textColor=colors.HexColor("#1a1a2e"), spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("body", fontSize=9.5, fontName="Helvetica",
                                 leading=14, spaceAfter=4)
    bullet_style = ParagraphStyle("bullet", fontSize=9.5, fontName="Helvetica",
                                   leading=14, leftIndent=12, spaceAfter=2)
    job_title_style = ParagraphStyle("job_title", fontSize=10, fontName="Helvetica-Bold",
                                      spaceAfter=0)
    job_meta_style = ParagraphStyle("job_meta", fontSize=9, fontName="Helvetica",
                                     textColor=colors.HexColor("#666666"), spaceAfter=4)

    story = []

    name = structured.get("name", settings.USER_FIRST_NAME + " " + settings.USER_LAST_NAME)
    story.append(Paragraph(name, name_style))

    contacts = []
    if structured.get("email"):
        contacts.append(structured["email"])
    if structured.get("phone"):
        contacts.append(structured["phone"])
    if structured.get("location"):
        contacts.append(structured["location"])
    if structured.get("linkedin"):
        contacts.append(structured["linkedin"])
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
            title = exp.get("title", "")
            company = exp.get("company", "")
            start = exp.get("start_date", "")
            end = exp.get("end_date", "")
            story.append(Paragraph(f"{title} — {company}", job_title_style))
            story.append(Paragraph(f"{start} – {end}", job_meta_style))
            for bullet in exp.get("achievements", []):
                story.append(Paragraph(f"• {bullet}", bullet_style))
            story.append(Spacer(1, 4))

    education = structured.get("education", [])
    if education:
        story.append(Paragraph("EDUCATION", section_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 4))
        for edu in education:
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
        lang_str = " · ".join([f"{l['language']} ({l['level']})" for l in languages])
        story.append(Paragraph(lang_str, body_style))

    doc.build(story)
    return filepath


def generate_cover_letter_pdf(cover_letter_text: str, profile: dict,
                               job: dict, output_dir: str = "/app/generated") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"cl_{uuid.uuid4().hex[:8]}.pdf"
    filepath = os.path.join(output_dir, filename)

    structured = profile.get("structured", {})
    name = structured.get("name", settings.USER_FIRST_NAME + " " + settings.USER_LAST_NAME)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=2.5*cm, leftMargin=2.5*cm,
                            topMargin=2.5*cm, bottomMargin=2.5*cm)

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle("header", fontSize=13, fontName="Helvetica-Bold",
                                   textColor=colors.HexColor("#1a1a2e"), spaceAfter=4)
    meta_style = ParagraphStyle("meta", fontSize=9, fontName="Helvetica",
                                 textColor=colors.HexColor("#666666"), spaceAfter=16)
    body_style = ParagraphStyle("body", fontSize=10.5, fontName="Helvetica",
                                 leading=16, spaceAfter=12)

    story = []
    story.append(Paragraph(name, header_style))
    contacts = " · ".join(filter(None, [
        structured.get("email"), structured.get("phone"), structured.get("location")
    ]))
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
    story.append(Paragraph(f"<b>{name}</b>", body_style))

    doc.build(story)
    return filepath
