"""Agent 工具的实际实现。

每个 handler 接收两个参数：
  args: dict —— Qwen 解析出来的参数（来自 tool_calls.arguments）
  context: dict —— 调用方信息（student_id、db session 等）

返回值会被 JSON 序列化后发回给 Qwen。
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from models.entities import (
    Student, ClassStudentRelation, Classroom,
    StudentAbility, LearningSession, Homework,
)
from typing import Any


logger = logging.getLogger(__name__)


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


def query_my_abilities(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """查询当前学生的四维能力分数 + AI 诊断 + 薄弱点。"""
    db = context["db"]
    student_id = context["student_id"]

    ability = db.scalar(
        select(StudentAbility).where(StudentAbility.student_id == student_id)
    )
    if not ability:
        return {"error": "学情画像未生成,可能学生从未开始学习"}

    student = db.scalar(select(Student).where(Student.id == student_id))

    # 计算最强/最弱维度(只看 4 项语言技能)
    scores = {
        "listening": ability.listening,
        "speaking": ability.speaking,
        "reading": ability.reading,
        "writing": ability.writing,
    }
    weakest = min(scores, key=scores.get)
    strongest = max(scores, key=scores.get)

    return {
        "listening": ability.listening,
        "speaking": ability.speaking,
        "reading": ability.reading,
        "writing": ability.writing,
        "weakest_dimension": weakest,
        "weakest_score": scores[weakest],
        "strongest_dimension": strongest,
        "strongest_score": scores[strongest],
        "weak_point": student.weak_point if student else None,  # 学生表里的薄弱点描述
        "ai_diagnosis": ability.ai_diagnosis or "暂无 AI 诊断",
        "overall_score": float(student.overall_score) if student and student.overall_score is not None else None,
    }


def query_my_recent_activity(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """查询当前学生最近 N 天的学习活动统计。
    
    args:
        days: int, 查询天数,默认 7,最大 30
    """
    db = context["db"]
    student_id = context["student_id"]

    days = max(1, min(int(args.get("days", 7)), 30))
    since = datetime.now() - timedelta(days=days)

    # 按模块聚合
    rows = db.execute(
        select(
            LearningSession.module,
            func.count(LearningSession.id).label("session_count"),
            func.coalesce(func.sum(LearningSession.duration_minutes), 0).label("total_minutes"),
        )
        .where(
            LearningSession.student_id == student_id,
            LearningSession.created_at >= since,
        )
        .group_by(LearningSession.module)
        .order_by(desc("total_minutes"))
    ).all()

    if not rows:
        return {
            "period_days": days,
            "total_sessions": 0,
            "total_minutes": 0,
            "by_module": {},
            "most_active_module": None,
            "summary": f"最近 {days} 天没有学习记录",
        }

    by_module = {}
    total_sessions = 0
    total_minutes = 0
    for module, cnt, mins in rows:
        by_module[module] = {"sessions": int(cnt), "minutes": int(mins or 0)}
        total_sessions += int(cnt)
        total_minutes += int(mins or 0)

    most_active = rows[0][0]  # 排序后第一行的 module

    return {
        "period_days": days,
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "by_module": by_module,
        "most_active_module": most_active,
        "summary": f"最近 {days} 天累计学习 {total_minutes} 分钟,共 {total_sessions} 次活动,主要在「{most_active}」模块",
    }


def query_my_homeworks(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """查询当前学生的作业列表。
    
    args:
        limit: int, 最近 N 条,默认 10,最大 30
        status: str | None, 可选筛选 ('已完成' / '未提交' / '进行中' / '待订正' / '逾期补交')
    """
    db = context["db"]
    student_id = context["student_id"]

    limit = max(1, min(int(args.get("limit", 10)), 30))
    status_filter = args.get("status")

    query = select(Homework).where(Homework.student_id == student_id)
    if status_filter:
        query = query.where(Homework.status == status_filter)
    query = query.order_by(desc(Homework.submitted_at).nullsfirst()).limit(limit)
    # nullsfirst:让"未提交"(submitted_at=NULL)排在前面,提醒学生

    homeworks = list(db.scalars(query))

    if not homeworks:
        return {
            "total_count": 0,
            "items": [],
            "summary": "没有作业记录",
        }

    # 计算统计
    completed = [h for h in homeworks if h.status == "已完成"]
    pending = [h for h in homeworks if h.status in ("未提交", "进行中")]
    avg_score = None
    scored = [float(h.score) for h in completed if h.score is not None]
    if scored:
        avg_score = round(sum(scored) / len(scored), 2)

    items = [
        {
            "id": h.id,
            "title": h.title,
            "status": h.status,
            "score": float(h.score) if h.score is not None else None,
            "submitted_at": h.submitted_at.isoformat() if h.submitted_at else None,
            "ai_comment": (h.ai_comment[:100] + "...") if h.ai_comment and len(h.ai_comment) > 100 else h.ai_comment,
        }
        for h in homeworks
    ]

    return {
        "total_count": len(homeworks),
        "completed_count": len(completed),
        "pending_count": len(pending),
        "average_score": avg_score,
        "items": items,
        "summary": (
            f"共 {len(homeworks)} 份作业,已完成 {len(completed)} 份"
            + (f",平均分 {avg_score}" if avg_score is not None else "")
            + (f",有 {len(pending)} 份待完成" if pending else "")
        ),
    }