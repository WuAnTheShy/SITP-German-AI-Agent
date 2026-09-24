"""widen users.user_no for historical student identifiers

Revision ID: 20260924_0001
Revises: 20260507_2300
Create Date: 2026-09-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260924_0001"
down_revision = "20260507_2300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "user_no",
        existing_type=sa.String(length=8),
        type_=sa.String(length=32),
        existing_nullable=True,
        existing_comment="对外业务编号：学生学号7位/教师工号5位/管理员0000000",
        comment="对外业务编号：学生学号/教师工号/管理员编号",
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "user_no",
        existing_type=sa.String(length=32),
        type_=sa.String(length=8),
        existing_nullable=True,
        existing_comment="对外业务编号：学生学号/教师工号/管理员编号",
        comment="对外业务编号：学生学号7位/教师工号5位/管理员0000000",
    )
