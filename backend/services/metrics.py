from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from crud.repositories import LearningSessionCRUD, StudentAbilityCRUD
from models.entities import (
    ChatMessage,
    ChatSession,
    GrammarSubmission,
    Homework,
    SpeakingEvaluation,
    Student,
    StudentVocabCollection,
    WritingSession,
)
from schemas.entities import LearningSessionCreate, StudentAbilityUpsert


def parse_duration_minutes(duration_text: str | None) -> int:
    """解析听力时长文本，兼容 `mm:ss` / `xh` / `xmin`。"""
    if not duration_text:
        return 5
    text = duration_text.strip().lower()
    if ":" in text:
        parts = text.split(":")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            minutes = int(parts[0])
            seconds = int(parts[1])
            return max(1, minutes + (1 if seconds >= 30 else 0))
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return 5
    value = int(digits)
    if "h" in text:
        return max(1, value * 60)
    return max(1, value)


def track_learning_activity(
    db: Session,
    student_id: int,
    module: str,
    duration_minutes: int,
    content: str | None = None,
) -> None:
    """记录学习行为到 learning_sessions，作为后续统计的数据来源。"""
    if duration_minutes <= 0:
        return
    LearningSessionCRUD.create(
        db,
        LearningSessionCreate(
            student_id=student_id,
            module=module,
            duration_minutes=duration_minutes,
            content=content,
            session_date=datetime.now(),
        ),
    )


def compute_student_interaction_minutes(db: Session, student_id: int, days: int = 7) -> int:
    """按会话真实时间跨度统计互动时长，并结合用户发言数做下限保护。"""
    cutoff = datetime.utcnow() - timedelta(days=days)

    rows = db.execute(
        select(
            ChatMessage.session_id,
            func.min(ChatMessage.created_at).label("first_ts"),
            func.max(ChatMessage.created_at).label("last_ts"),
            func.sum(case((ChatMessage.role == "user", 1), else_=0)).label("user_count"),
        )
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .where(
            ChatSession.student_id == student_id,
            ChatMessage.created_at >= cutoff,
        )
        .group_by(ChatMessage.session_id)
    ).all()

    total_minutes = 0
    for _, first_ts, last_ts, user_count in rows:
        if not first_ts or not last_ts:
            continue
        span_minutes = int(max(0, (last_ts - first_ts).total_seconds()) // 60)
        message_floor = int(user_count or 0)
        measured = max(span_minutes, message_floor)
        total_minutes += min(90, measured)

    return total_minutes


def compute_student_active_score(db: Session, student_id: int, days: int = 7) -> int:
    """根据最近学习行为自动计算积极度，范围 0-100。"""
    cutoff = datetime.utcnow() - timedelta(days=days)

    week_minutes = LearningSessionCRUD.week_minutes(db, student_id)
    interaction_minutes = compute_student_interaction_minutes(db, student_id, days=days)

    grammar_cnt = db.scalar(
        select(func.count(GrammarSubmission.id)).where(
            GrammarSubmission.student_id == student_id,
            GrammarSubmission.submitted_at >= cutoff,
        )
    ) or 0
    speaking_cnt = db.scalar(
        select(func.count(SpeakingEvaluation.id)).where(
            SpeakingEvaluation.student_id == student_id,
            SpeakingEvaluation.evaluated_at >= cutoff,
        )
    ) or 0
    writing_cnt = db.scalar(
        select(func.count(WritingSession.id)).where(
            WritingSession.student_id == student_id,
            WritingSession.created_at >= cutoff,
        )
    ) or 0
    homework_cnt = db.scalar(
        select(func.count(Homework.id)).where(
            Homework.student_id == student_id,
            Homework.status == "已完成",
            func.coalesce(Homework.submitted_at, Homework.created_at) >= cutoff,
        )
    ) or 0

    time_score = min(55, week_minutes * 0.65)
    interaction_score = min(25, interaction_minutes * 0.5)
    practice_score = min(20, grammar_cnt * 2 + speaking_cnt * 4 + writing_cnt * 3 + homework_cnt * 3)

    return int(round(min(100, time_score + interaction_score + practice_score)))


def refresh_student_active_score(db: Session, student_id: int, days: int = 7) -> int:
    """刷新并持久化学生积极度，返回最新分值。"""
    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        return 0
    new_score = compute_student_active_score(db, student_id, days=days)
    if student.active_score != new_score:
        student.active_score = new_score
        db.commit()
        db.refresh(student)
    return int(student.active_score)


def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def compute_student_ability_profile(db: Session, student_id: int) -> dict[str, int | str]:
    """基于真实学习行为计算学生德语能力画像。"""
    total_grammar = db.scalar(
        select(func.count(GrammarSubmission.id)).where(GrammarSubmission.student_id == student_id)
    ) or 0
    correct_grammar = db.scalar(
        select(func.count(GrammarSubmission.id)).where(
            GrammarSubmission.student_id == student_id,
            GrammarSubmission.is_correct.is_(True),
        )
    ) or 0
    grammar_acc = (correct_grammar / total_grammar * 100) if total_grammar else 0

    speaking_avg = db.execute(
        select(
            func.avg(SpeakingEvaluation.total_score),
            func.avg(SpeakingEvaluation.pronunciation_score),
            func.avg(SpeakingEvaluation.fluency_score),
            func.avg(SpeakingEvaluation.intonation_score),
        ).where(SpeakingEvaluation.student_id == student_id)
    ).one()
    sp_total = float(speaking_avg[0] or 0)
    sp_pron = float(speaking_avg[1] or 0)
    sp_flu = float(speaking_avg[2] or 0)
    sp_into = float(speaking_avg[3] or 0)

    writing_stats = db.execute(
        select(
            func.count(WritingSession.id),
            func.avg(func.length(WritingSession.user_text)),
        ).where(WritingSession.student_id == student_id)
    ).one()
    writing_cnt = int(writing_stats[0] or 0)
    avg_writing_len = float(writing_stats[1] or 0)

    vocab_cnt = db.scalar(
        select(func.count(StudentVocabCollection.id)).where(StudentVocabCollection.student_id == student_id)
    ) or 0

    chat_user_cnt = db.scalar(
        select(func.count(ChatMessage.id))
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .where(ChatSession.student_id == student_id, ChatMessage.role == "user")
    ) or 0

    homework_avg_score = db.scalar(
        select(func.avg(Homework.score)).where(
            Homework.student_id == student_id,
            Homework.status == "已完成",
            Homework.score.is_not(None),
        )
    )
    homework_avg = float(homework_avg_score or 0)

    listening = _clamp_score(sp_total * 0.45 + sp_pron * 0.30 + sp_into * 0.25)
    speaking = _clamp_score(sp_total * 0.35 + sp_flu * 0.45 + min(100, chat_user_cnt * 2) * 0.20)
    reading = _clamp_score(grammar_acc * 0.60 + min(100, vocab_cnt * 3) * 0.25 + homework_avg * 0.15)
    writing = _clamp_score(min(100, writing_cnt * 8) * 0.40 + min(100, avg_writing_len / 4) * 0.20 + grammar_acc * 0.25 + homework_avg * 0.15)

    if total_grammar == 0 and writing_cnt == 0 and float(sp_total) == 0:
        # 没有行为数据时给出保守初始值，避免 0 分误导
        listening, speaking, reading, writing = 60, 60, 60, 60

    weakest_name, weakest_score = min(
        [
            ("听力", listening),
            ("口语", speaking),
            ("阅读", reading),
            ("写作", writing),
        ],
        key=lambda x: x[1],
    )
    diagnosis = f"系统评估显示当前薄弱项为{weakest_name}（{weakest_score}分），建议优先完成对应专项训练。"
    weak_map = {"听力": "听力理解", "口语": "口语表达", "阅读": "阅读理解", "写作": "写作表达"}

    return {
        "listening": listening,
        "speaking": speaking,
        "reading": reading,
        "writing": writing,
        "diagnosis": diagnosis,
        "weak_point": weak_map.get(weakest_name, "综合能力"),
    }


def refresh_student_performance(db: Session, student_id: int) -> dict[str, float | int | str]:
    """刷新学生综合评分与能力画像。"""
    student = db.scalar(select(Student).where(Student.id == student_id))
    if not student:
        return {"overall_score": 0.0, "weak_point": "暂无"}

    profile = compute_student_ability_profile(db, student_id)
    overall = round(
        profile["listening"] * 0.25
        + profile["speaking"] * 0.30
        + profile["reading"] * 0.20
        + profile["writing"] * 0.25,
        1,
    )

    StudentAbilityCRUD.upsert(
        db,
        StudentAbilityUpsert(
            student_id=student_id,
            listening=int(profile["listening"]),
            speaking=int(profile["speaking"]),
            reading=int(profile["reading"]),
            writing=int(profile["writing"]),
            ai_diagnosis=str(profile["diagnosis"]),
        ),
    )

    student.overall_score = overall
    student.weak_point = str(profile["weak_point"])
    db.commit()
    db.refresh(student)
    return {
        "overall_score": float(student.overall_score),
        "weak_point": student.weak_point or "暂无",
    }


def refresh_student_metrics(db: Session, student_id: int) -> dict[str, float | int | str]:
    """统一刷新积极度、综合评分、能力画像。"""
    active = refresh_student_active_score(db, student_id)
    perf = refresh_student_performance(db, student_id)
    return {
        "active_score": active,
        "overall_score": float(perf.get("overall_score", 0.0)),
        "weak_point": str(perf.get("weak_point", "暂无")),
    }
