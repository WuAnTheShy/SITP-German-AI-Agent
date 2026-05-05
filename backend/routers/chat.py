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

router = APIRouter()

STUDENT_LOBBY_SCENE_NAME = "大厅AI"
AGENT_SCENE_NAME = "AI助教-Agent"

# 大厅类(智能对话)所有 scene_name:普通对话 + Agent 对话
LOBBY_SCENE_NAMES = [STUDENT_LOBBY_SCENE_NAME, AGENT_SCENE_NAME]


logger = logging.getLogger(__name__)


AGENT_SYSTEM_PROMPT = """你是同济大学德语 AI 助教"小智",可以调用工具查询学生的真实学情数据来回答问题。

你的能力:
- 查询学生档案(姓名、班级、学号、薄弱点)
- 查询学生四维能力(听/说/读/写)和 AI 诊断
- 查询学生最近学习活动(各模块时长)
- 查询学生作业列表(已完成/未完成/平均分)

行为准则:
1. 当用户问及个人学情(我的成绩/我哪里弱/最近学了什么/我的作业)时,**必须主动调用工具**获取真实数据,不要凭空回答。
2. 工具返回数据后,用自然中文整理给用户,不要直接复述 JSON。
3. 对于德语学习问题(语法、词汇、翻译),不需要调用工具,直接回答。
4. 回答要简洁、友好、个性化,根据学情给出针对性建议。
5. 不知道时如实说"不知道",不要编造数据。

回答用中文,适当用 emoji 让回答生动,但别滥用。"""

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


@router.post("/api/chat")
def chat_endpoint(
    bg: BackgroundTasks,
    req: Request,
    request: TeacherChatReq,
    db: Session = Depends(get_db),
):
    """教师端 AI：跨天续接 + 长期摘要"""
    user = require_teacher(req, db)
    try:
        print(f"[教师AI] user_id={user.id} 消息长度: {len(request.message)}", flush=True)
    except Exception:
        print("[教师AI] 教师消息", flush=True)
    try:
        session = resolve_teacher_session(
            db, user.id, new_thread=request.new_thread, session_id=request.session_id
        )
        TeacherChatMessageCRUD.create(
            db, TeacherChatMessageCreate(session_id=session.id, role="user", content=request.message)
        )
        TeacherChatSessionCRUD.set_title_if_empty(db, session.id, request.message)
        history = TeacherChatMessageCRUD.list_by_session(db, session.id)
        messages = []
        if getattr(user, "long_memory_summary", None):
            messages.append({"role": "user", "content": "[Teaching context]\n" + user.long_memory_summary})
        rag_context, rag_sources, rag_top_score = build_rag_context(
            db,
            request.message,
            viewer_user_id=user.id,
            viewer_session_key=f"teacher:{session.id}",
        )
        if rag_context:
            messages.append({"role": "user", "content": "[Knowledge Base]\n" + rag_context})
        messages.extend(history_to_messages(history, max_turns=14))
        reply_text = generate_response(messages, system_instruction=TEACHER_SYSTEM)
        if not (reply_text or "").strip():
            reply_text = "AI 服务暂不可用，请检查后端 LLM 环境变量配置后重试。"
        # 仅当 AI 实际引用知识库时才显示参考资料，避免"未命中却显示参考资料"的矛盾
        _kb_miss_markers = ("知识库未命中", "通用回答", "未命中")
        if rag_sources and not any(m in reply_text for m in _kb_miss_markers):
            reply_text = reply_text + "\n\n参考资料: " + "; ".join(rag_sources[:5])
        TeacherChatMessageCRUD.create(
            db, TeacherChatMessageCreate(session_id=session.id, role="assistant", content=reply_text)
        )
        TeacherChatSessionCRUD.touch(db, session.id)
        n = len(history) + 2
        if n >= MEMORY_REFRESH_EVERY and n % MEMORY_REFRESH_EVERY == 0:
            bg.add_task(refresh_teacher_memory, user.id, session.id)
        return {"reply": reply_text, "session_id": session.id}
    except HTTPException:
        raise
    except Exception as e:
        err_name = type(e).__name__
        err_msg = str(e).strip() or ""
        log_path = Path(__file__).resolve().parent.parent / "encoding_error.log"
        try:
            log_path.write_text(
                traceback.format_exc() + "\n---\n",
                encoding="utf-8",
                errors="replace",
            )
        except Exception:
            pass
        try:
            print(f"[教师AI] AI调用失败: {err_name} {err_msg[:200]}", flush=True)
        except Exception:
            print("[教师AI] AI调用失败", flush=True)
        detail = f"{err_name}: {err_msg[:150]}" if err_msg else err_name
        return {"reply": f"AI 暂时无法响应，请稍后重试。错误信息: {detail}"}


@router.post("/api/student/chat")
def student_chat_endpoint(
    bg: BackgroundTasks,
    req: Request,
    request: StudentChatReq,
    db: Session = Depends(get_db),
):
    student = require_student(req, db)
    try:
        print(f"[学生AI] student_id={student.id} 消息长度: {len(request.message)}", flush=True)
    except Exception:
        print("[学生AI] 学生消息", flush=True)
    try:
        session = resolve_student_session(
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
        messages = []
        if getattr(student, "long_memory_summary", None):
            messages.append({"role": "user", "content": "[Learner profile]\n" + student.long_memory_summary})
        rag_context, rag_sources, rag_top_score = build_rag_context(
            db,
            request.message,
            viewer_user_id=student.user_id,
            viewer_session_key=f"student:{session.id}",
        )
        if rag_context:
            messages.append({"role": "user", "content": "[Knowledge Base]\n" + rag_context})
        messages.extend(history_to_messages(history, max_turns=14))
        reply_text = generate_response(messages, system_instruction=STUDENT_SYSTEM)
        if not (reply_text or "").strip():
            reply_text = "Entschuldigung, der KI-Dienst ist derzeit nicht verfugbar. (抱歉，AI 服务暂不可用。)"
        # 仅当 AI 实际引用知识库时才显示参考资料，避免"未命中却显示参考资料"的矛盾
        _kb_miss_markers = ("知识库未命中", "通用回答", "未命中")
        if rag_sources and not any(m in reply_text for m in _kb_miss_markers):
            reply_text = reply_text + "\n\n参考资料: " + "; ".join(rag_sources[:5])
        ChatMessageCRUD.create(
            db,
            ChatMessageCreate(session_id=session.id, role="assistant", content=reply_text, correction=None),
        )
        chat_minutes = max(1, min(8, len(request.message.strip()) // 60 + 1))
        track_learning_activity(
            db,
            student_id=student.id,
            module="情景对话",
            duration_minutes=chat_minutes,
            content="大厅AI对话",
        )
        refresh_student_metrics(db, student.id)
        ChatSessionCRUD.touch(db, session.id)
        n = len(history) + 2
        if n >= MEMORY_REFRESH_EVERY and n % MEMORY_REFRESH_EVERY == 0:
            bg.add_task(refresh_student_memory, student.id, session.id)
        return {"reply": reply_text, "session_id": session.id}
    except HTTPException:
        raise
    except Exception as e:
        err_name = type(e).__name__
        err_msg = str(e).strip() or ""
        log_path = Path(__file__).resolve().parent.parent / "encoding_error.log"
        try:
            log_path.write_text(
                traceback.format_exc() + "\n---\n",
                encoding="utf-8",
                errors="replace",
            )
        except Exception:
            pass
        try:
            print(f"[学生AI] AI调用失败: {err_name} {err_msg[:200]}", flush=True)
        except Exception:
            print("[学生AI] AI调用失败", flush=True)
        detail = f"{err_name}: {err_msg[:150]}" if err_msg else err_name
        return {"reply": f"AI 暂时无法响应，请稍后重试。错误信息: {detail}"}
    

@router.post("/api/student/agent/chat")
def student_agent_chat(
    bg: BackgroundTasks,
    req: Request,
    request: StudentChatReq,
    db: Session = Depends(get_db),
):
    """学生端 Agent 对话:支持工具调用的智能对话。
    
    与 /api/student/chat 的区别:
    - chat: 单纯 LLM 对话 + RAG,适合开放式问题
    - agent/chat: 接入工具集,LLM 可主动查询学生学情数据(成绩/能力/作业等)
    
    复用 chat_sessions 表,通过 scene_name='AI助教-Agent' 区分。
    保留长期记忆 + 历史消息,但不做 RAG(由工具替代)。
    """
    student = require_student(req, db)
    logger.info(f"学生 Agent 对话: student_id={student.id}, msg_len={len(request.message)}")
    
    try:
        # 1. 解析会话(复用现有 resolve_student_session,scene_name 区分)
        session = resolve_student_session(
            db,
            student.id,
            None,
            "AI助教-Agent",          # 关键:scene_name 区分 Agent 会话
            new_thread=request.new_thread,
            session_id=request.session_id,
        )
        
        # 2. 写入用户消息
        ChatMessageCRUD.create(
            db, ChatMessageCreate(session_id=session.id, role="user", content=request.message)
        )
        ChatSessionCRUD.set_title_if_empty(db, session.id, request.message)
        
        # 3. 取历史消息(转为 LLM messages 格式)
        history = ChatMessageCRUD.list_by_session(db, session.id)
        messages: list[dict] = []
        
        # 4. 注入长期记忆(如有)
        if getattr(student, "long_memory_summary", None):
            messages.append({
                "role": "user",
                "content": "[Learner profile]\n" + student.long_memory_summary,
            })
        
        # 5. 加历史消息(最近 14 轮,避免上下文过长)
        messages.extend(history_to_messages(history, max_turns=14))
        
        # 6. 调 Agent(带工具)
        context = {"db": db, "student_id": student.id}
        reply_text = generate_response_with_tools(
            messages=messages,
            system_instruction=AGENT_SYSTEM_PROMPT,
            context=context,
        )
        
        if not (reply_text or "").strip():
            reply_text = "抱歉,AI 助教暂时无法响应,请稍后再试。"
        
        # 7. 写入 AI 回复
        ChatMessageCRUD.create(
            db,
            ChatMessageCreate(
                session_id=session.id, role="assistant", content=reply_text, correction=None,
            ),
        )
        
        # 8. 跟踪学习活动(Agent 对话也算学习)
        chat_minutes = max(1, min(8, len(request.message.strip()) // 60 + 1))
        track_learning_activity(
            db, student_id=student.id,
            module="AI助教",
            duration_minutes=chat_minutes,
            content="Agent 对话",
        )
        refresh_student_metrics(db, student.id)
        ChatSessionCRUD.touch(db, session.id)
        
        # 9. 长期记忆刷新(后台任务)
        n = len(history) + 2
        if n >= MEMORY_REFRESH_EVERY and n % MEMORY_REFRESH_EVERY == 0:
            bg.add_task(refresh_student_memory, student.id, session.id)
        
        return {"reply": reply_text, "session_id": session.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"学生 Agent 对话失败: {type(e).__name__}: {e}", exc_info=True)
        return {"reply": f"AI 助教调用失败: {type(e).__name__}", "session_id": None}


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
    return ok(
        [
            {
                "id": r.id,
                "title": (getattr(r, "title", None) or "").strip() or None,
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
