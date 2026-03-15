import traceback
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from google.genai import types

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
    history_to_gemini_contents,
    refresh_student_memory,
    refresh_teacher_memory,
    MEMORY_REFRESH_EVERY,
)

router = APIRouter()

STUDENT_LOBBY_SCENE_NAME = "大厅AI"


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
        contents_to_send = []
        if getattr(user, "long_memory_summary", None):
            contents_to_send.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="[Teaching context]\n" + user.long_memory_summary)],
                )
            )
        contents_to_send.extend(history_to_gemini_contents(history, max_turns=14))
        response = get_client().models.generate_content(
            model=MODEL_ID,
            contents=contents_to_send,
            config=types.GenerateContentConfig(
                system_instruction=TEACHER_SYSTEM,
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
            print(f"[教师AI] Gemini调用失败: {err_name} {err_msg[:200]}", flush=True)
        except Exception:
            print("[教师AI] Gemini调用失败", flush=True)
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
        contents_to_send = []
        if getattr(student, "long_memory_summary", None):
            contents_to_send.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="[Learner profile]\n" + student.long_memory_summary)],
                )
            )
        contents_to_send.extend(history_to_gemini_contents(history, max_turns=14))
        response = get_client().models.generate_content(
            model=MODEL_ID,
            contents=contents_to_send,
            config=types.GenerateContentConfig(
                system_instruction=STUDENT_SYSTEM,
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
            print(f"[学生AI] Gemini调用失败: {err_name} {err_msg[:200]}", flush=True)
        except Exception:
            print("[学生AI] Gemini调用失败", flush=True)
        detail = f"{err_name}: {err_msg[:150]}" if err_msg else err_name
        return {"reply": f"AI 暂时无法响应，请稍后重试。错误信息: {detail}"}


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
    if s.scene_id is not None or (s.scene_name or "") != STUDENT_LOBBY_SCENE_NAME:
        return fail("仅支持大厅智能对话会话", 403)
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
        ChatSessionCRUD.touch(db, session.id)
        return ok({"reply": reply, "correction": correction, "session_id": session.id})
    except Exception as e:
        return fail(f"对话失败: {e}")
