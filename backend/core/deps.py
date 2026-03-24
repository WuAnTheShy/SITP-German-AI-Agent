from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.session import get_db
from crud.repositories import UserCRUD, StudentCRUD, ClassroomCRUD
from core.token import parse_token, allow_legacy_tokens


def require_teacher(req: Request, db: Session = Depends(get_db)):
    """从 Authorization 头解析教师身份，失败则抛 401"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth.replace("Bearer ", "").strip()
        payload = parse_token(token, allow_legacy=allow_legacy_tokens())
        if payload and str(payload.get("role", "")) == "teacher":
            try:
                user_id = int(str(payload.get("sub", "")))
            except ValueError:
                raise HTTPException(status_code=401, detail="无效的教师令牌")
            user = UserCRUD.get_by_id(db, user_id)
            if user and user.role == "teacher":
                if getattr(user, "status", "approved") != "approved":
                    raise HTTPException(status_code=403, detail="教师账号未通过审核，无法访问")
                if not getattr(user, "is_active", True):
                    raise HTTPException(status_code=403, detail="教师账号已被停用，请联系管理员")
                return user
    raise HTTPException(status_code=401, detail="未登录或令牌无效，请重新登录")


def require_admin(req: Request, db: Session = Depends(get_db)):
    """从 Authorization 头解析管理员身份，失败则抛 401/403。仅管理员可调用。"""
    auth = req.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或令牌无效，请使用管理员账号登录")
    token = auth.replace("Bearer ", "").strip()
    payload = parse_token(token, allow_legacy=allow_legacy_tokens())
    if not payload or str(payload.get("role", "")) != "admin":
        raise HTTPException(status_code=401, detail="无效的管理员令牌")
    try:
        user_id = int(str(payload.get("sub", "")))
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
    返回: (teacher, classroom)，其中 classroom 为该教师名下的第一个班级（兼容旧逻辑）。
    """
    teacher = require_teacher(req, db)
    classrooms = ClassroomCRUD.list_by_teacher(db, teacher.id)
    if not classrooms:
        raise HTTPException(
            status_code=403,
            detail="您尚未关联班级，请联系管理员分配班级后再使用教师端功能。",
        )
    return teacher, classrooms[0]


def get_current_teacher_and_classrooms(req: Request, db: Session = Depends(get_db)):
    """获取当前教师与其所有关联班级。未关联班级时抛 403。"""
    teacher = require_teacher(req, db)
    classrooms = ClassroomCRUD.list_by_teacher(db, teacher.id)
    if not classrooms:
        raise HTTPException(
            status_code=403,
            detail="您尚未关联班级，请联系管理员分配班级后再使用教师端功能。",
        )
    return teacher, classrooms


def require_student(req: Request, db: Session = Depends(get_db)):
    """从 Authorization 头解析学生身份，失败则抛 401"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth.replace("Bearer ", "").strip()
        payload = parse_token(token, allow_legacy=allow_legacy_tokens())
        if payload and str(payload.get("role", "")) == "student":
            uid = str(payload.get("sub", "")).strip()
            s = StudentCRUD.get_by_uid(db, uid)
            if s:
                user = UserCRUD.get_by_id(db, s.user_id)
                if not user:
                    raise HTTPException(status_code=401, detail="用户不存在，请重新登录")
                if getattr(s, "status", "approved") != "approved":
                    raise HTTPException(status_code=403, detail="学生账号未通过审核，无法访问")
                if not getattr(user, "is_active", True):
                    raise HTTPException(status_code=403, detail="学生账号已被停用，请联系管理员")
                return s
    raise HTTPException(status_code=401, detail="未登录或令牌无效，请重新登录")


def current_student(req: Request, db: Session):
    """从 Authorization 头解析学生，无有效 token 返回 None"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth.replace("Bearer ", "").strip()
        payload = parse_token(token, allow_legacy=allow_legacy_tokens())
        if payload and str(payload.get("role", "")) == "student":
            uid = str(payload.get("sub", "")).strip()
            s = StudentCRUD.get_by_uid(db, uid)
            if s:
                user = UserCRUD.get_by_id(db, s.user_id)
                if user and getattr(s, "status", "approved") == "approved" and getattr(user, "is_active", True):
                    return s
    return None


def require_login_user(req: Request, db: Session = Depends(get_db)):
    """
    统一解析已登录用户（teacher/student/admin）。
    返回 dict: {role, user_id, username, display_name, student_id?}
    """
    auth = req.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或令牌无效，请重新登录")
    token = auth.replace("Bearer ", "")
    parts = token.split("-")
    if len(parts) < 4:
        raise HTTPException(status_code=401, detail="无效令牌")

    if token.startswith("teacher-token-") or token.startswith("admin-token-"):
        try:
            uid = int(parts[2])
        except ValueError:
            raise HTTPException(status_code=401, detail="无效令牌")
        user = UserCRUD.get_by_id(db, uid)
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        if token.startswith("teacher-token-") and user.role != "teacher":
            raise HTTPException(status_code=403, detail="需要教师权限")
        if token.startswith("admin-token-") and user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        return {
            "role": user.role,
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
        }

    if token.startswith("student-token-"):
        stu_uid = parts[2]
        s = StudentCRUD.get_by_uid(db, stu_uid)
        if not s:
            raise HTTPException(status_code=401, detail="学生不存在")
        user = UserCRUD.get_by_id(db, s.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        return {
            "role": "student",
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "student_id": s.id,
        }

    raise HTTPException(status_code=401, detail="未登录或令牌无效，请重新登录")
