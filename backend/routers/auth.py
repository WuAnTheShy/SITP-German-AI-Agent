from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from crud.repositories import UserCRUD, StudentCRUD, ClassroomCRUD, StudentAbilityCRUD
from schemas.entities import UserCreate, StudentCreate, StudentAbilityUpsert
from core.responses import ok, fail
from core.seed import _ensure_demo_data, _ensure_admin

router = APIRouter()


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


class StudentLoginReq(BaseModel):
    username: str
    password: str


@router.put("/api/user/password")
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
    except Exception:
        return fail("修改密码失败", 500)


@router.post("/api/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        _ensure_demo_data(db)
        # 登录时再次确保默认管理员存在且身份正确，避免库中原有 admin 为教师
        _ensure_admin(db)
        # 确保后续查询拿到最新数据（避免 session 缓存导致 role 仍是旧值）
        db.expire_all()

        username = (request.username or "").strip()
        user = UserCRUD.get_by_username(db, username)
        if not user:
            return fail("用户不存在，请检查工号后重试", 401)

        if user.role == "admin":
            if user.password_hash != request.password:
                return fail("密码错误，请重新输入", 401)
            token = f"admin-token-{user.id}-{uuid4().hex[:8]}"
        elif user.role == "teacher":
            if user.password_hash != request.password:
                return fail("密码错误，请重新输入", 401)
            token = f"teacher-token-{user.id}-{uuid4().hex[:8]}"
        else:
            return fail("该账号不是教师或管理员账号", 403)
        user_info = {"id": user.username, "name": user.display_name, "role": user.role}
        return {
            "code": 200,
            "message": "登录成功",
            "token": token,
            "user": user_info,
            "data": {"token": token, "user": user_info},
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return fail("登录失败", 500)


@router.post("/api/auth/student-login")
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
    except Exception:
        return fail("登录失败", 500)


@router.post("/api/auth/student-register")
def student_register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing_user = UserCRUD.get_by_username(db, req.username)
        if existing_user:
            return fail("该学号已被注册", 409)

        existing_student = StudentCRUD.get_by_uid(db, req.username)
        if existing_student:
            return fail("该学号已被注册", 409)

        _ensure_demo_data(db)
        class_code = req.class_code or "SE-2026-4"
        classroom = ClassroomCRUD.get_by_code(db, class_code)
        if not classroom:
            return fail(f"班级 {class_code} 不存在", 404)

        user = UserCRUD.create(
            db,
            UserCreate(
                username=req.username,
                password_hash=req.password,
                role="student",
                display_name=req.display_name,
            ),
        )

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

        UserCRUD.create(
            db,
            UserCreate(
                username=req.username,
                password_hash=req.password,
                role="teacher",
                display_name=req.display_name,
            ),
        )
        return ok({"username": req.username, "name": req.display_name}, "注册成功")
    except Exception:
        return fail("注册失败", 500)
