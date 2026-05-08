import traceback
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from crud.repositories import (
    ChatSessionCRUD,
    ChatMessageCRUD,
    TeacherChatSessionCRUD,
    TeacherChatMessageCRUD,
)
from schemas.entities import (
    ChatSessionCreate,
    ChatMessageCreate,
    TeacherChatMessageCreate,
    TeacherChatSessionCreate,
)
from core.responses import ok, fail
from core.deps import require_teacher, require_student, current_student
from services.session import resolve_student_session, resolve_teacher_session
from services.llm import (
    get_client,
    MODEL_ID,
    TEACHER_SYSTEM,
    STUDENT_SYSTEM,
    history_to_messages,
    generate_response,
    refresh_student_memory,
    refresh_teacher_memory,
    MEMORY_REFRESH_EVERY,
)
from services.metrics import track_learning_activity, refresh_student_metrics
from services.rag import build_rag_context
from services.llm import generate_response_with_tools  # 关键:Agent 函数
from services.prompts import load_prompt
from services.observability import ExecutionTrace

logger = logging.getLogger(__name__)

router = APIRouter()

STUDENT_LOBBY_SCENE_NAME = "大厅AI"
AGENT_SCENE_NAME = "AI助教-Agent"

# 大厅类(智能对话)所有 scene_name:普通对话 + Agent 对话
LOBBY_SCENE_NAMES = [STUDENT_LOBBY_SCENE_NAME, AGENT_SCENE_NAME]

# 场景显示标签映射:scene_name(内部标识) → 用户可见的展示文字
SCENE_DISPLAY_MAP: dict[str, dict[str, str]] = {
    AGENT_SCENE_NAME: {
        "label": "AI 助教对话",
        "subtitle": "基于学情数据的智能助教",
        "icon": "🤖",
    },
    STUDENT_LOBBY_SCENE_NAME: {
        "label": "智能对话",
        "subtitle": "通用德语学习对话",
        "icon": "💬",
    },
}

# 兜底 display(未知 scene_name 时使用)
DEFAULT_SCENE_DISPLAY = {
    "label": "对话",
    "subtitle": "",
    "icon": "💬",
}


def get_scene_display(scene_name: str | None) -> dict[str, str]:
    """根据 scene_name 返回前端展示用的标签/副标题/图标。"""
    if not scene_name:
        return DEFAULT_SCENE_DISPLAY
    return SCENE_DISPLAY_MAP.get(scene_name, DEFAULT_SCENE_DISPLAY)




# AGENT_SYSTEM_PROMPT = """你是同济大学德语 AI 助教"小智",可以调用工具查询学生的真实学情数据来回答问题。

# 你的能力:
# - 查询学生档案(姓名、班级、学号、薄弱点)
# - 查询学生四维能力(听/说/读/写)和 AI 诊断
# - 查询学生最近学习活动(各模块时长)
# - 查询学生作业列表(已完成/未完成/平均分)

# 行为准则:
# 1. 当用户问及个人学情(我的成绩/我哪里弱/最近学了什么/我的作业)时,**必须主动调用工具**获取真实数据,不要凭空回答。
# 2. 工具返回数据后,用自然中文整理给用户,不要直接复述 JSON。
# 3. 对于德语学习问题(语法、词汇、翻译),不需要调用工具,直接回答。
# 4. 回答要简洁、友好、个性化,根据学情给出针对性建议。
# 5. 不知道时如实说"不知道",不要编造数据。

# 回答用中文,适当用 emoji 让回答生动,但别滥用。"""


# TEACHER_AGENT_SYSTEM_PROMPT = """你是德语教研助手"小研",专为同济大学德语教师服务,可调用工具查询所教班级和学生的真实数据来辅助教学决策。

# 你的能力:
# - 查询任教班级总览(query_class_overview):学生数、活跃度、能力均分、薄弱点分布
# - 按学号查指定学生学情(query_student_by_uid):需 7 位学号
# - 找薄弱学生(find_struggling_students):按维度+阈值,返回需重点关注的学生
# - 推荐考点(recommend_exam_focus):基于学生错题热点,给试卷出题建议

# 行为准则:
# 1. 当教师询问班务相关问题(班里情况/某学生学情/谁需要关注/考什么)时,**必须主动调用工具**获取真实数据。
# 2. 工具返回数据后,用专业、严谨的中文整理给教师,辅助教学决策。
# 3. 对于教学法问题(如何讲解某语法点、如何备课),不需要调用工具,直接给建议。
# 4. 教师权限有边界,如果工具返回"无权访问"等错误,不要绕过校验,如实告知教师。
# 5. 不知道时如实说"不知道",不要编造数据。

# 回答用中文,语气专业不浮夸,适度使用表格/列表呈现数据。"""


# Agent system prompts(从 markdown 加载)
AGENT_SYSTEM_PROMPT = load_prompt("student_agent")
TEACHER_AGENT_SYSTEM_PROMPT = load_prompt("teacher_agent")

class TeacherChatReq(BaseModel):
    message: str
    new_thread: bool = False
    session_id: int | None = None


class StudentChatReq(BaseModel):
    message: str
    new_thread: bool = False
    session_id: int | None = None


class SceneChatReq(BaseModel):
    sceneId: int | None = None
    sceneName: str | None = None
    userMessage: str


def _resolve_scene_single_thread(db: Session, student_id: int, scene_id: int, scene_name: str):
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


@router.post("/api/teacher/chat")
def chat_endpoint(
    bg: BackgroundTasks,
    req: Request,
    request: TeacherChatReq,
    db: Session = Depends(get_db),
):
    """教师统一对话入口:轻量预 RAG + 教师工具集 Agent + Trace。"""
    user = require_teacher(req, db)
    logger.info(f"教师统一对话: user_id={user.id}, msg_len={len(request.message)}")
    
    trace = ExecutionTrace(
        role="teacher",
        user_id=user.id,
        session_id=None,
        user_message=request.message,
    )
    
    try:
        session = resolve_teacher_session(
            db, user.id,
            new_thread=request.new_thread,
            session_id=request.session_id,
        )
        trace.session_id = session.id
        
        TeacherChatMessageCRUD.create(
            db, TeacherChatMessageCreate(session_id=session.id, role="user", content=request.message)
        )
        TeacherChatSessionCRUD.set_title_if_empty(db, session.id, request.message)
        history = TeacherChatMessageCRUD.list_by_session(db, session.id)
        
        messages: list[dict] = []
        
        if getattr(user, "long_memory_summary", None):
            messages.append({"role": "user", "content": "[Teaching context]\n" + user.long_memory_summary})
        
        rag_context, rag_sources, rag_top_score = build_rag_context(
            db, request.message,
            viewer_user_id=user.id,
            viewer_session_key=f"teacher:{session.id}",
            trace=trace,
        )
        if rag_context and rag_top_score >= 0.4:
            messages.append({
                "role": "user",
                "content": "[Knowledge Base 预检索结果,可参考]\n" + rag_context,
            })
            logger.info(f"教师预 RAG 命中: top_score={rag_top_score:.3f}")
            trace.rag_used = True
            trace.rag_top_score = rag_top_score
        
        messages.extend(history_to_messages(history, max_turns=14))
        
        context = {"db": db, "teacher_user_id": user.id}
        reply_text, tool_calls_used = generate_response_with_tools(
            messages=messages,
            system_instruction=TEACHER_AGENT_SYSTEM_PROMPT,
            context=context,
            toolset="teacher",
            trace=trace,
        )
        
        if not (reply_text or "").strip():
            reply_text = "抱歉,教研助手暂时无法响应,请稍后再试。"
        
        _kb_miss_markers = ("知识库未命中", "通用回答", "未命中")
        if rag_sources and rag_top_score >= 0.4 and not any(m in reply_text for m in _kb_miss_markers):
            reply_text = reply_text + "\n\n参考资料: " + "; ".join(rag_sources[:5])
        
        TeacherChatMessageCRUD.create(
            db, TeacherChatMessageCreate(session_id=session.id, role="assistant", content=reply_text)
        )
        TeacherChatSessionCRUD.touch(db, session.id)
        
        n = len(history) + 2
        if n >= MEMORY_REFRESH_EVERY and n % MEMORY_REFRESH_EVERY == 0:
            bg.add_task(refresh_teacher_memory, user.id, session.id)
        
        # Trace 完成
        trace.finalize(reply_text=reply_text, success=True)
        trace.persist(db)
        
        return {
            "reply": reply_text,
            "session_id": session.id,
            "tool_calls_used": tool_calls_used,
            "rag_used": trace.rag_used,
            "trace_id": trace.trace_id,
        }
    except HTTPException:
        trace.finalize(reply_text=None, success=False, error_type="HTTPException")
        try:
            trace.persist(db)
        except Exception:
            pass
        raise
    except Exception as e:
        logger.error(f"教师统一对话失败: {type(e).__name__}: {e}", exc_info=True)
        trace.finalize(
            reply_text=None,
            success=False,
            error_type=type(e).__name__,
            error_message=str(e),
        )
        try:
            trace.persist(db)
        except Exception:
            pass
        return {
            "reply": f"教研助手调用失败: {type(e).__name__}",
            "session_id": None,
            "trace_id": trace.trace_id,
        }


@router.post("/api/student/chat")
def student_chat_endpoint(
    bg: BackgroundTasks,
    req: Request,
    request: StudentChatReq,
    db: Session = Depends(get_db),
):
    """学生统一对话入口:轻量预 RAG + 学生工具集 Agent + Trace。"""
    student = require_student(req, db)
    logger.info(f"学生统一对话: student_id={student.id}, msg_len={len(request.message)}")
    
    # 创建 trace(在 session 解析之前就创建,session_id 后填)
    trace = ExecutionTrace(
        role="student",
        user_id=student.id,
        session_id=None,
        user_message=request.message,
    )
    
    try:
        session = resolve_student_session(
            db, student.id, None, STUDENT_LOBBY_SCENE_NAME,
            new_thread=request.new_thread,
            session_id=request.session_id,
        )
        trace.session_id = session.id  # 拿到后回填
        
        ChatMessageCRUD.create(
            db, ChatMessageCreate(session_id=session.id, role="user", content=request.message)
        )
        ChatSessionCRUD.set_title_if_empty(db, session.id, request.message)
        history = ChatMessageCRUD.list_by_session(db, session.id)
        
        messages: list[dict] = []
        
        # 长期记忆
        if getattr(student, "long_memory_summary", None):
            messages.append({
                "role": "user",
                "content": "[Learner profile]\n" + student.long_memory_summary,
            })
        
        # 轻量预 RAG(用 trace 包裹)
        rag_context, rag_sources, rag_top_score = build_rag_context(
            db, request.message,
            viewer_user_id=student.user_id,
            viewer_session_key=f"student:{session.id}",
            trace=trace,    # ← 透传 trace
        )
        if rag_context and rag_top_score >= 0.4:
            messages.append({
                "role": "user",
                "content": "[Knowledge Base 预检索结果,可参考]\n" + rag_context,
            })
            logger.info(f"学生预 RAG 命中: top_score={rag_top_score:.3f}")
            trace.rag_used = True
            trace.rag_top_score = rag_top_score
        
        messages.extend(history_to_messages(history, max_turns=14))
        
        # Agent(传 trace)
        context = {"db": db, "student_id": student.id}
        reply_text, tool_calls_used = generate_response_with_tools(
            messages=messages,
            system_instruction=AGENT_SYSTEM_PROMPT,
            context=context,
            toolset="student",
            trace=trace,    # ← 透传 trace
        )
        
        if not (reply_text or "").strip():
            reply_text = "抱歉,AI 助教暂时无法响应,请稍后再试。"
        
        _kb_miss_markers = ("知识库未命中", "通用回答", "未命中")
        if rag_sources and rag_top_score >= 0.4 and not any(m in reply_text for m in _kb_miss_markers):
            reply_text = reply_text + "\n\n参考资料: " + "; ".join(rag_sources[:5])
        
        ChatMessageCRUD.create(
            db,
            ChatMessageCreate(session_id=session.id, role="assistant", content=reply_text, correction=None),
        )
        
        chat_minutes = max(1, min(8, len(request.message.strip()) // 60 + 1))
        track_learning_activity(
            db, student_id=student.id,
            module="AI助教",
            duration_minutes=chat_minutes,
            content="统一对话",
        )
        refresh_student_metrics(db, student.id)
        ChatSessionCRUD.touch(db, session.id)
        
        n = len(history) + 2
        if n >= MEMORY_REFRESH_EVERY and n % MEMORY_REFRESH_EVERY == 0:
            bg.add_task(refresh_student_memory, student.id, session.id)
        
        # ─── Trace 完成 + 持久化 ───
        trace.finalize(reply_text=reply_text, success=True)
        trace.persist(db)
        
        return {
            "reply": reply_text,
            "session_id": session.id,
            "tool_calls_used": tool_calls_used,
            "rag_used": trace.rag_used,
            "trace_id": trace.trace_id,    # ← 新增
        }
    except HTTPException:
        # HTTPException 直接抛出,但先记录 trace 失败
        trace.finalize(reply_text=None, success=False, error_type="HTTPException")
        try:
            trace.persist(db)
        except Exception:
            pass
        raise
    except Exception as e:
        logger.error(f"学生统一对话失败: {type(e).__name__}: {e}", exc_info=True)
        trace.finalize(
            reply_text=None,
            success=False,
            error_type=type(e).__name__,
            error_message=str(e),
        )
        try:
            trace.persist(db)
        except Exception:
            pass
        return {
            "reply": f"AI 调用失败: {type(e).__name__}",
            "session_id": None,
            "trace_id": trace.trace_id,
        }


@router.post("/api/student/chat/new-session")
def student_chat_new_session(req: Request, db: Session = Depends(get_db)):
    student = require_student(req, db)
    ChatSessionCRUD.close_open_for_channel(db, student.id, None, STUDENT_LOBBY_SCENE_NAME)
    s = ChatSessionCRUD.create(
        db, ChatSessionCreate(student_id=student.id, scene_id=None, scene_name=STUDENT_LOBBY_SCENE_NAME)
    )
    return ok({"session_id": s.id})


@router.get("/api/student/chat/sessions")
def student_chat_sessions(req: Request, db: Session = Depends(get_db)):
    student = require_student(req, db)
    rows = ChatSessionCRUD.list_channel_sessions(
        db, student.id, None, LOBBY_SCENE_NAMES, limit=80
    )
    return ok(
        [
            {
                "id": r.id,
                "title": (r.title or "").strip() or None,
                "scene_name": r.scene_name,  # 让前端能区分 "AI助教-Agent" vs 普通大厅
                "display": get_scene_display(r.scene_name),  # ← 新增
                "closed": r.closed_at is not None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
    )


@router.get("/api/student/chat/messages")
def student_chat_messages(
    req: Request,
    db: Session = Depends(get_db),
    session_id: int = Query(..., description="大厅会话 id"),
):
    student = require_student(req, db)
    s = ChatSessionCRUD.get_by_id(db, session_id)
    if not s or s.student_id != student.id:
        return fail("会话不存在", 404)
    # 允许大厅普通对话 + AI 助教 Agent 对话
    if s.scene_id is not None or (s.scene_name or "") not in LOBBY_SCENE_NAMES:
        return fail("仅支持大厅或 AI 助教会话", 403)
    msgs = ChatMessageCRUD.list_by_session(db, session_id)
    return ok([{"id": m.id, "role": m.role, "content": m.content} for m in msgs])


@router.delete("/api/student/chat/session/{session_id}")
def student_chat_delete_session(
    session_id: int,
    req: Request,
    db: Session = Depends(get_db),
):
    student = require_student(req, db)
    ok_del = ChatSessionCRUD.delete_lobby_session(
        db, student.id, session_id, STUDENT_LOBBY_SCENE_NAME
    )
    if not ok_del:
        return fail("会话不存在或无权删除", 404)
    return ok(message="已删除")


@router.post("/api/teacher/chat/new-session")
def teacher_chat_new_session(req: Request, db: Session = Depends(get_db)):
    user = require_teacher(req, db)
    TeacherChatSessionCRUD.close_open_for_user(db, user.id)
    s = TeacherChatSessionCRUD.create(db, TeacherChatSessionCreate(user_id=user.id))
    return ok({"session_id": s.id})


@router.get("/api/teacher/chat/sessions")
def teacher_chat_sessions(req: Request, db: Session = Depends(get_db)):
    user = require_teacher(req, db)
    rows = TeacherChatSessionCRUD.list_by_user(db, user.id, limit=80)
    
    # 教师对话目前只有一类(教研助手),统一返回相同 display
    teacher_display = {
        "label": "AI 教研助手",
        "subtitle": "智能查询班级与学生学情",
        "icon": "📊",
    }
    
    return ok(
        [
            {
                "id": r.id,
                "title": (getattr(r, "title", None) or "").strip() or None,
                "display": teacher_display,
                "closed": r.closed_at is not None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
    )


@router.get("/api/teacher/chat/messages")
def teacher_chat_messages(
    req: Request,
    db: Session = Depends(get_db),
    session_id: int = Query(..., description="会话 id"),
):
    user = require_teacher(req, db)
    s = TeacherChatSessionCRUD.get_by_id(db, session_id)
    if not s or s.user_id != user.id:
        return fail("会话不存在", 404)
    msgs = TeacherChatMessageCRUD.list_by_session(db, session_id)
    return ok([{"id": m.id, "role": m.role, "content": m.content} for m in msgs])


@router.delete("/api/teacher/chat/session/{session_id}")
def teacher_chat_delete_session(
    session_id: int,
    req: Request,
    db: Session = Depends(get_db),
):
    user = require_teacher(req, db)
    ok_del = TeacherChatSessionCRUD.delete_session(db, user.id, session_id)
    if not ok_del:
        return fail("会话不存在或无权删除", 404)
    return ok(message="已删除")


@router.get("/api/student/scene-chat/state")
def scene_chat_state(
    request: Request,
    db: Session = Depends(get_db),
    scene_id: int = Query(...),
    scene_name: str = Query(...),
):
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


@router.delete("/api/student/scene-chat/clear")
def scene_chat_clear(
    request: Request,
    db: Session = Depends(get_db),
    scene_id: int = Query(...),
    scene_name: str = Query(...),
):
    student = require_student(request, db)
    name = (scene_name or "").strip() or "自由对话"
    n = ChatSessionCRUD.delete_all_channel_sessions(db, student.id, scene_id, name)
    return ok({"deleted": n}, message="已清空本情景记录" if n else "暂无记录")


@router.post("/api/student/scene-chat")
def scene_chat(req: SceneChatReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        scene_name = req.sceneName or "自由对话"
        if req.sceneId is None:
            return fail("场景对话需要 sceneId", 400)
        session = _resolve_scene_single_thread(db, student.id, req.sceneId, scene_name)
        ChatMessageCRUD.create(
            db, ChatMessageCreate(session_id=session.id, role="user", content=req.userMessage)
        )
        ChatSessionCRUD.set_title_if_empty(db, session.id, req.userMessage)
        history = ChatMessageCRUD.list_by_session(db, session.id)
        conv_lines = [
            f"{'学生' if m.role == 'user' else 'AI助教'}: {m.content}" for m in history
        ]
        from services.llm import ai_json
        prompt = (
            f"场景：「{scene_name}」德语对话练习。\n"
            f"对话历史:\n" + "\n".join(conv_lines) + "\n\n"
            f"请用德语回复（括号内中文翻译），如有语法错误请纠正。\n"
            f'返回JSON: {{"reply":"德语回复","correction":"纠错说明或null"}}'
        )
        result = ai_json(prompt, {
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
        chat_minutes = max(1, min(8, len(req.userMessage.strip()) // 60 + 1))
        track_learning_activity(
            db,
            student_id=student.id,
            module="情景对话",
            duration_minutes=chat_minutes,
            content=f"场景对话: {scene_name}",
        )
        refresh_student_metrics(db, student.id)
        ChatSessionCRUD.touch(db, session.id)
        return ok({"reply": reply, "correction": correction, "session_id": session.id})
    except Exception as e:
        return fail(f"对话失败: {e}")
