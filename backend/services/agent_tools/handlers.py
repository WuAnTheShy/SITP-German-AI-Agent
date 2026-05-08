"""Agent 工具的实际实现。

每个 handler 接收两个参数：
  args: dict —— Qwen 解析出来的参数（来自 tool_calls.arguments）
  context: dict —— 调用方信息（student_id、db session 等）

返回值会被 JSON 序列化后发回给 Qwen。
"""
import logging
import json
from services.llm import ai_json
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

from services.agent_tools.schemas import (
    StudentProfileResult,
    AbilityResult,
    HomeworksResult,
    HomeworkItem,
    ClassOverviewResult,
    ClassOverviewItem,
    StudentByUidResult,
    WritingEvaluationResult,
    WritingScores,
    GrammarError,
    VocabularySuggestion,
    RewriteDemo,
)

logger = logging.getLogger(__name__)


def _generate_via_llm_json(
    prompt: str,
    expected_key: str,
    min_items: int = 1,
) -> tuple[list[dict] | None, str | None]:
    """通用工具:用 LLM 生成 JSON 数组并校验。
    
    被 AI 生成类工具(题/作文题/试卷)复用。
    
    Args:
        prompt: 给 LLM 的指令(必须要求 JSON 输出)
        expected_key: 期望返回 JSON 的顶层 key(如 'exercises'/'topics'/'questions')
        min_items: 最少需要多少项,少于此数视为失败
    
    Returns:
        (items, error_msg) 二元组:
          - 成功: (items_list, None)
          - 失败: (None, error_msg)
    """
    from services.llm import ai_json
    
    try:
        result = ai_json(prompt)
    except Exception as e:
        logger.error(f"_generate_via_llm_json LLM 调用失败: {type(e).__name__}: {e}")
        return None, "AI 服务暂时不可用,请稍后重试"
    
    if not result or not isinstance(result, dict):
        return None, "AI 返回格式异常(非 dict)"
    
    items = result.get(expected_key)
    if not isinstance(items, list) or len(items) < min_items:
        return None, f"AI 未生成有效 {expected_key}(返回 {len(items) if isinstance(items, list) else 0} 项)"
    
    return items, None

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

    return StudentProfileResult(
        student_id=student.id,
        name=student.name,
        uid=student.uid,
        class_name=class_name,
        weak_point=student.weak_point,
        overall_score=float(student.overall_score) if student.overall_score is not None else None,
        active_score=student.active_score,
    ).model_dump()


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

    return AbilityResult(
        listening=ability.listening,
        speaking=ability.speaking,
        reading=ability.reading,
        writing=ability.writing,
        weakest_dimension=weakest,
        weakest_score=scores[weakest],
        strongest_dimension=strongest,
        strongest_score=scores[strongest],
        weak_point=student.weak_point if student else None,
        ai_diagnosis=ability.ai_diagnosis,
    ).model_dump()

    # return {
    #     "listening": ability.listening,
    #     "speaking": ability.speaking,
    #     "reading": ability.reading,
    #     "writing": ability.writing,
    #     "weakest_dimension": weakest,
    #     "weakest_score": scores[weakest],
    #     "strongest_dimension": strongest,
    #     "strongest_score": scores[strongest],
    #     "weak_point": student.weak_point if student else None,  # 学生表里的薄弱点描述
    #     "ai_diagnosis": ability.ai_diagnosis or "暂无 AI 诊断",
    #     "overall_score": float(student.overall_score) if student and student.overall_score is not None else None,
    # }


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

    homework_items = [
        HomeworkItem(
            id=h.id,
            title=h.title or "",
            status=h.status or "未知",
            score=float(h.score) if h.score is not None else None,
            submitted_at=h.submitted_at.isoformat() if h.submitted_at else None,
            feedback=getattr(h, "ai_feedback", None) or getattr(h, "feedback", None),
        )
        for h in homeworks
    ]
    
    return HomeworksResult(
        total_count=len(homeworks),
        completed_count=len(completed),
        pending_count=len(pending),
        average_score=avg_score if avg_score else None,
        homeworks=homework_items,
    ).model_dump()

    # items = [
    #     {
    #         "id": h.id,
    #         "title": h.title,
    #         "status": h.status,
    #         "score": float(h.score) if h.score is not None else None,
    #         "submitted_at": h.submitted_at.isoformat() if h.submitted_at else None,
    #         "ai_comment": (h.ai_comment[:100] + "...") if h.ai_comment and len(h.ai_comment) > 100 else h.ai_comment,
    #     }
    #     for h in homeworks
    # ]

    # return {
    #     "total_count": len(homeworks),
    #     "completed_count": len(completed),
    #     "pending_count": len(pending),
    #     "average_score": avg_score,
    #     "items": items,
    #     "summary": (
    #         f"共 {len(homeworks)} 份作业,已完成 {len(completed)} 份"
    #         + (f",平均分 {avg_score}" if avg_score is not None else "")
    #         + (f",有 {len(pending)} 份待完成" if pending else "")
    #     ),
    # }



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
    
    fallback 策略(v3.1 改进):
    1. 用户指定 category_name → 精确匹配
    2. 学生 weak_point 精确匹配题库分类 → 直接用
    3. weak_point 关键词语义匹配题库分类 → 找最近似的
    4. 都失败 → 退到题库最大分类(并明确告知)
    
    args:
        count: int, 推荐题目数量,默认 5,最大 10
        category_name: str | None, 指定语法分类
    """
    db: Session = context["db"]
    student_id = context["student_id"]
    
    count = max(1, min(int(args.get("count", 5)), 10))
    requested_category = args.get("category_name")
    
    target_category = None
    reason = ""
    fallback_used = False
    
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
        reason = f"按你指定的分类「{target_category.name}」推荐"
    else:
        # 按学生 weak_point 推
        student = db.scalar(select(Student).where(Student.id == student_id))
        weak_point = student.weak_point if student else None
        
        if weak_point:
            # ─── 策略 1: 精确匹配 ───
            target_category = db.scalar(
                select(GrammarCategory).where(GrammarCategory.name == weak_point)
            )
            if target_category:
                reason = f"基于你的薄弱点「{weak_point}」推荐针对性练习"
            else:
                # ─── 策略 2: 关键词语义匹配 ───
                target_category, match_reason = _semantic_match_category(db, weak_point)
                if target_category:
                    reason = f"你的薄弱点「{weak_point}」未在题库分类中,{match_reason}"
                    fallback_used = True
        
        # ─── 策略 3: 都失败,用最大分类 ───
        if not target_category:
            target_category = db.scalar(
                select(GrammarCategory)
                .join(GrammarExercise, GrammarExercise.category_id == GrammarCategory.id)
                .group_by(GrammarCategory.id)
                .order_by(desc(func.count(GrammarExercise.id)))
                .limit(1)
            )
            if weak_point: 
                reason = (
                    f"基于你的薄弱点「{weak_point}」,推荐你练「{target_category.name}」分类——"
                    f"这是题库中题量最丰富的语法点,涵盖面广,适合做综合训练"
                )
            else:
                reason = f"未识别明确的薄弱点,推荐题库最丰富的分类「{target_category.name if target_category else '未知'}」"
                fallback_used = True
    
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
    
    return {
        "recommended_category": target_category.name,
        "reason": reason,
        "count": len(exercises),
        "exercises": [
            {
                "id": e.id,
                "category_id": e.category_id,
                "question": e.question,
                "correct_answer": e.correct_answer,
                "analysis": e.analysis,
            }
            for e in exercises
        ],
    }


# ─── 辅助:weak_point 语义匹配题库分类 ───

# 关键词映射:weak_point 关键词 → 题库分类候选(按相关度排序)
WEAK_POINT_KEYWORD_MAP = {
    "听力": [],  # 题库无听力题,主动返回空让上层 fallback
    "口语": [],  # 题库无口语题
    "阅读": [],  # 题库无阅读题
    "写作": [],  # 题库无写作题
    "动词": ["动词变位", "完成时", "过去式", "情态动词", "被动语态"],
    "变位": ["动词变位", "完成时", "过去式"],
    "时态": ["完成时", "过去式", "现在完成时"],
    "完成时": ["完成时"],
    "名词": ["名词格变化", "名词性别"],
    "格变化": ["名词格变化", "形容词词尾变化"],
    "格": ["名词格变化"],
    "性别": ["名词性别"],
    "形容词": ["形容词词尾变化", "比较级最高级"],
    "比较级": ["比较级最高级"],
    "代词": ["代词使用", "反身代词"],
    "介词": ["介词搭配"],
    "从句": ["从句", "关系从句"],
    "被动": ["被动语态"],
    "虚拟": ["虚拟式"],
    "条件": ["虚拟式"],
}


def  _semantic_match_category(db: Session, weak_point: str):
    """根据 weak_point 关键词匹配题库分类。
    
    Returns:
        (GrammarCategory | None, str): (匹配到的分类, 匹配说明)
    """
    if not weak_point:
        return None, ""
    
    # 取所有题库分类
    all_categories = list(db.scalars(select(GrammarCategory)))
    if not all_categories:
        return None, ""
    
    category_names = {c.name: c for c in all_categories}
    
    # 1) 部分字符匹配:weak_point 包含分类名,或分类名包含 weak_point
    for cat_name, cat in category_names.items():
        if cat_name in weak_point or weak_point in cat_name:
            return cat, f"匹配到近似分类「{cat_name}」(基于关键词重叠)"
    
    # 2) 关键词映射查找
    for keyword, candidate_names in WEAK_POINT_KEYWORD_MAP.items():
        if keyword in weak_point:
            # 找第一个真实存在于题库的候选
            for candidate in candidate_names:
                if candidate in category_names:
                    return category_names[candidate], (
                        f"识别到关键词「{keyword}」,匹配到相关分类「{candidate}」"
                    )
            # 候选都不存在(如"听力"对应空列表),返回 None 让上层 fallback
            return None, ""
    
    return None, ""


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
    class_items = [ClassOverviewItem(**c) for c in overview]
    return ClassOverviewResult(
        total_classes=len(class_items),
        classes=class_items,
        summary=(
            f"共 {len(class_items)} 个班级,"
            + f"总人数 {sum(c.student_count for c in class_items)} 人"
        ),
    ).model_dump()

    # return {
    #     "total_classes": len(overview),
    #     "classes": overview,
    #     "summary": (
    #         f"共 {len(overview)} 个班级,"
    #         + f"总人数 {sum(c['student_count'] for c in overview)} 人"
    #     ),
    # }


def query_student_by_uid(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """教师查询指定学生学情。支持按学号(uid)或姓名查找。
    
    args:
        uid: str | None, 学生学号(如 '2452001')
        name: str | None, 学生姓名(支持模糊匹配,如 '李娜' / '李')
    
    必须至少提供 uid 或 name 之一。如同时提供以 uid 为准。
    
    若按姓名查询且匹配多人,返回 disambiguation 列表(让 LLM 追问选哪个)。
    """
    db: Session = context["db"]
    teacher_user_id = context["teacher_user_id"]
    
    uid = (args.get("uid") or "").strip()
    name = (args.get("name") or "").strip()
    
    if not uid and not name:
        return {"error": "请至少提供 uid(学号)或 name(姓名)之一"}
    
    # 先拿教师管的班级(后续鉴权用,姓名查找也要在这范围内)
    teacher_class_ids = _teacher_class_ids(db, teacher_user_id)
    if not teacher_class_ids:
        return {"error": "你没有任教的班级"}
    
    # ─── 解析学生 ───
    if uid:
        student = db.scalar(select(Student).where(Student.uid == uid))
        if not student:
            return {"error": f"未找到学号 {uid} 对应的学生"}
    else:
        # 按姓名模糊匹配,且只在教师能管的班级内查找
        student_ids_in_classes = list(db.scalars(
            select(ClassStudentRelation.student_id).where(
                ClassStudentRelation.class_id.in_(teacher_class_ids)
            )
        ))
        if not student_ids_in_classes:
            return {"error": "你任教的班级暂无学生"}
        
        candidates = list(db.scalars(
            select(Student)
            .where(
                Student.id.in_(student_ids_in_classes),
                Student.name.like(f"%{name}%"),
            )
        ))
        
        if not candidates:
            return {"error": f"在你任教的班级中未找到姓名包含「{name}」的学生"}
        
        if len(candidates) > 1:
            # 重名情况:返回 disambiguation
            return {
                "ambiguous": True,
                "matched_count": len(candidates),
                "candidates": [
                    {"name": c.name, "uid": c.uid, "student_id": c.id}
                    for c in candidates
                ],
                "advice_to_llm": (
                    f"姓名「{name}」匹配到 {len(candidates)} 个学生,"
                    "请询问教师具体是哪一个(可让教师提供学号),"
                    "或下次调用时传入具体的 uid。"
                ),
            }
        
        student = candidates[0]
    
    # ─── 鉴权:学生班级与教师班级要有交集 ───
    student_class_ids = list(db.scalars(
        select(ClassStudentRelation.class_id).where(
            ClassStudentRelation.student_id == student.id
        )
    ))
    common_class_ids = set(teacher_class_ids) & set(student_class_ids)
    if not common_class_ids:
        return {"error": f"你无权查看学生 {student.name}(不在你任教的班级)"}
    
    cls = db.scalar(select(Classroom).where(Classroom.id == next(iter(common_class_ids))))
    class_name = cls.class_name if cls else None
    
    # ─── 取数据 ───
    ability = db.scalar(
        select(StudentAbility).where(StudentAbility.student_id == student.id)
    )
    recent_homeworks = list(db.scalars(
        select(Homework)
        .where(Homework.student_id == student.id)
        .order_by(desc(Homework.submitted_at).nullsfirst())
        .limit(5)
    ))
    unmastered_errors = db.scalar(
        select(func.count(ErrorBookEntry.id)).where(
            ErrorBookEntry.student_id == student.id,
            ErrorBookEntry.is_mastered == False,
        )
    ) or 0
    
    abilities_dict = (
        {
            "listening": ability.listening,
            "speaking": ability.speaking,
            "reading": ability.reading,
            "writing": ability.writing,
            "ai_diagnosis": ability.ai_diagnosis,
        } if ability else None
    )
    
    return StudentByUidResult(
        student_id=student.id,
        name=student.name,
        uid=student.uid,
        class_name=class_name,
        weak_point=student.weak_point,
        overall_score=float(student.overall_score) if student.overall_score is not None else None,
        active_score=student.active_score,
        abilities=abilities_dict,
        recent_homeworks_count=len(recent_homeworks),
        completed_homeworks_count=sum(1 for h in recent_homeworks if h.status == "已完成"),
        unmastered_errors=int(unmastered_errors),
        recent_homeworks=[
            {
                "title": h.title,
                "status": h.status,
                "score": float(h.score) if h.score is not None else None,
            } for h in recent_homeworks
        ],
    ).model_dump()

    # return {
    #     "student_id": student.id,
    #     "name": student.name,
    #     "uid": student.uid,
    #     "class_name": class_name,
    #     "weak_point": student.weak_point,
    #     "overall_score": float(student.overall_score) if student.overall_score is not None else None,
    #     "active_score": student.active_score,
    #     "abilities": (
    #         {
    #             "listening": ability.listening,
    #             "speaking": ability.speaking,
    #             "reading": ability.reading,
    #             "writing": ability.writing,
    #             "ai_diagnosis": ability.ai_diagnosis,
    #         } if ability else None
    #     ),
    #     "recent_homeworks_count": len(recent_homeworks),
    #     "completed_homeworks_count": sum(1 for h in recent_homeworks if h.status == "已完成"),
    #     "unmastered_errors": int(unmastered_errors),
    #     "recent_homeworks": [
    #         {
    #             "title": h.title,
    #             "status": h.status,
    #             "score": float(h.score) if h.score is not None else None,
    #         } for h in recent_homeworks
    #     ],
    # }


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


def generate_grammar_exercises_with_ai(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """AI 生成语法练习题(教师备课工具)。
    
    与 recommend_grammar_exercises 区别:
    - recommend: 从已有题库随机抽题
    - generate: 用 LLM 实时生成新题(题库没有也能出)
    
    args:
        category: str 必填,语法分类("虚拟式"/"被动语态"等)
        count: int 默认 5,最大 10
        difficulty: str "easy"/"medium"/"hard",默认 "medium"
        save_to_db: bool 默认 False,True 则入库到 grammar_exercises 表
    """
    
    
    db: Session = context["db"]
    
    category = (args.get("category") or "").strip()
    if not category:
        return {"error": "category 参数不能为空,例如'虚拟式'/'被动语态'"}
    
    count = max(1, min(int(args.get("count", 5)), 10))
    difficulty = args.get("difficulty", "medium")
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"
    save_to_db = bool(args.get("save_to_db", False))
    
    # 校验分类是否存在(如果 save_to_db 则必须存在)
    cat_obj = db.scalar(
        select(GrammarCategory).where(GrammarCategory.name == category)
    )
    if save_to_db and not cat_obj:
        available = [c.name for c in db.scalars(select(GrammarCategory)).all()]
        return {
            "error": f"分类'{category}'不存在,无法入库",
            "available_categories": available,
        }
    
    # 难度提示
    difficulty_hint = {
        "easy": "基础水平,A1-A2,词汇简单,语法点单一",
        "medium": "中等水平,B1,词汇常见,可能涉及多个语法点",
        "hard": "进阶水平,B2-C1,词汇较复杂,语法点综合",
    }[difficulty]
    
    # Prompt 设计
    from services.prompts import render_prompt
    prompt = render_prompt(
        "gen_grammar_exercises",
        category=category,
        count=count,
        difficulty_hint=difficulty_hint,
    )
#     prompt = f"""你是德语教师助手,需要生成 {count} 道高质量的德语语法练习题。

# 要求:
# - 语法分类: {category}
# - 难度: {difficulty_hint}
# - 题目形式: 填空题(用 ___ 表示填空位置)
# - 每题必须包含中文翻译辅助理解

# 输出严格的 JSON 格式(不要任何额外文本):
# {{
#   "exercises": [
#     {{
#       "question": "Wenn ich Zeit ___ (haben), würde ich ins Kino gehen.",
#       "translation": "如果我有时间,我会去看电影。",
#       "correct_answer": "hätte",
#       "analysis": "虚拟式 II,与现在事实相反的假设,haben 的虚拟式形式是 hätte。"
#     }}
#   ]
# }}

# 注意:
# - correct_answer 只填空白处的答案,不重复整句
# - analysis 必须是中文,讲清考点
# - 确保所有题目都属于"{category}"分类,不要混入其他语法点
# - 题目难度尽量分散,不要全是同样的句式
# """
    items, error = _generate_via_llm_json(
        prompt=prompt,
        expected_key="exercises",
        min_items=1,
    )
    if error:
        return {"error": error}
    
    # 校验每题字段
    valid_exercises = []
    for ex in items:
        if not isinstance(ex, dict):
            continue
        if not ex.get("question") or not ex.get("correct_answer"):
            continue
        valid_exercises.append({
            "question": str(ex.get("question", "")).strip(),
            "translation": str(ex.get("translation", "")).strip(),
            "correct_answer": str(ex.get("correct_answer", "")).strip(),
            "analysis": str(ex.get("analysis", "")).strip(),
        })
    
    if not valid_exercises:
        return {"error": "AI 生成的题目格式无效"}
    
    # 可选入库
    saved_ids = []
    if save_to_db and cat_obj:
        for ex in valid_exercises:
            new_ex = GrammarExercise(
                category_id=cat_obj.id,
                question=ex["question"],
                correct_answer=ex["correct_answer"],
                analysis=ex["analysis"] or ex.get("translation", ""),
            )
            db.add(new_ex)
        db.commit()
        # 重新查最近入库的题取 ID(简化处理)
        saved = list(db.scalars(
            select(GrammarExercise)
            .where(GrammarExercise.category_id == cat_obj.id)
            .order_by(desc(GrammarExercise.id))
            .limit(len(valid_exercises))
        ))
        saved_ids = [e.id for e in saved]
    
    return {
        "category": category,
        "difficulty": difficulty,
        "count": len(valid_exercises),
        "exercises": valid_exercises,
        "saved_to_db": save_to_db,
        "saved_ids": saved_ids,
        "summary": f"AI 已生成 {len(valid_exercises)} 道{category}({difficulty})题"
                   + (f",已入库 ID: {saved_ids}" if save_to_db else ""),
    }


def generate_writing_topic(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """AI 生成德语写作题(教师备课/学生练习)。
    
    args:
        theme: str 必填,主题方向("校园生活"/"家庭"/"环保"等)
        level: str A1/A2/B1/B2,默认 B1
        count: int 默认 3,最大 5
    """
    theme = (args.get("theme") or "").strip()
    if not theme:
        return {"error": "theme 参数不能为空,例如'校园生活'/'环保'/'未来计划'"}
    
    level = args.get("level", "B1")
    if level not in ("A1", "A2", "B1", "B2", "C1"):
        level = "B1"
    count = max(1, min(int(args.get("count", 3)), 5))

    from services.prompts import render_prompt
    prompt = render_prompt(
        "gen_writing_topic",
        theme=theme,
        level=level,
        count=count,
    )
    
#     prompt = f"""你是德语写作教学助手,需要生成 {count} 个德语写作题。

# 要求:
# - 主题方向: {theme}
# - 难度等级: {level}
# - 每题包含明确的写作要求(字数、人称、要点提示等)

# 输出严格的 JSON(不要任何额外文本):
# {{
#   "topics": [
#     {{
#       "title": "题目标题(德语)",
#       "title_zh": "题目中文翻译",
#       "requirements": "写作要求(中文,清晰说明字数、要点等)",
#       "key_vocabulary": ["示例词1", "示例词2", "示例词3"],
#       "outline_hint": "建议结构提示(中文)"
#     }}
#   ]
# }}

# 注意:
# - 题目应该真实、贴近{theme}主题
# - 字数要求按 {level} 等级合理设定(A1: 30-50 词, B1: 100-150 词, B2: 200-300 词)
# - key_vocabulary 给 5-8 个相关核心词汇
# """
    
    items, error = _generate_via_llm_json(
        prompt=prompt,
        expected_key="topics",
        min_items=1,
    )
    if error:
        return {"error": error}
    
    valid_topics = []
    for t in items:
        if not isinstance(t, dict) or not t.get("title"):
            continue
        valid_topics.append({
            "title": str(t.get("title", "")).strip(),
            "title_zh": str(t.get("title_zh", "")).strip(),
            "requirements": str(t.get("requirements", "")).strip(),
            "key_vocabulary": t.get("key_vocabulary", [])[:10] if isinstance(t.get("key_vocabulary"), list) else [],
            "outline_hint": str(t.get("outline_hint", "")).strip(),
        })

    
    if not valid_topics:
        return {"error": "AI 生成的题目格式无效"}
    
    return {
        "theme": theme,
        "level": level,
        "count": len(valid_topics),
        "topics": valid_topics,
        "summary": f"AI 已生成 {len(valid_topics)} 个'{theme}'主题的{level}级写作题",
    }


def generate_exam_paper(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """AI 生成完整的德语考试卷(教师出卷工具)。
    
    args:
        focus_topics: list[str] 必填,重点考察的内容
        total_score: int 默认 100
        sections_count: int 默认 3,最多 5(简化:不再细分题型分布,LLM 自定)
    """
    focus_topics = args.get("focus_topics") or []
    if not isinstance(focus_topics, list) or not focus_topics:
        return {"error": "focus_topics 参数必须是非空列表,例如 ['虚拟式','被动语态']"}
    
    total_score = int(args.get("total_score", 100))
    sections_count = max(2, min(int(args.get("sections_count", 3)), 5))
    
    topics_str = "、".join(focus_topics[:5])
    
    # 简化的 prompt:减少嵌套层,强调 JSON 结构
    from services.prompts import render_prompt
    prompt = render_prompt(
        "gen_exam_paper",
        topics_str=topics_str,
        total_score=total_score,
        sections_count=sections_count,
    )
#     prompt = f"""生成一份德语考试卷。重点考察: {topics_str}。总分: {total_score}。

# 要求 {sections_count} 个 section,每 section 含 2-3 道题(不要太多)。
# 每题包含: 题型(grammar/vocabulary/translation/writing)、题干(德语)、答案、分值、解析。
# 所有 section 分值之和必须等于 {total_score}。

# 只输出 JSON,不要任何解释文字、不要 markdown 代码块标记。直接以 {{ 开头,以 }} 结尾。

# JSON 格式示例:
# {{
#   "title": "德语周测 - 虚拟式与被动语态",
#   "total_score": {total_score},
#   "duration_minutes": 60,
#   "sections": [
#     {{
#       "section_name": "一、语法填空",
#       "instruction": "在空格处填入正确的形式",
#       "subtotal_score": 30,
#       "questions": [
#         {{"type": "grammar", "question": "Wenn ich Zeit ___ (haben), ginge ich.", "answer": "hätte", "score": 6, "analysis": "虚拟式 II"}}
#       ]
#     }}
#   ]
# }}
# """
    
    # 重试机制:LLM 偶尔输出非严格 JSON,重试 2 次
    last_error = None
    for attempt in range(3):
        try:
            result = ai_json(prompt, max_tokens=4000)
            if result and isinstance(result, dict) and result.get("sections"):
                break
            last_error = "AI 返回格式不符合预期(缺 sections)"
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning(f"generate_exam_paper attempt {attempt + 1}/3 失败: {last_error}")
            result = None
    
    if not result or not isinstance(result, dict):
        return {"error": f"AI 生成失败(已重试 3 次): {last_error}"}
    
    sections = result.get("sections")
    if not isinstance(sections, list) or not sections:
        return {"error": "AI 未生成有效试卷结构(无 sections)"}
    
    # 校验 + 清洗
    valid_sections = []
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        questions = sec.get("questions", [])
        if not isinstance(questions, list):
            continue
        valid_questions = [
            {
                "type": q.get("type", "grammar"),
                "question": str(q.get("question", "")).strip(),
                "answer": str(q.get("answer", "")).strip(),
                "score": int(q.get("score", 0)) if str(q.get("score", "")).replace(".", "").isdigit() else 0,
                "analysis": str(q.get("analysis", "")).strip(),
            }
            for q in questions
            if isinstance(q, dict) and q.get("question")
        ]
        if not valid_questions:
            continue
        valid_sections.append({
            "section_name": str(sec.get("section_name", "")).strip(),
            "instruction": str(sec.get("instruction", "")).strip(),
            "subtotal_score": int(sec.get("subtotal_score", 0)) if str(sec.get("subtotal_score", "")).replace(".", "").isdigit() else 0,
            "questions": valid_questions,
        })
    
    if not valid_sections:
        return {"error": "AI 生成的试卷所有 section 均无效"}
    
    total_questions = sum(len(s["questions"]) for s in valid_sections)
    actual_score = sum(s["subtotal_score"] for s in valid_sections)
    
    return {
        "focus_topics": focus_topics,
        "title": str(result.get("title", "德语考试卷")).strip(),
        "total_score": int(result.get("total_score", total_score)),
        "actual_score_sum": actual_score,
        "duration_minutes": int(result.get("duration_minutes", 60)),
        "sections": valid_sections,
        "section_count": len(valid_sections),
        "total_questions": total_questions,
        "summary": (
            f"已生成《{result.get('title', '德语考试卷')}》:"
            f"{len(valid_sections)} 个 section,共 {total_questions} 道题,标称总分 {total_score}"
            + (f"(实际分值之和 {actual_score} 与标称不符,建议人工核对)" if actual_score != total_score else "")
        ),
    }



def evaluate_student_writing(args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """对学生作文进行 AI 多维评估(语法/词汇/结构/切题)。
    
    args:
        text: str 必填,学生作文原文
        level: str A1/A2/B1/B2,默认 B1
        topic: str | None 可选,写作题目(用于判断是否切题)
    """
    from services.prompts import render_prompt
    
    text = (args.get("text") or "").strip()
    if not text:
        return {"error": "text 参数不能为空,请提供学生作文原文"}
    
    if len(text) < 30:
        return {"error": "作文过短(< 30 字符),无法做有意义的评估,请确认完整提交"}
    
    if len(text) > 3000:
        return {"error": "作文过长(> 3000 字符),请截取核心段落"}
    
    level = args.get("level", "B1")
    if level not in ("A1", "A2", "B1", "B2", "C1"):
        level = "B1"
    
    topic = args.get("topic", "")
    topic_hint = topic if topic else "未指定题目,请基于内容判断"
    
    prompt = render_prompt(
        "evaluate_writing",
        level=level,
        topic_hint=topic_hint,
        text=text,
    )
    
    # 重试机制(LLM 多维输出偶尔格式跑偏)
    last_error = None
    result = None
    for attempt in range(3):
        try:
            result = ai_json(prompt, max_tokens=3000)
            if result and isinstance(result, dict) and "scores" in result and "overall_score" in result:
                break
            last_error = "AI 返回格式不符合预期(缺 scores/overall_score)"
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning(f"evaluate_student_writing attempt {attempt + 1}/3 失败: {last_error}")
            result = None
    
    if not result or not isinstance(result, dict):
        return {"error": f"AI 评估失败(已重试 3 次): {last_error}"}
    
    # 用 Pydantic 校验输出
    try:
        validated = WritingEvaluationResult(
            overall_score=float(result.get("overall_score", 0)),
            scores=WritingScores(**result.get("scores", {})),
            summary=str(result.get("summary", "")).strip(),
            grammar_errors=[
                GrammarError(**g) for g in result.get("grammar_errors", [])[:5]
                if isinstance(g, dict) and g.get("original")
            ],
            vocabulary_suggestions=[
                VocabularySuggestion(**v) for v in result.get("vocabulary_suggestions", [])[:5]
                if isinstance(v, dict) and v.get("original")
            ],
            structure_feedback=str(result.get("structure_feedback", "")).strip(),
            rewrite_demo=(
                RewriteDemo(**result["rewrite_demo"])
                if isinstance(result.get("rewrite_demo"), dict)
                and result["rewrite_demo"].get("original")
                else None
            ),
            encouragement=str(result.get("encouragement", "")).strip(),
            text_length=len(text),
            level=level,
        )
    except Exception as e:
        logger.error(f"WritingEvaluationResult schema 校验失败: {e}")
        return {
            "error": "AI 评估结果格式异常",
            "_internal": str(e)[:200],
        }
    
    return validated.model_dump()