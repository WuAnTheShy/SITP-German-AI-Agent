"""add user_no add teachers drop class_id and uid migrate file_size

Revision ID: <自动生成,不改>
Revises: 20260330_0002
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers - 这两行保留 alembic 自动生成的内容,不要改
revision = '20260505_0001'
down_revision = '20260330_0002'
branch_labels = None
depends_on = None


def upgrade():
    # ─── Step 1: users 表加 user_no 字段 ───
    op.add_column(
        'users',
        sa.Column('user_no', sa.String(length=8), nullable=True,
                  comment='对外业务编号：学生学号7位/教师工号5位/管理员0000000')
    )
    op.create_index('ix_users_user_no', 'users', ['user_no'], unique=True)
    
    # ─── Step 2: 数据回填 ───
    # 学生：user_no = students.uid（学号 7 位）
    op.execute("""
        UPDATE users 
        SET user_no = s.uid
        FROM students s
        WHERE users.id = s.user_id AND users.role = 'student'
    """)
    
    # 教师：按 id 顺序生成 26001 / 26002 / 26003
    # 用 row_number() 保证顺序
    op.execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn
            FROM users WHERE role = 'teacher'
        )
        UPDATE users
        SET user_no = LPAD((26000 + numbered.rn)::text, 5, '0')
        FROM numbered
        WHERE users.id = numbered.id
    """)
    
    # 管理员：0000000
    op.execute("UPDATE users SET user_no = '0000000' WHERE role = 'admin'")
    
    # ─── Step 3: 新建 teachers 表 + 数据回填 ───
    op.create_table(
        'teachers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), 
                  sa.ForeignKey('users.id', ondelete='CASCADE'), 
                  unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.func.now(), nullable=False),
    )
    op.execute("""
        INSERT INTO teachers (user_id, created_at, updated_at)
        SELECT id, NOW(), NOW() FROM users WHERE role = 'teacher'
    """)
    
    # ─── Step 4: students 表删 class_id 字段（中间表已对齐） ───
    op.drop_column('students', 'class_id')
    
    # ─── Step 5: homeworks.file_size: String → BigInteger ───
    # 旧值 "24 KB" 这种字符串没法直接转,清成 NULL
    op.execute("UPDATE homeworks SET file_size = NULL")
    op.alter_column(
        'homeworks', 'file_size',
        existing_type=sa.String(length=64),
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using='file_size::bigint'
    )


def downgrade():
    # 回滚顺序：和 upgrade 反向
    op.alter_column(
        'homeworks', 'file_size',
        existing_type=sa.BigInteger(),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
    op.add_column('students',
        sa.Column('class_id', sa.Integer(), 
                  sa.ForeignKey('classes.id'), nullable=True)
    )
    op.execute("""
        UPDATE students SET class_id = csr.class_id
        FROM class_student_relations csr WHERE students.id = csr.student_id
    """)
    op.drop_table('teachers')
    op.drop_index('ix_users_user_no', table_name='users')
    op.drop_column('users', 'user_no')