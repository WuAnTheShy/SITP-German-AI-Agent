import json
import os
import sys
import io
import time
from datetime import date, datetime, timedelta, timezone
from statistics import mean
from uuid import uuid4

# load_dotenv 必须在所有读取环境变量的 import 之前调用
# 否则 db/session.py 等模块在 import 时读不到 .env 中的 DATABASE_URL
from dotenv import load_dotenv
load_dotenv()

# Windows 下统一使用 UTF-8 输出，避免第三方库（如 Google Genai SDK）内部写控制台时触发 UnicodeEncodeError
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from crud.repositories import (
    ChatMessageCRUD,
    ChatSessionCRUD,
    TeacherChatMessageCRUD,
    TeacherChatSessionCRUD,
    ClassroomCRUD,
    ErrorBookCategoryCRUD,
    ErrorBookEntryCRUD,
    ExamAssignmentCRUD,
    ExamCRUD,
    FavoriteCategoryCRUD,
    FavoriteCRUD,
    GrammarCategoryCRUD,
    GrammarExerciseCRUD,
    GrammarSubmissionCRUD,
    HomeworkCRUD,
    HomeworkReviewCRUD,
    LearningSessionCRUD,
    ListeningMaterialCRUD,
    ScenarioCRUD,
    ScenarioPushCRUD,
    SpeakingEvaluationCRUD,
    StudentAbilityCRUD,
    StudentCRUD,
    StudentKnowledgeMasteryCRUD,
    StudentVocabCollectionCRUD,
    UserCRUD,
    VocabularyCRUD,
    WritingSessionCRUD,
)
from db.session import get_db
from models.entities import (
    ChatSession as ChatSessionModel,
    ExamAssignment,
    Exam,
    Homework,
    Scenario,
    ScenarioPush,
    TeacherChatSession,
)
from schemas.entities import (
    ChatMessageCreate,
    ChatSessionCreate,
    TeacherChatMessageCreate,
    TeacherChatSessionCreate,
    ClassroomCreate,
    ErrorBookEntryCreate,
    ExamAssignmentCreate,
    ExamCreate,
    FavoriteCreate,
    GrammarSubmissionCreate,
    HomeworkCreate,
    HomeworkReviewCreate,
    LearningSessionCreate,
    ScenarioCreate,
    ScenarioPushCreate,
    SpeakingEvaluationCreate,
    StudentAbilityUpsert,
    StudentCreate,
    StudentKnowledgeMasteryUpsert,
    StudentVocabCollectionCreate,
    UserCreate,
    VocabularyCreate,
    WritingSessionCreate,
)
from core.responses import ok, fail, to_float
from core.deps import require_teacher, require_student, current_student
from services.llm import ai_text, ai_json, MODEL_ID, LLM_PROVIDER
from routers.auth import router as auth_router
from routers.admin import router as admin_router
from routers.teacher import router as teacher_router
from routers.chat import router as chat_router
from routers.student import router as student_router
from routers.student_tasks import router as student_tasks_router
from routers.student_learning import router as student_learning_router
from routers.user_kb import router as user_kb_router

# ════════════════════ 1. 环境与 AI 配置 ════════════════════
_proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
if _proxy:
    print(f"代理已启用: {_proxy}")
else:
    print("提示: 未配置代理，如需访问在线 API 请在 .env 中设置 HTTP_PROXY")
if LLM_PROVIDER == "qwen" and not os.getenv("QWEN_API_KEY"):
    print("警告: 当前为 qwen 模式，但未找到 QWEN_API_KEY")
print(f"[AI] Provider={LLM_PROVIDER}, Model={MODEL_ID}")

app = FastAPI()


def _is_production() -> bool:
    env = (os.getenv("APP_ENV", "") or "").strip().lower()
    return env in {"prod", "production"}


def _cors_allow_origins() -> list[str]:
    raw = (os.getenv("CORS_ALLOW_ORIGINS", "") or "").strip()
    if not raw:
        if _is_production():
            return []
        return [
            "http://localhost",
            "http://localhost:5173",
            "http://127.0.0.1",
            "http://127.0.0.1:5173",
        ]
    return [x.strip() for x in raw.split(",") if x.strip()]

@app.on_event("startup")
def startup_event():
    from sqlalchemy import text
    from db.session import engine

    # Docker 重建时 backend 可能先于 db 启动，先等待数据库可连接再执行迁移。
    max_retries = int(os.getenv("DB_READY_MAX_RETRIES", "30"))
    retry_interval = float(os.getenv("DB_READY_RETRY_INTERVAL", "2"))
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception as e:
            if attempt == max_retries:
                print(f"[Server] Database not ready after {max_retries} attempts: {e}")
                return
            print(f"[Server] Waiting for database ({attempt}/{max_retries})... {e}")
            time.sleep(retry_interval)

    print("[Server] Checking for database migrations...")
    try:
        with engine.begin() as conn:
            # 检查 content 字段是否已存在
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='exams' AND column_name='content';
            """))
            if not result.fetchone():
                print("[Server] Missing 'content' column in 'exams' table. Applying patch...")
                conn.execute(text("ALTER TABLE exams ADD COLUMN content JSONB DEFAULT '[]'::jsonb NOT NULL;"))
                print("[Server] Database patch applied successfully to exams.")
            
            # 检查 personalized_content 是否已存在于 exam_assignments
            result2 = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='exam_assignments' AND column_name='personalized_content';
            """))
            if not result2.fetchone():
                print("[Server] Missing 'personalized_content' in 'exam_assignments'. Applying patch...")
                conn.execute(text("ALTER TABLE exam_assignments ADD COLUMN personalized_content JSONB;"))
                print("[Server] Database patch applied successfully to exam_assignments.")
                
            # 移除 homeworks 表的 file_type 检查约束，以便支持 JSON 类型的试卷
            try:
                conn.execute(text("ALTER TABLE homeworks DROP CONSTRAINT IF EXISTS ck_homeworks_file_type;"))
                conn.execute(text("ALTER TABLE homeworks DROP CONSTRAINT IF EXISTS homeworks_file_type_check;"))
                print("[Server] Dropped restrictive homeworks file_type check constraints.")
            except Exception as e:
                print(f"[Server] Note: Could not drop constraint, it might not exist. {e}")

            # 检查 exam_assignment_id 是否已存在于 homeworks
            result3 = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='homeworks' AND column_name='exam_assignment_id';
            """))
            if not result3.fetchone():
                print("[Server] Missing 'exam_assignment_id' in 'homeworks'. Applying patch...")
                conn.execute(text("ALTER TABLE homeworks ADD COLUMN exam_assignment_id INTEGER;"))
                print("[Server] Database patch applied successfully to homeworks.")

            # 教师教研助手对话表（按用户隔离）
            r_tc = conn.execute(text(
                "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='teacher_chat_sessions'"
            ))
            if not r_tc.fetchone():
                print("[Server] Creating teacher_chat_sessions / teacher_chat_messages...")
                conn.execute(text(
                    "CREATE TABLE teacher_chat_sessions ("
                    "id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE, "
                    "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
                ))
                conn.execute(text(
                    "CREATE TABLE teacher_chat_messages ("
                    "id BIGSERIAL PRIMARY KEY, session_id BIGINT NOT NULL REFERENCES teacher_chat_sessions(id) ON DELETE CASCADE, "
                    "role VARCHAR(16) NOT NULL CHECK (role IN ('user','assistant')), content TEXT NOT NULL, "
                    "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
                ))
                conn.execute(text("CREATE INDEX idx_teacher_chat_sessions_user ON teacher_chat_sessions(user_id)"))
                conn.execute(text("CREATE INDEX idx_teacher_chat_messages_session ON teacher_chat_messages(session_id)"))
                print("[Server] Teacher chat tables created.")

            # Agent memory columns
            for tbl, cols in [
                ("chat_sessions", [("closed_at", "TIMESTAMPTZ NULL"), ("updated_at", "TIMESTAMPTZ NOT NULL DEFAULT NOW()"), ("title", "VARCHAR(128) NULL")]),
                ("teacher_chat_sessions", [("closed_at", "TIMESTAMPTZ NULL"), ("updated_at", "TIMESTAMPTZ NOT NULL DEFAULT NOW()"), ("title", "VARCHAR(128) NULL")]),
                ("students", [("long_memory_summary", "TEXT NULL"), ("memory_updated_at", "TIMESTAMPTZ NULL")]),
                ("users", [("long_memory_summary", "TEXT NULL"), ("memory_updated_at", "TIMESTAMPTZ NULL")]),
            ]:
                for col_name, col_def in cols:
                    r = conn.execute(text(
                        "SELECT 1 FROM information_schema.columns WHERE table_name=:t AND column_name=:c"
                    ), {"t": tbl, "c": col_name})
                    if not r.fetchone():
                        conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col_name} {col_def}"))
                        print(f"[Server] Added {tbl}.{col_name}")
            conn.execute(text(
                "UPDATE chat_sessions SET updated_at = created_at WHERE updated_at < created_at OR updated_at IS NULL"
            ))
            conn.execute(text(
                "UPDATE teacher_chat_sessions SET updated_at = created_at WHERE updated_at < created_at OR updated_at IS NULL"
            ))

            # Migrate missing 'status' columns
            for tbl in ["users", "students"]:
                r = conn.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name='{tbl}' AND column_name='status'"))
                if not r.fetchone():
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'approved'"))
                    print(f"[Server] Added {tbl}.status")
            
            # Create system_settings table if not exists
            r_ss = conn.execute(text("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='system_settings'"))
            if not r_ss.fetchone():
                conn.execute(text(
                    "CREATE TABLE system_settings ("
                    "id SERIAL PRIMARY KEY, "
                    "setting_key VARCHAR(64) UNIQUE NOT NULL, "
                    "setting_value VARCHAR(255) NOT NULL, "
                    "description TEXT)"
                ))
                print("[Server] Created system_settings table.")

            # 允许 users.role 为 admin（兼容已有库；PostgreSQL 可能生成 ck_users_role 或 users_role_check）
            try:
                conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_role"))
                conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check"))
                conn.execute(text("ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK (role IN ('teacher', 'student', 'admin'))"))
                print("[Server] users.role constraint updated to include 'admin'.")
            except Exception as e:
                print(f"[Server] Note: users role constraint update: {e}")

            # 学生可不关联班级（先注册后加入班级）
            try:
                conn.execute(text("ALTER TABLE students ALTER COLUMN class_id DROP NOT NULL"))
                print("[Server] students.class_id allowed NULL.")
            except Exception as e:
                print(f"[Server] Note: students class_id nullable: {e}")

            # 班级可暂不设置主教师（多教师关系以关系表为准）
            try:
                conn.execute(text("ALTER TABLE classes ALTER COLUMN teacher_user_id DROP NOT NULL"))
                print("[Server] classes.teacher_user_id allowed NULL.")
            except Exception as e:
                print(f"[Server] Note: classes teacher_user_id nullable: {e}")

            # 班级-教师多对多关系表
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS class_teacher_relations ("
                "id BIGSERIAL PRIMARY KEY, "
                "class_id BIGINT NOT NULL REFERENCES classes(id) ON DELETE CASCADE, "
                "teacher_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE, "
                "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
                "UNIQUE (class_id, teacher_user_id))"
            ))

            # 班级-学生多对多关系表
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS class_student_relations ("
                "id BIGSERIAL PRIMARY KEY, "
                "class_id BIGINT NOT NULL REFERENCES classes(id) ON DELETE CASCADE, "
                "student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE, "
                "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
                "UNIQUE (class_id, student_id))"
            ))

            # 从旧单字段回填关系表
            conn.execute(text(
                "INSERT INTO class_teacher_relations (class_id, teacher_user_id) "
                "SELECT id, teacher_user_id FROM classes WHERE teacher_user_id IS NOT NULL "
                "ON CONFLICT (class_id, teacher_user_id) DO NOTHING"
            ))
            conn.execute(text(
                "INSERT INTO class_student_relations (class_id, student_id) "
                "SELECT class_id, id FROM students WHERE class_id IS NOT NULL "
                "ON CONFLICT (class_id, student_id) DO NOTHING"
            ))

            # RAG 知识库：pgvector + 文档/切片表
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                print("[Server] pgvector extension ensured.")
            except Exception as e:
                print(f"[Server] Note: pgvector extension unavailable: {e}")

            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS kb_documents ("
                "id BIGSERIAL PRIMARY KEY, "
                "title VARCHAR(255) NOT NULL, "
                "source_name VARCHAR(255) NOT NULL, "
                "source_path TEXT NOT NULL, "
                "mime_type VARCHAR(128) NULL, "
                "status VARCHAR(32) NOT NULL DEFAULT 'processing', "
                "scope VARCHAR(16) NOT NULL DEFAULT 'public', "
                "owner_user_id BIGINT NULL REFERENCES users(id) ON DELETE CASCADE, "
                "is_active BOOLEAN NOT NULL DEFAULT TRUE, "
                "chunk_count INTEGER NOT NULL DEFAULT 0, "
                "error_message TEXT NULL, "
                "uploaded_by BIGINT NULL REFERENCES users(id) ON DELETE SET NULL, "
                "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
                "updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                ")"
            ))
            try:
                conn.execute(text("ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS scope VARCHAR(16) NOT NULL DEFAULT 'public'"))
                conn.execute(text("ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS owner_user_id BIGINT NULL REFERENCES users(id) ON DELETE CASCADE"))
                conn.execute(text("ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
                conn.execute(text("ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS is_temporary BOOLEAN NOT NULL DEFAULT FALSE"))
                conn.execute(text("ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS session_key VARCHAR(128) NULL"))
            except Exception as e:
                print(f"[Server] Note: kb_documents scope/owner migration: {e}")
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS kb_chunks ("
                "id BIGSERIAL PRIMARY KEY, "
                "document_id BIGINT NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE, "
                "chunk_index INTEGER NOT NULL, "
                "content TEXT NOT NULL, "
                "token_count INTEGER NOT NULL DEFAULT 0, "
                "metadata JSONB NOT NULL DEFAULT '{}'::jsonb, "
                "embedding vector, "
                "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
                "UNIQUE(document_id, chunk_index)"
                ")"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_kb_documents_status ON kb_documents(status)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_kb_chunks_doc ON kb_chunks(document_id)"
            ))
            try:
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding_ivfflat "
                    "ON kb_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
                ))
            except Exception as e:
                print(f"[Server] Note: ivfflat index skipped: {e}")

            print("[Server] Database schema checks completed.")
    except Exception as e:
        print(f"[Server] Database migration failed (might be handled by alembic): {e}")

    # 确保管理员账号存在（由环境变量 INIT_ADMIN_USERNAME / INIT_ADMIN_PASSWORD 控制）
    try:
        from db.session import SessionLocal
        from core.seed import _ensure_admin
        _db = SessionLocal()
        try:
            _ensure_admin(_db)
        finally:
            _db.close()
    except Exception as e:
        print(f"[Server] ensure admin failed: {e}")

# ════════════════════ 2. 跨域中间件 ════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(teacher_router)
app.include_router(chat_router)
app.include_router(student_router)
app.include_router(student_tasks_router)
app.include_router(student_learning_router)
app.include_router(user_kb_router)

# ════════════════════ 3. 公共数据模型与工具函数 ════════════════════
# (student_learning routes moved to routers/student_learning.py)


# ════════════════════ 8. 根路由 ════════════════════


@app.get("/")
def read_root():
    return {"status": "ok", "message": "SITP German Agent 后端正在运行中! 🚀"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
