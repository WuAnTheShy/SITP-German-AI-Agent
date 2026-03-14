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
    exam_assignment_id: int | None = None


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
    exam_assignment_id: int | None = None


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
    content: list[Any] = []


class ExamRead(ORMBase):
    id: int
    exam_code: str
    teacher_user_id: int
    grammar_items: int
    writing_items: int
    strategy: str
    focus_areas: list[Any]
    content: list[Any]
    created_at: datetime


class ExamAssignmentCreate(BaseModel):
    exam_id: int
    student_id: int
    status: str = "assigned"
    personalized_content: list[Any] | None = None


class ExamAssignmentRead(ORMBase):
    id: int
    exam_id: int
    student_id: int
    assigned_at: datetime
    status: str
    personalized_content: list[Any] | None = None


# =====================================================================
# 学生端功能 Schema (V2)
# =====================================================================


# ---------- 场景对话 ----------

class ChatSceneRead(ORMBase):
    id: int
    name: str
    description: str | None = None


class ChatSessionCreate(BaseModel):
    student_id: int
    scene_id: int | None = None
    scene_name: str | None = None
    title: str | None = None


class ChatSessionRead(ORMBase):
    id: int
    student_id: int
    scene_id: int | None = None
    scene_name: str | None = None
    title: str | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ChatMessageCreate(BaseModel):
    session_id: int
    role: str
    content: str
    correction: str | None = None


class ChatMessageRead(ORMBase):
    id: int
    session_id: int
    role: str
    content: str
    correction: str | None = None
    created_at: datetime


class TeacherChatSessionCreate(BaseModel):
    user_id: int


class TeacherChatMessageCreate(BaseModel):
    session_id: int
    role: str
    content: str


# ---------- 词汇学习 ----------

class VocabularyCreate(BaseModel):
    german: str
    chinese: str
    example: str | None = None
    level: str = "A1"
    topic: str = "日常通用"


class VocabularyRead(ORMBase):
    id: int
    german: str
    chinese: str
    example: str | None = None
    level: str
    topic: str


class StudentVocabCollectionCreate(BaseModel):
    student_id: int
    vocab_id: int


class StudentVocabCollectionRead(ORMBase):
    id: int
    student_id: int
    vocab_id: int
    collected_at: datetime


# ---------- 语法练习 ----------

class GrammarCategoryRead(ORMBase):
    id: int
    name: str
    description: str | None = None


class GrammarExerciseRead(ORMBase):
    id: int
    category_id: int
    question: str
    correct_answer: str
    analysis: str | None = None


class GrammarSubmissionCreate(BaseModel):
    student_id: int
    exercise_id: int
    user_answer: str
    is_correct: bool
    ai_analysis: str | None = None


class GrammarSubmissionRead(ORMBase):
    id: int
    student_id: int
    exercise_id: int
    user_answer: str
    is_correct: bool
    ai_analysis: str | None = None
    submitted_at: datetime


# ---------- 听说训练 ----------

class ListeningMaterialRead(ORMBase):
    id: int
    title: str
    level: str
    duration: str
    audio_url: str
    script: str | None = None


class SpeakingEvaluationCreate(BaseModel):
    student_id: int
    material_id: int
    audio_url: str | None = None
    total_score: float | None = None
    pronunciation_score: float | None = None
    fluency_score: float | None = None
    intonation_score: float | None = None
    analysis: str | None = None
    suggestion: str | None = None


class SpeakingEvaluationRead(ORMBase):
    id: int
    student_id: int
    material_id: int
    audio_url: str | None = None
    total_score: float | None = None
    pronunciation_score: float | None = None
    fluency_score: float | None = None
    intonation_score: float | None = None
    analysis: str | None = None
    suggestion: str | None = None
    evaluated_at: datetime


# ---------- 写作辅助 ----------

class WritingSessionCreate(BaseModel):
    student_id: int
    session_type: str
    user_text: str
    result_json: dict | None = None


class WritingSessionRead(ORMBase):
    id: int
    student_id: int
    session_type: str
    user_text: str
    result_json: dict | None = None
    created_at: datetime


# ---------- 错题本 ----------

class ErrorBookCategoryRead(ORMBase):
    id: int
    name: str


class ErrorBookEntryCreate(BaseModel):
    student_id: int
    category_id: int
    source: str = "语法练习"
    question: str
    user_answer: str
    correct_answer: str
    analysis: str | None = None


class ErrorBookEntryRead(ORMBase):
    id: int
    student_id: int
    category_id: int
    source: str
    question: str
    user_answer: str
    correct_answer: str
    analysis: str | None = None
    is_mastered: bool


# ---------- 收藏夹 ----------

class FavoriteCategoryRead(ORMBase):
    id: int
    type: str
    name: str


class FavoriteCreate(BaseModel):
    student_id: int
    category_id: int
    content: str
    translate: str | None = None
    rule: str | None = None
    note: str | None = None


class FavoriteRead(ORMBase):
    id: int
    student_id: int
    category_id: int
    content: str
    translate: str | None = None
    rule: str | None = None
    note: str | None = None
    created_at: datetime


# ---------- 学习进度 ----------

class LearningSessionCreate(BaseModel):
    student_id: int
    module: str
    duration_minutes: int = 0
    content: str | None = None
    session_date: datetime | None = None


class LearningSessionRead(ORMBase):
    id: int
    student_id: int
    module: str
    duration_minutes: int
    content: str | None = None
    session_date: datetime
    created_at: datetime


class StudentKnowledgeMasteryUpsert(BaseModel):
    student_id: int
    knowledge_name: str
    mastery_level: str = "一般"


class StudentKnowledgeMasteryRead(ORMBase):
    id: int
    student_id: int
    knowledge_name: str
    mastery_level: str
