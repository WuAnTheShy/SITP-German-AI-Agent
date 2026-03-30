"""move legacy startup db patches into alembic

Revision ID: 20260330_0002
Revises: 20260330_0001
Create Date: 2026-03-30 00:30:00

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260330_0002"
down_revision = "20260330_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Exams and assignments schema updates
    op.execute("ALTER TABLE exams ADD COLUMN IF NOT EXISTS content JSONB DEFAULT '[]'::jsonb NOT NULL")
    op.execute("ALTER TABLE exam_assignments ADD COLUMN IF NOT EXISTS personalized_content JSONB")

    # Homework constraints/columns for exam linkage
    op.execute("ALTER TABLE homeworks DROP CONSTRAINT IF EXISTS ck_homeworks_file_type")
    op.execute("ALTER TABLE homeworks DROP CONSTRAINT IF EXISTS homeworks_file_type_check")
    op.execute("ALTER TABLE homeworks ADD COLUMN IF NOT EXISTS exam_assignment_id INTEGER")

    # Teacher research chat tables
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS teacher_chat_sessions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS teacher_chat_messages (
            id BIGSERIAL PRIMARY KEY,
            session_id BIGINT NOT NULL REFERENCES teacher_chat_sessions(id) ON DELETE CASCADE,
            role VARCHAR(16) NOT NULL CHECK (role IN ('user','assistant')),
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_teacher_chat_sessions_user ON teacher_chat_sessions(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_teacher_chat_messages_session ON teacher_chat_messages(session_id)")

    # Agent memory columns
    op.execute("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ NULL")
    op.execute("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
    op.execute("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS title VARCHAR(128) NULL")

    op.execute("ALTER TABLE teacher_chat_sessions ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ NULL")
    op.execute("ALTER TABLE teacher_chat_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
    op.execute("ALTER TABLE teacher_chat_sessions ADD COLUMN IF NOT EXISTS title VARCHAR(128) NULL")

    op.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS long_memory_summary TEXT NULL")
    op.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS memory_updated_at TIMESTAMPTZ NULL")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS long_memory_summary TEXT NULL")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS memory_updated_at TIMESTAMPTZ NULL")

    op.execute("UPDATE chat_sessions SET updated_at = created_at WHERE updated_at < created_at OR updated_at IS NULL")
    op.execute(
        "UPDATE teacher_chat_sessions SET updated_at = created_at WHERE updated_at < created_at OR updated_at IS NULL"
    )

    # status columns on users/students
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'approved'")
    op.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'approved'")

    # system settings
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            id SERIAL PRIMARY KEY,
            setting_key VARCHAR(64) UNIQUE NOT NULL,
            setting_value VARCHAR(255) NOT NULL,
            description TEXT
        )
        """
    )

    # users role and optional relation columns
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_role")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check")
    op.execute("ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK (role IN ('teacher', 'student', 'admin'))")

    op.execute("ALTER TABLE students ALTER COLUMN class_id DROP NOT NULL")
    op.execute("ALTER TABLE classes ALTER COLUMN teacher_user_id DROP NOT NULL")

    # class relation tables and backfill
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS class_teacher_relations (
            id BIGSERIAL PRIMARY KEY,
            class_id BIGINT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
            teacher_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (class_id, teacher_user_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS class_student_relations (
            id BIGSERIAL PRIMARY KEY,
            class_id BIGINT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
            student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (class_id, student_id)
        )
        """
    )

    op.execute(
        """
        INSERT INTO class_teacher_relations (class_id, teacher_user_id)
        SELECT id, teacher_user_id FROM classes WHERE teacher_user_id IS NOT NULL
        ON CONFLICT (class_id, teacher_user_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO class_student_relations (class_id, student_id)
        SELECT class_id, id FROM students WHERE class_id IS NOT NULL
        ON CONFLICT (class_id, student_id) DO NOTHING
        """
    )


def downgrade() -> None:
    # Intentionally conservative: do not attempt destructive rollback of legacy compatibility patches.
    pass
