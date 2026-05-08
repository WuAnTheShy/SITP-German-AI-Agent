"""add agent_traces and agent_spans tables for observability

Revision ID: 20260507_2300
Revises: 20260506_xxxx  # ← 替换为你当前 head revision
Create Date: 2026-05-07 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260507_2300"
down_revision = "20260506_0001"   
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── agent_traces ───
    op.create_table(
        "agent_traces",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trace_id", sa.String(40), nullable=False, unique=True),
        
        # 上下文
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=True),
        
        # 请求
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("user_message_length", sa.Integer(), nullable=True),
        
        # 响应
        sa.Column("reply_text", sa.Text(), nullable=True),
        sa.Column("reply_length", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("error_type", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        
        # 性能聚合
        sa.Column("total_duration_ms", sa.Integer(), nullable=False),
        sa.Column("total_llm_calls", sa.Integer(), server_default="0"),
        sa.Column("total_tool_calls", sa.Integer(), server_default="0"),
        sa.Column("total_input_tokens", sa.Integer(), server_default="0"),
        sa.Column("total_output_tokens", sa.Integer(), server_default="0"),
        sa.Column("estimated_cost_yuan", sa.Numeric(10, 4), server_default="0"),
        
        # Agent 行为
        sa.Column("rag_used", sa.Boolean(), server_default=sa.text("FALSE")),
        sa.Column("rag_top_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("iterations_used", sa.Integer(), server_default="0"),
        sa.Column("tools_called", postgresql.JSONB(), nullable=True),
        
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_agent_traces_role_created", "agent_traces", ["role", "created_at"])
    op.create_index("idx_agent_traces_session", "agent_traces", ["session_id"])
    
    # ─── agent_spans ───
    op.create_table(
        "agent_spans",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("trace_id", sa.String(40), nullable=False),
        
        sa.Column("span_type", sa.String(30), nullable=False),
        sa.Column("span_name", sa.String(100), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        
        sa.Column("input_data", postgresql.JSONB(), nullable=True),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        
        sa.Column("rag_recall_count", sa.Integer(), nullable=True),
        sa.Column("rag_rerank_score", sa.Numeric(4, 3), nullable=True),
        
        sa.Column("success", sa.Boolean(), server_default=sa.text("TRUE")),
        sa.Column("error_message", sa.Text(), nullable=True),
        
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        
        sa.ForeignKeyConstraint(["trace_id"], ["agent_traces.trace_id"], ondelete="CASCADE"),
    )
    op.create_index("idx_agent_spans_trace", "agent_spans", ["trace_id", "sequence"])
    op.create_index("idx_agent_spans_type", "agent_spans", ["span_type", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_agent_spans_type", "agent_spans")
    op.drop_index("idx_agent_spans_trace", "agent_spans")
    op.drop_table("agent_spans")
    
    op.drop_index("idx_agent_traces_session", "agent_traces")
    op.drop_index("idx_agent_traces_role_created", "agent_traces")
    op.drop_table("agent_traces")