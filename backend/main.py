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

    print("[Server] Checking database schema status (read-only)...")
    try:
        with engine.connect() as conn:
            version_table = conn.execute(text("SELECT to_regclass('public.alembic_version')")).scalar()
            if version_table:
                version_row = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                version_num = version_row.scalar()
                if version_num:
                    print(f"[Server] Alembic version: {version_num}")
                else:
                    print("[Server] Alembic version is empty. Run `alembic upgrade head`.")
            else:
                print("[Server] Alembic version table is missing. Run `alembic upgrade head`.")

            ext_row = conn.execute(text("SELECT extname FROM pg_extension WHERE extname='vector'"))
            has_vector = bool(ext_row.fetchone())
            docs_row = conn.execute(text("SELECT to_regclass('public.kb_documents')"))
            chunks_row = conn.execute(text("SELECT to_regclass('public.kb_chunks')"))
            has_docs = bool((docs_row.scalar() or "").strip())
            has_chunks = bool((chunks_row.scalar() or "").strip())
            if has_vector and has_docs and has_chunks:
                print("[Server] RAG check: pgvector and kb schema are present.")
            else:
                print("[Server] RAG check: missing extension/schema. Run `alembic upgrade head`.")

            print("[Server] Database schema checks completed.")
    except Exception as e:
        print(f"[Server] Database schema check failed: {e}")

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
