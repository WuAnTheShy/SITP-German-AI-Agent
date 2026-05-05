import json
import os
import sys
import io
import time
import logging
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
# 配置全局 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# 减少第三方库噪音
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

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
            
            # 初始化 chat_scenes 表
            from models.entities import ChatScene, GrammarCategory, GrammarExercise
            from sqlalchemy import select
            
            # 检查 chat_scenes 表是否为空
            existing_scenes = _db.scalars(select(ChatScene)).all()
            if not existing_scenes:
                print("[Server] Initializing chat_scenes table...")
                # 添加前端定义的场景
                scenes = [
                    {"id": 1, "name": "校园课堂问答", "description": "和老师互动、回答课堂问题"},
                    {"id": 2, "name": "日常购物交流", "description": "超市/商店买东西的德语对话"},
                    {"id": 3, "name": "留学面试沟通", "description": "德国大学入学面试常见问题"},
                    {"id": 4, "name": "餐厅点餐对话", "description": "德国餐厅点餐、询问菜品"},
                ]
                for scene_data in scenes:
                    scene = ChatScene(
                        id=scene_data["id"],
                        name=scene_data["name"],
                        description=scene_data["description"]
                    )
                    _db.add(scene)
                _db.commit()
                print("[Server] chat_scenes table initialized successfully")
            
            # 初始化 grammar_categories 表
            existing_categories = _db.scalars(select(GrammarCategory)).all()
            if not existing_categories:
                print("[Server] Initializing grammar_categories table...")
                # 添加默认语法分类
                categories = [
                    {"id": 1, "name": "动词变位", "description": "学习德语动词的各种变位形式"},
                    {"id": 2, "name": "名词格变化", "description": "掌握德语名词的四个格变化"},
                    {"id": 3, "name": "完成时", "description": "学习德语完成时的构成和用法"},
                    {"id": 4, "name": "被动语态", "description": "掌握德语被动语态的构成和用法"},
                    {"id": 5, "name": "虚拟式", "description": "学习德语虚拟式的用法"},
                    {"id": 6, "name": "介词搭配", "description": "掌握德语介词的正确搭配"},
                    {"id": 7, "name": "句序", "description": "学习德语句子的正确语序"},
                ]
                for cat_data in categories:
                    category = GrammarCategory(
                        id=cat_data["id"],
                        name=cat_data["name"],
                        description=cat_data["description"]
                    )
                    _db.add(category)
                _db.commit()
                print("[Server] grammar_categories table initialized successfully")
                
                # 为每个分类添加一些练习题
                print("[Server] Adding sample grammar exercises...")
                exercises = [
                    # 动词变位练习
                    {"category_id": 1, "question": "Ich ______ (sein) Student.", "correct_answer": "bin", "analysis": "sein的第一人称单数变位是bin"},
                    {"category_id": 1, "question": "Du ______ (haben) ein Buch.", "correct_answer": "hast", "analysis": "haben的第二人称单数变位是hast"},
                    {"category_id": 1, "question": "Er ______ (gehen) zur Schule.", "correct_answer": "geht", "analysis": "gehen的第三人称单数变位是geht"},
                    
                    # 名词格变化练习
                    {"category_id": 2, "question": "Der Hund beißt ______ (der) Mann.", "correct_answer": "den", "analysis": "四格宾语，阳性名词der变den"},
                    {"category_id": 2, "question": "Ich gebe ______ (die) Frau ein Buch.", "correct_answer": "der", "analysis": "三格宾语，阴性名词die变der"},
                    
                    # 完成时练习
                    {"category_id": 3, "question": "Ich ______ (essen) schon.", "correct_answer": "habe gegessen", "analysis": "完成时由haben+第二分词构成"},
                    {"category_id": 3, "question": "Er ______ (gehen) nach Hause.", "correct_answer": "ist gegangen", "analysis": "gehen是不及物动词，完成时用sein"},
                    
                    # 被动语态练习
                    {"category_id": 4, "question": "Das Buch ______ (lesen) von mir.", "correct_answer": "wird gelesen", "analysis": "现在时被动语态：werden+第二分词"},
                    
                    # 虚拟式练习
                    {"category_id": 5, "question": "Wenn ich Zeit ______ (haben), gehe ich ins Kino.", "correct_answer": "hätte", "analysis": "第二虚拟式，表示与现在事实相反的假设"},
                    
                    # 介词搭配练习
                    {"category_id": 6, "question": "Ich komme ______ Deutschland.", "correct_answer": "aus", "analysis": "kommen aus表示来自"},
                    {"category_id": 6, "question": "Er geht ______ Schule.", "correct_answer": "zur", "analysis": "gehen zur Schule表示去上学"},
                    
                    # 句序练习
                    {"category_id": 7, "question": "Ich / gern / Fußball / spiele", "correct_answer": "Ich spiele gern Fußball", "analysis": "德语基本语序：主语+谓语+宾语"},
                ]
                for ex_data in exercises:
                    exercise = GrammarExercise(
                        category_id=ex_data["category_id"],
                        question=ex_data["question"],
                        correct_answer=ex_data["correct_answer"],
                        analysis=ex_data["analysis"]
                    )
                    _db.add(exercise)
                _db.commit()
                print("[Server] Sample grammar exercises added successfully")
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
