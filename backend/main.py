import json
import os
import io
from datetime import date, datetime, timedelta, timezone
from statistics import mean
from uuid import uuid4

# load_dotenv 必须在所有读取环境变量的 import 之前调用
# 否则 db/session.py 等模块在 import 时读不到 .env 中的 DATABASE_URL
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
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

# ════════════════════ 1. 环境与 AI 配置 ════════════════════

# ── 代理配置（国内访问 Google API 需要，在 .env 中配置） ──
# 如果 .env 里配了 HTTP_PROXY / HTTPS_PROXY，会自动生效
# 没配则不使用代理（适合国外或已全局代理的环境）
_proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
if _proxy:
    os.environ.setdefault("HTTP_PROXY", _proxy)
    os.environ.setdefault("HTTPS_PROXY", _proxy)
    print(f"代理已启用: {_proxy}")
else:
    print("提示: 未配置代理，如果 Gemini API 连不上请在 .env 中设置 HTTP_PROXY")

if not os.getenv("GOOGLE_API_KEY"):
    print("警告: 未找到 GOOGLE_API_KEY")

# 新版 google-genai SDK 客户端
_gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

_MODEL_ID = "gemini-2.5-flash"

_TEACHER_SYSTEM = (
    "你是一个高级教学AI教研助手，负责协助德语教师分析学情、制定教案和出题等。"
    "请用中文与教师进行沟通，提供专业、基于数据的教学建议和德语教学方案。"
)

_STUDENT_SYSTEM = (
    "你是同济大学的 AI 德语助教，帮助学生学习德语。"
    "回复简洁、准确。除非用户要求中文，否则用德语回答并在括号内给出中文翻译。"
)

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
                ("teacher_chat_sessions", [("closed_at", "TIMESTAMPTZ NULL"), ("updated_at", "TIMESTAMPTZ NOT NULL DEFAULT NOW()")]),
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

# ════════════════════ 3. 公共数据模型与工具函数 ════════════════════

class ChatRequest(BaseModel):
    message: str


class StudentChatReq(BaseModel):
    message: str
    new_thread: bool = False
    session_id: int | None = None


class TeacherChatReq(BaseModel):
    message: str
    new_thread: bool = False
    session_id: int | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordUpdateReq(BaseModel):
    oldPassword: str
    newPassword: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str
    class_code: str | None = None



class ScenarioPublishRequest(BaseModel):
    config: dict
    timestamp: str | None = None


class ExamGenerateRequest(BaseModel):
    config: dict
    timestamp: str | None = None


class HomeworkSaveRequest(BaseModel):
    homeworkId: int
    score: float
    feedback: str | None = None
    timestamp: str | None = None


class PushSchemeRequest(BaseModel):
    studentId: str
    name: str | None = None
    diagnosis: str | None = None
    timestamp: str | None = None


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


def fail(message: str, code: int = 500):
    return {"code": code, "message": message, "data": None}


def to_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


# ════════════════════ 3.5 权限校验依赖 ════════════════════


def require_teacher(req: Request, db: Session = Depends(get_db)):
    """从 Authorization 头解析教师身份，失败则抛 401"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer teacher-token-"):
        parts = auth.replace("Bearer ", "").split("-")
        # token 格式: teacher-token-{user_id}-{random}
        if len(parts) >= 4:
            try:
                user_id = int(parts[2])
            except ValueError:
                raise HTTPException(status_code=401, detail="无效的教师令牌")
            user = UserCRUD.get_by_id(db, user_id)
            if user and user.role == "teacher":
                return user
    raise HTTPException(status_code=401, detail="未登录或令牌无效，请重新登录")


def require_student(req: Request, db: Session = Depends(get_db)):
    """从 Authorization 头解析学生身份，失败则抛 401"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer student-token-"):
        parts = auth.replace("Bearer ", "").split("-")
        # token 格式: student-token-{uid}-{random}
        if len(parts) >= 4:
            uid = parts[2]
            s = StudentCRUD.get_by_uid(db, uid)
            if s:
                return s
    raise HTTPException(status_code=401, detail="未登录或令牌无效，请重新登录")


# ════════════════════ 4. 学生端辅助函数与请求模型 ════════════════════


def _current_student(req: Request, db: Session):
    """从 Authorization 头解析学生，无有效 token 返回 None"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer student-token-"):
        parts = auth.replace("Bearer ", "").split("-")
        if len(parts) >= 4:
            uid = parts[2]
            s = StudentCRUD.get_by_uid(db, uid)
            if s:
                return s
    return None


def _ai_text(prompt: str, fallback: str = "") -> str:
    """安全调用 Gemini 返回纯文本"""
    try:
        resp = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_STUDENT_SYSTEM,
            ),
        )
        return resp.text.strip()
    except Exception as e:
        print(f"[AI] {e}")
        return fallback


def _ai_json(prompt: str, fallback=None):
    """调用 Gemini 并尝试解析 JSON，失败返回 fallback"""
    try:
        resp = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_STUDENT_SYSTEM,
            ),
        )
        text = resp.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())
    except Exception as e:
        print(f"[AI JSON] {e}")
        return fallback


def _match_error_category(grammar_name: str, error_cats: dict[str, int]) -> int | None:
    """将语法分类名模糊映射到错题本分类"""
    mapping = {
        "动词变位": "动词变位", "Konjugation": "动词变位",
        "名词": "名词格变化", "Deklination": "名词格变化",
        "完成时": "时态错误", "Perfekt": "时态错误",
        "被动": "时态错误", "Passiv": "时态错误",
        "虚拟": "时态错误", "Konjunktiv": "时态错误",
        "句序": "句序错误", "介词": "介词搭配",
    }
    for keyword, cat_name in mapping.items():
        if keyword in grammar_name and cat_name in error_cats:
            return error_cats[cat_name]
    return next(iter(error_cats.values()), None) if error_cats else None


def _resolve_student_session(
    db: Session,
    student_id: int,
    scene_id: int | None,
    scene_name: str,
    *,
    new_thread: bool = False,
    session_id: int | None = None,
) -> ChatSessionModel:
    """未关闭会话续接；new_thread 关闭旧会话并新建；可选指定 session_id 继续某开放会话"""
    if new_thread:
        ChatSessionCRUD.close_open_for_channel(db, student_id, scene_id, scene_name)
        return ChatSessionCRUD.create(
            db, ChatSessionCreate(student_id=student_id, scene_id=scene_id, scene_name=scene_name)
        )
    if session_id is not None:
        s = ChatSessionCRUD.get_by_id(db, session_id)
        if not s or s.student_id != student_id:
            raise HTTPException(status_code=404, detail="会话不存在")
        if scene_id is None and (s.scene_name or "") != scene_name:
            raise HTTPException(status_code=400, detail="会话与当前通道不符")
        if scene_id is not None and s.scene_id != scene_id:
            raise HTTPException(status_code=400, detail="会话与当前通道不符")
        if getattr(s, "closed_at", None) is not None:
            ChatSessionCRUD.reopen(db, s.id)
        return ChatSessionCRUD.get_by_id(db, session_id) or s
    open_s = ChatSessionCRUD.find_open_session(db, student_id, scene_id, scene_name)
    if open_s:
        return open_s
    return ChatSessionCRUD.create(
        db, ChatSessionCreate(student_id=student_id, scene_id=scene_id, scene_name=scene_name)
    )


def _resolve_teacher_session(
    db: Session, user_id: int, *, new_thread: bool = False, session_id: int | None = None
) -> TeacherChatSession:
    if new_thread:
        TeacherChatSessionCRUD.close_open_for_user(db, user_id)
        return TeacherChatSessionCRUD.create(db, TeacherChatSessionCreate(user_id=user_id))
    if session_id is not None:
        s = TeacherChatSessionCRUD.get_by_id(db, session_id)
        if s and s.user_id == user_id and getattr(s, "closed_at", None) is None:
            return s
        if s and s.user_id == user_id:
            raise HTTPException(status_code=400, detail="会话已结束")
        raise HTTPException(status_code=404, detail="会话不存在")
    open_s = TeacherChatSessionCRUD.find_open_session(db, user_id)
    if open_s:
        return open_s
    return TeacherChatSessionCRUD.create(db, TeacherChatSessionCreate(user_id=user_id))


MEMORY_REFRESH_EVERY = 16

_MEMORY_SUMMARY_PROMPT = """You maintain a short learner profile (max 400 Chinese characters).
Previous profile (may be empty):
---
{prev}
---
Recent dialogue (latest lines):
---
{dialogue}
---
Output ONLY the updated profile: level, goals, recurring mistakes, current topics. No markdown."""


def _refresh_student_memory(student_id: int, session_id: int) -> None:
    from db.session import SessionLocal
    db = SessionLocal()
    try:
        st = StudentCRUD.get_by_id(db, student_id)
        if not st:
            return
        msgs = ChatMessageCRUD.list_by_session(db, session_id)
        tail = msgs[-24:] if len(msgs) > 24 else msgs
        dialogue = "\n".join(f"{'U' if m.role == 'user' else 'A'}: {m.content[:500]}" for m in tail)
        prev = (st.long_memory_summary or "")[:1200]
        prompt = _MEMORY_SUMMARY_PROMPT.format(prev=prev, dialogue=dialogue)
        resp = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(http_options={"timeout": 60_000}),
        )
        text = (resp.text or "").strip()[:2000]
        if text:
            StudentCRUD.update_long_memory(db, student_id, text)
    except Exception as e:
        print(f"[Memory] student refresh skip: {e}", flush=True)
    finally:
        db.close()


def _refresh_teacher_memory(user_id: int, session_id: int) -> None:
    from db.session import SessionLocal
    db = SessionLocal()
    try:
        u = UserCRUD.get_by_id(db, user_id)
        if not u:
            return
        msgs = TeacherChatMessageCRUD.list_by_session(db, session_id)
        tail = msgs[-24:] if len(msgs) > 24 else msgs
        dialogue = "\n".join(f"{'U' if m.role == 'user' else 'A'}: {m.content[:500]}" for m in tail)
        prev = (u.long_memory_summary or "")[:1200]
        prompt = (
            "Update a short teaching-assistant context (max 400 Chinese chars) for this teacher. "
            "Previous:\n---\n" + prev + "\n---\nRecent:\n---\n" + dialogue + "\n---\nOutput only the summary."
        )
        resp = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(http_options={"timeout": 60_000}),
        )
        text = (resp.text or "").strip()[:2000]
        if text:
            UserCRUD.update_long_memory(db, user_id, text)
    except Exception as e:
        print(f"[Memory] teacher refresh skip: {e}", flush=True)
    finally:
        db.close()


def _history_to_gemini_contents(messages: list, max_turns: int = 12) -> list:
    """将库中 user/assistant 消息转为 Gemini contents（每条为 user 或 model）"""
    slice_msgs = messages[-(max_turns * 2) :] if len(messages) > max_turns * 2 else messages
    out = []
    for m in slice_msgs:
        role = "user" if m.role == "user" else "model"
        out.append(types.Content(role=role, parts=[types.Part.from_text(text=m.content)]))
    return out


# 学生端请求体模型
class StudentLoginReq(BaseModel):
    username: str
    password: str


class SceneChatReq(BaseModel):
    sceneId: int | None = None
    sceneName: str | None = None
    userMessage: str


class VocabCollectReq(BaseModel):
    vocabId: int
    isCollect: bool


class VocabGenerateReq(BaseModel):
    level: str = "A1"
    topic: str = "日常通用"


class GrammarAnswerItem(BaseModel):
    exerciseId: int
    userAnswer: str


class GrammarSubmitReq(BaseModel):
    categoryId: int
    answers: list[GrammarAnswerItem]


class SpeakingEvalReq(BaseModel):
    materialId: int
    audioUrl: str | None = None


class WritingReq(BaseModel):
    userText: str


class ErrorReviewReq(BaseModel):
    categoryId: int
    categoryName: str | None = None


class ErrorMasterReq(BaseModel):
    errorId: int
    categoryId: int | None = None


class FavAIExtendReq(BaseModel):
    content: str
    type: str


# ════════════════════ 5. 教师端 Demo 数据初始化 ════════════════════


def _ensure_demo_data(db: Session):
    teacher = UserCRUD.get_by_username(db, "t_zhang")
    if not teacher:
        teacher = UserCRUD.create(
            db,
            UserCreate(
                username="t_zhang",
                password_hash="demo_hash_teacher",
                role="teacher",
                display_name="张老师",
            ),
        )

    classroom = ClassroomCRUD.get_by_code(db, "SE-2026-4")
    if not classroom:
        classroom = ClassroomCRUD.create(
            db,
            ClassroomCreate(
                class_code="SE-2026-4",
                class_name="软件工程(四)班",
                grade="2026",
                teacher_user_id=teacher.id,
            ),
        )

    def ensure_student(uid: str, username: str, name: str, active: int, overall: float, weak: str):
        stu_user = UserCRUD.get_by_username(db, username)
        if not stu_user:
            stu_user = UserCRUD.create(
                db,
                UserCreate(
                    username=username,
                    password_hash="demo_hash_student",
                    role="student",
                    display_name=name,
                ),
            )

        student = StudentCRUD.get_by_uid(db, uid)
        if not student:
            student = StudentCRUD.create(
                db,
                StudentCreate(
                    uid=uid,
                    user_id=stu_user.id,
                    class_id=classroom.id,
                    name=name,
                    active_score=active,
                    overall_score=overall,
                    weak_point=weak,
                ),
            )

        StudentAbilityCRUD.upsert(
            db,
            StudentAbilityUpsert(
                student_id=student.id,
                listening=min(100, active + 1),
                speaking=max(0, active - 2),
                reading=min(100, int(overall)),
                writing=max(0, int(overall - 3)),
                ai_diagnosis=f"{name}在{weak}方面需要重点强化。",
            ),
        )

        if not HomeworkCRUD.list_by_student(db, student.id):
            HomeworkCRUD.create(
                db,
                HomeworkCreate(
                    student_id=student.id,
                    title="德语写作作业-第3周",
                    status="已完成",
                    submitted_at=datetime.utcnow(),
                    score=to_float(overall),
                    file_type="text",
                    file_url=f"https://example.com/{uid}/week3.txt",
                    file_name=f"{uid}-week3.txt",
                    file_size="24 KB",
                    ai_comment="结构清晰，建议继续优化复杂句表达。",
                ),
            )

    ensure_student("2452001", "s_li", "李娜", 88, 91.5, "虚拟式")
    ensure_student("2452002", "s_wang", "王强", 64, 78.0, "被动语态")

    return teacher, classroom


# ════════════════════ 6. 教师端 API ════════════════════


@app.post("/api/chat")
def chat_endpoint(
    bg: BackgroundTasks,
    req: Request,
    request: TeacherChatReq,
    db: Session = Depends(get_db),
):
    """教师端 AI：跨天续接 + 长期摘要"""
    user = require_teacher(req, db)
    print(f"[教师AI] user_id={user.id} 消息: {request.message[:80]!r}...", flush=True)
    try:
        session = _resolve_teacher_session(
            db, user.id, new_thread=request.new_thread, session_id=request.session_id
        )
        TeacherChatMessageCRUD.create(
            db, TeacherChatMessageCreate(session_id=session.id, role="user", content=request.message)
        )
        history = TeacherChatMessageCRUD.list_by_session(db, session.id)
        contents_to_send = []
        if getattr(user, "long_memory_summary", None):
            contents_to_send.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="[Teaching context]\n" + user.long_memory_summary)],
                )
            )
        contents_to_send.extend(_history_to_gemini_contents(history, max_turns=14))
        response = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=contents_to_send,
            config=types.GenerateContentConfig(
                system_instruction=_TEACHER_SYSTEM,
                http_options={"timeout": 90_000},
            ),
        )
        reply_text = response.text or ""
        TeacherChatMessageCRUD.create(
            db, TeacherChatMessageCreate(session_id=session.id, role="assistant", content=reply_text)
        )
        TeacherChatSessionCRUD.touch(db, session.id)
        n = len(history) + 2
        if n >= MEMORY_REFRESH_EVERY and n % MEMORY_REFRESH_EVERY == 0:
            bg.add_task(_refresh_teacher_memory, user.id, session.id)
        return {"reply": reply_text, "session_id": session.id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[教师AI] Gemini调用失败: {type(e).__name__}: {e}", flush=True)
        return {"reply": f"AI 暂时无法响应，请稍后重试。错误信息: {type(e).__name__}"}


@app.put("/api/user/password")
def update_user_password(req_body: PasswordUpdateReq, req: Request, db: Session = Depends(get_db)):
    try:
        auth = req.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return fail("未登录", 401)
        
        token = auth.replace("Bearer ", "")
        parts = token.split("-")
        
        user = None
        if token.startswith("teacher-token-") and len(parts) >= 4:
            try:
                user_id = int(parts[2])
                user = UserCRUD.get_by_id(db, user_id)
            except ValueError:
                pass
        elif token.startswith("student-token-") and len(parts) >= 4:
            uid = parts[2]
            student = StudentCRUD.get_by_uid(db, uid)
            if student:
                user = UserCRUD.get_by_id(db, student.user_id)
                
        if not user:
            return fail("无效的令牌或用户不存在", 401)
            
        if user.password_hash != req_body.oldPassword:
            return fail("原密码错误", 400)
            
        user.password_hash = req_body.newPassword
        db.commit()
        
        return ok(message="密码修改成功")
    except Exception as e:
        return fail(f"修改密码失败: {e}")


@app.post("/api/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        _ensure_demo_data(db)

        user = UserCRUD.get_by_username(db, request.username)
        if not user:
            return fail("用户不存在，请检查工号后重试", 401)

        if user.role != "teacher":
            return fail("该账号不是教师账号", 403)

        if user.password_hash != request.password:
            return fail("密码错误，请重新输入", 401)

        token = f"teacher-token-{user.id}-{uuid4().hex[:8]}"
        user_info = {"id": user.username, "name": user.display_name, "role": user.role}
        return {
            "code": 200,
            "message": "登录成功",
            "token": token,
            "user": user_info,
            "data": {"token": token, "user": user_info},
        }
    except Exception as e:
        return fail(f"登录失败: {e}")


@app.get("/api/teacher/dashboard")
def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        require_teacher(request, db)
        teacher, classroom = _ensure_demo_data(db)
        students = StudentCRUD.list_by_class(db, classroom.id)

        all_homeworks = []
        for s in students:
            all_homeworks.extend(HomeworkCRUD.list_by_student(db, s.id))

        avg_score = round(mean([to_float(s.overall_score) for s in students]), 1) if students else 0
        completion_count = sum(1 for h in all_homeworks if h.status == "已完成")
        completion_rate = round((completion_count / len(all_homeworks)) * 100) if all_homeworks else 0

        payload = {
            "teacherName": teacher.display_name,
            "className": classroom.class_name,
            "pendingTasks": 3,
            "stats": {
                "totalStudents": len(students),
                "totalStudentsTrend": "+0",
                "avgDuration": 12.5,
                "avgDurationTrend": "↑ 2%",
                "avgScore": avg_score,
                "avgScoreTrend": "↑ 0.5",
                "completionRate": completion_rate,
                "completionRateTrend": "稳定",
            },
            "students": [
                {
                    "name": s.name,
                    "uid": s.uid,
                    "class": classroom.class_name,
                    "active": s.active_score,
                    "score": to_float(s.overall_score),
                    "weak": s.weak_point or "暂无",
                }
                for s in students
            ],
        }
        return ok(payload)
    except Exception as e:
        return fail(f"仪表盘加载失败: {e}")


@app.post("/api/scenario/publish")
def publish_scenario(request: ScenarioPublishRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(req, db)
        teacher, classroom = _ensure_demo_data(db)
        cfg = request.config or {}
        goals = cfg.get("goals", {})

        scenario_code = f"SCN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"
        scenario = ScenarioCRUD.create(
            db,
            ScenarioCreate(
                scenario_code=scenario_code,
                teacher_user_id=teacher.id,
                theme=cfg.get("theme", "默认主题"),
                difficulty=cfg.get("difficulty", "A1"),
                persona=cfg.get("persona", "友好耐心"),
                goal_require_perfect_tense=bool(goals.get("requirePerfectTense", False)),
                goal_require_b1_vocab=bool(goals.get("requireB1Vocab", False)),
            ),
        )

        for s in StudentCRUD.list_by_class(db, classroom.id):
            ScenarioPushCRUD.create_or_get(
                db,
                ScenarioPushCreate(scenario_id=scenario.id, student_id=s.id, push_status="pushed"),
            )

        return ok({"scenarioId": scenario.scenario_code}, "任务发布成功")
    except Exception as e:
        return fail(f"任务发布失败: {e}")


@app.post("/api/exam/generate")
def generate_exam(request: ExamGenerateRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(req, db)
        teacher, classroom = _ensure_demo_data(db)
        cfg = request.config or {}

        exam_code = f"EXM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"
        grammar_count = int(cfg.get("grammarItems", 15))
        writing_count = int(cfg.get("writingItems", 2))
        
        # ----------- 使用 AI 实时生成题目 -----------
        focus_desc = "、".join(cfg.get("focusAreas", [])) or "综合考察"
        strategy = cfg.get("strategy", "personalized")
        strategy_desc = "个性化差异出题" if strategy == "personalized" else "统一标准出题"

        def _generate_questions_for_student(student_info: str = "") -> list:
            prompt = f"""你是一个专业的德语考试出题系统。请根据以下配置生成德语考试试卷：

- 语法题数量：{grammar_count} 题
- 写作题数量：{writing_count} 题
- 出题策略：{strategy_desc}
- 重点考察领域：{focus_desc}
{student_info}

要求：
1. 每道语法题都必须**不同**，涵盖不同语法考点（如动词变位、格变化、被动语态、虚拟式、从句语序、介词搭配等）
2. 语法题为选择填空题，每题4个选项(A/B/C/D)，需标注正确答案
3. 写作题需要不同的写作场景和主题，字数要求100-150词
4. 题目难度为 B1 水平

请严格按照以下 JSON 格式返回（不要加任何额外文字或markdown）：
[
  {{
    "type": "grammar",
    "id": "G-1",
    "instruction": "语法题描述（说明考察什么语法点）",
    "content": "题目本身，用___表示需要填写的空",
    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
    "answer": "正确答案字母",
    "score": 2
  }},
  {{
    "type": "writing",
    "id": "W-1",
    "instruction": "写作题描述",
    "content": "写作要求和情景说明，字数要求：100-150词。",
    "score": 15
  }}
]

请确保生成 {grammar_count} 道语法题和 {writing_count} 道写作题。"""

            print(f"[试卷生成] 正在调用 AI 生成 {grammar_count} 道语法题 + {writing_count} 道写作题...", flush=True)

            ai_questions = None
            try:
                resp = _gemini_client.models.generate_content(
                    model=_MODEL_ID,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="你是专业的德语考试出题助手，只返回JSON格式数据。",
                        http_options={"timeout": 90_000},
                    ),
                )
                text = resp.text.strip()
                # 清洗 markdown 代码块
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                ai_questions = json.loads(text.strip())
                print(f"[试卷生成] AI 成功生成 {len(ai_questions)} 道题目", flush=True)
            except Exception as e:
                print(f"[试卷生成] AI 生成失败: {type(e).__name__}: {e}", flush=True)

            # AI 生成失败时使用基础 fallback
            if not ai_questions or not isinstance(ai_questions, list):
                print("[试卷生成] 使用 fallback 基础题目", flush=True)
                ai_questions = []
                grammar_topics = [
                    ("动词变位", "Ich ___ gestern ins Kino gegangen.", ["A. bin", "B. habe", "C. war", "D. wurde"], "A"),
                    ("格变化", "Er gibt ___ Freund ein Buch.", ["A. sein", "B. seinem", "C. seinen", "D. seiner"], "B"),
                    ("被动语态", "Das Haus ___ letztes Jahr gebaut.", ["A. hat", "B. ist", "C. wird", "D. wurde"], "D"),
                    ("虚拟式", "Wenn ich reich ___, würde ich reisen.", ["A. bin", "B. wäre", "C. war", "D. sei"], "B"),
                    ("从句语序", "Ich weiß, dass er morgen nach Berlin ___.", ["A. fahrt", "B. fährt", "C. gefahren", "D. fahren"], "B"),
                    ("介词搭配", "Wir warten ___ den Bus.", ["A. für", "B. auf", "C. an", "D. um"], "B"),
                    ("冠词", "Das ist ___ interessantes Buch.", ["A. ein", "B. eine", "C. einen", "D. einem"], "A"),
                    ("反身动词", "Er ___ sich für Musik.", ["A. interessiert", "B. interessieren", "C. interessiere", "D. interessierst"], "A"),
                ]
                for i in range(grammar_count):
                    t = grammar_topics[i % len(grammar_topics)]
                    ai_questions.append({
                        "type": "grammar", "id": f"G-{i+1}",
                        "instruction": f"语法题 {i+1}（考点：{t[0]}）：请选择正确的选项填空。",
                        "content": t[1], "options": t[2], "answer": t[3], "score": 2
                    })
                writing_topics = [
                    "你的一位德国朋友即将来中国旅行，请给他写一封邮件，推荐几个必去的城市，并说明理由。字数要求：100-150词。",
                    "请描述你理想的大学生活，包括学习、社交和课外活动。字数要求：100-150词。",
                    "请写一篇短文，介绍你最喜欢的一道中国菜的做法和它的文化意义。字数要求：100-150词。",
                ]
                for i in range(writing_count):
                    ai_questions.append({
                        "type": "writing", "id": f"W-{i+1}",
                        "instruction": f"写作题 {i+1}：请根据以下情景进行写作。",
                        "content": writing_topics[i % len(writing_topics)], "score": 15
                    })
            return ai_questions

        students = StudentCRUD.list_by_class(db, classroom.id)

        if strategy != "personalized":
            ai_questions = _generate_questions_for_student()
            exam = ExamCRUD.create(
                db,
                ExamCreate(
                    exam_code=exam_code,
                    teacher_user_id=teacher.id,
                    grammar_items=grammar_count,
                    writing_items=writing_count,
                    strategy=strategy,
                    focus_areas=cfg.get("focusAreas", []),
                    content=ai_questions,
                ),
            )
            for s in students:
                ExamAssignmentCRUD.create_or_get(
                    db,
                    ExamAssignmentCreate(exam_id=exam.id, student_id=s.id, status="assigned"),
                )
        else:
            exam = ExamCRUD.create(
                db,
                ExamCreate(
                    exam_code=exam_code,
                    teacher_user_id=teacher.id,
                    grammar_items=grammar_count,
                    writing_items=writing_count,
                    strategy=strategy,
                    focus_areas=cfg.get("focusAreas", []),
                    content=[], 
                ),
            )
            for s in students:
                ability = StudentAbilityCRUD.get_by_student_id(db, s.id)
                student_info = f"\n- 针对学生情况：该学生在【{s.weak_point or '其他'}】有薄弱点。"
                if ability and ability.ai_diagnosis:
                    student_info += f"\n- AI诊断信息：{ability.ai_diagnosis}"
                student_info += "\n**请务必针对该学生的薄弱点设计题目，体现出个性化！**"
                
                print(f"[千人千面] 正在为学生 {s.name}({s.uid}) 生成个性化试卷...", flush=True)
                personalized_q = _generate_questions_for_student(student_info)
                
                ExamAssignmentCRUD.create_or_get(
                    db,
                    ExamAssignmentCreate(
                        exam_id=exam.id, 
                        student_id=s.id, 
                        status="assigned", 
                        personalized_content=personalized_q
                    ),
                )

        return ok({"examId": exam.exam_code, "studentCount": len(students)}, "试卷生成成功")
    except Exception as e:
        return fail(f"试卷生成失败: {e}")


@app.get("/api/teacher/scenario/list")
def list_teacher_scenarios(request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher = require_teacher(request, db)
        scenarios = ScenarioCRUD.list_by_teacher(db, teacher.id)
        result = [
            {
                "id": s.id,
                "code": s.scenario_code,
                "theme": s.theme,
                "difficulty": s.difficulty,
                "persona": s.persona,
                "createdAt": s.created_at.isoformat(),
            }
            for s in scenarios
        ]
        return ok(result)
    except Exception as e:
        return fail(f"获取情景任务记录失败: {e}")


@app.get("/api/teacher/exam/list")
def list_teacher_exams(request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher = require_teacher(request, db)
        exams = ExamCRUD.list_by_teacher(db, teacher.id)
        result = [
            {
                "id": e.id,
                "code": e.exam_code,
                "grammarItems": e.grammar_items,
                "writingItems": e.writing_items,
                "strategy": e.strategy,
                "createdAt": e.created_at.isoformat(),
            }
            for e in exams
        ]
        return ok(result)
    except Exception as e:
        return fail(f"获取试卷记录失败: {e}")


@app.get("/api/teacher/exam/{exam_id}")
def get_teacher_exam_detail(exam_id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher = require_teacher(request, db)
        exam = ExamCRUD.get_by_id(db, exam_id)
        if not exam:
            return fail("试卷不存在", 404)
        if exam.teacher_user_id != teacher.id:
            return fail("无权访问该试卷", 403)
            
        content = {
            "代码": exam.exam_code,
            "语法题数量": exam.grammar_items,
            "写作题数量": exam.writing_items,
            "出题策略": "智能个性化" if exam.strategy == 'personalized' else "统一出题",
            "重点考察区域": exam.focus_areas,
            "生成时间": exam.created_at.isoformat(),
            "题目列表": exam.content
        }
        return ok(content)
    except Exception as e:
        return fail(f"获取试卷详情失败: {e}")


@app.get("/api/student/detail")
def get_student_detail(id: str, request: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(request, db)
        _ensure_demo_data(db)
        student = StudentCRUD.get_by_uid(db, id)
        if not student:
            return fail("学生不存在", 404)

        ability = StudentAbilityCRUD.get_by_student_id(db, student.id)
        homeworks = HomeworkCRUD.list_by_student(db, student.id)
        
        # 获取考试分配记录
        from sqlalchemy import select
        from models.entities import ExamAssignment, Exam
        exam_assignments = list(db.scalars(
            select(ExamAssignment).where(ExamAssignment.student_id == student.id).order_by(ExamAssignment.assigned_at.desc())
        ))
        exams_data = []
        for ea in exam_assignments:
            exam = ExamCRUD.get_by_id(db, ea.exam_id)
            if exam:
                exams_data.append({
                    "id": ea.id,
                    "examId": exam.id,
                    "examCode": exam.exam_code,
                    "strategy": exam.strategy,
                    "assignedAt": ea.assigned_at.strftime("%Y-%m-%d"),
                    "content": ea.personalized_content if exam.strategy == "personalized" else exam.content,
                })

        data = {
            "info": {
                "name": student.name,
                "uid": student.uid,
                "class": "软件工程",
                "active": student.active_score,
                "score": to_float(student.overall_score),
            },
            "ability": {
                "listening": ability.listening if ability else 0,
                "speaking": ability.speaking if ability else 0,
                "reading": ability.reading if ability else 0,
                "writing": ability.writing if ability else 0,
            },
            "aiDiagnosis": ability.ai_diagnosis if ability else "暂无诊断",
            "homeworks": [
                {
                    "id": h.id,
                    "title": h.title,
                    "date": (h.submitted_at or h.created_at).strftime("%Y-%m-%d"),
                    "status": h.status,
                    "score": to_float(h.score, None),
                    "feedback": h.ai_comment,
                }
                for h in homeworks
            ],
            "exams": exams_data,
        }
        return ok(data)
    except Exception as e:
        return fail(f"获取学生详情失败: {e}")


@app.get("/api/homework/detail")
def get_homework_detail(id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(request, db)
        _ensure_demo_data(db)
        hw = HomeworkCRUD.get_by_id(db, id)
        if not hw:
            return fail("作业不存在", 404)

        file_url = hw.file_url
        if hw.file_type == "json_exam":
            # 如果是试卷类型，跳转到专门的下载接口生成文本
            file_url = f"/api/homework/download/{hw.id}"

        data = {
            "type": hw.file_type or "text",
            "meta": {
                "fileUrl": file_url,
                "fileName": hw.file_name or f"homework-{hw.id}.txt",
                "fileSize": hw.file_size or "自动生成",
                "uploadTime": (hw.submitted_at or hw.created_at).strftime("%Y-%m-%d %H:%M"),
            },
            "aiComment": hw.ai_comment or "暂无 AI 评价数据。",
        }
        return ok(data)
    except Exception as e:
        return fail(f"获取作业详情失败: {e}")


@app.get("/api/homework/download/{id}")
def download_homework_as_text(id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(request, db)
        hw = HomeworkCRUD.get_by_id(db, id)
        if not hw:
            raise HTTPException(status_code=404, detail="作业不存在")

        if hw.file_type != "json_exam":
            # 非试卷类型直接重定向到原始 URL（如果是文件的话）
            if hw.file_url and hw.file_url.startswith("http"):
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=hw.file_url)
            raise HTTPException(status_code=400, detail="该作业类型不支持直接下载文本")

        # 获取试卷内容
        assignment = None
        if hw.exam_assignment_id:
            assignment = db.scalar(select(ExamAssignment).where(ExamAssignment.id == hw.exam_assignment_id))
        
        if not assignment:
             raise HTTPException(status_code=404, detail="找不到对应的试卷分配记录")

        exam = db.scalar(select(Exam).where(Exam.id == assignment.exam_id))
        if not exam:
            raise HTTPException(status_code=404, detail="找不到对应的原始试卷")

        content = assignment.personalized_content if assignment.personalized_content else exam.content
        
        # 解析答案
        answers = {}
        try:
            if hw.file_url:
                answers = json.loads(hw.file_url)
        except Exception:
            pass

        student = StudentCRUD.get_by_id(db, hw.student_id)
        
        # 生成导出文本
        buffer = io.StringIO()
        buffer.write(f"学生姓名: {student.name if student else '未知'}\n")
        buffer.write(f"试卷代码: {exam.exam_code or 'N/A'}\n")
        buffer.write(f"提交时间: {hw.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if hw.submitted_at else '未知'}\n")
        buffer.write(f"最终得分: {hw.score if hw.score is not None else '未评分'}\n")
        buffer.write("=" * 40 + "\n\n")

        for idx, q in enumerate(content or []):
            q_type = q.get('type', '未知')
            buffer.write(f"题目 {idx + 1} [{q_type}]\n")
            buffer.write(f"要求: {q.get('instruction', '')}\n")
            buffer.write(f"内容: {q.get('content', '')}\n")
            
            if q_type == 'grammar':
                buffer.write("选项:\n")
                for opt in q.get('options', []):
                    buffer.write(f"  - {opt}\n")
                
                correct_ans = str(q.get('answer', ''))
                student_ans = str(answers.get(str(idx), ''))
                buffer.write(f"正确答案: {correct_ans}\n")
                buffer.write(f"学生答案: {student_ans}\n")
                
                # 简单校验
                is_correct = False
                if student_ans.strip().upper() == correct_ans.strip().upper() or \
                   (student_ans.startswith(correct_ans) and (len(student_ans) == len(correct_ans) or student_ans[len(correct_ans)] in '. ')):
                    is_correct = True
                
                buffer.write(f"判定: {'正确 ✅' if is_correct else '错误 ❌'}\n")
            else:
                student_ans = answers.get(str(idx), '')
                buffer.write(f"学生回答:\n{student_ans}\n")
            
            buffer.write("-" * 20 + "\n\n")

        buffer.write("AI 评价与反馈:\n")
        buffer.write(hw.ai_comment or "暂无反馈")
        buffer.write("\n")

        content_str = buffer.getvalue()
        buffer.close()

        import urllib.parse
        student_name = student.name if student else "student"
        exam_code = exam.exam_code or "EXAM"
        filename = f"答卷_{exam_code}_{student_name}.txt"
        encoded_filename = urllib.parse.quote(filename)

        return StreamingResponse(
            io.BytesIO(content_str.encode('utf-8')),
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"下载生成失败: {str(e)}")


@app.post("/api/homework/save")
def save_homework_review(request: HomeworkSaveRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(req, db)
        teacher, _ = _ensure_demo_data(db)
        hw = HomeworkCRUD.get_by_id(db, request.homeworkId)
        if not hw:
            return fail("作业不存在", 404)

        HomeworkReviewCRUD.create(
            db,
            HomeworkReviewCreate(
                homework_id=request.homeworkId,
                teacher_user_id=teacher.id,
                score=request.score,
                feedback=request.feedback,
            ),
        )
        HomeworkCRUD.update_score_feedback(db, request.homeworkId, request.score, request.feedback)
        return ok({"homeworkId": request.homeworkId, "saved": True}, "评分保存成功")
    except Exception as e:
        return fail(f"评分保存失败: {e}")


@app.post("/api/student/push-scheme")
def push_student_scheme(request: PushSchemeRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(req, db)
        teacher, _ = _ensure_demo_data(db)
        student = StudentCRUD.get_by_uid(db, request.studentId)
        if not student:
            return fail("学生不存在", 404)

        scenario_code = f"SCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"
        scenario = ScenarioCRUD.create(
            db,
            ScenarioCreate(
                scenario_code=scenario_code,
                teacher_user_id=teacher.id,
                theme="个性化强化方案",
                difficulty="自适应",
                persona="严谨纠错",
                goal_require_perfect_tense=True,
                goal_require_b1_vocab=False,
            ),
        )

        ScenarioPushCRUD.create_or_get(
            db,
            ScenarioPushCreate(scenario_id=scenario.id, student_id=student.id, push_status="pushed"),
        )

        return ok({"schemeName": "个性化强化方案"}, "推送成功")
    except Exception as e:
        return fail(f"推送失败: {e}")


# ════════════════════ 7. 学生端 API ════════════════════


# ╔═══════════════════════════════════════════════════════╗
# ║  7-1. 学生登录                                       ║
# ╚═══════════════════════════════════════════════════════╝


@app.post("/api/auth/student-login")
def student_login(req: StudentLoginReq, db: Session = Depends(get_db)):
    try:
        student = StudentCRUD.get_by_uid(db, req.username)
        if not student:
            return fail("学号不存在，请检查后重试", 401)

        user = UserCRUD.get_by_id(db, student.user_id)
        if not user:
            return fail("用户记录异常", 500)

        if user.password_hash != req.password:
            return fail("密码错误，请重新输入", 401)

        token = f"student-token-{student.uid}-{uuid4().hex[:8]}"
        info = {
            "id": student.uid,
            "name": student.name,
            "role": "student",
            "studentId": student.id,
        }
        return {
            "code": 200,
            "message": "登录成功",
            "token": token,
            "user": info,
            "data": {"token": token, "user": info},
        }
    except Exception as e:
        return fail(f"登录失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-1a. 学生注册                                      ║
# ╚═══════════════════════════════════════════════════════╝


@app.post("/api/auth/student-register")
def student_register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        # 1. 检查用户名(学号)是否已存在
        existing_user = UserCRUD.get_by_username(db, req.username)
        if existing_user:
            return fail("该学号已被注册", 409)

        existing_student = StudentCRUD.get_by_uid(db, req.username)
        if existing_student:
            return fail("该学号已被注册", 409)

        # 2. 确保默认班级存在
        _ensure_demo_data(db)
        class_code = req.class_code or "SE-2026-4"
        classroom = ClassroomCRUD.get_by_code(db, class_code)
        if not classroom:
            return fail(f"班级 {class_code} 不存在", 404)

        # 3. 创建 User 记录
        user = UserCRUD.create(
            db,
            UserCreate(
                username=req.username,
                password_hash=req.password,
                role="student",
                display_name=req.display_name,
            ),
        )

        # 4. 创建 Student 记录
        student = StudentCRUD.create(
            db,
            StudentCreate(
                uid=req.username,
                user_id=user.id,
                class_id=classroom.id,
                name=req.display_name,
                active_score=0,
                overall_score=0,
            ),
        )

        # 5. 初始化 StudentAbility
        StudentAbilityCRUD.upsert(
            db,
            StudentAbilityUpsert(
                student_id=student.id,
                listening=0,
                speaking=0,
                reading=0,
                writing=0,
                ai_diagnosis=f"{req.display_name}刚注册，暂无学习数据。",
            ),
        )

        return ok({"username": req.username, "name": req.display_name}, "注册成功")
    except Exception as e:
        return fail(f"注册失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-1b. 教师注册                                      ║
# ╚═══════════════════════════════════════════════════════╝


@app.post("/api/auth/teacher-register")
def teacher_register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        # 1. 检查用户名(工号)是否已存在
        existing_user = UserCRUD.get_by_username(db, req.username)
        if existing_user:
            return fail("该工号已被注册", 409)

        # 2. 创建 User 记录
        user = UserCRUD.create(
            db,
            UserCreate(
                username=req.username,
                password_hash=req.password,
                role="teacher",
                display_name=req.display_name,
            ),
        )

        return ok({"username": req.username, "name": req.display_name}, "注册成功")
    except Exception as e:
        return fail(f"注册失败: {e}")



# ╔═══════════════════════════════════════════════════════╗
# ║  7-1.5. 学生端大厅 AI 对话 (Student Chat)              ║
# ║  按学生隔离，使用 chat_sessions + chat_messages        ║
# ╚═══════════════════════════════════════════════════════╝

STUDENT_LOBBY_SCENE_NAME = "大厅AI"


@app.post("/api/student/chat")
def student_chat_endpoint(
    bg: BackgroundTasks,
    req: Request,
    request: StudentChatReq,
    db: Session = Depends(get_db),
):
    student = require_student(req, db)
    print(f"[学生AI] student_id={student.id} 消息: {request.message[:80]!r}...", flush=True)
    try:
        session = _resolve_student_session(
            db,
            student.id,
            None,
            STUDENT_LOBBY_SCENE_NAME,
            new_thread=request.new_thread,
            session_id=request.session_id,
        )
        ChatMessageCRUD.create(
            db, ChatMessageCreate(session_id=session.id, role="user", content=request.message)
        )
        ChatSessionCRUD.set_title_if_empty(db, session.id, request.message)
        history = ChatMessageCRUD.list_by_session(db, session.id)
        contents_to_send = []
        if getattr(student, "long_memory_summary", None):
            contents_to_send.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="[Learner profile]\n" + student.long_memory_summary)],
                )
            )
        contents_to_send.extend(_history_to_gemini_contents(history, max_turns=14))
        response = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=contents_to_send,
            config=types.GenerateContentConfig(
                system_instruction=_STUDENT_SYSTEM,
                http_options={"timeout": 90_000},
            ),
        )
        reply_text = response.text or ""
        ChatMessageCRUD.create(
            db,
            ChatMessageCreate(session_id=session.id, role="assistant", content=reply_text, correction=None),
        )
        ChatSessionCRUD.touch(db, session.id)
        n = len(history) + 2
        if n >= MEMORY_REFRESH_EVERY and n % MEMORY_REFRESH_EVERY == 0:
            bg.add_task(_refresh_student_memory, student.id, session.id)
        return {"reply": reply_text, "session_id": session.id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[学生AI] Gemini调用失败: {type(e).__name__}: {e}", flush=True)
        return {"reply": f"AI 暂时无法响应，请稍后重试。错误信息: {type(e).__name__}"}


@app.post("/api/student/chat/new-session")
def student_chat_new_session(req: Request, db: Session = Depends(get_db)):
    """关闭当前大厅会话并返回新 session_id（下一条消息将写入新会话）"""
    student = require_student(req, db)
    ChatSessionCRUD.close_open_for_channel(db, student.id, None, STUDENT_LOBBY_SCENE_NAME)
    s = ChatSessionCRUD.create(
        db, ChatSessionCreate(student_id=student.id, scene_id=None, scene_name=STUDENT_LOBBY_SCENE_NAME)
    )
    return ok({"session_id": s.id})


@app.get("/api/student/chat/sessions")
def student_chat_sessions(req: Request, db: Session = Depends(get_db)):
    student = require_student(req, db)
    rows = ChatSessionCRUD.list_channel_sessions(
        db, student.id, None, STUDENT_LOBBY_SCENE_NAME, limit=80
    )
    return ok(
        [
            {
                "id": r.id,
                "title": (r.title or "").strip() or None,
                "closed": r.closed_at is not None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
    )


@app.get("/api/student/chat/messages")
def student_chat_messages(
    req: Request,
    db: Session = Depends(get_db),
    session_id: int = Query(..., description="大厅会话 id"),
):
    """拉取某条大厅会话的全部消息（留痕查阅 / 切换会话展示）"""
    student = require_student(req, db)
    s = ChatSessionCRUD.get_by_id(db, session_id)
    if not s or s.student_id != student.id:
        return fail("会话不存在", 404)
    if s.scene_id is not None or (s.scene_name or "") != STUDENT_LOBBY_SCENE_NAME:
        return fail("仅支持大厅智能对话会话", 403)
    msgs = ChatMessageCRUD.list_by_session(db, session_id)
    return ok(
        [
            {"id": m.id, "role": m.role, "content": m.content}
            for m in msgs
        ]
    )


@app.delete("/api/student/chat/session/{session_id}")
def student_chat_delete_session(
    session_id: int,
    req: Request,
    db: Session = Depends(get_db),
):
    """删除指定大厅会话及全部消息（不可恢复）"""
    student = require_student(req, db)
    ok_del = ChatSessionCRUD.delete_lobby_session(
        db, student.id, session_id, STUDENT_LOBBY_SCENE_NAME
    )
    if not ok_del:
        return fail("会话不存在或无权删除", 404)
    return ok(message="已删除")


@app.post("/api/teacher/chat/new-session")
def teacher_chat_new_session(req: Request, db: Session = Depends(get_db)):
    user = require_teacher(req, db)
    TeacherChatSessionCRUD.close_open_for_user(db, user.id)
    s = TeacherChatSessionCRUD.create(db, TeacherChatSessionCreate(user_id=user.id))
    return ok({"session_id": s.id})


@app.get("/api/teacher/chat/sessions")
def teacher_chat_sessions(req: Request, db: Session = Depends(get_db)):
    user = require_teacher(req, db)
    rows = TeacherChatSessionCRUD.list_by_user(db, user.id, limit=40)
    return ok(
        [
            {
                "id": r.id,
                "closed": r.closed_at is not None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
    )


# ╔═══════════════════════════════════════════════════════╗
# ║  7-2. 场景对话 (AISceneChat) 每情景单线程、长期续接    ║
# ╚═══════════════════════════════════════════════════════╝


def _resolve_scene_single_thread(
    db: Session, student_id: int, scene_id: int, scene_name: str
):
    """每情景一条线：优先沿用该情景下最近更新的会话（含已暂停则自动 reopen），否则新建。"""
    rows = ChatSessionCRUD.list_channel_sessions(
        db, student_id, scene_id, scene_name, limit=1
    )
    if rows:
        s = rows[0]
        if getattr(s, "closed_at", None) is not None:
            ChatSessionCRUD.reopen(db, s.id)
        return ChatSessionCRUD.get_by_id(db, s.id) or s
    return ChatSessionCRUD.create(
        db,
        ChatSessionCreate(
            student_id=student_id, scene_id=scene_id, scene_name=scene_name
        ),
    )


@app.get("/api/student/scene-chat/state")
def scene_chat_state(
    request: Request,
    db: Session = Depends(get_db),
    scene_id: int = Query(...),
    scene_name: str = Query(...),
):
    """当前情景下的连续对话：最近一条会话的全部消息（无则空）"""
    student = require_student(request, db)
    name = (scene_name or "").strip() or "自由对话"
    rows = ChatSessionCRUD.list_channel_sessions(db, student.id, scene_id, name, limit=1)
    if not rows:
        return ok({"session_id": None, "messages": []})
    sid = rows[0].id
    msgs = ChatMessageCRUD.list_by_session(db, sid)
    out = [
        {"id": m.id, "role": m.role, "content": m.content, "correction": m.correction}
        for m in msgs
    ]
    return ok({"session_id": sid, "messages": out})


@app.delete("/api/student/scene-chat/clear")
def scene_chat_clear(
    request: Request,
    db: Session = Depends(get_db),
    scene_id: int = Query(...),
    scene_name: str = Query(...),
):
    """清空该情景下全部历史（可选），下次发送会新开一条会话"""
    student = require_student(request, db)
    name = (scene_name or "").strip() or "自由对话"
    n = ChatSessionCRUD.delete_all_channel_sessions(db, student.id, scene_id, name)
    return ok({"deleted": n}, message="已清空本情景记录" if n else "暂无记录")


@app.post("/api/student/scene-chat")
def scene_chat(req: SceneChatReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        scene_name = req.sceneName or "自由对话"
        if req.sceneId is None:
            return fail("场景对话需要 sceneId", 400)
        session = _resolve_scene_single_thread(
            db, student.id, req.sceneId, scene_name
        )

        ChatMessageCRUD.create(
            db, ChatMessageCreate(session_id=session.id, role="user", content=req.userMessage)
        )
        ChatSessionCRUD.set_title_if_empty(db, session.id, req.userMessage)

        history = ChatMessageCRUD.list_by_session(db, session.id)
        conv_lines = [
            f"{'学生' if m.role == 'user' else 'AI助教'}: {m.content}" for m in history
        ]

        prompt = (
            f"场景：「{scene_name}」德语对话练习。\n"
            f"对话历史:\n" + "\n".join(conv_lines) + "\n\n"
            f"请用德语回复（括号内中文翻译），如有语法错误请纠正。\n"
            f'返回JSON: {{"reply":"德语回复","correction":"纠错说明或null"}}'
        )
        result = _ai_json(prompt, {
            "reply": "Entschuldigung, bitte versuchen Sie es noch einmal. (请再试一次)",
            "correction": None,
        })
        reply = result.get("reply", "Bitte versuchen Sie es noch einmal.")
        correction = result.get("correction")

        ChatMessageCRUD.create(
            db,
            ChatMessageCreate(
                session_id=session.id, role="assistant", content=reply, correction=correction
            ),
        )
        ChatSessionCRUD.touch(db, session.id)

        return ok({"reply": reply, "correction": correction, "session_id": session.id})
    except Exception as e:
        return fail(f"对话失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-3. 词汇学习 (VocabLearning)                      ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/vocab/list")
def vocab_list(request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        words = VocabularyCRUD.list_all(db)
        data = []
        for w in words:
            collected = (
                StudentVocabCollectionCRUD.is_collected(db, student.id, w.id) if student else False
            )
            data.append({
                "id": w.id, "german": w.german, "chinese": w.chinese,
                "example": w.example, "isCollected": collected,
            })
        return ok(data)
    except Exception as e:
        return fail(f"获取词汇失败: {e}")


@app.post("/api/student/vocab/collect")
def vocab_collect(req: VocabCollectReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        if req.isCollect:
            StudentVocabCollectionCRUD.collect(
                db, StudentVocabCollectionCreate(student_id=student.id, vocab_id=req.vocabId)
            )
            # ── 同步写入收藏夹（favorites 表），使"我的收藏"页面可见 ──
            vocab = VocabularyCRUD.get_by_id(db, req.vocabId)
            vocab_cat = FavoriteCategoryCRUD.get_by_type(db, "vocab")
            if vocab and vocab_cat:
                # 避免重复插入：检查是否已存在同内容收藏
                existing_favs = FavoriteCRUD.list_by_student_and_category(db, student.id, vocab_cat.id)
                already_exists = any(f.content == vocab.german for f in existing_favs)
                if not already_exists:
                    FavoriteCRUD.create(db, FavoriteCreate(
                        student_id=student.id,
                        category_id=vocab_cat.id,
                        content=vocab.german,
                        translate=vocab.chinese,
                        note=vocab.example,
                    ))
        else:
            StudentVocabCollectionCRUD.uncollect(db, student.id, req.vocabId)
            # ── 同步从收藏夹删除 ──
            vocab = VocabularyCRUD.get_by_id(db, req.vocabId)
            vocab_cat = FavoriteCategoryCRUD.get_by_type(db, "vocab")
            if vocab and vocab_cat:
                existing_favs = FavoriteCRUD.list_by_student_and_category(db, student.id, vocab_cat.id)
                for f in existing_favs:
                    if f.content == vocab.german:
                        FavoriteCRUD.delete(db, f.id)
                        break
        return ok(None, "操作成功")
    except Exception as e:
        return fail(f"收藏操作失败: {e}")


@app.post("/api/student/vocab/generate")
def vocab_generate(req: VocabGenerateReq, db: Session = Depends(get_db)):
    try:
        existing = VocabularyCRUD.list_all(db, level=req.level, topic=req.topic)
        existing_words = [w.german for w in existing]

        prompt = (
            f"请生成5个德语{req.level}级别、主题「{req.topic}」的新词汇。\n"
            f"已有(不要重复): {', '.join(existing_words[:20])}\n"
            f'返回JSON数组: [{{"german":"…","chinese":"…","example":"例句…"}}]\n只返回JSON。'
        )
        words = _ai_json(prompt, [])

        saved = []
        for w in words or []:
            if not isinstance(w, dict) or "german" not in w:
                continue
            try:
                v = VocabularyCRUD.create(
                    db,
                    VocabularyCreate(
                        german=w["german"], chinese=w.get("chinese", ""),
                        example=w.get("example"), level=req.level, topic=req.topic,
                    ),
                )
                saved.append({
                    "id": v.id, "german": v.german, "chinese": v.chinese,
                    "example": v.example, "isCollected": False,
                })
            except Exception:
                pass
        return ok(saved)
    except Exception as e:
        return fail(f"生成词汇失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-4. 语法练习 (GrammarPractice)                     ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/grammar/categories")
def grammar_categories(request: Request, db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        cats = GrammarCategoryCRUD.list_all(db)
        return ok([{"id": c.id, "name": c.name, "desc": c.description or ""} for c in cats])
    except Exception as e:
        return fail(f"获取分类失败: {e}")


@app.get("/api/student/grammar/exercises")
def grammar_exercises(request: Request, categoryId: int = Query(...), db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        exs = GrammarExerciseCRUD.list_by_category(db, categoryId)
        return ok([{"id": e.id, "question": e.question} for e in exs])
    except Exception as e:
        return fail(f"获取练习失败: {e}")


@app.post("/api/student/grammar/submit")
def grammar_submit(req: GrammarSubmitReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        details = []
        correct_count = 0
        error_cats = {c.name: c.id for c in ErrorBookCategoryCRUD.list_all(db)}

        for ans in req.answers:
            ex = GrammarExerciseCRUD.get_by_id(db, ans.exerciseId)
            if not ex:
                continue

            is_correct = ans.userAnswer.strip().lower() == ex.correct_answer.strip().lower()
            if is_correct:
                correct_count += 1

            analysis = ex.analysis or ""
            if not is_correct and not analysis:
                analysis = _ai_text(
                    f"德语语法题:\n题目:{ex.question}\n学生答:{ans.userAnswer}\n"
                    f"正确答案:{ex.correct_answer}\n请用中文简短解释错误原因(50字以内)。",
                    "请参考正确答案复习。",
                )

            GrammarSubmissionCRUD.create(
                db,
                GrammarSubmissionCreate(
                    student_id=student.id, exercise_id=ans.exerciseId,
                    user_answer=ans.userAnswer, is_correct=is_correct,
                    ai_analysis=analysis if not is_correct else None,
                ),
            )

            if not is_correct:
                grammar_cat = GrammarCategoryCRUD.get_by_id(db, req.categoryId)
                eb_cat_id = _match_error_category(
                    grammar_cat.name if grammar_cat else "", error_cats
                )
                if eb_cat_id:
                    try:
                        ErrorBookEntryCRUD.create(
                            db,
                            ErrorBookEntryCreate(
                                student_id=student.id, category_id=eb_cat_id,
                                source="语法练习", question=ex.question,
                                user_answer=ans.userAnswer,
                                correct_answer=ex.correct_answer, analysis=analysis,
                            ),
                        )
                    except Exception:
                        pass

            details.append({
                "exerciseId": ex.id, "isCorrect": is_correct,
                "correctAnswer": ex.correct_answer,
                "analysis": analysis if not is_correct else "",
            })

        wrong_count = len(req.answers) - correct_count
        return ok({
            "totalCount": len(req.answers), "correctCount": correct_count,
            "wrongCount": wrong_count, "detailList": details,
        })
    except Exception as e:
        return fail(f"提交失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-5. 听说训练 (ListeningSpeaking)                   ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/listening/materials")
def listening_materials(db: Session = Depends(get_db)):
    try:
        mats = ListeningMaterialCRUD.list_all(db)
        return ok([
            {"id": m.id, "title": m.title, "level": m.level, "duration": m.duration}
            for m in mats
        ])
    except Exception as e:
        return fail(f"获取听力材料失败: {e}")


@app.get("/api/student/listening/material/detail")
def listening_material_detail(materialId: int = Query(...), db: Session = Depends(get_db)):
    try:
        m = ListeningMaterialCRUD.get_by_id(db, materialId)
        if not m:
            return fail("材料不存在", 404)
        return ok({"audioUrl": m.audio_url, "script": m.script or ""})
    except Exception as e:
        return fail(f"获取详情失败: {e}")


@app.post("/api/student/speaking/evaluate")
def speaking_evaluate(req: SpeakingEvalReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        material = ListeningMaterialCRUD.get_by_id(db, req.materialId)
        if not material:
            return fail("听力材料不存在", 404)

        prompt = (
            f"你是德语口语评估助手。学生朗读了以下听力材料:\n"
            f"标题: {material.title}\n原文: {material.script or '(无原文)'}\n"
            f"请给出评分(0-100)和建议。返回JSON:\n"
            f'{{"totalScore":85,"pronunciationScore":88,"fluencyScore":82,'
            f'"intonationScore":85,"analysis":"分析","suggestion":"建议"}}'
        )
        result = _ai_json(prompt, {
            "totalScore": 78, "pronunciationScore": 80,
            "fluencyScore": 76, "intonationScore": 78,
            "analysis": "发音基本准确，需注意元音长短区分。",
            "suggestion": "建议多听原文录音，模仿语调节奏。",
        })

        SpeakingEvaluationCRUD.create(
            db,
            SpeakingEvaluationCreate(
                student_id=student.id, material_id=req.materialId,
                audio_url=req.audioUrl,
                total_score=result.get("totalScore"),
                pronunciation_score=result.get("pronunciationScore"),
                fluency_score=result.get("fluencyScore"),
                intonation_score=result.get("intonationScore"),
                analysis=result.get("analysis"),
                suggestion=result.get("suggestion"),
            ),
        )

        return ok(result)
    except Exception as e:
        return fail(f"评估失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-6. 写作辅助 (WritingAssistant)                    ║
# ╚═══════════════════════════════════════════════════════╝


@app.post("/api/student/writing/check")
def writing_check(req: WritingReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)

        prompt = (
            f"请检查以下德语文本的语法和拼写错误:\n\n{req.userText}\n\n"
            f"返回JSON: {{\"errors\":[{{\"position\":\"出错位置\",\"error\":\"错误描述\","
            f"\"suggestion\":\"修改建议\"}}],\"polishedText\":\"修正后完整文本\"}}\n只返回JSON。"
        )
        result = _ai_json(prompt, {"errors": [], "polishedText": req.userText})

        if student:
            WritingSessionCRUD.create(
                db,
                WritingSessionCreate(
                    student_id=student.id, session_type="check",
                    user_text=req.userText, result_json=result,
                ),
            )

        return ok(result)
    except Exception as e:
        return fail(f"检查失败: {e}")


@app.post("/api/student/writing/generate-sample")
def writing_generate_sample(req: WritingReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)

        prompt = (
            f"学生正在练习德语写作，主题/草稿如下:\n\n{req.userText}\n\n"
            f"请生成一篇优秀的德语范文(A2-B1水平，150-200词)。\n"
            f'返回JSON: {{"sampleEssay":"范文内容"}}\n只返回JSON。'
        )
        result = _ai_json(prompt, {
            "sampleEssay": "Entschuldigung, die Beispielgeneration ist momentan nicht verfügbar. "
                           "(抱歉，范文生成暂时不可用。)"
        })

        if student:
            WritingSessionCRUD.create(
                db,
                WritingSessionCreate(
                    student_id=student.id, session_type="generate",
                    user_text=req.userText, result_json=result,
                ),
            )

        return ok(result)
    except Exception as e:
        return fail(f"生成范文失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-7. 错题本 (ErrorBookReview)                       ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/error-book/categories")
def error_book_categories(request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        data = ErrorBookEntryCRUD.count_by_category(db, student.id)
        return ok(data)
    except Exception as e:
        return fail(f"获取错题分类失败: {e}")


@app.get("/api/student/error-book/list")
def error_book_list(
    categoryId: int = Query(...), request: Request = None, db: Session = Depends(get_db)
):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        entries = ErrorBookEntryCRUD.list_by_student_and_category(db, student.id, categoryId)
        return ok([
            {
                "id": e.id, "source": e.source, "question": e.question,
                "userAnswer": e.user_answer, "correctAnswer": e.correct_answer,
                "analysis": e.analysis or "",
            }
            for e in entries
        ])
    except Exception as e:
        return fail(f"获取错题列表失败: {e}")


@app.post("/api/student/error-book/start-review")
def error_book_start_review(req: ErrorReviewReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        entries = ErrorBookEntryCRUD.list_by_student_and_category(db, student.id, req.categoryId)
        cat_name = req.categoryName or "此分类"

        if not entries:
            return ok({"reviewTip": f"🎉 「{cat_name}」没有未掌握的错题，继续保持！"})

        questions_summary = "\n".join(
            [f"- 题目: {e.question} | 学生答: {e.user_answer} | 正确: {e.correct_answer}" for e in entries[:5]]
        )
        prompt = (
            f"学生在「{cat_name}」分类下有以下错题:\n{questions_summary}\n"
            f"请用中文给出针对性的复习建议(100字以内)。"
        )
        tip = _ai_text(prompt, f"建议重点复习「{cat_name}」相关语法规则，结合例句反复练习。")
        return ok({"reviewTip": tip})
    except Exception as e:
        return fail(f"生成复习建议失败: {e}")


@app.post("/api/student/error-book/mark-mastered")
def error_book_mark_mastered(req: ErrorMasterReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        entry = ErrorBookEntryCRUD.get_by_id(db, req.errorId)
        if not entry:
            return fail("错题不存在", 404)
        if entry.student_id != student.id:
            return fail("无权操作该错题", 403)
        ErrorBookEntryCRUD.mark_mastered(db, req.errorId)
        return ok(None, "已标记为掌握")
    except Exception as e:
        return fail(f"标记失败: {e}")


@app.delete("/api/student/error-book/delete/{error_id}")
def error_book_delete(error_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        entry = ErrorBookEntryCRUD.get_by_id(db, error_id)
        if not entry:
            return fail("错题不存在", 404)
        if entry.student_id != student.id:
            return fail("无权操作该错题", 403)
        ErrorBookEntryCRUD.delete(db, error_id)
        return ok(None, "删除成功")
    except Exception as e:
        return fail(f"删除失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-8. 收藏夹 (FavoritesPage)                        ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/favorites/categories")
def favorites_categories(request: Request, db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        cats = FavoriteCategoryCRUD.list_all(db)
        return ok([{"id": c.id, "type": c.type, "name": c.name} for c in cats])
    except Exception as e:
        return fail(f"获取收藏分类失败: {e}")


@app.get("/api/student/favorites/list")
def favorites_list(
    type: str = Query(...), request: Request = None, db: Session = Depends(get_db)
):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        items = FavoriteCRUD.list_by_student_and_type(db, student.id, type)
        return ok([
            {
                "id": f.id, "content": f.content,
                "translate": f.translate, "rule": f.rule, "note": f.note,
            }
            for f in items
        ])
    except Exception as e:
        return fail(f"获取收藏列表失败: {e}")


@app.delete("/api/student/favorites/{fav_id}")
def favorites_delete(fav_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        fav = FavoriteCRUD.get_by_id(db, fav_id)
        if not fav:
            return fail("收藏不存在", 404)
        if fav.student_id != student.id:
            return fail("无权操作该收藏", 403)

        # ── 若删除的是词汇类收藏，同步清除 student_vocab_collections 记录 ──
        vocab_cat = FavoriteCategoryCRUD.get_by_type(db, "vocab")
        if vocab_cat and fav.category_id == vocab_cat.id:
            # 按 content(德语单词) 反查词汇表，找到 vocab_id 后取消收藏
            all_vocabs = VocabularyCRUD.list_all(db)
            for v in all_vocabs:
                if v.german == fav.content:
                    StudentVocabCollectionCRUD.uncollect(db, student.id, v.id)
                    break

        FavoriteCRUD.delete(db, fav_id)
        return ok(None, "删除成功")
    except Exception as e:
        return fail(f"删除失败: {e}")


@app.post("/api/student/favorites/ai-extend")
def favorites_ai_extend(req: FavAIExtendReq, request: Request = None, db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        type_prompts = {
            "vocab": f"请对德语词汇「{req.content}」进行扩展：给出词性、复数形式、常用搭配和2个例句。用中文回答。",
            "grammar": f"请对德语语法规则「{req.content}」进行扩展讲解：给出详细说明和3个例句。用中文回答。",
            "sentence": f"请对德语句子「{req.content}」进行分析：逐词翻译、语法结构、类似表达。用中文回答。",
            "note": f"请对学习笔记「{req.content}」进行扩展：补充相关知识点和记忆技巧。用中文回答。",
        }
        prompt = type_prompts.get(req.type, f"请对「{req.content}」进行扩展讲解，用中文回答。")
        extended = _ai_text(prompt, f"暂无法为「{req.content}」生成扩展内容。")
        return ok({"extendContent": extended})
    except Exception as e:
        return fail(f"AI扩展失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-9. 学习进度 (LearningProgress)                    ║
# ╚═══════════════════════════════════════════════════════╝

DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


@app.get("/api/student/learning/progress")
def learning_progress(request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        total_time = LearningSessionCRUD.total_minutes(db, student.id)
        week_time = LearningSessionCRUD.week_minutes(db, student.id)

        sessions = LearningSessionCRUD.list_by_student(db, student.id)
        module_map: dict[str, int] = {}
        for s in sessions:
            module_map[s.module] = module_map.get(s.module, 0) + s.duration_minutes

        all_modules = ["词汇学习", "语法练习", "情景对话", "听说训练", "写作辅助"]
        max_minutes = max(module_map.values()) if module_map else 1
        modules = [
            {"name": m, "rate": round(module_map.get(m, 0) / max_minutes * 100) if max_minutes else 0}
            for m in all_modules
        ]

        knowledge_list = StudentKnowledgeMasteryCRUD.list_by_student(db, student.id)
        knowledge = [{"name": k.knowledge_name, "level": k.mastery_level} for k in knowledge_list]

        mastered_count = sum(1 for k in knowledge_list if k.mastery_level == "熟练")
        finish_rate = round(mastered_count / len(knowledge_list) * 100) if knowledge_list else 0

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_sessions = [
            s for s in sessions
            if hasattr(s.session_date, 'date')
            and s.session_date.date() >= week_start
            or (isinstance(s.session_date, date) and s.session_date >= week_start)
        ]

        day_map: dict[int, dict] = {}
        for s in week_sessions:
            sd = s.session_date.date() if hasattr(s.session_date, 'date') else s.session_date
            weekday = sd.weekday()
            if weekday not in day_map:
                day_map[weekday] = {"time": 0, "contents": []}
            day_map[weekday]["time"] += s.duration_minutes
            if s.content:
                day_map[weekday]["contents"].append(s.content)

        week_report = [
            {
                "day": DAY_NAMES[i],
                "time": day_map[i]["time"] if i in day_map else 0,
                "content": "、".join(day_map[i]["contents"]) if i in day_map else "",
            }
            for i in range(7)
        ]

        return ok({
            "totalTime": total_time,
            "weekTime": week_time,
            "finishRate": finish_rate,
            "modules": modules,
            "knowledge": knowledge,
            "weekReport": week_report,
        })
    except Exception as e:
        return fail(f"获取学习进度失败: {e}")


# ════════════════════ 8. 根路由 ════════════════════


@app.get("/")
def read_root():
    return {"status": "ok", "message": "SITP German Agent 后端正在运行中! 🚀"}

# ╔═══════════════════════════════════════════════════════╗
# ║  8. 学生端任务中心 (Student Tasks)                     ║
# ╚═══════════════════════════════════════════════════════╝

@app.get("/api/student/tasks")
def get_student_tasks(request: Request, db: Session = Depends(get_db)):
    student = _current_student(request, db)
    if not student: return fail("请先登录", 401)
    
    tasks = []
    
    # 获取试卷任务 ExamAssignments
    assignments = db.scalars(
        select(ExamAssignment)
        .where(ExamAssignment.student_id == student.id)
        .order_by(ExamAssignment.assigned_at.desc())
    ).all()
    for a in assignments:
        exam = db.scalar(select(Exam).where(Exam.id == a.exam_id))
        if exam:
            tasks.append({
                "id": f"exam_{a.id}",
                "type": "exam",
                "exam_id": exam.id,
                "assignment_id": a.id,
                "title": f"📝 测验: {exam.exam_code} ({exam.strategy == 'personalized' and '千人千面' or '基础出题'})",
                "createdAt": a.assigned_at.isoformat() if a.assigned_at else None,
                "status": "completed" if a.status == "completed" else "pending",
                "isPersonalized": exam.strategy == "personalized"
            })
            
    # 获取情景任务 ScenarioPush
    pushes = db.scalars(
        select(ScenarioPush)
        .where(ScenarioPush.student_id == student.id)
        .order_by(ScenarioPush.pushed_at.desc())
    ).all()
    for p in pushes:
        scenario = db.scalar(select(Scenario).where(Scenario.id == p.scenario_id))
        if scenario:
            tasks.append({
                "id": f"scenario_{p.id}",
                "type": "scenario",
                "scenario_id": scenario.id,
                "push_id": p.id,
                "title": f"💬 对话任务: {scenario.theme} - {scenario.persona}",
                "createdAt": p.pushed_at.isoformat() if p.pushed_at else None,
                "status": "completed" if p.push_status == "completed" else "pending",
                "difficulty": scenario.difficulty
            })
            
    tasks.sort(key=lambda x: x["createdAt"] or "", reverse=True)
    return ok(tasks)


@app.get("/api/student/exam/assignment/{assignment_id}")
def get_exam_for_student(assignment_id: int, request: Request, db: Session = Depends(get_db)):
    student = _current_student(request, db)
    if not student: return fail("未授权", 401)
    
    assignment = db.scalar(select(ExamAssignment).where(ExamAssignment.id == assignment_id, ExamAssignment.student_id == student.id))
    if not assignment: return fail("找不到该试卷分配记录")
    
    exam = db.scalar(select(Exam).where(Exam.id == assignment.exam_id))
    if not exam: return fail("找不到对应试卷")
    
    content = assignment.personalized_content if assignment.personalized_content else exam.content
    return ok({
        "assignment_id": assignment.id,
        "exam_id": exam.id,
        "exam_code": exam.exam_code,
        "strategy": exam.strategy,
        "content": content,
        "status": assignment.status
    })


class StudentExamSubmitReq(BaseModel):
    assignment_id: int
    answers: dict

class TaskCompleteReq(BaseModel):
    task_type: str
    task_id: int

@app.post("/api/student/exam/submit")
def submit_exam_answers(req: StudentExamSubmitReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student: return fail("未授权", 401)
        
        assignment = db.scalar(select(ExamAssignment).where(ExamAssignment.id == req.assignment_id, ExamAssignment.student_id == student.id))
        if not assignment: return fail("任务不存在")
        if assignment.status == "completed": return fail("该试卷已提交过")
        
        exam = db.scalar(select(Exam).where(Exam.id == assignment.exam_id))
        content = assignment.personalized_content if assignment.personalized_content else exam.content
        
        if not content:
            content = []
            
        earned_score = 0
        ai_comment_lines = []
        
        for idx, q_data in enumerate(content):
            q_score = q_data.get("score", 0)
            u_ans = req.answers.get(str(idx), "")
            
            if q_data.get("type") == "grammar":
                correct_ans = str(q_data.get("answer", ""))
                if correct_ans and (u_ans.startswith(correct_ans + '.') or u_ans.startswith(correct_ans + ' ') or u_ans == correct_ans or correct_ans.startswith(u_ans) or u_ans.startswith(correct_ans)):
                    earned_score += q_score
                else:
                    ai_comment_lines.append(f"第 {idx + 1} 题(语法): 答错了，你的答案 [{u_ans}]；正确答案 [{correct_ans}]")
            else:
                ai_comment_lines.append(f"第 {idx + 1} 题(写作): 已记录答案，待教师或AI后续评分。")
                
        assignment.status = "completed"
        
        HomeworkCRUD.create(db, HomeworkCreate(
            student_id=student.id,
            title=f"[随堂测验] {exam.exam_code} 的答卷",
            status="已完成",
            submitted_at=datetime.now(),
            score=float(earned_score),
            file_type="json_exam",
            file_url=json.dumps(req.answers, ensure_ascii=False),
            ai_comment="\n".join(ai_comment_lines) if ai_comment_lines else "语法全对！大题待教师评分。",
            exam_assignment_id=assignment.id
        ))
        db.commit()
        
        return ok({"score": earned_score, "message": "提交成功"})
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print(f"Error in submit_exam_answers: {trace}")
        return fail(f"Server error: {str(e)}", 500)

@app.get("/api/student/exam/result/{assignment_id}")
def get_exam_result(assignment_id: int, request: Request, db: Session = Depends(get_db)):
    student = _current_student(request, db)
    if not student: return fail("未授权", 401)
    
    assignment = db.scalar(select(ExamAssignment).where(ExamAssignment.id == assignment_id, ExamAssignment.student_id == student.id))
    if not assignment: return fail("该记录不存在")
    
    exam = db.scalar(select(Exam).where(Exam.id == assignment.exam_id))
    content = assignment.personalized_content if assignment.personalized_content else exam.content
    
    # 获取对应的 homework 记录以提取答案
    homework = db.scalar(select(Homework).where(Homework.exam_assignment_id == assignment_id, Homework.student_id == student.id))
    answers = {}
    if homework and homework.file_url:
        try:
            answers = json.loads(homework.file_url)
        except:
            pass
            
    return ok({
        "exam_code": exam.exam_code,
        "content": content,
        "answers": answers,
        "score": homework.score if homework else 0,
        "ai_comment": homework.ai_comment if homework else ""
    })


@app.post("/api/student/task/complete")
def complete_task(req: TaskCompleteReq, request: Request, db: Session = Depends(get_db)):
    student = _current_student(request, db)
    if not student: return fail("未授权", 401)
    
    if req.task_type == "scenario":
        p = db.scalar(select(ScenarioPush).where(ScenarioPush.id == req.task_id, ScenarioPush.student_id == student.id))
        if p and p.push_status != "completed":
            p.push_status = "completed"
            db.commit()
    return ok()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
