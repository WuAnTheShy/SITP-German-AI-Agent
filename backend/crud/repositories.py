from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.entities import (
    Classroom,
    Exam,
    ExamAssignment,
    Homework,
    HomeworkReview,
    Scenario,
    ScenarioPush,
    Student,
    StudentAbility,
    User,
    # V2 学生端
    ChatMessage,
    ChatScene,
    ChatSession,
    TeacherChatMessage,
    TeacherChatSession,
    ErrorBookCategory,
    ErrorBookEntry,
    Favorite,
    FavoriteCategory,
    GrammarCategory,
    GrammarExercise,
    GrammarSubmission,
    LearningSession,
    ListeningMaterial,
    SpeakingEvaluation,
    StudentKnowledgeMastery,
    StudentVocabCollection,
    Vocabulary,
    WritingSession,
)
from schemas.entities import (
    ClassroomCreate,
    ExamAssignmentCreate,
    ExamCreate,
    HomeworkCreate,
    HomeworkReviewCreate,
    ScenarioCreate,
    ScenarioPushCreate,
    StudentAbilityUpsert,
    StudentCreate,
    UserCreate,
    # V2 学生端
    ChatMessageCreate,
    ChatSessionCreate,
    TeacherChatMessageCreate,
    TeacherChatSessionCreate,
    ErrorBookEntryCreate,
    FavoriteCreate,
    GrammarSubmissionCreate,
    LearningSessionCreate,
    SpeakingEvaluationCreate,
    StudentKnowledgeMasteryUpsert,
    StudentVocabCollectionCreate,
    VocabularyCreate,
    WritingSessionCreate,
)


class UserCRUD:
    @staticmethod
    def create(db: Session, payload: UserCreate) -> User:
        obj = User(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        return db.scalar(select(User).where(User.username == username))

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.scalar(select(User).where(User.id == user_id))

    @staticmethod
    def update_long_memory(db: Session, user_id: int, summary: str) -> None:
        db.execute(
            update(User)
            .where(User.id == user_id)
            .values(long_memory_summary=summary, memory_updated_at=datetime.now(timezone.utc))
        )
        db.commit()


class ClassroomCRUD:
    @staticmethod
    def create(db: Session, payload: ClassroomCreate) -> Classroom:
        obj = Classroom(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_teacher(db: Session, teacher_user_id: int) -> list[Classroom]:
        return list(db.scalars(select(Classroom).where(Classroom.teacher_user_id == teacher_user_id)))

    @staticmethod
    def get_by_code(db: Session, class_code: str) -> Classroom | None:
        return db.scalar(select(Classroom).where(Classroom.class_code == class_code))


class StudentCRUD:
    @staticmethod
    def create(db: Session, payload: StudentCreate) -> Student:
        obj = Student(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_by_uid(db: Session, uid: str) -> Student | None:
        return db.scalar(select(Student).where(Student.uid == uid))

    @staticmethod
    def list_by_class(db: Session, class_id: int) -> list[Student]:
        return list(db.scalars(select(Student).where(Student.class_id == class_id)))

    @staticmethod
    def get_by_id(db: Session, student_id: int) -> Student | None:
        return db.scalar(select(Student).where(Student.id == student_id))

    @staticmethod
    def update_long_memory(db: Session, student_id: int, summary: str) -> None:
        db.execute(
            update(Student)
            .where(Student.id == student_id)
            .values(long_memory_summary=summary, memory_updated_at=datetime.now(timezone.utc))
        )
        db.commit()


class StudentAbilityCRUD:
    @staticmethod
    def upsert(db: Session, payload: StudentAbilityUpsert) -> StudentAbility:
        existing = db.scalar(select(StudentAbility).where(StudentAbility.student_id == payload.student_id))
        if existing:
            for k, v in payload.model_dump().items():
                setattr(existing, k, v)
            db.commit()
            db.refresh(existing)
            return existing

        obj = StudentAbility(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_by_student_id(db: Session, student_id: int) -> StudentAbility | None:
        return db.scalar(select(StudentAbility).where(StudentAbility.student_id == student_id))


class HomeworkCRUD:
    @staticmethod
    def create(db: Session, payload: HomeworkCreate) -> Homework:
        obj = Homework(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_by_id(db: Session, homework_id: int) -> Homework | None:
        return db.scalar(select(Homework).where(Homework.id == homework_id))

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[Homework]:
        return list(db.scalars(select(Homework).where(Homework.student_id == student_id).order_by(Homework.created_at.desc())))

    @staticmethod
    def update_score_feedback(db: Session, homework_id: int, score: float, feedback: str | None) -> Homework | None:
        homework = db.scalar(select(Homework).where(Homework.id == homework_id))
        if not homework:
            return None
        homework.score = score
        if feedback:
            homework.ai_comment = feedback
        db.commit()
        db.refresh(homework)
        return homework


class HomeworkReviewCRUD:
    @staticmethod
    def create(db: Session, payload: HomeworkReviewCreate) -> HomeworkReview:
        obj = HomeworkReview(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


class ScenarioCRUD:
    @staticmethod
    def create(db: Session, payload: ScenarioCreate) -> Scenario:
        obj = Scenario(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_teacher(db: Session, teacher_user_id: int) -> list[Scenario]:
        from sqlalchemy import desc
        return list(db.scalars(
            select(Scenario).where(Scenario.teacher_user_id == teacher_user_id).order_by(desc(Scenario.created_at))
        ))


class ScenarioPushCRUD:
    @staticmethod
    def create(db: Session, payload: ScenarioPushCreate) -> ScenarioPush:
        obj = ScenarioPush(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_or_get(db: Session, payload: ScenarioPushCreate) -> ScenarioPush:
        existing = db.scalar(
            select(ScenarioPush).where(
                ScenarioPush.scenario_id == payload.scenario_id,
                ScenarioPush.student_id == payload.student_id,
            )
        )
        if existing:
            return existing
        return ScenarioPushCRUD.create(db, payload)


class ExamCRUD:
    @staticmethod
    def create(db: Session, payload: ExamCreate) -> Exam:
        obj = Exam(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_teacher(db: Session, teacher_user_id: int) -> list[Exam]:
        from sqlalchemy import desc
        return list(db.scalars(
            select(Exam).where(Exam.teacher_user_id == teacher_user_id).order_by(desc(Exam.created_at))
        ))

    @staticmethod
    def get_by_id(db: Session, exam_id: int) -> Exam | None:
        return db.scalar(select(Exam).where(Exam.id == exam_id))


class ExamAssignmentCRUD:
    @staticmethod
    def create(db: Session, payload: ExamAssignmentCreate) -> ExamAssignment:
        obj = ExamAssignment(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def create_or_get(db: Session, payload: ExamAssignmentCreate) -> ExamAssignment:
        existing = db.scalar(
            select(ExamAssignment).where(
                ExamAssignment.exam_id == payload.exam_id,
                ExamAssignment.student_id == payload.student_id,
            )
        )
        if existing:
            return existing
        return ExamAssignmentCRUD.create(db, payload)


# =====================================================================
# 学生端 CRUD (V2)
# =====================================================================


class ChatSceneCRUD:
    @staticmethod
    def list_all(db: Session) -> list[ChatScene]:
        return list(db.scalars(select(ChatScene).order_by(ChatScene.id)))

    @staticmethod
    def get_by_id(db: Session, scene_id: int) -> ChatScene | None:
        return db.scalar(select(ChatScene).where(ChatScene.id == scene_id))

    @staticmethod
    def get_by_name(db: Session, name: str) -> ChatScene | None:
        return db.scalar(select(ChatScene).where(ChatScene.name == name))


class ChatSessionCRUD:
    @staticmethod
    def create(db: Session, payload: ChatSessionCreate) -> ChatSession:
        obj = ChatSession(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_by_id(db: Session, session_id: int) -> ChatSession | None:
        return db.scalar(select(ChatSession).where(ChatSession.id == session_id))

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[ChatSession]:
        return list(db.scalars(
            select(ChatSession).where(ChatSession.student_id == student_id).order_by(ChatSession.created_at.desc())
        ))

    @staticmethod
    def close_open_for_channel(
        db: Session, student_id: int, scene_id: int | None, scene_name: str | None
    ) -> None:
        now = datetime.now(timezone.utc)
        w = [
            ChatSession.student_id == student_id,
            ChatSession.closed_at.is_(None),
        ]
        if scene_id is not None:
            w.append(ChatSession.scene_id == scene_id)
        else:
            w.append(ChatSession.scene_id.is_(None))
            w.append(ChatSession.scene_name == (scene_name or ""))
        db.execute(update(ChatSession).where(*w).values(closed_at=now))
        db.commit()

    @staticmethod
    def find_open_session(
        db: Session, student_id: int, scene_id: int | None, scene_name: str | None
    ) -> ChatSession | None:
        q = select(ChatSession).where(
            ChatSession.student_id == student_id,
            ChatSession.closed_at.is_(None),
        )
        if scene_id is not None:
            q = q.where(ChatSession.scene_id == scene_id)
        else:
            q = q.where(ChatSession.scene_id.is_(None), ChatSession.scene_name == scene_name)
        q = q.order_by(ChatSession.updated_at.desc()).limit(1)
        return db.scalar(q)

    @staticmethod
    def touch(db: Session, session_id: int) -> None:
        db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        db.commit()

    @staticmethod
    def set_title_if_empty(db: Session, session_id: int, title: str) -> None:
        s = db.scalar(select(ChatSession).where(ChatSession.id == session_id))
        if not s or (s.title and str(s.title).strip()):
            return
        t = (title or "").strip().replace("\n", " ")[:80]
        if not t:
            return
        db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(title=t, updated_at=datetime.now(timezone.utc))
        )
        db.commit()

    @staticmethod
    def reopen(db: Session, session_id: int) -> None:
        """已结束会话再次发消息时重新打开，保留教学留痕"""
        db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(closed_at=None, updated_at=datetime.now(timezone.utc))
        )
        db.commit()

    @staticmethod
    def delete_lobby_session(db: Session, student_id: int, session_id: int, lobby_scene_name: str) -> bool:
        """删除大厅会话及级联消息；返回是否删除成功"""
        s = db.scalar(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.student_id == student_id,
                ChatSession.scene_id.is_(None),
                ChatSession.scene_name == lobby_scene_name,
            )
        )
        if not s:
            return False
        db.delete(s)
        db.commit()
        return True

    @staticmethod
    def delete_scene_session(
        db: Session,
        student_id: int,
        session_id: int,
        scene_id: int,
        scene_name: str,
    ) -> bool:
        """删除某场景通道下的会话及消息"""
        s = db.scalar(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.student_id == student_id,
                ChatSession.scene_id == scene_id,
                ChatSession.scene_name == scene_name,
            )
        )
        if not s:
            return False
        db.delete(s)
        db.commit()
        return True

    @staticmethod
    def list_channel_sessions(
        db: Session,
        student_id: int,
        scene_id: int | None,
        scene_name: str | None,
        limit: int = 30,
    ) -> list[ChatSession]:
        q = select(ChatSession).where(ChatSession.student_id == student_id)
        if scene_id is not None:
            q = q.where(ChatSession.scene_id == scene_id)
        else:
            q = q.where(ChatSession.scene_id.is_(None), ChatSession.scene_name == scene_name)
        q = q.order_by(ChatSession.updated_at.desc()).limit(limit)
        return list(db.scalars(q))

    @staticmethod
    def delete_all_channel_sessions(
        db: Session,
        student_id: int,
        scene_id: int,
        scene_name: str,
    ) -> int:
        """删除该情景下全部会话（清空本情景历史）；返回删除条数"""
        q = select(ChatSession).where(
            ChatSession.student_id == student_id,
            ChatSession.scene_id == scene_id,
            ChatSession.scene_name == scene_name,
        )
        rows = list(db.scalars(q))
        n = len(rows)
        for s in rows:
            db.delete(s)
        if n:
            db.commit()
        return n


class ChatMessageCRUD:
    @staticmethod
    def create(db: Session, payload: ChatMessageCreate) -> ChatMessage:
        obj = ChatMessage(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_session(db: Session, session_id: int) -> list[ChatMessage]:
        return list(db.scalars(
            select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
        ))

    @staticmethod
    def count_by_session(db: Session, session_id: int) -> int:
        from sqlalchemy import func as sa_func
        return db.scalar(
            select(sa_func.count()).select_from(ChatMessage).where(ChatMessage.session_id == session_id)
        ) or 0


class TeacherChatSessionCRUD:
    @staticmethod
    def create(db: Session, payload: TeacherChatSessionCreate) -> TeacherChatSession:
        obj = TeacherChatSession(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_by_id(db: Session, session_id: int) -> TeacherChatSession | None:
        return db.scalar(select(TeacherChatSession).where(TeacherChatSession.id == session_id))

    @staticmethod
    def close_open_for_user(db: Session, user_id: int) -> None:
        now = datetime.now(timezone.utc)
        db.execute(
            update(TeacherChatSession)
            .where(TeacherChatSession.user_id == user_id, TeacherChatSession.closed_at.is_(None))
            .values(closed_at=now)
        )
        db.commit()

    @staticmethod
    def find_open_session(db: Session, user_id: int) -> TeacherChatSession | None:
        return db.scalar(
            select(TeacherChatSession)
            .where(TeacherChatSession.user_id == user_id, TeacherChatSession.closed_at.is_(None))
            .order_by(TeacherChatSession.updated_at.desc())
            .limit(1)
        )

    @staticmethod
    def touch(db: Session, session_id: int) -> None:
        db.execute(
            update(TeacherChatSession)
            .where(TeacherChatSession.id == session_id)
            .values(updated_at=datetime.now(timezone.utc))
        )
        db.commit()

    @staticmethod
    def list_by_user(db: Session, user_id: int, limit: int = 30) -> list[TeacherChatSession]:
        return list(
            db.scalars(
                select(TeacherChatSession)
                .where(TeacherChatSession.user_id == user_id)
                .order_by(TeacherChatSession.updated_at.desc())
                .limit(limit)
            )
        )


class TeacherChatMessageCRUD:
    @staticmethod
    def create(db: Session, payload: TeacherChatMessageCreate) -> TeacherChatMessage:
        obj = TeacherChatMessage(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_session(db: Session, session_id: int) -> list[TeacherChatMessage]:
        return list(
            db.scalars(
                select(TeacherChatMessage)
                .where(TeacherChatMessage.session_id == session_id)
                .order_by(TeacherChatMessage.created_at)
            )
        )


class VocabularyCRUD:
    @staticmethod
    def create(db: Session, payload: VocabularyCreate) -> Vocabulary:
        obj = Vocabulary(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_all(db: Session, level: str | None = None, topic: str | None = None) -> list[Vocabulary]:
        stmt = select(Vocabulary)
        if level:
            stmt = stmt.where(Vocabulary.level == level)
        if topic:
            stmt = stmt.where(Vocabulary.topic == topic)
        return list(db.scalars(stmt.order_by(Vocabulary.id)))

    @staticmethod
    def get_by_id(db: Session, vocab_id: int) -> Vocabulary | None:
        return db.scalar(select(Vocabulary).where(Vocabulary.id == vocab_id))


class StudentVocabCollectionCRUD:
    @staticmethod
    def collect(db: Session, payload: StudentVocabCollectionCreate) -> StudentVocabCollection:
        existing = db.scalar(
            select(StudentVocabCollection).where(
                StudentVocabCollection.student_id == payload.student_id,
                StudentVocabCollection.vocab_id == payload.vocab_id,
            )
        )
        if existing:
            return existing
        obj = StudentVocabCollection(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def uncollect(db: Session, student_id: int, vocab_id: int) -> bool:
        obj = db.scalar(
            select(StudentVocabCollection).where(
                StudentVocabCollection.student_id == student_id,
                StudentVocabCollection.vocab_id == vocab_id,
            )
        )
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[StudentVocabCollection]:
        return list(db.scalars(
            select(StudentVocabCollection).where(StudentVocabCollection.student_id == student_id)
        ))

    @staticmethod
    def is_collected(db: Session, student_id: int, vocab_id: int) -> bool:
        return db.scalar(
            select(StudentVocabCollection).where(
                StudentVocabCollection.student_id == student_id,
                StudentVocabCollection.vocab_id == vocab_id,
            )
        ) is not None


class GrammarCategoryCRUD:
    @staticmethod
    def list_all(db: Session) -> list[GrammarCategory]:
        return list(db.scalars(select(GrammarCategory).order_by(GrammarCategory.id)))

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> GrammarCategory | None:
        return db.scalar(select(GrammarCategory).where(GrammarCategory.id == category_id))


class GrammarExerciseCRUD:
    @staticmethod
    def list_by_category(db: Session, category_id: int) -> list[GrammarExercise]:
        return list(db.scalars(
            select(GrammarExercise).where(GrammarExercise.category_id == category_id).order_by(GrammarExercise.id)
        ))

    @staticmethod
    def get_by_id(db: Session, exercise_id: int) -> GrammarExercise | None:
        return db.scalar(select(GrammarExercise).where(GrammarExercise.id == exercise_id))


class GrammarSubmissionCRUD:
    @staticmethod
    def create(db: Session, payload: GrammarSubmissionCreate) -> GrammarSubmission:
        obj = GrammarSubmission(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[GrammarSubmission]:
        return list(db.scalars(
            select(GrammarSubmission).where(GrammarSubmission.student_id == student_id).order_by(GrammarSubmission.submitted_at.desc())
        ))


class ListeningMaterialCRUD:
    @staticmethod
    def list_all(db: Session, level: str | None = None) -> list[ListeningMaterial]:
        stmt = select(ListeningMaterial)
        if level:
            stmt = stmt.where(ListeningMaterial.level == level)
        return list(db.scalars(stmt.order_by(ListeningMaterial.id)))

    @staticmethod
    def get_by_id(db: Session, material_id: int) -> ListeningMaterial | None:
        return db.scalar(select(ListeningMaterial).where(ListeningMaterial.id == material_id))


class SpeakingEvaluationCRUD:
    @staticmethod
    def create(db: Session, payload: SpeakingEvaluationCreate) -> SpeakingEvaluation:
        obj = SpeakingEvaluation(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[SpeakingEvaluation]:
        return list(db.scalars(
            select(SpeakingEvaluation).where(SpeakingEvaluation.student_id == student_id).order_by(SpeakingEvaluation.evaluated_at.desc())
        ))


class WritingSessionCRUD:
    @staticmethod
    def create(db: Session, payload: WritingSessionCreate) -> WritingSession:
        obj = WritingSession(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[WritingSession]:
        return list(db.scalars(
            select(WritingSession).where(WritingSession.student_id == student_id).order_by(WritingSession.created_at.desc())
        ))


class ErrorBookCategoryCRUD:
    @staticmethod
    def list_all(db: Session) -> list[ErrorBookCategory]:
        return list(db.scalars(select(ErrorBookCategory).order_by(ErrorBookCategory.id)))

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> ErrorBookCategory | None:
        return db.scalar(select(ErrorBookCategory).where(ErrorBookCategory.id == category_id))


class ErrorBookEntryCRUD:
    @staticmethod
    def create(db: Session, payload: ErrorBookEntryCreate) -> ErrorBookEntry:
        obj = ErrorBookEntry(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_student_and_category(db: Session, student_id: int, category_id: int) -> list[ErrorBookEntry]:
        return list(db.scalars(
            select(ErrorBookEntry).where(
                ErrorBookEntry.student_id == student_id,
                ErrorBookEntry.category_id == category_id,
                ErrorBookEntry.is_mastered == False,  # noqa: E712
            ).order_by(ErrorBookEntry.created_at.desc())
        ))

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[ErrorBookEntry]:
        return list(db.scalars(
            select(ErrorBookEntry).where(
                ErrorBookEntry.student_id == student_id,
                ErrorBookEntry.is_mastered == False,  # noqa: E712
            ).order_by(ErrorBookEntry.created_at.desc())
        ))

    @staticmethod
    def get_by_id(db: Session, entry_id: int) -> ErrorBookEntry | None:
        return db.scalar(select(ErrorBookEntry).where(ErrorBookEntry.id == entry_id))

    @staticmethod
    def mark_mastered(db: Session, entry_id: int) -> ErrorBookEntry | None:
        entry = db.scalar(select(ErrorBookEntry).where(ErrorBookEntry.id == entry_id))
        if entry:
            entry.is_mastered = True
            db.commit()
            db.refresh(entry)
        return entry

    @staticmethod
    def delete(db: Session, entry_id: int) -> bool:
        entry = db.scalar(select(ErrorBookEntry).where(ErrorBookEntry.id == entry_id))
        if entry:
            db.delete(entry)
            db.commit()
            return True
        return False

    @staticmethod
    def count_by_category(db: Session, student_id: int) -> list[dict]:
        """返回每个分类的未掌握错题数 [{category_id, category_name, count}]"""
        from sqlalchemy import func as sa_func
        rows = db.execute(
            select(
                ErrorBookCategory.id,
                ErrorBookCategory.name,
                sa_func.count(ErrorBookEntry.id).label("cnt"),
            )
            .outerjoin(ErrorBookEntry, (ErrorBookEntry.category_id == ErrorBookCategory.id) & (ErrorBookEntry.student_id == student_id) & (ErrorBookEntry.is_mastered == False))  # noqa: E712
            .group_by(ErrorBookCategory.id, ErrorBookCategory.name)
            .order_by(ErrorBookCategory.id)
        ).all()
        return [{"id": r.id, "name": r.name, "count": r.cnt} for r in rows]


class FavoriteCategoryCRUD:
    @staticmethod
    def list_all(db: Session) -> list[FavoriteCategory]:
        return list(db.scalars(select(FavoriteCategory).order_by(FavoriteCategory.id)))

    @staticmethod
    def get_by_type(db: Session, fav_type: str) -> FavoriteCategory | None:
        return db.scalar(select(FavoriteCategory).where(FavoriteCategory.type == fav_type))


class FavoriteCRUD:
    @staticmethod
    def create(db: Session, payload: FavoriteCreate) -> Favorite:
        obj = Favorite(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_student_and_category(db: Session, student_id: int, category_id: int) -> list[Favorite]:
        return list(db.scalars(
            select(Favorite).where(
                Favorite.student_id == student_id,
                Favorite.category_id == category_id,
            ).order_by(Favorite.created_at.desc())
        ))

    @staticmethod
    def list_by_student_and_type(db: Session, student_id: int, fav_type: str) -> list[Favorite]:
        return list(db.scalars(
            select(Favorite)
            .join(FavoriteCategory, Favorite.category_id == FavoriteCategory.id)
            .where(Favorite.student_id == student_id, FavoriteCategory.type == fav_type)
            .order_by(Favorite.created_at.desc())
        ))

    @staticmethod
    def get_by_id(db: Session, fav_id: int) -> Favorite | None:
        return db.scalar(select(Favorite).where(Favorite.id == fav_id))

    @staticmethod
    def delete(db: Session, fav_id: int) -> bool:
        obj = db.scalar(select(Favorite).where(Favorite.id == fav_id))
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False


class LearningSessionCRUD:
    @staticmethod
    def create(db: Session, payload: LearningSessionCreate) -> LearningSession:
        data = payload.model_dump()
        if data.get("session_date") is None:
            from datetime import date
            data["session_date"] = date.today()
        obj = LearningSession(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[LearningSession]:
        return list(db.scalars(
            select(LearningSession).where(LearningSession.student_id == student_id).order_by(LearningSession.session_date.desc())
        ))

    @staticmethod
    def total_minutes(db: Session, student_id: int) -> int:
        from sqlalchemy import func as sa_func
        result = db.scalar(
            select(sa_func.coalesce(sa_func.sum(LearningSession.duration_minutes), 0))
            .where(LearningSession.student_id == student_id)
        )
        return int(result)

    @staticmethod
    def week_minutes(db: Session, student_id: int) -> int:
        from datetime import date, timedelta
        from sqlalchemy import func as sa_func
        week_start = date.today() - timedelta(days=date.today().weekday())
        result = db.scalar(
            select(sa_func.coalesce(sa_func.sum(LearningSession.duration_minutes), 0))
            .where(LearningSession.student_id == student_id, LearningSession.session_date >= week_start)
        )
        return int(result)


class StudentKnowledgeMasteryCRUD:
    @staticmethod
    def upsert(db: Session, payload: StudentKnowledgeMasteryUpsert) -> StudentKnowledgeMastery:
        existing = db.scalar(
            select(StudentKnowledgeMastery).where(
                StudentKnowledgeMastery.student_id == payload.student_id,
                StudentKnowledgeMastery.knowledge_name == payload.knowledge_name,
            )
        )
        if existing:
            existing.mastery_level = payload.mastery_level
            db.commit()
            db.refresh(existing)
            return existing
        obj = StudentKnowledgeMastery(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def list_by_student(db: Session, student_id: int) -> list[StudentKnowledgeMastery]:
        return list(db.scalars(
            select(StudentKnowledgeMastery).where(StudentKnowledgeMastery.student_id == student_id).order_by(StudentKnowledgeMastery.id)
        ))
