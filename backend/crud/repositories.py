from sqlalchemy import select
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
