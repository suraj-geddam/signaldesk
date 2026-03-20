CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(10) NOT NULL CHECK (role IN ('admin', 'member')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feedback (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,
    source          VARCHAR(20) NOT NULL CHECK (source IN ('email', 'call', 'slack', 'chat', 'other')),
    priority        VARCHAR(10) NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
    status          VARCHAR(15) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'in_progress', 'done')),
    created_by      UUID NOT NULL REFERENCES users(id),
    idempotency_key VARCHAR(100) UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_feedback_updated_at ON feedback;
CREATE TRIGGER trg_feedback_updated_at
    BEFORE UPDATE ON feedback
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback (created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback (status);
CREATE INDEX IF NOT EXISTS idx_feedback_status_priority ON feedback (status, priority);
CREATE INDEX IF NOT EXISTS idx_feedback_trgm ON feedback USING gin ((title || ' ' || description) gin_trgm_ops);

CREATE TABLE IF NOT EXISTS ai_summaries (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insights       JSONB NOT NULL,
    feedback_hash  VARCHAR(64) NOT NULL,
    feedback_count INTEGER NOT NULL,
    model_used     VARCHAR(50) NOT NULL,
    generated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_summaries_generated_at ON ai_summaries (generated_at DESC);
