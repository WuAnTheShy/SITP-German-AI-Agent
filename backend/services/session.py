from fastapi import HTTPException
from sqlalchemy.orm import Session

from crud.repositories import ChatSessionCRUD, TeacherChatSessionCRUD
from schemas.entities import ChatSessionCreate, TeacherChatSessionCreate
from models.entities import ChatSession as ChatSessionModel, TeacherChatSession


def resolve_student_session(
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


def resolve_teacher_session(
    db: Session, user_id: int, *, new_thread: bool = False, session_id: int | None = None
) -> TeacherChatSession:
    if new_thread:
        TeacherChatSessionCRUD.close_open_for_user(db, user_id)
        return TeacherChatSessionCRUD.create(db, TeacherChatSessionCreate(user_id=user_id))
    if session_id is not None:
        s = TeacherChatSessionCRUD.get_by_id(db, session_id)
        if not s or s.user_id != user_id:
            raise HTTPException(status_code=404, detail="会话不存在")
        if getattr(s, "closed_at", None) is not None:
            TeacherChatSessionCRUD.reopen(db, s.id)
        return TeacherChatSessionCRUD.get_by_id(db, session_id) or s
    open_s = TeacherChatSessionCRUD.find_open_session(db, user_id)
    if open_s:
        return open_s
    return TeacherChatSessionCRUD.create(db, TeacherChatSessionCreate(user_id=user_id))
