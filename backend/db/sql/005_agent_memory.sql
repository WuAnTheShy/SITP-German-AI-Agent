-- Agent memory: cross-day sessions + long summary
BEGIN;

ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ NULL;
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS title VARCHAR(128) NULL;
UPDATE chat_sessions SET updated_at = created_at WHERE updated_at IS NULL OR updated_at < created_at;

ALTER TABLE teacher_chat_sessions ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ NULL;
ALTER TABLE teacher_chat_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
UPDATE teacher_chat_sessions SET updated_at = created_at WHERE updated_at IS NULL OR updated_at < created_at;

ALTER TABLE students ADD COLUMN IF NOT EXISTS long_memory_summary TEXT NULL;
ALTER TABLE students ADD COLUMN IF NOT EXISTS memory_updated_at TIMESTAMPTZ NULL;

ALTER TABLE users ADD COLUMN IF NOT EXISTS long_memory_summary TEXT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS memory_updated_at TIMESTAMPTZ NULL;

COMMIT;
