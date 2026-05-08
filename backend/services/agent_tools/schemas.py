"""Agent 工具的输出数据契约(Pydantic schema)。

设计原则:
- 用 Pydantic 强类型,字段缺失/类型错误在开发期就被发现
- 不是所有工具都要严格 schema(生成类工具输出灵活)
- schema 命名: <ToolName>Result(返回值) / <ToolName>Args(参数)

使用示例:
    from services.agent_tools.schemas import AbilityResult
    
    def query_my_abilities(args, context) -> dict:
        ability = ...
        return AbilityResult(
            listening=ability.listening,
            speaking=ability.speaking,
            ...
        ).model_dump()
"""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


# ─────────────────────────────────────────────
# 学生工具 schemas
# ─────────────────────────────────────────────

class StudentProfileResult(BaseModel):
    """学生个人档案查询结果。"""
    model_config = ConfigDict(extra="forbid")  # 禁止额外字段,防止拼写错误
    
    student_id: int = Field(description="学生 ID")
    name: str = Field(description="学生姓名")
    uid: str = Field(description="学号")
    class_name: str | None = Field(default=None, description="班级名称")
    weak_point: str | None = Field(default=None, description="AI 诊断的薄弱点")
    overall_score: float | None = Field(default=None, description="综合分数")
    active_score: int | None = Field(default=None, ge=0, le=100, description="活跃度分数")


class AbilityResult(BaseModel):
    """学生四维能力查询结果。"""
    model_config = ConfigDict(extra="forbid")
    
    listening: int = Field(ge=0, le=100, description="听力分数")
    speaking: int = Field(ge=0, le=100, description="口语分数")
    reading: int = Field(ge=0, le=100, description="阅读分数")
    writing: int = Field(ge=0, le=100, description="写作分数")
    weakest_dimension: Literal["listening", "speaking", "reading", "writing"]
    weakest_score: int = Field(ge=0, le=100)
    strongest_dimension: Literal["listening", "speaking", "reading", "writing"]
    strongest_score: int = Field(ge=0, le=100)
    weak_point: str | None = Field(default=None, description="AI 诊断的具体薄弱点描述")
    ai_diagnosis: str | None = Field(default=None, description="AI 学情诊断完整文本")


class HomeworkItem(BaseModel):
    """单条作业信息(嵌套用)。"""
    model_config = ConfigDict(extra="forbid")
    
    id: int
    title: str
    status: str = Field(description="作业状态:已完成/待完成/已批改 等")
    score: float | None = Field(default=None, ge=0)
    submitted_at: str | None = Field(default=None, description="提交时间 ISO 字符串")
    feedback: str | None = Field(default=None, description="教师/AI 反馈")


class HomeworksResult(BaseModel):
    """学生作业列表查询结果。"""
    model_config = ConfigDict(extra="forbid")
    
    total_count: int = Field(ge=0, description="作业总数")
    completed_count: int = Field(ge=0)
    pending_count: int = Field(ge=0)
    average_score: float | None = Field(default=None, ge=0, description="已完成作业的平均分")
    homeworks: list[HomeworkItem]


# ─────────────────────────────────────────────
# 教师工具 schemas
# ─────────────────────────────────────────────

class WeakPointDistribution(BaseModel):
    """薄弱点分布(用于班级总览嵌套)。"""
    model_config = ConfigDict(extra="allow")  # 允许动态键(每个 weak_point 是一个 key)


class ClassOverviewItem(BaseModel):
    """单个班级的总览信息。"""
    model_config = ConfigDict(extra="forbid")
    
    class_id: int
    class_name: str
    class_code: str
    student_count: int = Field(ge=0)
    active_students_7d: int = Field(default=0, ge=0)
    active_rate: float = Field(default=0.0, ge=0, le=100, description="近 7 天活跃率(百分比)")
    avg_listening: float = Field(default=0.0, ge=0, le=100)
    avg_speaking: float = Field(default=0.0, ge=0, le=100)
    avg_reading: float = Field(default=0.0, ge=0, le=100)
    avg_writing: float = Field(default=0.0, ge=0, le=100)
    avg_four_dims: float = Field(default=0.0, ge=0, le=100, description="四维平均")
    weak_point_distribution: dict[str, int] = Field(
        default_factory=dict, description="weak_point → 学生数"
    )


class ClassOverviewResult(BaseModel):
    """班级总览查询结果。"""
    model_config = ConfigDict(extra="forbid")
    
    total_classes: int = Field(ge=0)
    classes: list[ClassOverviewItem]
    summary: str


class StudentByUidResult(BaseModel):
    """按学号查指定学生学情的结果。"""
    model_config = ConfigDict(extra="forbid")
    
    student_id: int
    name: str
    uid: str
    class_name: str | None = None
    weak_point: str | None = None
    overall_score: float | None = None
    active_score: int | None = None
    abilities: dict[str, int | str | None] | None = Field(
        default=None, description="四维能力 + AI 诊断"
    )
    recent_homeworks_count: int = Field(default=0, ge=0)
    completed_homeworks_count: int = Field(default=0, ge=0)
    unmastered_errors: int = Field(default=0, ge=0)
    recent_homeworks: list[dict] = Field(default_factory=list)



# ─────────────────────────────────────────────
# 写作辅助 schemas
# ─────────────────────────────────────────────

class WritingScores(BaseModel):
    """写作四维评分。"""
    model_config = ConfigDict(extra="forbid")
    
    grammar: float = Field(ge=0, le=10, description="语法分(0-10)")
    vocabulary: float = Field(ge=0, le=10, description="词汇分(0-10)")
    structure: float = Field(ge=0, le=10, description="结构分(0-10)")
    relevance: float = Field(ge=0, le=10, description="切题分(0-10)")


class GrammarError(BaseModel):
    """单条语法错误。"""
    model_config = ConfigDict(extra="forbid")
    
    original: str
    issue: str
    correction: str
    explanation: str


class VocabularySuggestion(BaseModel):
    """单条用词建议。"""
    model_config = ConfigDict(extra="forbid")
    
    original: str
    suggested: str
    reason: str


class RewriteDemo(BaseModel):
    """改写示范。"""
    model_config = ConfigDict(extra="forbid")
    
    original: str
    rewritten: str
    explanation: str


class WritingEvaluationResult(BaseModel):
    """学生作文多维评估结果。"""
    model_config = ConfigDict(extra="forbid")
    
    overall_score: float = Field(ge=0, le=10)
    scores: WritingScores
    summary: str
    grammar_errors: list[GrammarError] = Field(default_factory=list)
    vocabulary_suggestions: list[VocabularySuggestion] = Field(default_factory=list)
    structure_feedback: str
    rewrite_demo: RewriteDemo | None = None
    encouragement: str
    
    # 元数据
    text_length: int = Field(ge=0, description="作文字数(粗略统计)")
    level: str = Field(description="评估时使用的学生等级")



# ─────────────────────────────────────────────
# 学习计划 schemas
# ─────────────────────────────────────────────

class LearningTask(BaseModel):
    """单个学习任务。"""
    model_config = ConfigDict(extra="forbid")
    
    order: int = Field(ge=1, description="任务顺序号")
    module: str = Field(description="所属模块,如'听力训练'/'语法练习'/'写作'")
    title: str = Field(description="任务标题(简短)")
    duration_minutes: int = Field(ge=5, le=120, description="预计耗时(分钟)")
    action_steps: list[str] = Field(description="具体动作步骤(2-4 步)")
    rationale: str = Field(description="为什么推荐这个任务(基于学生数据)")


class DailyLearningPlanResult(BaseModel):
    """日学习计划完整输出。"""
    model_config = ConfigDict(extra="forbid")
    
    student_name: str
    plan_date: str = Field(description="计划日期 ISO 字符串")
    
    today_focus: str = Field(description="今日学习重点(基于薄弱点的 1-2 句概括)")
    weak_dimension: str = Field(description="重点改进的能力维度")
    
    tasks: list[LearningTask] = Field(min_length=2, max_length=6)
    total_duration_minutes: int = Field(ge=15, le=240, description="计划总时长")
    
    encouragement: str = Field(description="鼓励语(1-2 句)")
    
    # 元数据(给上层 Agent 看)
    based_on: dict = Field(description="基于的学生数据快照")