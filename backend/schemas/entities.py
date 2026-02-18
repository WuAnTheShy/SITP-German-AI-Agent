from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    password_hash: str
    role: str
    display_name: str


class UserRead(ORMBase):
    id: int
    username: str
    role: str
    display_name: str
    is_active: bool


class ClassroomCreate(BaseModel):
    class_code: str
    class_name: str
    grade: str | None = None
    teacher_user_id: int


class ClassroomRead(ORMBase):
    id: int
    class_code: str
    class_name: str
    grade: str | None = None
    teacher_user_id: int


class StudentCreate(BaseModel):
    uid: str
    user_id: int
    class_id: int
    name: str
    active_score: int = 0
    overall_score: float = 0
    weak_point: str | None = None


class StudentRead(ORMBase):
    id: int
    uid: str
    user_id: int
    class_id: int
    name: str
    active_score: int
    overall_score: float
    weak_point: str | None = None


class StudentAbilityUpsert(BaseModel):
    student_id: int
    listening: int
    speaking: int
    reading: int
    writing: int
    ai_diagnosis: str | None = None


class StudentAbilityRead(ORMBase):
    id: int
    student_id: int
    listening: int
    speaking: int
    reading: int
    writing: int
    ai_diagnosis: str | None = None


class HomeworkCreate(BaseModel):
    student_id: int
    title: str
    status: str = "未提交"
    submitted_at: datetime | None = None
    score: float | None = None
    file_type: str | None = None
    file_url: str | None = None
    file_name: str | None = None
    file_size: str | None = None
    ai_comment: str | None = None


class HomeworkRead(ORMBase):
    id: int
    student_id: int
    title: str
    status: str
    submitted_at: datetime | None = None
    score: float | None = None
    file_type: str | None = None
    file_url: str | None = None
    file_name: str | None = None
    file_size: str | None = None
    ai_comment: str | None = None


class HomeworkReviewCreate(BaseModel):
    homework_id: int
    teacher_user_id: int
    score: float
    feedback: str | None = None


class HomeworkReviewRead(ORMBase):
    id: int
    homework_id: int
    teacher_user_id: int
    score: float
    feedback: str | None = None
    reviewed_at: datetime


class ScenarioCreate(BaseModel):
    scenario_code: str
    teacher_user_id: int
    theme: str
    difficulty: str
    persona: str
    goal_require_perfect_tense: bool = False
    goal_require_b1_vocab: bool = False


class ScenarioRead(ORMBase):
    id: int
    scenario_code: str
    teacher_user_id: int
    theme: str
    difficulty: str
    persona: str
    goal_require_perfect_tense: bool
    goal_require_b1_vocab: bool
    created_at: datetime


class ScenarioPushCreate(BaseModel):
    scenario_id: int
    student_id: int
    push_status: str = "pushed"


class ScenarioPushRead(ORMBase):
    id: int
    scenario_id: int
    student_id: int
    push_status: str
    pushed_at: datetime


class ExamCreate(BaseModel):
    exam_code: str
    teacher_user_id: int
    grammar_items: int
    writing_items: int
    strategy: str
    focus_areas: list[Any] = []


class ExamRead(ORMBase):
    id: int
    exam_code: str
    teacher_user_id: int
    grammar_items: int
    writing_items: int
    strategy: str
    focus_areas: list[Any]
    created_at: datetime


class ExamAssignmentCreate(BaseModel):
    exam_id: int
    student_id: int
    status: str = "assigned"


class ExamAssignmentRead(ORMBase):
    id: int
    exam_id: int
    student_id: int
    assigned_at: datetime
    status: str
