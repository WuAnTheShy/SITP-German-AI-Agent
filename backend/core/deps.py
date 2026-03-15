from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.session import get_db
from crud.repositories import UserCRUD, StudentCRUD


def require_teacher(req: Request, db: Session = Depends(get_db)):
    """从 Authorization 头解析教师身份，失败则抛 401"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer teacher-token-"):
        parts = auth.replace("Bearer ", "").split("-")
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
        if len(parts) >= 4:
            uid = parts[2]
            s = StudentCRUD.get_by_uid(db, uid)
            if s:
                return s
    raise HTTPException(status_code=401, detail="未登录或令牌无效，请重新登录")


def current_student(req: Request, db: Session):
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
