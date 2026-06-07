from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from database import Base

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_text = Column(Text)
    structured = Column(JSONB)
    file_path = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    company = Column(Text, nullable=False)
    location = Column(Text)
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(Text)
    job_type = Column(Text)
    source = Column(Text, nullable=False)
    source_url = Column(Text, unique=True)
    source_id = Column(Text)
    portal_url = Column(Text)
    hr_email = Column(Text)
    contact_name = Column(Text)
    posted_at = Column(DateTime(timezone=True))
    deadline = Column(DateTime(timezone=True))
    status = Column(Text, default="found")
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Application(Base):
    __tablename__ = "applications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    status = Column(Text, default="pending")
    method = Column(Text)
    custom_cv_path = Column(Text)
    cover_letter_path = Column(Text)
    custom_cv_text = Column(Text)
    cover_letter_text = Column(Text)
    email_sent_at = Column(DateTime(timezone=True))
    portal_applied_at = Column(DateTime(timezone=True))
    email_to = Column(Text)
    subject = Column(Text)
    notes = Column(Text)
    error = Column(Text)
    task_id = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class SearchRun(Base):
    __tablename__ = "search_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text)
    location = Column(Text)
    sources = Column(JSONB)
    jobs_found = Column(Integer, default=0)
    status = Column(Text, default="running")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
