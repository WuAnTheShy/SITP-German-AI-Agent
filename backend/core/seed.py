from datetime import datetime

from sqlalchemy.orm import Session

from crud.repositories import (
    UserCRUD,
    ClassroomCRUD,
    StudentCRUD,
    StudentAbilityCRUD,
    HomeworkCRUD,
)
from schemas.entities import (
    UserCreate,
    ClassroomCreate,
    StudentCreate,
    StudentAbilityUpsert,
    HomeworkCreate,
)
from core.responses import to_float
from core.password import ensure_transport_hash, hash_password, verify_password


def _ensure_user_password(db: Session, user, raw_password: str) -> None:
    """确保账号密码与约定默认值一致，兼容旧库残留哈希格式。"""
    if not user:
        return
    expected = ensure_transport_hash(raw_password)
    if not verify_password(expected, getattr(user, "password_hash", "")):
        user.password_hash = hash_password(expected)
        db.commit()


def _ensure_admin(db: Session):
    """确保默认管理员存在：username=admin, password=admin123，项目启动时调用。
    若已存在用户名为 admin 的账号（如曾注册为教师），则强制改为管理员身份。
    """
    admin_user = UserCRUD.get_by_username(db, "admin")
    if admin_user:
        if admin_user.role != "admin":
            admin_user.role = "admin"
            admin_user.display_name = "管理员"
            db.commit()
        _ensure_user_password(db, admin_user, "admin123")
        return
    UserCRUD.create(
        db,
        UserCreate(
            username="admin",
            password_hash=hash_password(ensure_transport_hash("admin123")),
            role="admin",
            display_name="管理员",
        ),
    )


def _ensure_demo_data(db: Session):
    def ensure_teacher(username: str, display_name: str):
        teacher = UserCRUD.get_by_username(db, username)
        if not teacher:
            teacher = UserCRUD.create(
                db,
                UserCreate(
                    username=username,
                    password_hash=hash_password(ensure_transport_hash("demo_hash_teacher")),
                    role="teacher",
                    display_name=display_name,
                ),
            )
        else:
            _ensure_user_password(db, teacher, "demo_hash_teacher")
        return teacher

    def ensure_classroom(class_code: str, class_name: str, grade: str, teacher_user_id: int):
        classroom = ClassroomCRUD.get_by_code(db, class_code)
        if not classroom:
            classroom = ClassroomCRUD.create(
                db,
                ClassroomCreate(
                    class_code=class_code,
                    class_name=class_name,
                    grade=grade,
                    teacher_user_id=teacher_user_id,
                ),
            )
        return classroom

    teacher_zhang = ensure_teacher("t_zhang", "张老师")
    teacher_liu = ensure_teacher("t_liu", "刘老师")
    teacher_chen = ensure_teacher("t_chen", "陈老师")

    classroom_se = ensure_classroom("SE-2026-4", "软件工程(四)班", "2026", teacher_zhang.id)
    classroom_ds = ensure_classroom("DS-2026-1", "数据科学(一)班", "2026", teacher_liu.id)
    classroom_fa = ensure_classroom("FA-2025-2", "德语强化(二)班", "2025", teacher_chen.id)

    def ensure_student(uid: str, username: str, name: str, class_id: int, active: int, overall: float, weak: str):
        stu_user = UserCRUD.get_by_username(db, username)
        if not stu_user:
            stu_user = UserCRUD.create(
                db,
                UserCreate(
                    username=username,
                    password_hash=hash_password(ensure_transport_hash("demo_hash_student")),
                    role="student",
                    display_name=name,
                ),
            )
        else:
            _ensure_user_password(db, stu_user, "demo_hash_student")

        student = StudentCRUD.get_by_uid(db, uid)
        if not student:
            student = StudentCRUD.create(
                db,
                StudentCreate(
                    uid=uid,
                    user_id=stu_user.id,
                    class_id=class_id,
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

    ensure_student("2452001", "s_li", "李娜", classroom_se.id, 88, 91.5, "虚拟式")
    ensure_student("2452002", "s_wang", "王强", classroom_se.id, 64, 78.0, "被动语态")
    ensure_student("2452003", "s_zhao", "赵敏", classroom_ds.id, 72, 82.5, "名词格变化")
    ensure_student("2452004", "s_sun", "孙浩", classroom_ds.id, 59, 71.0, "词序")
    ensure_student("2452005", "s_qian", "钱雨", classroom_fa.id, 85, 89.0, "介词搭配")
    ensure_student("2452006", "s_he", "何宁", classroom_fa.id, 67, 76.5, "虚拟式")

    return teacher_zhang, classroom_se
