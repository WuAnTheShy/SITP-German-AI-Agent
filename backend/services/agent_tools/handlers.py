"""Agent 工具的实际实现。

每个 handler 接收两个参数：
  args: dict —— Qwen 解析出来的参数（来自 tool_calls.arguments）
  context: dict —— 调用方信息（student_id、db session 等）

返回值会被 JSON 序列化后发回给 Qwen。
"""

from typing import Any

from sqlalchemy import select

from models.entities import Student, ClassStudentRelation, Classroom


def query_my_profile(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """查询当前学生的基本档案（姓名、学号、班级）。"""
    db = context["db"]
    student_id = context["student_id"]

    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        return {"error": "学生信息未找到"}

    # 通过中间表查班级（实际数据存在 class_student_relations）
    rel = db.scalar(
        select(ClassStudentRelation).where(
            ClassStudentRelation.student_id == student_id
        )
    )
    class_name = None
    class_code = None
    if rel:
        cls = db.scalar(select(Classroom).where(Classroom.id == rel.class_id))
        if cls:
            class_name = cls.class_name
            class_code = cls.class_code

    return {
        "student_id": student.id,
        "name": student.name,
        "uid": student.uid,                           # 学号
        "class_name": class_name,
        "class_code": class_code,
        "overall_score": float(student.overall_score) if student.overall_score is not None else 0.0,
        "active_score": student.active_score,
        "weak_point": student.weak_point,             # 薄弱点
    }