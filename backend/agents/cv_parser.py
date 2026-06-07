import pdfplumber
import anthropic
from config import settings
import json

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def parse_cv(file_path: str) -> dict:
    raw_text = extract_text_from_pdf(file_path)

    prompt = f"""You are parsing a CV/resume. Extract all information and return a structured JSON object.

CV TEXT:
{raw_text}

Return ONLY valid JSON with this structure:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "phone number",
  "location": "city, country",
  "linkedin": "url or null",
  "github": "url or null",
  "website": "url or null",
  "summary": "professional summary paragraph",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "location": "City, Country",
      "start_date": "Month Year",
      "end_date": "Month Year or Present",
      "description": "role description",
      "achievements": ["achievement 1", "achievement 2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "institution": "School Name",
      "location": "City, Country",
      "start_date": "Year",
      "end_date": "Year",
      "gpa": "GPA or null",
      "relevant_courses": []
    }}
  ],
  "certifications": ["cert 1", "cert 2"],
  "languages": [
    {{"language": "English", "level": "Native"}}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "what it does",
      "technologies": ["tech1"],
      "url": "url or null"
    }}
  ]
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    response_text = response_text.strip().rstrip("```")

    return {"raw_text": raw_text, "structured": json.loads(response_text)}
