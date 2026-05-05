"""add composite indexes on hot tables

Revision ID: 53e5bf8d607b
Revises: 20260505_0001
Create Date: 2026-05-05 18:15:21.891056

"""
from alembic import op


revision = '<保留 alembic 自动填的>'
down_revision = '20260505_0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        'ix_chat_messages_session_created',
        'chat_messages',
        ['session_id', 'created_at'],
    )
    op.create_index(
        'ix_learning_sessions_student_created',
        'learning_sessions',
        ['student_id', 'created_at'],
    )
    op.create_index(
        'ix_homeworks_student_created',
        'homeworks',
        ['student_id', 'submitted_at'],
    )
    op.create_index(
        'ix_error_book_entries_student_mastered',
        'error_book_entries',
        ['student_id', 'is_mastered'],
    )


def downgrade():
    op.drop_index('ix_error_book_entries_student_mastered', table_name='error_book_entries')
    op.drop_index('ix_homeworks_student_created', table_name='homeworks')
    op.drop_index('ix_learning_sessions_student_created', table_name='learning_sessions')
    op.drop_index('ix_chat_messages_session_created', table_name='chat_messages')