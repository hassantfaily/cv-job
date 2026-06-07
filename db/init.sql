CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_text TEXT,
    structured JSONB,
    file_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    requirements TEXT,
    salary_range TEXT,
    job_type TEXT,
    source TEXT NOT NULL,
    source_url TEXT UNIQUE,
    source_id TEXT,
    portal_url TEXT,
    hr_email TEXT,
    contact_name TEXT,
    posted_at TIMESTAMPTZ,
    deadline TIMESTAMPTZ,
    status TEXT DEFAULT 'found',
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id),
    profile_id UUID REFERENCES profiles(id),
    status TEXT DEFAULT 'pending',
    method TEXT,
    custom_cv_path TEXT,
    cover_letter_path TEXT,
    custom_cv_text TEXT,
    cover_letter_text TEXT,
    email_sent_at TIMESTAMPTZ,
    portal_applied_at TIMESTAMPTZ,
    email_to TEXT,
    subject TEXT,
    notes TEXT,
    error TEXT,
    task_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query TEXT,
    location TEXT,
    sources JSONB,
    jobs_found INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
