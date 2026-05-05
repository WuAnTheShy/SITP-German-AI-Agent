import os

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select  
from models.entities import User, Student  
from sqlalchemy.orm import Session

from db.session import get_db
from crud.repositories import UserCRUD, StudentCRUD, ClassroomCRUD, StudentAbilityCRUD, SystemSettingCRUD
from schemas.entities import UserCreate, StudentCreate, StudentAbilityUpsert
from core.responses import ok, fail
from core.seed import _ensure_demo_data, _ensure_admin, should_seed_demo_data
from core.password import ensure_transport_hash, hash_password, verify_password
from core.token import issue_token, parse_token, allow_legacy_tokens

router = APIRouter()
_SEED_CHECK_DONE = False


def _ensure_seed_once(db: Session) -> None:
    """避免每次登录都执行补种逻辑导致响应变慢。"""
    global _SEED_CHECK_DONE
    if _SEED_CHECK_DONE:
        return
    if should_seed_demo_data():
        _ensure_demo_data(db)
    _ensure_admin(db)
    _SEED_CHECK_DONE = True


def _migrate_legacy_password_hash(user, db: Session) -> None:
    """把旧库的非 bcrypt 密码统一迁移为 bcrypt(sha256(password))。"""
    if not user or not getattr(user, "password_hash", None):
        return
    if user.password_hash.startswith("$2"):
        return
    user.password_hash = hash_password(ensure_transport_hash(user.password_hash))
    db.commit()


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


# class StudentLoginReq(BaseModel):
#     username: str
#     password: str


@router.put("/api/user/password")
def update_user_password(req_body: PasswordUpdateReq, req: Request, db: Session = Depends(get_db)):
    try:
        auth = req.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return fail("未登录", 401)

        token = auth.replace("Bearer ", "").strip()
        payload = parse_token(token, allow_legacy=allow_legacy_tokens())
        if not payload:
            return fail("无效的令牌或用户不存在", 401)

        user = None
        role = str(payload.get("role", "")).strip()
        subject = str(payload.get("sub", "")).strip()
        if role in {"teacher", "admin"}:
            try:
                user_id = int(subject)
                user = UserCRUD.get_by_id(db, user_id)
            except ValueError:
                pass
        elif role == "student":
            uid = subject
            student = StudentCRUD.get_by_uid(db, uid)
            if student:
                user = UserCRUD.get_by_id(db, student.user_id)

        if not user:
            return fail("无效的令牌或用户不存在", 401)

        _migrate_legacy_password_hash(user, db)

        old_pwd = ensure_transport_hash(req_body.oldPassword)
        new_pwd = ensure_transport_hash(req_body.newPassword)

        if not verify_password(old_pwd, user.password_hash):
            return fail("原密码错误", 400)

        user.password_hash = hash_password(new_pwd)
        db.commit()

        return ok(message="密码修改成功")
    except Exception:
        return fail("修改密码失败", 500)


@router.post("/api/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """统一登录入口。
    
    支持学生/教师/管理员通过 user_no（学号/工号/管理员编号）登录。
    根据 user.role 自动识别角色,返回对应的用户信息。
    兼容旧数据:既支持 user_no,也支持 username。
    """
    try:
        _ensure_seed_once(db)
        db.expire_all()

        account = (request.username or "").strip()
        # 兼容历史登录方式:user_no 优先,username 兜底
        user = db.scalar(
            select(User).where(
                (User.user_no == account) | (User.username == account)
            )
        )
        if not user:
            return fail("账号不存在,请检查后重试", 401)

        # 通用状态校验
        if user.role == "teacher":
            if getattr(user, "status", "approved") == "pending":
                return fail("您的账号正在等待审核,请耐心等待", 403)
            if getattr(user, "status", "approved") == "rejected":
                return fail("您的注册申请已被拒绝", 403)
        if not getattr(user, "is_active", True):
            return fail("您的账号已被管理员停用,请联系管理员", 403)

        _migrate_legacy_password_hash(user, db)
        login_pwd = ensure_transport_hash(request.password)
        if not verify_password(login_pwd, user.password_hash):
            return fail("密码错误,请重新输入", 401)

        # 学生需要额外校验 student 状态
        if user.role == "student":
            student = db.scalar(select(Student).where(Student.user_id == user.id))
            if not student:
                return fail("学生记录异常", 500)
            if getattr(student, "status", "approved") == "pending":
                return fail("您的账号正在等待教师审核,请耐心等待", 403)
            if getattr(student, "status", "approved") == "rejected":
                return fail("您的注册申请已被拒绝", 403)
            
            # 学生 token 用 student.uid(保持兼容,以后再统一)
            token = issue_token("student", str(student.uid))
            class_ids = StudentCRUD.list_class_ids(db, student.id)
            class_objs = [ClassroomCRUD.get_by_id(db, cid) for cid in class_ids]
            class_objs = [c for c in class_objs if c]
            class_id = class_ids[0] if class_ids else None
            class_name = class_objs[0].class_name if class_objs else None
            user_info = {
                "id": student.uid,
                "name": student.name,
                "role": "student",
                "studentId": student.id,
                "classId": class_id,
                "className": class_name,
                "classIds": class_ids,
                "classNames": [c.class_name for c in class_objs],
            }
        elif user.role in ("teacher", "admin"):
            token = issue_token(user.role, str(user.id))
            user_info = {
                "id": user.user_no or user.username,
                "name": user.display_name,
                "role": user.role,
            }
        else:
            return fail("未知的账号角色", 403)

        return {
            "code": 200,
            "message": "登录成功",
            "token": token,
            "user": user_info,
            "data": {"token": token, "user": user_info},
        }
    except Exception:
        if (os.getenv("APP_ENV", "") or "").strip().lower() not in {"prod", "production"}:
            import traceback
            traceback.print_exc()
        return fail("登录失败", 500)


# @router.post("/api/auth/student-login")
# def student_login(req: StudentLoginReq, db: Session = Depends(get_db)):
#     try:
#         student = StudentCRUD.get_by_uid(db, req.username)
#         if not student:
#             return fail("学号不存在，请检查后重试", 401)

#         if getattr(student, "status", "approved") == "pending":
#             return fail("您的账号正在等待教师审核，请耐心等待", 403)
#         elif getattr(student, "status", "approved") == "rejected":
#             return fail("您的注册申请已被拒绝", 403)

#         user = UserCRUD.get_by_id(db, student.user_id)
#         if not user:
#             return fail("用户记录异常", 500)

#         if not getattr(user, "is_active", True):
#             return fail("您的账号已被管理员停用，请联系管理员", 403)

#         _migrate_legacy_password_hash(user, db)
#         login_pwd = ensure_transport_hash(req.password)

#         if not verify_password(login_pwd, user.password_hash):
#             return fail("密码错误，请重新输入", 401)

#         token = issue_token("student", str(student.uid))
#         class_ids = StudentCRUD.list_class_ids(db, student.id)
#         class_objs = [ClassroomCRUD.get_by_id(db, class_id) for class_id in class_ids]
#         class_objs = [c for c in class_objs if c]
#         class_id = class_ids[0] if class_ids else None
#         class_name = class_objs[0].class_name if class_objs else None
#         info = {
#             "id": student.uid,
#             "name": student.name,
#             "role": "student",
#             "studentId": student.id,
#             "classId": class_id,
#             "className": class_name,
#             "classIds": class_ids,
#             "classNames": [c.class_name for c in class_objs],
#         }
#         return {
#             "code": 200,
#             "message": "登录成功",
#             "token": token,
#             "user": info,
#             "data": {"token": token, "user": info},
#         }
#     except Exception:
#         return fail("登录失败", 500)
# @router.post("/api/auth/student-login")
# def student_login(req: StudentLoginReq, db: Session = Depends(get_db)):
#     """已废弃: 转发到统一登录入口 /api/auth/login。
    
#     保留此 endpoint 是为了兼容旧客户端。新代码应使用 /api/auth/login。
#     """
#     return login(LoginRequest(username=req.username, password=req.password), db)


@router.post("/api/auth/student-register")
def student_register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing_user = UserCRUD.get_by_username(db, req.username)
        if existing_user:
            return fail("该学号已被注册", 409)

        existing_student = StudentCRUD.get_by_uid(db, req.username)
        if existing_student:
            return fail("该学号已被注册", 409)

        if should_seed_demo_data():
            _ensure_demo_data(db)

        class_id_val = None
        if req.class_code:
            classroom = ClassroomCRUD.get_by_code(db, req.class_code)
            if not classroom:
                return fail("无效的班级邀请码", 400)
            class_id_val = classroom.id

        require_approval = SystemSettingCRUD.get_setting_value(db, "REQUIRE_STUDENT_APPROVAL", "false") == "true"
        status_val = "pending" if require_approval else "approved"

        user = UserCRUD.create(
            db,
            UserCreate(
                username=req.username,
                password_hash=hash_password(ensure_transport_hash(req.password)),
                role="student",
                display_name=req.display_name,
                status=status_val,
            ),
        )

        student = StudentCRUD.create(
            db,
            StudentCreate(
                uid=req.username,
                user_id=user.id,
                name=req.display_name,
                status=status_val,
                active_score=0,
                overall_score=0,
            ),
        )
        # 新生注册时若提供了班级邀请码,写入中间表
        if class_id_val:
            StudentCRUD.set_classes(db, student, [class_id_val])

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
    except Exception:
        return fail("注册失败", 500)


@router.post("/api/auth/teacher-register")
def teacher_register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing_user = UserCRUD.get_by_username(db, req.username)
        if existing_user:
            return fail("该工号已被注册", 409)

        require_approval = SystemSettingCRUD.get_setting_value(db, "REQUIRE_TEACHER_APPROVAL", "false") == "true"
        status_val = "pending" if require_approval else "approved"

        UserCRUD.create(
            db,
            UserCreate(
                username=req.username,
                password_hash=hash_password(ensure_transport_hash(req.password)),
                role="teacher",
                display_name=req.display_name,
                status=status_val,
            ),
        )
        return ok({"username": req.username, "name": req.display_name}, "注册成功")
    except Exception:
        return fail("注册失败", 500)
