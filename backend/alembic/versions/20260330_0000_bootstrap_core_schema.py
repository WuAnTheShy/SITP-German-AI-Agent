"""bootstrap core schema from legacy sql baseline

Revision ID: 20260330_0000
Revises:
Create Date: 2026-03-30 02:20:00

"""
from __future__ import annotations

from pathlib import Path

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "20260330_0000"
down_revision = None
branch_labels = None
depends_on = None


def _run_sql_file(file_name: str) -> None:
    base_dir = Path(__file__).resolve().parents[2]
    sql_file = base_dir / "db" / "sql" / file_name
    content = sql_file.read_text(encoding="utf-8")

    lines: list[str] = []
    for line in content.splitlines():
        marker = line.strip().upper()
        if marker in {"BEGIN;", "COMMIT;"}:
            continue
        lines.append(line)

    cleaned = "\n".join(lines)
    for chunk in cleaned.split(";"):
        statement = chunk.strip()
        if not statement:
            continue
        op.execute(text(statement))


def upgrade() -> None:
    # Build core app schema from existing SQL baselines so a fresh DB can start from Alembic only.
    _run_sql_file("001_init_schema.sql")
    _run_sql_file("003_student_schema.sql")


def downgrade() -> None:
    # Keep downgrade conservative for legacy bootstrap migration.
    pass
