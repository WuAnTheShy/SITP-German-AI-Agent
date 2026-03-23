"""管理员接口：教师、班级、学生与系统设置管理。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from db.session import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel

from crud.repositories import UserCRUD, ClassroomCRUD, SystemSettingCRUD, StudentCRUD
from models.entities import Student
from schemas.entities import ClassroomCreate
from core.deps import require_admin
from core.password import ensure_transport_hash, hash_password
from services.metrics import refresh_student_metrics

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ClassCreateBody(BaseModel):
    class_code: str
    class_name: str
    grade: str | None = None
    teacher_user_id: int | None = None
    teacher_user_ids: list[int] | None = None


class ClassUpdateBody(BaseModel):
    class_code: str | None = None
    class_name: str | None = None
    grade: str | None = None
    teacher_user_id: int | None = None
    teacher_user_ids: list[int] | None = None


class TeacherUpdateBody(BaseModel):
    display_name: str | None = None
    status: str | None = None
    is_active: bool | None = None
    class_ids: list[int] | None = None


class StudentUpdateBody(BaseModel):
    name: str | None = None
    class_id: int | None = None
    class_ids: list[int] | None = None
    status: str | None = None
    is_active: bool | None = None
    active_score: int | None = None
    overall_score: float | None = None
    weak_point: str | None = None


class AdminResetPasswordBody(BaseModel):
    new_password: str


@router.get("/teachers")
def list_teachers(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """列出所有教师（供管理员分配班级时选择）。"""
    teachers = UserCRUD.list_teachers(db)
    result = []
    for u in teachers:
        class_count = len(ClassroomCRUD.list_by_teacher(db, u.id))
        result.append(
            {
                "id": u.id,
                "username": u.username,
                "display_name": u.display_name,
                "status": u.status,
                "is_active": u.is_active,
                "class_count": class_count,
            }
        )
    return result


@router.put("/teachers/{user_id}")
def update_teacher(
    user_id: int,
    body: TeacherUpdateBody,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    teacher = UserCRUD.get_by_id(db, user_id)
    if not teacher or teacher.role != "teacher":
        raise HTTPException(status_code=404, detail="教师不存在")

    updates = body.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="教师状态非法")

    # 提取 class_ids 单独处理
    class_ids = updates.pop("class_ids", None)

    # 更新教师基本信息
    for key, value in updates.items():
        if hasattr(teacher, key):
            setattr(teacher, key, value)
    db.commit()
    db.refresh(teacher)

    # 处理班级关联
    if class_ids is not None:
        # 获取所有班级
        all_classes = ClassroomCRUD.list_all(db)
        
        # 对于每个班级，检查是否需要添加或删除该教师
        for classroom in all_classes:
            current_teachers = ClassroomCRUD.get_teacher_ids(db, classroom.id)
            should_have = classroom.id in class_ids
            has_teacher = user_id in current_teachers
            
            if should_have and not has_teacher:
                # 添加教师到班级
                current_teachers.append(user_id)
                ClassroomCRUD.set_teachers(db, classroom.id, current_teachers)
            elif not should_have and has_teacher:
                # 从班级中删除教师
                current_teachers.remove(user_id)
                ClassroomCRUD.set_teachers(db, classroom.id, current_teachers)

    return {
        "id": teacher.id,
        "username": teacher.username,
        "display_name": teacher.display_name,
        "status": teacher.status,
        "is_active": teacher.is_active,
    }


@router.delete("/teachers/{user_id}")
def delete_teacher(user_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    teacher = UserCRUD.get_by_id(db, user_id)
    if not teacher or teacher.role != "teacher":
        raise HTTPException(status_code=404, detail="教师不存在")

    related_classes = ClassroomCRUD.list_by_teacher(db, teacher.id)
    if related_classes:
        raise HTTPException(status_code=400, detail="该教师仍有负责班级，请先调整班级教师后再删除")

    db.delete(teacher)
    db.commit()
    return {"message": "教师删除成功"}


@router.get("/classes")
def list_classes(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """列出所有班级及对应教师信息。"""
    classes = ClassroomCRUD.list_all(db)
    result = []
    for c in classes:
        teacher_ids = ClassroomCRUD.get_teacher_ids(db, c.id)
        teachers = [UserCRUD.get_by_id(db, t_id) for t_id in teacher_ids]
        teachers = [t for t in teachers if t and t.role == "teacher"]
        teacher = teachers[0] if teachers else None
        result.append({
            "id": c.id,
            "class_code": c.class_code,
            "class_name": c.class_name,
            "grade": c.grade,
            "teacher_user_id": teacher.id if teacher else None,
            "teacher_user_ids": [t.id for t in teachers],
            "teacher_username": teacher.username if teacher else None,
            "teacher_display_name": teacher.display_name if teacher else None,
            "teacher_usernames": [t.username for t in teachers],
            "teacher_display_names": [t.display_name for t in teachers],
        })
    return result


@router.get("/students")
def list_students(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    students = list(db.scalars(select(Student).order_by(Student.id)))
    result = []
    for s in students:
        latest_metrics = refresh_student_metrics(db, s.id)
        user = UserCRUD.get_by_id(db, s.user_id)
        class_ids = StudentCRUD.list_class_ids(db, s.id)
        class_objs = [ClassroomCRUD.get_by_id(db, c_id) for c_id in class_ids]
        class_objs = [c for c in class_objs if c]
        classroom = class_objs[0] if class_objs else None
        result.append(
            {
                "id": s.id,
                "user_id": s.user_id,
                "uid": s.uid,
                "name": s.name,
                "status": s.status,
                "is_active": bool(user.is_active) if user else True,
                "class_id": s.class_id,
                "class_ids": class_ids,
                "class_name": classroom.class_name if classroom else None,
                "class_code": classroom.class_code if classroom else None,
                "class_names": [c.class_name for c in class_objs],
                "class_codes": [c.class_code for c in class_objs],
                "active_score": latest_metrics["active_score"],
                "overall_score": latest_metrics["overall_score"],
                "weak_point": latest_metrics["weak_point"],
                "username": user.username if user else None,
                "created_at": s.created_at.isoformat(),
            }
        )
    return result


@router.put("/students/{student_id}")
def update_student(
    student_id: int,
    body: StudentUpdateBody,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    updates = body.model_dump(exclude_unset=True)
    updates.pop("active_score", None)
    updates.pop("overall_score", None)
    class_ids = updates.pop("class_ids", None)
    if class_ids is None and "class_id" in updates:
        class_ids = [] if updates["class_id"] is None else [updates["class_id"]]
    if "status" in updates and updates["status"] not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="学生状态非法")
    if class_ids is not None:
        for class_id in class_ids:
            classroom = ClassroomCRUD.get_by_id(db, class_id)
            if not classroom:
                raise HTTPException(status_code=400, detail=f"班级不存在: {class_id}")

    for key, value in updates.items():
        if hasattr(student, key):
            setattr(student, key, value)

    if class_ids is not None:
        StudentCRUD.set_classes(db, student, class_ids)

    user = UserCRUD.get_by_id(db, student.user_id)
    if user:
        if "name" in updates:
            user.display_name = updates["name"]
        if "status" in updates:
            user.status = updates["status"]
        if "is_active" in updates:
            user.is_active = bool(updates["is_active"])

    db.commit()
    db.refresh(student)
    latest_metrics = refresh_student_metrics(db, student.id)
    final_class_ids = StudentCRUD.list_class_ids(db, student.id)
    class_objs = [ClassroomCRUD.get_by_id(db, c_id) for c_id in final_class_ids]
    class_objs = [c for c in class_objs if c]
    classroom = class_objs[0] if class_objs else None
    return {
        "id": student.id,
        "uid": student.uid,
        "name": student.name,
        "status": student.status,
        "is_active": bool(user.is_active) if user else True,
        "class_id": student.class_id,
        "class_ids": final_class_ids,
        "class_name": classroom.class_name if classroom else None,
        "class_names": [c.class_name for c in class_objs],
        "active_score": latest_metrics["active_score"],
        "overall_score": latest_metrics["overall_score"],
        "weak_point": latest_metrics["weak_point"],
    }


@router.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    user = UserCRUD.get_by_id(db, student.user_id)
    if user:
        db.delete(user)
    else:
        db.delete(student)
    db.commit()
    return {"message": "学生删除成功"}


@router.post("/classes")
def create_class(
    body: ClassCreateBody,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """创建班级并指定负责教师。"""
    teacher_ids = body.teacher_user_ids
    if teacher_ids is None:
        teacher_ids = [body.teacher_user_id] if body.teacher_user_id is not None else []
    teacher_ids = sorted(set(int(x) for x in teacher_ids if x is not None))
    for teacher_id in teacher_ids:
        teacher = UserCRUD.get_by_id(db, teacher_id)
        if not teacher or teacher.role != "teacher":
            raise HTTPException(status_code=400, detail=f"指定的教师不存在或不是教师账号: {teacher_id}")

    existing = ClassroomCRUD.get_by_code(db, body.class_code)
    if existing:
        raise HTTPException(status_code=400, detail="班级代码已存在")

    primary_teacher_id = teacher_ids[0] if teacher_ids else None
    classroom = ClassroomCRUD.create(
        db,
        ClassroomCreate(
            class_code=body.class_code,
            class_name=body.class_name,
            grade=body.grade,
            teacher_user_id=primary_teacher_id,
        ),
    )

    if teacher_ids:
        ClassroomCRUD.set_teachers(db, classroom.id, teacher_ids)

    return {"id": classroom.id, "class_code": classroom.class_code, "class_name": classroom.class_name}


@router.put("/classes/{class_id}")
def update_class(
    class_id: int,
    body: ClassUpdateBody,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """更新班级信息或重新分配教师。"""
    classroom = ClassroomCRUD.get_by_id(db, class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="班级不存在")
    updates = body.model_dump(exclude_unset=True)
    teacher_ids = updates.pop("teacher_user_ids", None)
    if teacher_ids is None and "teacher_user_id" in updates:
        teacher_ids = [] if updates["teacher_user_id"] is None else [updates["teacher_user_id"]]
    if teacher_ids is not None:
        teacher_ids = sorted(set(int(x) for x in teacher_ids if x is not None))
        for teacher_id in teacher_ids:
            teacher = UserCRUD.get_by_id(db, teacher_id)
            if not teacher or teacher.role != "teacher":
                raise HTTPException(status_code=400, detail=f"指定的教师不存在或不是教师账号: {teacher_id}")
        updates["teacher_user_id"] = teacher_ids[0] if teacher_ids else None
    if "class_code" in updates:
        other = ClassroomCRUD.get_by_code(db, updates["class_code"])
        if other and other.id != class_id:
            raise HTTPException(status_code=400, detail="班级代码已被其他班级使用")
    ClassroomCRUD.update(db, classroom, **updates)

    if teacher_ids is not None:
        ClassroomCRUD.set_teachers(db, classroom.id, teacher_ids)

    return {"id": classroom.id, "class_code": classroom.class_code, "class_name": classroom.class_name}


class SystemSettingsUpdate(BaseModel):
    REQUIRE_TEACHER_APPROVAL: bool | None = None
    REQUIRE_STUDENT_APPROVAL: bool | None = None


@router.get("/system/settings")
def get_system_settings(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    teacher_approval = SystemSettingCRUD.get_setting_value(db, "REQUIRE_TEACHER_APPROVAL", "false")
    student_approval = SystemSettingCRUD.get_setting_value(db, "REQUIRE_STUDENT_APPROVAL", "false")
    return {
        "REQUIRE_TEACHER_APPROVAL": teacher_approval == "true",
        "REQUIRE_STUDENT_APPROVAL": student_approval == "true",
    }


@router.put("/system/settings")
def update_system_settings(body: SystemSettingsUpdate, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    if body.REQUIRE_TEACHER_APPROVAL is not None:
        SystemSettingCRUD.set_setting(db, "REQUIRE_TEACHER_APPROVAL", "true" if body.REQUIRE_TEACHER_APPROVAL else "false")
    if body.REQUIRE_STUDENT_APPROVAL is not None:
        SystemSettingCRUD.set_setting(db, "REQUIRE_STUDENT_APPROVAL", "true" if body.REQUIRE_STUDENT_APPROVAL else "false")
    return {"message": "设置已保存"}


@router.get("/users/pending-teachers")
def list_pending_teachers(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    teachers = UserCRUD.list_pending_teachers(db)
    return [
        {"id": u.id, "username": u.username, "display_name": u.display_name, "created_at": u.created_at.isoformat()}
        for u in teachers
    ]


@router.put("/users/teachers/{user_id}/approve")
def approve_teacher(user_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    user = UserCRUD.get_by_id(db, user_id)
    if not user or user.role != "teacher":
        raise HTTPException(status_code=404, detail="教师不存在")
    UserCRUD.update_status(db, user_id, "approved")
    return {"message": "审核通过成功"}


@router.put("/users/teachers/{user_id}/reject")
def reject_teacher(user_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    user = UserCRUD.get_by_id(db, user_id)
    if not user or user.role != "teacher":
        raise HTTPException(status_code=404, detail="教师不存在")
    UserCRUD.update_status(db, user_id, "rejected")
    return {"message": "已拒绝该教师注册"}


@router.delete("/classes/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    classroom = ClassroomCRUD.get_by_id(db, class_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="班级不存在")
    db.delete(classroom)
    db.commit()
    return {"message": "班级删除成功"}


@router.put("/users/{user_id}/password")
def reset_user_password_by_admin(
    user_id: int,
    body: AdminResetPasswordBody,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    user = UserCRUD.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")

    new_pwd = ensure_transport_hash(body.new_password)
    if not new_pwd:
        raise HTTPException(status_code=400, detail="新密码不能为空")

    user.password_hash = hash_password(new_pwd)
    db.commit()
    return {"message": "密码重置成功"}
