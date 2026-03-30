"""add rag kb schema

Revision ID: 20260330_0001
Revises:
Create Date: 2026-03-30 00:00:00

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260330_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS kb_documents (
            id BIGSERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            source_name VARCHAR(255) NOT NULL,
            source_path TEXT NOT NULL,
            mime_type VARCHAR(128) NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'processing',
            scope VARCHAR(16) NOT NULL DEFAULT 'public',
            owner_user_id BIGINT NULL REFERENCES users(id) ON DELETE CASCADE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_temporary BOOLEAN NOT NULL DEFAULT FALSE,
            session_key VARCHAR(128) NULL,
            chunk_count INTEGER NOT NULL DEFAULT 0,
            error_message TEXT NULL,
            uploaded_by BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS kb_chunks (
            id BIGSERIAL PRIMARY KEY,
            document_id BIGINT NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            token_count INTEGER NOT NULL DEFAULT 0,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            embedding vector,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(document_id, chunk_index)
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS idx_kb_documents_status ON kb_documents(status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_kb_chunks_doc ON kb_chunks(document_id)")
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding_ivfflat
                ON kb_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'Skip idx_kb_chunks_embedding_ivfflat creation: %', SQLERRM;
            END;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_kb_chunks_embedding_ivfflat")
    op.execute("DROP INDEX IF EXISTS idx_kb_chunks_doc")
    op.execute("DROP INDEX IF EXISTS idx_kb_documents_status")
    op.execute("DROP TABLE IF EXISTS kb_chunks")
    op.execute("DROP TABLE IF EXISTS kb_documents")
