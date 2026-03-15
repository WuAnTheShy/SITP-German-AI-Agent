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


def _ensure_admin(db: Session):
    """确保默认管理员存在：username=admin, password=admin123，项目启动时调用。
    若已存在用户名为 admin 的账号（如曾注册为教师），则强制改为管理员身份。
    """
    admin_user = UserCRUD.get_by_username(db, "admin")
    if admin_user:
        if admin_user.role != "admin":
            admin_user.role = "admin"
            admin_user.password_hash = "admin123"
            admin_user.display_name = "管理员"
            db.commit()
        return
    UserCRUD.create(
        db,
        UserCreate(
            username="admin",
            password_hash="admin123",
            role="admin",
            display_name="管理员",
        ),
    )


def _ensure_demo_data(db: Session):
    teacher = UserCRUD.get_by_username(db, "t_zhang")
    if not teacher:
        teacher = UserCRUD.create(
            db,
            UserCreate(
                username="t_zhang",
                password_hash="demo_hash_teacher",
                role="teacher",
                display_name="张老师",
            ),
        )

    classroom = ClassroomCRUD.get_by_code(db, "SE-2026-4")
    if not classroom:
        classroom = ClassroomCRUD.create(
            db,
            ClassroomCreate(
                class_code="SE-2026-4",
                class_name="软件工程(四)班",
                grade="2026",
                teacher_user_id=teacher.id,
            ),
        )

    def ensure_student(uid: str, username: str, name: str, active: int, overall: float, weak: str):
        stu_user = UserCRUD.get_by_username(db, username)
        if not stu_user:
            stu_user = UserCRUD.create(
                db,
                UserCreate(
                    username=username,
                    password_hash="demo_hash_student",
                    role="student",
                    display_name=name,
                ),
            )

        student = StudentCRUD.get_by_uid(db, uid)
        if not student:
            student = StudentCRUD.create(
                db,
                StudentCreate(
                    uid=uid,
                    user_id=stu_user.id,
                    class_id=classroom.id,
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

    ensure_student("2452001", "s_li", "李娜", 88, 91.5, "虚拟式")
    ensure_student("2452002", "s_wang", "王强", 64, 78.0, "被动语态")

    return teacher, classroom
