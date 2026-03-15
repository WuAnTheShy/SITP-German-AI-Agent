"""管理员接口：教师列表、班级列表与班级的创建/更新（分配教师）。"""
from fastapi import APIRouter, Depends, HTTPException

from db.session import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel

from crud.repositories import UserCRUD, ClassroomCRUD
from schemas.entities import ClassroomCreate
from core.deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ClassCreateBody(BaseModel):
    class_code: str
    class_name: str
    grade: str | None = None
    teacher_user_id: int


class ClassUpdateBody(BaseModel):
    class_code: str | None = None
    class_name: str | None = None
    grade: str | None = None
    teacher_user_id: int | None = None


@router.get("/teachers")
def list_teachers(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """列出所有教师（供管理员分配班级时选择）。"""
    teachers = UserCRUD.list_teachers(db)
    return [
        {"id": u.id, "username": u.username, "display_name": u.display_name}
        for u in teachers
    ]


@router.get("/classes")
def list_classes(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """列出所有班级及对应教师信息。"""
    classes = ClassroomCRUD.list_all(db)
    result = []
    for c in classes:
        teacher = UserCRUD.get_by_id(db, c.teacher_user_id) if c.teacher_user_id else None
        result.append({
            "id": c.id,
            "class_code": c.class_code,
            "class_name": c.class_name,
            "grade": c.grade,
            "teacher_user_id": c.teacher_user_id,
            "teacher_username": teacher.username if teacher else None,
            "teacher_display_name": teacher.display_name if teacher else None,
        })
    return result


@router.post("/classes")
def create_class(
    body: ClassCreateBody,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """创建班级并指定负责教师。"""
    teacher = UserCRUD.get_by_id(db, body.teacher_user_id)
    if not teacher or teacher.role != "teacher":
        raise HTTPException(status_code=400, detail="指定的教师不存在或不是教师账号")
    existing = ClassroomCRUD.get_by_code(db, body.class_code)
    if existing:
        raise HTTPException(status_code=400, detail="班级代码已存在")
    classroom = ClassroomCRUD.create(
        db,
        ClassroomCreate(
            class_code=body.class_code,
            class_name=body.class_name,
            grade=body.grade,
            teacher_user_id=body.teacher_user_id,
        ),
    )
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
    if "teacher_user_id" in updates:
        teacher = UserCRUD.get_by_id(db, updates["teacher_user_id"])
        if not teacher or teacher.role != "teacher":
            raise HTTPException(status_code=400, detail="指定的教师不存在或不是教师账号")
    if "class_code" in updates:
        other = ClassroomCRUD.get_by_code(db, updates["class_code"])
        if other and other.id != class_id:
            raise HTTPException(status_code=400, detail="班级代码已被其他班级使用")
    ClassroomCRUD.update(db, classroom, **updates)
    return {"id": classroom.id, "class_code": classroom.class_code, "class_name": classroom.class_name}
