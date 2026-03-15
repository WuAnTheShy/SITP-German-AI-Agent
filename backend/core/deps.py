from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.session import get_db
from crud.repositories import UserCRUD, StudentCRUD, ClassroomCRUD


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


def require_admin(req: Request, db: Session = Depends(get_db)):
    """从 Authorization 头解析管理员身份，失败则抛 401/403。仅管理员可调用。"""
    auth = req.headers.get("authorization", "")
    if not auth.startswith("Bearer admin-token-"):
        raise HTTPException(status_code=401, detail="未登录或令牌无效，请使用管理员账号登录")
    parts = auth.replace("Bearer ", "").split("-")
    if len(parts) < 4:
        raise HTTPException(status_code=401, detail="无效的管理员令牌")
    try:
        user_id = int(parts[2])
    except ValueError:
        raise HTTPException(status_code=401, detail="无效的管理员令牌")
    user = UserCRUD.get_by_id(db, user_id)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def get_current_teacher_and_classroom(req: Request, db: Session = Depends(get_db)):
    """
    统一获取「当前登录教师 + 其管理的班级」。
    教师端需要按班级做数据隔离的接口应使用本依赖，不再用 _ensure_demo_data 取演示数据。
    若该教师尚未关联任何班级，返回 403。
    返回: (teacher, classroom)，其中 classroom 为该教师名下的第一个班级（一师一班场景）。
    """
    teacher = require_teacher(req, db)
    classrooms = ClassroomCRUD.list_by_teacher(db, teacher.id)
    if not classrooms:
        raise HTTPException(
            status_code=403,
            detail="您尚未关联班级，请联系管理员分配班级后再使用教师端功能。",
        )
    return teacher, classrooms[0]


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
