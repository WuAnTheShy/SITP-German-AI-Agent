"""Agent 工具的实际实现。

每个 handler 接收两个参数：
  args: dict —— Qwen 解析出来的参数（来自 tool_calls.arguments）
  context: dict —— 调用方信息（student_id、db session 等）

返回值会被 JSON 序列化后发回给 Qwen。
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from models.entities import (
    Student, ClassStudentRelation, Classroom,
    StudentAbility, LearningSession, Homework,
    ChatSession, ChatMessage,                      # 工具 5 用
    GrammarCategory, GrammarExercise,              # 工具 6 用
)


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



def query_my_recent_chats(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """查询当前学生最近 N 个对话会话的标题和首问。
    
    args:
        limit: int, 返回最近几个会话,默认 5,最大 20
    """
    db: Session = context["db"]
    student_id = context["student_id"]
    
    limit = max(1, min(int(args.get("limit", 5)), 20))
    
    # 取最近 N 个会话(按 updated_at 倒序)
    sessions = list(db.scalars(
        select(ChatSession)
        .where(ChatSession.student_id == student_id)
        .order_by(desc(ChatSession.updated_at))
        .limit(limit)
    ))
    
    if not sessions:
        return {
            "total_recent_sessions": 0,
            "items": [],
            "summary": "暂无对话历史",
        }
    
    items = []
    for s in sessions:
        # 找该会话的第一条 user 消息(展现学生意图)
        first_user_msg = db.scalar(
            select(ChatMessage)
            .where(ChatMessage.session_id == s.id, ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.asc())
            .limit(1)
        )
        # 该会话总消息数
        msg_count = db.scalar(
            select(func.count(ChatMessage.id))
            .where(ChatMessage.session_id == s.id)
        ) or 0
        
        items.append({
            "session_id": s.id,
            "title": (s.title or "").strip() or "未命名对话",
            "scene_name": s.scene_name,
            "first_question": (first_user_msg.content[:80] + "...") 
                              if first_user_msg and len(first_user_msg.content) > 80 
                              else (first_user_msg.content if first_user_msg else ""),
            "message_count": int(msg_count),
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        })
    
    # 简单总结主题(取前 3 个标题)
    titles = [i["title"] for i in items[:3] if i["title"] != "未命名对话"]
    summary = (
        f"最近 {len(items)} 次对话,主要话题:" + "、".join(titles)
        if titles 
        else f"最近 {len(items)} 次对话"
    )
    
    return {
        "total_recent_sessions": len(items),
        "items": items,
        "summary": summary,
    }


def recommend_grammar_exercises(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """根据学生薄弱点(或指定分类)推荐语法练习题。
    
    args:
        count: int, 推荐题目数量,默认 5,最大 10
        category_name: str | None, 指定语法分类(如"被动语态"、"虚拟式"等),
                       不指定则按学生薄弱点自动选
    """
    db: Session = context["db"]
    student_id = context["student_id"]
    
    count = max(1, min(int(args.get("count", 5)), 10))
    requested_category = args.get("category_name")
    
    # 决策推荐分类
    target_category = None
    reason = ""
    
    if requested_category:
        # 用户指定了分类
        target_category = db.scalar(
            select(GrammarCategory).where(GrammarCategory.name == requested_category)
        )
        if not target_category:
            return {
                "error": f"未找到分类'{requested_category}'",
                "available_categories": [
                    c.name for c in db.scalars(select(GrammarCategory)).all()
                ],
            }
        reason = f"按你的指定分类「{target_category.name}」推荐"
    else:
        # 按学生 weak_point 推
        student = db.scalar(select(Student).where(Student.id == student_id))
        weak_point = student.weak_point if student else None
        if weak_point:
            target_category = db.scalar(
                select(GrammarCategory).where(GrammarCategory.name == weak_point)
            )
            if target_category:
                reason = f"基于你的薄弱点「{weak_point}」推荐针对性练习"
        
        # 没有 weak_point 或匹配不到分类:用题目数量最多的分类
        if not target_category:
            target_category = db.scalar(
                select(GrammarCategory)
                .join(GrammarExercise, GrammarExercise.category_id == GrammarCategory.id)
                .group_by(GrammarCategory.id)
                .order_by(desc(func.count(GrammarExercise.id)))
                .limit(1)
            )
            reason = f"未识别明确的薄弱点,推荐题库最丰富的分类「{target_category.name if target_category else '未知'}」"
    
    if not target_category:
        return {"error": "题库为空,无法推荐"}
    
    # 取该分类下的题
    exercises = list(db.scalars(
        select(GrammarExercise)
        .where(GrammarExercise.category_id == target_category.id)
        .order_by(func.random())
        .limit(count)
    ))
    
    # 如果该分类题不够,从其他分类补
    if len(exercises) < count:
        exclude_ids = [e.id for e in exercises]
        more = list(db.scalars(
            select(GrammarExercise)
            .where(
                GrammarExercise.category_id != target_category.id,
                ~GrammarExercise.id.in_(exclude_ids) if exclude_ids else True,
            )
            .order_by(func.random())
            .limit(count - len(exercises))
        ))
        exercises.extend(more)
        if more:
            reason += f"(该分类题目不足,从其他分类补 {len(more)} 题)"
    
    items = [
        {
            "id": ex.id,
            "category_id": ex.category_id,
            "question": ex.question,
            "correct_answer": ex.correct_answer,
        }
        for ex in exercises
    ]
    
    return {
        "recommended_category": target_category.name,
        "reason": reason,
        "count": len(items),
        "exercises": items,
        "summary": f"为你推荐 {len(items)} 道{target_category.name}练习题",
    }


def search_knowledge_base(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """检索德语学习知识库,返回最相关的内容片段。
    
    包装 services.rag.search_knowledge,做两阶段检索(embedding 召回 + rerank 精排)。
    
    args:
        query: str, 必填,检索查询(德语语法/词汇/文化等问题)
        top_k: int, 返回多少个相关片段,默认 3,最大 5(实际由 rag.py 阈值控制)
    """
    db: Session = context["db"]
    
    query = (args.get("query") or "").strip()
    if not query:
        return {"error": "query 参数不能为空"}
    
    try:
        from services.rag import search_knowledge
        rows = search_knowledge(db, query, viewer_user_id=None, viewer_session_key=None)
    except Exception as e:
        logger.warning(f"RAG 检索失败: {type(e).__name__}: {e}")
        return {"error": "知识库暂时不可用,请稍后再试"}
    
    if not rows:
        return {
            "query": query,
            "results": [],
            "summary": "知识库中未找到相关内容",
            "advice_to_llm": (
                "知识库未命中,不要重试不同的查询关键词。"
                "请直接基于你已有的知识回答用户问题,并在回答开头说明'未在知识库中找到相关内容,以下是通用知识'。"
            ),
        }
    
    # 取前 top_k(虽然 rag.py 已经控制了 RAG_RERANK_TOP_N,这里再裁一刀)
    top_k = max(1, min(int(args.get("top_k", 3)), 5))
    rows = rows[:top_k]
    
    return {
        "query": query,
        "results": [
            {
                "title": r.get("title") or "未命名片段",
                "chunk_index": r.get("chunk_index", 0),
                "content": (r.get("content") or "")[:400],  # 限制 400 字避免 LLM 上下文爆炸
                "score": round(float(r.get("score", 0)), 3),
            }
            for r in rows
        ],
        "count": len(rows),
        "summary": f"从知识库检索到 {len(rows)} 个相关片段(top_score={round(float(rows[0].get('score', 0)), 3)})",
    }