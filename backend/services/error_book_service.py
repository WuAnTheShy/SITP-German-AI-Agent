"""错题本服务:统一处理错题写入逻辑。"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.entities import ErrorBookEntry, ErrorBookCategory


logger = logging.getLogger(__name__)


def _ensure_default_category_id(db: Session) -> int | None:
    """确保存在默认错题分类'全部',返回其 id。"""
    cat = db.scalar(select(ErrorBookCategory).where(ErrorBookCategory.name == "全部"))
    if cat:
        return cat.id
    cat = ErrorBookCategory(name="全部")
    db.add(cat)
    db.flush()
    return cat.id


class ErrorBookService:
    """错题本写入服务。"""

    @staticmethod
    def record_wrong_answers(
        db: Session,
        student_id: int,
        source: str,
        wrong_questions: list[dict[str, Any]],
        analysis_template: str = "",
    ) -> int:
        """批量写入错题(已存在则更新)。
        
        Args:
            db: 数据库会话
            student_id: 学生 id
            source: 错题来源(例如"试卷测验"、"语法练习")
            wrong_questions: ExamGrader.grade 返回的 wrong_questions 列表
            analysis_template: 解析模板(默认空)
        
        Returns:
            实际新增/更新的错题数量
        """
        if not wrong_questions:
            return 0

        category_id = _ensure_default_category_id(db)
        if not category_id:
            logger.warning("无法获取默认错题分类,跳过错题写入")
            return 0

        count = 0
        for wq in wrong_questions:
            try:
                question_text = wq.get("question", "")
                # 检查是否已有该题的错题记录
                existing = db.scalar(
                    select(ErrorBookEntry).where(
                        (ErrorBookEntry.student_id == student_id)
                        & (ErrorBookEntry.source == source)
                        & (ErrorBookEntry.question == question_text)
                    )
                )
                if existing:
                    # 更新现有错题
                    existing.user_answer = wq.get("user_answer", "")
                    existing.correct_answer = wq.get("correct_answer", "")
                    existing.is_mastered = False
                    db.merge(existing)
                else:
                    # 创建新错题
                    db.add(ErrorBookEntry(
                        student_id=student_id,
                        category_id=category_id,
                        source=source,
                        question=question_text,
                        user_answer=wq.get("user_answer", ""),
                        correct_answer=wq.get("correct_answer", ""),
                        analysis=analysis_template or "请参考正确答案复习。",
                    ))
                count += 1
            except Exception as e:
                logger.warning(f"写入错题失败: {e}")
        return count