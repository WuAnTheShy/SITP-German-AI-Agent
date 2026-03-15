import json
import os
import sys
import io
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
from core.seed import _ensure_demo_data
from services.llm import ai_text, ai_json, MODEL_ID
from routers.auth import router as auth_router
from routers.teacher import router as teacher_router
from routers.chat import router as chat_router
from routers.student import router as student_router
from routers.student_tasks import router as student_tasks_router
from routers.student_learning import router as student_learning_router

# ════════════════════ 1. 环境与 AI 配置 ════════════════════
_proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
if _proxy:
    print(f"代理已启用: {_proxy}")
else:
    print("提示: 未配置代理，如果 Gemini API 连不上请在 .env 中设置 HTTP_PROXY")
if not os.getenv("GOOGLE_API_KEY"):
    print("警告: 未找到 GOOGLE_API_KEY")

app = FastAPI()

@app.on_event("startup")
def startup_event():
    from sqlalchemy import text
    from db.session import engine
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
                
            print("[Server] Database schema checks completed.")
    except Exception as e:
        print(f"[Server] Database migration failed (might be handled by alembic): {e}")

# ════════════════════ 2. 跨域中间件 ════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(teacher_router)
app.include_router(chat_router)
app.include_router(student_router)
app.include_router(student_tasks_router)
app.include_router(student_learning_router)

# ════════════════════ 3. 公共数据模型与工具函数 ════════════════════
# (student_learning routes moved to routers/student_learning.py)


# ════════════════════ 8. 根路由 ════════════════════


@app.get("/")
def read_root():
    return {"status": "ok", "message": "SITP German Agent 后端正在运行中! 🚀"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
