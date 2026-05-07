"""Agent 工具的实际实现。

每个 handler 接收两个参数：
  args: dict —— Qwen 解析出来的参数（来自 tool_calls.arguments）
  context: dict —— 调用方信息（student_id、db session 等）

返回值会被 JSON 序列化后发回给 Qwen。
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import Session

from models.entities import (
    Student, ClassStudentRelation, Classroom,
    StudentAbility, LearningSession, Homework,
    ChatSession, ChatMessage,
    GrammarCategory, GrammarExercise,
    ClassTeacherRelation,           # 教师工具用
    ErrorBookEntry,                 # 教师工具用
    User,                           # 教师工具用
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




# ────────────────────────────────────────────────────
# 教师端工具公共辅助:获取该教师能管的班级 ID 列表
# ────────────────────────────────────────────────────

def _teacher_class_ids(db: Session, teacher_user_id: int) -> list[int]:
    """返回该教师任教的所有班级 id 列表。"""
    return list(db.scalars(
        select(ClassTeacherRelation.class_id).where(
            ClassTeacherRelation.teacher_user_id == teacher_user_id
        )
    ))


def query_class_overview(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """查询教师所教全部班级的总览(均分、活跃度、学生数、薄弱点分布)。
    
    args:
        class_code: str | None, 可选,只查指定班级(如 'SE-2026-4'),不指定则查所有
    """
    db: Session = context["db"]
    teacher_user_id = context["teacher_user_id"]
    
    class_ids = _teacher_class_ids(db, teacher_user_id)
    if not class_ids:
        return {"error": "你没有任教的班级"}
    
    # 可选过滤指定班级
    target_code = args.get("class_code")
    classes_query = select(Classroom).where(Classroom.id.in_(class_ids))
    if target_code:
        classes_query = classes_query.where(Classroom.class_code == target_code)
    classes = list(db.scalars(classes_query))
    
    if not classes:
        return {
            "error": f"未找到指定班级'{target_code}'" if target_code else "无班级数据"
        }
    
    overview = []
    for cls in classes:
        # 班级所有学生
        students = list(db.scalars(
            select(Student)
            .join(ClassStudentRelation, ClassStudentRelation.student_id == Student.id)
            .where(ClassStudentRelation.class_id == cls.id)
        ))
        
        if not students:
            overview.append({
                "class_id": cls.id,
                "class_name": cls.class_name,
                "class_code": cls.class_code,
                "student_count": 0,
                "summary": "暂无学生",
            })
            continue
        
        # 取该班所有学生的能力数据
        student_ids = [s.id for s in students]
        abilities = list(db.scalars(
            select(StudentAbility).where(StudentAbility.student_id.in_(student_ids))
        ))
        
        # 聚合四维平均
        if abilities:
            avg_listening = sum(a.listening for a in abilities) / len(abilities)
            avg_speaking = sum(a.speaking for a in abilities) / len(abilities)
            avg_reading = sum(a.reading for a in abilities) / len(abilities)
            avg_writing = sum(a.writing for a in abilities) / len(abilities)
            avg_four_dims = (avg_listening + avg_speaking + avg_reading + avg_writing) / 4
        else:
            avg_listening = avg_speaking = avg_reading = avg_writing = avg_four_dims = 0
        
        # 薄弱点分布(weak_point 频次统计)
        weak_distribution: dict[str, int] = {}
        for s in students:
            wp = s.weak_point or "未识别"
            weak_distribution[wp] = weak_distribution.get(wp, 0) + 1
        
        # 活跃度:近 7 天有学习记录的学生数
        seven_days_ago = datetime.now() - timedelta(days=7)
        active_count = db.scalar(
            select(func.count(func.distinct(LearningSession.student_id)))
            .where(
                LearningSession.student_id.in_(student_ids),
                LearningSession.created_at >= seven_days_ago,
            )
        ) or 0
        
        overview.append({
            "class_id": cls.id,
            "class_name": cls.class_name,
            "class_code": cls.class_code,
            "student_count": len(students),
            "active_students_7d": int(active_count),
            "active_rate": round(active_count / len(students) * 100, 1) if students else 0,
            "avg_listening": round(avg_listening, 1),
            "avg_speaking": round(avg_speaking, 1),
            "avg_reading": round(avg_reading, 1),
            "avg_writing": round(avg_writing, 1),
            "avg_four_dims": round(avg_four_dims, 1),
            "weak_point_distribution": weak_distribution,
        })
    
    return {
        "total_classes": len(overview),
        "classes": overview,
        "summary": (
            f"共 {len(overview)} 个班级,"
            + f"总人数 {sum(c['student_count'] for c in overview)} 人"
        ),
    }


def query_student_by_uid(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """教师按学号查指定学生学情。
    
    args:
        uid: str, 必填,学生学号(如 '2452001')
    """
    db: Session = context["db"]
    teacher_user_id = context["teacher_user_id"]
    
    uid = (args.get("uid") or "").strip()
    if not uid:
        return {"error": "uid 参数不能为空"}
    
    student = db.scalar(select(Student).where(Student.uid == uid))
    if not student:
        return {"error": f"未找到学号 {uid} 对应的学生"}
    
    # 鉴权:确保该教师能管这个学生
    teacher_class_ids = _teacher_class_ids(db, teacher_user_id)
    student_class_ids = list(db.scalars(
        select(ClassStudentRelation.class_id).where(
            ClassStudentRelation.student_id == student.id
        )
    ))
    common_class_ids = set(teacher_class_ids) & set(student_class_ids)
    if not common_class_ids:
        return {"error": f"你无权查看该学生(学号 {uid} 不在你任教的班级)"}
    
    # 取班级名(取第一个共同班)
    cls = db.scalar(select(Classroom).where(Classroom.id == next(iter(common_class_ids))))
    class_name = cls.class_name if cls else None
    
    # 能力数据
    ability = db.scalar(
        select(StudentAbility).where(StudentAbility.student_id == student.id)
    )
    
    # 最近作业
    recent_homeworks = list(db.scalars(
        select(Homework)
        .where(Homework.student_id == student.id)
        .order_by(desc(Homework.submitted_at).nullsfirst())
        .limit(5)
    ))
    
    # 错题数(未掌握)
    unmastered_errors = db.scalar(
        select(func.count(ErrorBookEntry.id)).where(
            ErrorBookEntry.student_id == student.id,
            ErrorBookEntry.is_mastered == False,
        )
    ) or 0
    
    return {
        "student_id": student.id,
        "name": student.name,
        "uid": student.uid,
        "class_name": class_name,
        "weak_point": student.weak_point,
        "overall_score": float(student.overall_score) if student.overall_score is not None else None,
        "active_score": student.active_score,
        "abilities": (
            {
                "listening": ability.listening,
                "speaking": ability.speaking,
                "reading": ability.reading,
                "writing": ability.writing,
                "ai_diagnosis": ability.ai_diagnosis,
            } if ability else None
        ),
        "recent_homeworks_count": len(recent_homeworks),
        "completed_homeworks_count": sum(1 for h in recent_homeworks if h.status == "已完成"),
        "unmastered_errors": int(unmastered_errors),
        "recent_homeworks": [
            {
                "title": h.title,
                "status": h.status,
                "score": float(h.score) if h.score is not None else None,
            } for h in recent_homeworks
        ],
    }


def find_struggling_students(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """找出薄弱学生:按指定维度或总分,返回低于阈值的学生列表。
    
    args:
        dimension: str | None, 可选,具体维度('listening'/'speaking'/'reading'/'writing'/'overall'),
                   默认 'overall'(综合判断)
        threshold: int, 默认 60,低于此分数算薄弱
        limit: int, 默认 20,返回最多多少人
    """
    db: Session = context["db"]
    teacher_user_id = context["teacher_user_id"]
    
    dimension = args.get("dimension", "overall")
    threshold = int(args.get("threshold", 60))
    limit = max(1, min(int(args.get("limit", 20)), 50))
    
    if dimension not in ("listening", "speaking", "reading", "writing", "overall"):
        return {"error": f"无效维度: {dimension}"}
    
    # 拿到教师管的所有班级里的所有学生
    class_ids = _teacher_class_ids(db, teacher_user_id)
    if not class_ids:
        return {"error": "你没有任教的班级"}
    
    student_ids = list(db.scalars(
        select(ClassStudentRelation.student_id).where(
            ClassStudentRelation.class_id.in_(class_ids)
        )
    ))
    if not student_ids:
        return {
            "dimension": dimension,
            "threshold": threshold,
            "struggling_count": 0,
            "students": [],
            "summary": "你任教的班级暂无学生",
        }
    
    # 取所有学生 + 能力
    rows = list(db.execute(
        select(Student, StudentAbility)
        .outerjoin(StudentAbility, StudentAbility.student_id == Student.id)
        .where(Student.id.in_(student_ids))
    ).all())
    
    # 按维度筛选低于阈值的
    struggling = []
    for student, ability in rows:
        if dimension == "overall":
            # 用四维平均(overall_score 字段已知有 bug,这里直接算)
            if not ability:
                continue
            score = (ability.listening + ability.speaking + ability.reading + ability.writing) / 4
        else:
            if not ability:
                continue
            score = getattr(ability, dimension)
        
        if score < threshold:
            struggling.append({
                "student_id": student.id,
                "uid": student.uid,
                "name": student.name,
                "score_in_dimension": round(float(score), 1),
                "weak_point": student.weak_point,
                "abilities": {
                    "listening": ability.listening,
                    "speaking": ability.speaking,
                    "reading": ability.reading,
                    "writing": ability.writing,
                },
            })
    
    # 按分数升序(最薄弱的在前)
    struggling.sort(key=lambda x: x["score_in_dimension"])
    struggling = struggling[:limit]
    
    return {
        "dimension": dimension,
        "threshold": threshold,
        "struggling_count": len(struggling),
        "students": struggling,
        "summary": (
            f"在「{dimension}」维度低于 {threshold} 分的学生共 {len(struggling)} 人"
            + (f",最薄弱的是 {struggling[0]['name']}({struggling[0]['score_in_dimension']} 分)"
               if struggling else "")
        ),
    }


def recommend_exam_focus(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """基于学生错题热点,推荐试卷应该重点考察的语法点。
    
    args:
        class_code: str | None, 可选,指定班级(默认综合所有任教班级)
        top_n: int, 默认 3,返回前 N 个最高频错题分类
    """
    db: Session = context["db"]
    teacher_user_id = context["teacher_user_id"]
    
    top_n = max(1, min(int(args.get("top_n", 3)), 10))
    target_code = args.get("class_code")
    
    # 确定要分析的班级
    class_ids = _teacher_class_ids(db, teacher_user_id)
    if not class_ids:
        return {"error": "你没有任教的班级"}
    
    if target_code:
        cls = db.scalar(
            select(Classroom).where(
                Classroom.class_code == target_code,
                Classroom.id.in_(class_ids)
            )
        )
        if not cls:
            return {"error": f"未找到班级 '{target_code}' 或你无权访问"}
        analyze_class_ids = [cls.id]
    else:
        analyze_class_ids = class_ids
    
    # 拿到这些班的学生
    student_ids = list(db.scalars(
        select(ClassStudentRelation.student_id).where(
            ClassStudentRelation.class_id.in_(analyze_class_ids)
        )
    ))
    if not student_ids:
        return {
            "analyzed_class_count": len(analyze_class_ids),
            "top_error_sources": [],
            "summary": "班级暂无学生",
        }
    
    # 按 source 聚合错题数
    rows = db.execute(
        select(
            ErrorBookEntry.source,
            func.count(ErrorBookEntry.id).label("error_count"),
            func.count(func.distinct(ErrorBookEntry.student_id)).label("affected_students"),
        )
        .where(ErrorBookEntry.student_id.in_(student_ids))
        .group_by(ErrorBookEntry.source)
        .order_by(desc("error_count"))
        .limit(top_n)
    ).all()
    
    if not rows:
        return {
            "analyzed_class_count": len(analyze_class_ids),
            "analyzed_student_count": len(student_ids),
            "top_error_sources": [],
            "summary": "暂无错题数据,无法推荐考点",
        }
    
    sources = [
        {
            "source": source,
            "error_count": int(error_count),
            "affected_students": int(affected_students),
            "affected_rate": round(affected_students / len(student_ids) * 100, 1),
        }
        for source, error_count, affected_students in rows
    ]
    
    return {
        "analyzed_class_count": len(analyze_class_ids),
        "analyzed_student_count": len(student_ids),
        "top_error_sources": sources,
        "summary": (
            f"分析 {len(student_ids)} 名学生的错题分布,"
            f"建议试卷重点考察方向(按错题频次排):"
            + ", ".join(f"{s['source']}({s['error_count']} 题)" for s in sources)
        ),
    }