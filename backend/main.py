import json
import os
from datetime import date, datetime, timedelta, timezone
from statistics import mean
from uuid import uuid4

# load_dotenv 必须在所有读取环境变量的 import 之前调用
# 否则 db/session.py 等模块在 import 时读不到 .env 中的 DATABASE_URL
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.orm import Session

from crud.repositories import (
    ChatMessageCRUD,
    ChatSessionCRUD,
    ClassroomCRUD,
    ErrorBookCategoryCRUD,
    ErrorBookEntryCRUD,
    ExamAssignmentCRUD,
    ExamCRUD,
    FavoriteCategoryCRUD,
    FavoriteCRUD,
    GrammarCategoryCRUD,
    GrammarExerciseCRUD,
    GrammarSubmissionCRUD,
    HomeworkCRUD,
    HomeworkReviewCRUD,
    LearningSessionCRUD,
    ListeningMaterialCRUD,
    ScenarioCRUD,
    ScenarioPushCRUD,
    SpeakingEvaluationCRUD,
    StudentAbilityCRUD,
    StudentCRUD,
    StudentKnowledgeMasteryCRUD,
    StudentVocabCollectionCRUD,
    UserCRUD,
    VocabularyCRUD,
    WritingSessionCRUD,
)
from db.session import get_db
from models.entities import ChatSession as ChatSessionModel
from schemas.entities import (
    ChatMessageCreate,
    ChatSessionCreate,
    ClassroomCreate,
    ErrorBookEntryCreate,
    ExamAssignmentCreate,
    ExamCreate,
    FavoriteCreate,
    GrammarSubmissionCreate,
    HomeworkCreate,
    HomeworkReviewCreate,
    LearningSessionCreate,
    ScenarioCreate,
    ScenarioPushCreate,
    SpeakingEvaluationCreate,
    StudentAbilityUpsert,
    StudentCreate,
    StudentKnowledgeMasteryUpsert,
    StudentVocabCollectionCreate,
    UserCreate,
    VocabularyCreate,
    WritingSessionCreate,
)

# ════════════════════ 1. 环境与 AI 配置 ════════════════════

# ── 代理配置（国内访问 Google API 需要，在 .env 中配置） ──
# 如果 .env 里配了 HTTP_PROXY / HTTPS_PROXY，会自动生效
# 没配则不使用代理（适合国外或已全局代理的环境）
_proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
if _proxy:
    os.environ.setdefault("HTTP_PROXY", _proxy)
    os.environ.setdefault("HTTPS_PROXY", _proxy)
    print(f"代理已启用: {_proxy}")
else:
    print("提示: 未配置代理，如果 Gemini API 连不上请在 .env 中设置 HTTP_PROXY")

if not os.getenv("GOOGLE_API_KEY"):
    print("警告: 未找到 GOOGLE_API_KEY")

# 新版 google-genai SDK 客户端
_gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

_MODEL_ID = "gemini-2.5-flash"

_TEACHER_SYSTEM = (
    "你是一个高级教学AI教研助手，负责协助德语教师分析学情、制定教案和出题等。"
    "请用中文与教师进行沟通，提供专业、基于数据的教学建议和德语教学方案。"
)

_STUDENT_SYSTEM = (
    "你是同济大学的 AI 德语助教，帮助学生学习德语。"
    "回复简洁、准确。除非用户要求中文，否则用德语回答并在括号内给出中文翻译。"
)

# 教师端多轮对话历史（简单内存存储）
_teacher_chat_history: list[types.Content] = []
# 学生端多轮对话历史（简单内存存储）
_student_chat_history: list[types.Content] = []

app = FastAPI()

# ════════════════════ 2. 跨域中间件 ════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ════════════════════ 3. 公共数据模型与工具函数 ════════════════════

class ChatRequest(BaseModel):
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ScenarioPublishRequest(BaseModel):
    config: dict
    timestamp: str | None = None


class ExamGenerateRequest(BaseModel):
    config: dict
    timestamp: str | None = None


class HomeworkSaveRequest(BaseModel):
    homeworkId: int
    score: float
    feedback: str | None = None
    timestamp: str | None = None


class PushSchemeRequest(BaseModel):
    studentId: str
    name: str | None = None
    diagnosis: str | None = None
    timestamp: str | None = None


def ok(data=None, message: str = "success"):
    return {"code": 200, "message": message, "data": data}


def fail(message: str, code: int = 500):
    return {"code": code, "message": message, "data": None}


def to_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


# ════════════════════ 3.5 权限校验依赖 ════════════════════


def require_teacher(req: Request, db: Session = Depends(get_db)):
    """从 Authorization 头解析教师身份，失败则抛 401"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer teacher-token-"):
        parts = auth.replace("Bearer ", "").split("-")
        # token 格式: teacher-token-{user_id}-{random}
        if len(parts) >= 4:
            try:
                user_id = int(parts[2])
            except ValueError:
                raise HTTPException(status_code=401, detail="无效的教师令牌")
            user = UserCRUD.get_by_id(db, user_id)
            if user and user.role == "teacher":
                return user
    raise HTTPException(status_code=401, detail="未登录或令牌无效，请重新登录")


def require_student(req: Request, db: Session = Depends(get_db)):
    """从 Authorization 头解析学生身份，失败则抛 401"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer student-token-"):
        parts = auth.replace("Bearer ", "").split("-")
        # token 格式: student-token-{uid}-{random}
        if len(parts) >= 4:
            uid = parts[2]
            s = StudentCRUD.get_by_uid(db, uid)
            if s:
                return s
    raise HTTPException(status_code=401, detail="未登录或令牌无效，请重新登录")


# ════════════════════ 4. 学生端辅助函数与请求模型 ════════════════════


def _current_student(req: Request, db: Session):
    """从 Authorization 头解析学生，无有效 token 返回 None"""
    auth = req.headers.get("authorization", "")
    if auth.startswith("Bearer student-token-"):
        parts = auth.replace("Bearer ", "").split("-")
        if len(parts) >= 4:
            uid = parts[2]
            s = StudentCRUD.get_by_uid(db, uid)
            if s:
                return s
    return None


def _ai_text(prompt: str, fallback: str = "") -> str:
    """安全调用 Gemini 返回纯文本"""
    try:
        resp = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_STUDENT_SYSTEM,
            ),
        )
        return resp.text.strip()
    except Exception as e:
        print(f"[AI] {e}")
        return fallback


def _ai_json(prompt: str, fallback=None):
    """调用 Gemini 并尝试解析 JSON，失败返回 fallback"""
    try:
        resp = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_STUDENT_SYSTEM,
            ),
        )
        text = resp.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())
    except Exception as e:
        print(f"[AI JSON] {e}")
        return fallback


def _match_error_category(grammar_name: str, error_cats: dict[str, int]) -> int | None:
    """将语法分类名模糊映射到错题本分类"""
    mapping = {
        "动词变位": "动词变位", "Konjugation": "动词变位",
        "名词": "名词格变化", "Deklination": "名词格变化",
        "完成时": "时态错误", "Perfekt": "时态错误",
        "被动": "时态错误", "Passiv": "时态错误",
        "虚拟": "时态错误", "Konjunktiv": "时态错误",
        "句序": "句序错误", "介词": "介词搭配",
    }
    for keyword, cat_name in mapping.items():
        if keyword in grammar_name and cat_name in error_cats:
            return error_cats[cat_name]
    return next(iter(error_cats.values()), None) if error_cats else None


def _get_or_create_session(db: Session, student_id: int, scene_id: int | None, scene_name: str):
    """同一学生 + 同一场景(或自由对话) 当天复用会话，保持多轮对话历史"""
    today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)

    if scene_id is not None:
        stmt = (
            select(ChatSessionModel)
            .where(
                ChatSessionModel.student_id == student_id,
                ChatSessionModel.scene_id == scene_id,
                ChatSessionModel.created_at >= today_start,
            )
            .order_by(ChatSessionModel.created_at.desc())
            .limit(1)
        )
    else:
        # 自由对话模式：按 student + scene_name + 当天 复用会话
        stmt = (
            select(ChatSessionModel)
            .where(
                ChatSessionModel.student_id == student_id,
                ChatSessionModel.scene_id.is_(None),
                ChatSessionModel.scene_name == scene_name,
                ChatSessionModel.created_at >= today_start,
            )
            .order_by(ChatSessionModel.created_at.desc())
            .limit(1)
        )

    existing = db.scalar(stmt)
    if existing:
        return existing

    return ChatSessionCRUD.create(
        db, ChatSessionCreate(student_id=student_id, scene_id=scene_id, scene_name=scene_name)
    )


# 学生端请求体模型
class StudentLoginReq(BaseModel):
    username: str
    password: str


class SceneChatReq(BaseModel):
    sceneId: int | None = None
    sceneName: str | None = None
    userMessage: str


class VocabCollectReq(BaseModel):
    vocabId: int
    isCollect: bool


class VocabGenerateReq(BaseModel):
    level: str = "A1"
    topic: str = "日常通用"


class GrammarAnswerItem(BaseModel):
    exerciseId: int
    userAnswer: str


class GrammarSubmitReq(BaseModel):
    categoryId: int
    answers: list[GrammarAnswerItem]


class SpeakingEvalReq(BaseModel):
    materialId: int
    audioUrl: str | None = None


class WritingReq(BaseModel):
    userText: str


class ErrorReviewReq(BaseModel):
    categoryId: int
    categoryName: str | None = None


class ErrorMasterReq(BaseModel):
    errorId: int
    categoryId: int | None = None


class FavAIExtendReq(BaseModel):
    content: str
    type: str


# ════════════════════ 5. 教师端 Demo 数据初始化 ════════════════════


def _ensure_demo_data(db: Session):
    teacher = UserCRUD.get_by_username(db, "t_zhang")
    if not teacher:
        teacher = UserCRUD.create(
            db,
            UserCreate(
                username="t_zhang",
                password_hash="demo_hash_teacher",
                role="teacher",
                display_name="张老师",
            ),
        )

    classroom = ClassroomCRUD.get_by_code(db, "SE-2026-4")
    if not classroom:
        classroom = ClassroomCRUD.create(
            db,
            ClassroomCreate(
                class_code="SE-2026-4",
                class_name="软件工程(四)班",
                grade="2026",
                teacher_user_id=teacher.id,
            ),
        )

    def ensure_student(uid: str, username: str, name: str, active: int, overall: float, weak: str):
        stu_user = UserCRUD.get_by_username(db, username)
        if not stu_user:
            stu_user = UserCRUD.create(
                db,
                UserCreate(
                    username=username,
                    password_hash="demo_hash_student",
                    role="student",
                    display_name=name,
                ),
            )

        student = StudentCRUD.get_by_uid(db, uid)
        if not student:
            student = StudentCRUD.create(
                db,
                StudentCreate(
                    uid=uid,
                    user_id=stu_user.id,
                    class_id=classroom.id,
                    name=name,
                    active_score=active,
                    overall_score=overall,
                    weak_point=weak,
                ),
            )

        StudentAbilityCRUD.upsert(
            db,
            StudentAbilityUpsert(
                student_id=student.id,
                listening=min(100, active + 1),
                speaking=max(0, active - 2),
                reading=min(100, int(overall)),
                writing=max(0, int(overall - 3)),
                ai_diagnosis=f"{name}在{weak}方面需要重点强化。",
            ),
        )

        if not HomeworkCRUD.list_by_student(db, student.id):
            HomeworkCRUD.create(
                db,
                HomeworkCreate(
                    student_id=student.id,
                    title="德语写作作业-第3周",
                    status="已完成",
                    submitted_at=datetime.utcnow(),
                    score=to_float(overall),
                    file_type="text",
                    file_url=f"https://example.com/{uid}/week3.txt",
                    file_name=f"{uid}-week3.txt",
                    file_size="24 KB",
                    ai_comment="结构清晰，建议继续优化复杂句表达。",
                ),
            )

    ensure_student("2452001", "s_li", "李娜", 88, 91.5, "虚拟式")
    ensure_student("2452002", "s_wang", "王强", 64, 78.0, "被动语态")

    return teacher, classroom


# ════════════════════ 6. 教师端 API ════════════════════


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, req: Request = None, db: Session = Depends(get_db)):
    # 教师端 AI 对话需要教师权限
    require_teacher(req, db)
    print(f"收到前端消息: {request.message}")
    try:
        global _teacher_chat_history
        _teacher_chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=request.message)]))
        response = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=_teacher_chat_history,
            config=types.GenerateContentConfig(
                system_instruction=_TEACHER_SYSTEM,
            ),
        )
        _teacher_chat_history.append(types.Content(role="model", parts=[types.Part.from_text(text=response.text)]))
        return {"reply": response.text}
    except Exception as e:
        print(f"Gemini调用失败: {e}")
        return {"reply": "Entschuldigung, ich habe ein Problem. (AI出错了)"}


@app.post("/api/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        _ensure_demo_data(db)

        user = UserCRUD.get_by_username(db, request.username)
        if not user:
            return fail("用户不存在，请检查工号后重试", 401)

        if user.role != "teacher":
            return fail("该账号不是教师账号", 403)

        if user.password_hash != request.password:
            return fail("密码错误，请重新输入", 401)

        token = f"teacher-token-{user.id}-{uuid4().hex[:8]}"
        user_info = {"id": user.username, "name": user.display_name, "role": user.role}
        return {
            "code": 200,
            "message": "登录成功",
            "token": token,
            "user": user_info,
            "data": {"token": token, "user": user_info},
        }
    except Exception as e:
        return fail(f"登录失败: {e}")


@app.get("/api/teacher/dashboard")
def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        require_teacher(request, db)
        teacher, classroom = _ensure_demo_data(db)
        students = StudentCRUD.list_by_class(db, classroom.id)

        all_homeworks = []
        for s in students:
            all_homeworks.extend(HomeworkCRUD.list_by_student(db, s.id))

        avg_score = round(mean([to_float(s.overall_score) for s in students]), 1) if students else 0
        completion_count = sum(1 for h in all_homeworks if h.status == "已完成")
        completion_rate = round((completion_count / len(all_homeworks)) * 100) if all_homeworks else 0

        payload = {
            "teacherName": teacher.display_name,
            "className": classroom.class_name,
            "pendingTasks": 3,
            "stats": {
                "totalStudents": len(students),
                "totalStudentsTrend": "+0",
                "avgDuration": 12.5,
                "avgDurationTrend": "↑ 2%",
                "avgScore": avg_score,
                "avgScoreTrend": "↑ 0.5",
                "completionRate": completion_rate,
                "completionRateTrend": "稳定",
            },
            "students": [
                {
                    "name": s.name,
                    "uid": s.uid,
                    "class": classroom.class_name,
                    "active": s.active_score,
                    "score": to_float(s.overall_score),
                    "weak": s.weak_point or "暂无",
                }
                for s in students
            ],
        }
        return ok(payload)
    except Exception as e:
        return fail(f"仪表盘加载失败: {e}")


@app.post("/api/scenario/publish")
def publish_scenario(request: ScenarioPublishRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(req, db)
        teacher, classroom = _ensure_demo_data(db)
        cfg = request.config or {}
        goals = cfg.get("goals", {})

        scenario_code = f"SCN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"
        scenario = ScenarioCRUD.create(
            db,
            ScenarioCreate(
                scenario_code=scenario_code,
                teacher_user_id=teacher.id,
                theme=cfg.get("theme", "默认主题"),
                difficulty=cfg.get("difficulty", "A1"),
                persona=cfg.get("persona", "友好耐心"),
                goal_require_perfect_tense=bool(goals.get("requirePerfectTense", False)),
                goal_require_b1_vocab=bool(goals.get("requireB1Vocab", False)),
            ),
        )

        for s in StudentCRUD.list_by_class(db, classroom.id):
            ScenarioPushCRUD.create_or_get(
                db,
                ScenarioPushCreate(scenario_id=scenario.id, student_id=s.id, push_status="pushed"),
            )

        return ok({"scenarioId": scenario.scenario_code}, "任务发布成功")
    except Exception as e:
        return fail(f"任务发布失败: {e}")


@app.post("/api/exam/generate")
def generate_exam(request: ExamGenerateRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(req, db)
        teacher, classroom = _ensure_demo_data(db)
        cfg = request.config or {}

        exam_code = f"EXM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"
        exam = ExamCRUD.create(
            db,
            ExamCreate(
                exam_code=exam_code,
                teacher_user_id=teacher.id,
                grammar_items=int(cfg.get("grammarItems", 15)),
                writing_items=int(cfg.get("writingItems", 2)),
                strategy=cfg.get("strategy", "personalized"),
                focus_areas=cfg.get("focusAreas", []),
            ),
        )

        students = StudentCRUD.list_by_class(db, classroom.id)
        for s in students:
            ExamAssignmentCRUD.create_or_get(
                db,
                ExamAssignmentCreate(exam_id=exam.id, student_id=s.id, status="assigned"),
            )

        return ok({"examId": exam.exam_code, "studentCount": len(students)}, "试卷生成成功")
    except Exception as e:
        return fail(f"试卷生成失败: {e}")


@app.get("/api/teacher/scenario/list")
def list_teacher_scenarios(request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher = require_teacher(request, db)
        scenarios = ScenarioCRUD.list_by_teacher(db, teacher.id)
        result = [
            {
                "id": s.id,
                "code": s.scenario_code,
                "theme": s.theme,
                "difficulty": s.difficulty,
                "persona": s.persona,
                "createdAt": s.created_at.isoformat(),
            }
            for s in scenarios
        ]
        return ok(result)
    except Exception as e:
        return fail(f"获取情景任务记录失败: {e}")


@app.get("/api/teacher/exam/list")
def list_teacher_exams(request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher = require_teacher(request, db)
        exams = ExamCRUD.list_by_teacher(db, teacher.id)
        result = [
            {
                "id": e.id,
                "code": e.exam_code,
                "grammarItems": e.grammar_items,
                "writingItems": e.writing_items,
                "strategy": e.strategy,
                "createdAt": e.created_at.isoformat(),
            }
            for e in exams
        ]
        return ok(result)
    except Exception as e:
        return fail(f"获取试卷记录失败: {e}")


@app.get("/api/teacher/exam/{exam_id}")
def get_teacher_exam_detail(exam_id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher = require_teacher(request, db)
        exam = ExamCRUD.get_by_id(db, exam_id)
        if not exam:
            return fail("试卷不存在", 404)
        if exam.teacher_user_id != teacher.id:
            return fail("无权访问该试卷", 403)
            
        content = {
            "代码": exam.exam_code,
            "语法题数量": exam.grammar_items,
            "写作题数量": exam.writing_items,
            "出题策略": "智能个性化" if exam.strategy == 'personalized' else "统一出题",
            "重点考察区域": exam.focus_areas,
            "生成时间": exam.created_at.isoformat()
        }
        return ok(content)
    except Exception as e:
        return fail(f"获取试卷详情失败: {e}")


@app.get("/api/student/detail")
def get_student_detail(id: str, request: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(request, db)
        _ensure_demo_data(db)
        student = StudentCRUD.get_by_uid(db, id)
        if not student:
            return fail("学生不存在", 404)

        ability = StudentAbilityCRUD.get_by_student_id(db, student.id)
        homeworks = HomeworkCRUD.list_by_student(db, student.id)

        data = {
            "info": {
                "name": student.name,
                "uid": student.uid,
                "class": "软件工程",
                "active": student.active_score,
                "score": to_float(student.overall_score),
            },
            "ability": {
                "listening": ability.listening if ability else 0,
                "speaking": ability.speaking if ability else 0,
                "reading": ability.reading if ability else 0,
                "writing": ability.writing if ability else 0,
            },
            "aiDiagnosis": ability.ai_diagnosis if ability else "暂无诊断",
            "homeworks": [
                {
                    "id": h.id,
                    "title": h.title,
                    "date": (h.submitted_at or h.created_at).strftime("%Y-%m-%d"),
                    "status": h.status,
                    "score": to_float(h.score, None),
                    "feedback": h.ai_comment,
                }
                for h in homeworks
            ],
        }
        return ok(data)
    except Exception as e:
        return fail(f"获取学生详情失败: {e}")


@app.get("/api/homework/detail")
def get_homework_detail(id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(request, db)
        _ensure_demo_data(db)
        hw = HomeworkCRUD.get_by_id(db, id)
        if not hw:
            return fail("作业不存在", 404)

        data = {
            "type": hw.file_type or "text",
            "meta": {
                "fileUrl": hw.file_url,
                "fileName": hw.file_name or f"homework-{hw.id}",
                "fileSize": hw.file_size or "Unknown",
                "uploadTime": (hw.submitted_at or hw.created_at).strftime("%Y-%m-%d %H:%M"),
            },
            "aiComment": hw.ai_comment or "暂无 AI 评价数据。",
        }
        return ok(data)
    except Exception as e:
        return fail(f"获取作业详情失败: {e}")


@app.post("/api/homework/save")
def save_homework_review(request: HomeworkSaveRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(req, db)
        teacher, _ = _ensure_demo_data(db)
        hw = HomeworkCRUD.get_by_id(db, request.homeworkId)
        if not hw:
            return fail("作业不存在", 404)

        HomeworkReviewCRUD.create(
            db,
            HomeworkReviewCreate(
                homework_id=request.homeworkId,
                teacher_user_id=teacher.id,
                score=request.score,
                feedback=request.feedback,
            ),
        )
        HomeworkCRUD.update_score_feedback(db, request.homeworkId, request.score, request.feedback)
        return ok({"homeworkId": request.homeworkId, "saved": True}, "评分保存成功")
    except Exception as e:
        return fail(f"评分保存失败: {e}")


@app.post("/api/student/push-scheme")
def push_student_scheme(request: PushSchemeRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(req, db)
        teacher, _ = _ensure_demo_data(db)
        student = StudentCRUD.get_by_uid(db, request.studentId)
        if not student:
            return fail("学生不存在", 404)

        scenario_code = f"SCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"
        scenario = ScenarioCRUD.create(
            db,
            ScenarioCreate(
                scenario_code=scenario_code,
                teacher_user_id=teacher.id,
                theme="个性化强化方案",
                difficulty="自适应",
                persona="严谨纠错",
                goal_require_perfect_tense=True,
                goal_require_b1_vocab=False,
            ),
        )

        ScenarioPushCRUD.create_or_get(
            db,
            ScenarioPushCreate(scenario_id=scenario.id, student_id=student.id, push_status="pushed"),
        )

        return ok({"schemeName": "个性化强化方案"}, "推送成功")
    except Exception as e:
        return fail(f"推送失败: {e}")


# ════════════════════ 7. 学生端 API ════════════════════


# ╔═══════════════════════════════════════════════════════╗
# ║  7-1. 学生登录                                       ║
# ╚═══════════════════════════════════════════════════════╝


@app.post("/api/auth/student-login")
def student_login(req: StudentLoginReq, db: Session = Depends(get_db)):
    try:
        student = StudentCRUD.get_by_uid(db, req.username)
        if not student:
            return fail("学号不存在，请检查后重试", 401)

        user = UserCRUD.get_by_id(db, student.user_id)
        if not user:
            return fail("用户记录异常", 500)

        if user.password_hash != req.password:
            return fail("密码错误，请重新输入", 401)

        token = f"student-token-{student.uid}-{uuid4().hex[:8]}"
        info = {
            "id": student.uid,
            "name": student.name,
            "role": "student",
            "studentId": student.id,
        }
        return {
            "code": 200,
            "message": "登录成功",
            "token": token,
            "user": info,
            "data": {"token": token, "user": info},
        }
    except Exception as e:
        return fail(f"登录失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-1.5. 学生端大厅 AI 对话 (Student Chat)              ║
# ╚═══════════════════════════════════════════════════════╝


@app.post("/api/student/chat")
async def student_chat_endpoint(request: ChatRequest, req: Request = None, db: Session = Depends(get_db)):
    require_student(req, db)
    print(f"收到学生端前端消息: {request.message}")
    try:
        global _student_chat_history
        _student_chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=request.message)]))
        response = _gemini_client.models.generate_content(
            model=_MODEL_ID,
            contents=_student_chat_history,
            config=types.GenerateContentConfig(
                system_instruction=_STUDENT_SYSTEM,
            ),
        )
        _student_chat_history.append(types.Content(role="model", parts=[types.Part.from_text(text=response.text)]))
        return {"reply": response.text}
    except Exception as e:
        print(f"Gemini调用失败: {e}")
        return {"reply": "Entschuldigung, ich habe ein Problem. (AI出错了)"}


# ╔═══════════════════════════════════════════════════════╗
# ║  7-2. 场景对话 (AISceneChat)                         ║
# ╚═══════════════════════════════════════════════════════╝


@app.post("/api/student/scene-chat")
def scene_chat(req: SceneChatReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        scene_name = req.sceneName or "自由对话"
        session = _get_or_create_session(db, student.id, req.sceneId, scene_name)

        ChatMessageCRUD.create(
            db, ChatMessageCreate(session_id=session.id, role="user", content=req.userMessage)
        )

        history = ChatMessageCRUD.list_by_session(db, session.id)
        conv_lines = [
            f"{'学生' if m.role == 'user' else 'AI助教'}: {m.content}" for m in history
        ]

        prompt = (
            f"场景：「{scene_name}」德语对话练习。\n"
            f"对话历史:\n" + "\n".join(conv_lines) + "\n\n"
            f"请用德语回复（括号内中文翻译），如有语法错误请纠正。\n"
            f'返回JSON: {{"reply":"德语回复","correction":"纠错说明或null"}}'
        )
        result = _ai_json(prompt, {
            "reply": "Entschuldigung, bitte versuchen Sie es noch einmal. (请再试一次)",
            "correction": None,
        })
        reply = result.get("reply", "Bitte versuchen Sie es noch einmal.")
        correction = result.get("correction")

        ChatMessageCRUD.create(
            db,
            ChatMessageCreate(
                session_id=session.id, role="assistant", content=reply, correction=correction
            ),
        )

        return ok({"reply": reply, "correction": correction})
    except Exception as e:
        return fail(f"对话失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-3. 词汇学习 (VocabLearning)                      ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/vocab/list")
def vocab_list(request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        words = VocabularyCRUD.list_all(db)
        data = []
        for w in words:
            collected = (
                StudentVocabCollectionCRUD.is_collected(db, student.id, w.id) if student else False
            )
            data.append({
                "id": w.id, "german": w.german, "chinese": w.chinese,
                "example": w.example, "isCollected": collected,
            })
        return ok(data)
    except Exception as e:
        return fail(f"获取词汇失败: {e}")


@app.post("/api/student/vocab/collect")
def vocab_collect(req: VocabCollectReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        if req.isCollect:
            StudentVocabCollectionCRUD.collect(
                db, StudentVocabCollectionCreate(student_id=student.id, vocab_id=req.vocabId)
            )
        else:
            StudentVocabCollectionCRUD.uncollect(db, student.id, req.vocabId)
        return ok(None, "操作成功")
    except Exception as e:
        return fail(f"收藏操作失败: {e}")


@app.post("/api/student/vocab/generate")
def vocab_generate(req: VocabGenerateReq, db: Session = Depends(get_db)):
    try:
        existing = VocabularyCRUD.list_all(db, level=req.level, topic=req.topic)
        existing_words = [w.german for w in existing]

        prompt = (
            f"请生成5个德语{req.level}级别、主题「{req.topic}」的新词汇。\n"
            f"已有(不要重复): {', '.join(existing_words[:20])}\n"
            f'返回JSON数组: [{{"german":"…","chinese":"…","example":"例句…"}}]\n只返回JSON。'
        )
        words = _ai_json(prompt, [])

        saved = []
        for w in words or []:
            if not isinstance(w, dict) or "german" not in w:
                continue
            try:
                v = VocabularyCRUD.create(
                    db,
                    VocabularyCreate(
                        german=w["german"], chinese=w.get("chinese", ""),
                        example=w.get("example"), level=req.level, topic=req.topic,
                    ),
                )
                saved.append({
                    "id": v.id, "german": v.german, "chinese": v.chinese,
                    "example": v.example, "isCollected": False,
                })
            except Exception:
                pass
        return ok(saved)
    except Exception as e:
        return fail(f"生成词汇失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-4. 语法练习 (GrammarPractice)                     ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/grammar/categories")
def grammar_categories(request: Request, db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        cats = GrammarCategoryCRUD.list_all(db)
        return ok([{"id": c.id, "name": c.name, "desc": c.description or ""} for c in cats])
    except Exception as e:
        return fail(f"获取分类失败: {e}")


@app.get("/api/student/grammar/exercises")
def grammar_exercises(request: Request, categoryId: int = Query(...), db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        exs = GrammarExerciseCRUD.list_by_category(db, categoryId)
        return ok([{"id": e.id, "question": e.question} for e in exs])
    except Exception as e:
        return fail(f"获取练习失败: {e}")


@app.post("/api/student/grammar/submit")
def grammar_submit(req: GrammarSubmitReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        details = []
        correct_count = 0
        error_cats = {c.name: c.id for c in ErrorBookCategoryCRUD.list_all(db)}

        for ans in req.answers:
            ex = GrammarExerciseCRUD.get_by_id(db, ans.exerciseId)
            if not ex:
                continue

            is_correct = ans.userAnswer.strip().lower() == ex.correct_answer.strip().lower()
            if is_correct:
                correct_count += 1

            analysis = ex.analysis or ""
            if not is_correct and not analysis:
                analysis = _ai_text(
                    f"德语语法题:\n题目:{ex.question}\n学生答:{ans.userAnswer}\n"
                    f"正确答案:{ex.correct_answer}\n请用中文简短解释错误原因(50字以内)。",
                    "请参考正确答案复习。",
                )

            GrammarSubmissionCRUD.create(
                db,
                GrammarSubmissionCreate(
                    student_id=student.id, exercise_id=ans.exerciseId,
                    user_answer=ans.userAnswer, is_correct=is_correct,
                    ai_analysis=analysis if not is_correct else None,
                ),
            )

            if not is_correct:
                grammar_cat = GrammarCategoryCRUD.get_by_id(db, req.categoryId)
                eb_cat_id = _match_error_category(
                    grammar_cat.name if grammar_cat else "", error_cats
                )
                if eb_cat_id:
                    try:
                        ErrorBookEntryCRUD.create(
                            db,
                            ErrorBookEntryCreate(
                                student_id=student.id, category_id=eb_cat_id,
                                source="语法练习", question=ex.question,
                                user_answer=ans.userAnswer,
                                correct_answer=ex.correct_answer, analysis=analysis,
                            ),
                        )
                    except Exception:
                        pass

            details.append({
                "exerciseId": ex.id, "isCorrect": is_correct,
                "correctAnswer": ex.correct_answer,
                "analysis": analysis if not is_correct else "",
            })

        wrong_count = len(req.answers) - correct_count
        return ok({
            "totalCount": len(req.answers), "correctCount": correct_count,
            "wrongCount": wrong_count, "detailList": details,
        })
    except Exception as e:
        return fail(f"提交失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-5. 听说训练 (ListeningSpeaking)                   ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/listening/materials")
def listening_materials(db: Session = Depends(get_db)):
    try:
        mats = ListeningMaterialCRUD.list_all(db)
        return ok([
            {"id": m.id, "title": m.title, "level": m.level, "duration": m.duration}
            for m in mats
        ])
    except Exception as e:
        return fail(f"获取听力材料失败: {e}")


@app.get("/api/student/listening/material/detail")
def listening_material_detail(materialId: int = Query(...), db: Session = Depends(get_db)):
    try:
        m = ListeningMaterialCRUD.get_by_id(db, materialId)
        if not m:
            return fail("材料不存在", 404)
        return ok({"audioUrl": m.audio_url, "script": m.script or ""})
    except Exception as e:
        return fail(f"获取详情失败: {e}")


@app.post("/api/student/speaking/evaluate")
def speaking_evaluate(req: SpeakingEvalReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        material = ListeningMaterialCRUD.get_by_id(db, req.materialId)
        if not material:
            return fail("听力材料不存在", 404)

        prompt = (
            f"你是德语口语评估助手。学生朗读了以下听力材料:\n"
            f"标题: {material.title}\n原文: {material.script or '(无原文)'}\n"
            f"请给出评分(0-100)和建议。返回JSON:\n"
            f'{{"totalScore":85,"pronunciationScore":88,"fluencyScore":82,'
            f'"intonationScore":85,"analysis":"分析","suggestion":"建议"}}'
        )
        result = _ai_json(prompt, {
            "totalScore": 78, "pronunciationScore": 80,
            "fluencyScore": 76, "intonationScore": 78,
            "analysis": "发音基本准确，需注意元音长短区分。",
            "suggestion": "建议多听原文录音，模仿语调节奏。",
        })

        SpeakingEvaluationCRUD.create(
            db,
            SpeakingEvaluationCreate(
                student_id=student.id, material_id=req.materialId,
                audio_url=req.audioUrl,
                total_score=result.get("totalScore"),
                pronunciation_score=result.get("pronunciationScore"),
                fluency_score=result.get("fluencyScore"),
                intonation_score=result.get("intonationScore"),
                analysis=result.get("analysis"),
                suggestion=result.get("suggestion"),
            ),
        )

        return ok(result)
    except Exception as e:
        return fail(f"评估失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-6. 写作辅助 (WritingAssistant)                    ║
# ╚═══════════════════════════════════════════════════════╝


@app.post("/api/student/writing/check")
def writing_check(req: WritingReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)

        prompt = (
            f"请检查以下德语文本的语法和拼写错误:\n\n{req.userText}\n\n"
            f"返回JSON: {{\"errors\":[{{\"position\":\"出错位置\",\"error\":\"错误描述\","
            f"\"suggestion\":\"修改建议\"}}],\"polishedText\":\"修正后完整文本\"}}\n只返回JSON。"
        )
        result = _ai_json(prompt, {"errors": [], "polishedText": req.userText})

        if student:
            WritingSessionCRUD.create(
                db,
                WritingSessionCreate(
                    student_id=student.id, session_type="check",
                    user_text=req.userText, result_json=result,
                ),
            )

        return ok(result)
    except Exception as e:
        return fail(f"检查失败: {e}")


@app.post("/api/student/writing/generate-sample")
def writing_generate_sample(req: WritingReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)

        prompt = (
            f"学生正在练习德语写作，主题/草稿如下:\n\n{req.userText}\n\n"
            f"请生成一篇优秀的德语范文(A2-B1水平，150-200词)。\n"
            f'返回JSON: {{"sampleEssay":"范文内容"}}\n只返回JSON。'
        )
        result = _ai_json(prompt, {
            "sampleEssay": "Entschuldigung, die Beispielgeneration ist momentan nicht verfügbar. "
                           "(抱歉，范文生成暂时不可用。)"
        })

        if student:
            WritingSessionCRUD.create(
                db,
                WritingSessionCreate(
                    student_id=student.id, session_type="generate",
                    user_text=req.userText, result_json=result,
                ),
            )

        return ok(result)
    except Exception as e:
        return fail(f"生成范文失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-7. 错题本 (ErrorBookReview)                       ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/error-book/categories")
def error_book_categories(request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        data = ErrorBookEntryCRUD.count_by_category(db, student.id)
        return ok(data)
    except Exception as e:
        return fail(f"获取错题分类失败: {e}")


@app.get("/api/student/error-book/list")
def error_book_list(
    categoryId: int = Query(...), request: Request = None, db: Session = Depends(get_db)
):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        entries = ErrorBookEntryCRUD.list_by_student_and_category(db, student.id, categoryId)
        return ok([
            {
                "id": e.id, "source": e.source, "question": e.question,
                "userAnswer": e.user_answer, "correctAnswer": e.correct_answer,
                "analysis": e.analysis or "",
            }
            for e in entries
        ])
    except Exception as e:
        return fail(f"获取错题列表失败: {e}")


@app.post("/api/student/error-book/start-review")
def error_book_start_review(req: ErrorReviewReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        entries = ErrorBookEntryCRUD.list_by_student_and_category(db, student.id, req.categoryId)
        cat_name = req.categoryName or "此分类"

        if not entries:
            return ok({"reviewTip": f"🎉 「{cat_name}」没有未掌握的错题，继续保持！"})

        questions_summary = "\n".join(
            [f"- 题目: {e.question} | 学生答: {e.user_answer} | 正确: {e.correct_answer}" for e in entries[:5]]
        )
        prompt = (
            f"学生在「{cat_name}」分类下有以下错题:\n{questions_summary}\n"
            f"请用中文给出针对性的复习建议(100字以内)。"
        )
        tip = _ai_text(prompt, f"建议重点复习「{cat_name}」相关语法规则，结合例句反复练习。")
        return ok({"reviewTip": tip})
    except Exception as e:
        return fail(f"生成复习建议失败: {e}")


@app.post("/api/student/error-book/mark-mastered")
def error_book_mark_mastered(req: ErrorMasterReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        entry = ErrorBookEntryCRUD.get_by_id(db, req.errorId)
        if not entry:
            return fail("错题不存在", 404)
        if entry.student_id != student.id:
            return fail("无权操作该错题", 403)
        ErrorBookEntryCRUD.mark_mastered(db, req.errorId)
        return ok(None, "已标记为掌握")
    except Exception as e:
        return fail(f"标记失败: {e}")


@app.delete("/api/student/error-book/delete/{error_id}")
def error_book_delete(error_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        entry = ErrorBookEntryCRUD.get_by_id(db, error_id)
        if not entry:
            return fail("错题不存在", 404)
        if entry.student_id != student.id:
            return fail("无权操作该错题", 403)
        ErrorBookEntryCRUD.delete(db, error_id)
        return ok(None, "删除成功")
    except Exception as e:
        return fail(f"删除失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-8. 收藏夹 (FavoritesPage)                        ║
# ╚═══════════════════════════════════════════════════════╝


@app.get("/api/student/favorites/categories")
def favorites_categories(request: Request, db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        cats = FavoriteCategoryCRUD.list_all(db)
        return ok([{"id": c.id, "type": c.type, "name": c.name} for c in cats])
    except Exception as e:
        return fail(f"获取收藏分类失败: {e}")


@app.get("/api/student/favorites/list")
def favorites_list(
    type: str = Query(...), request: Request = None, db: Session = Depends(get_db)
):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        items = FavoriteCRUD.list_by_student_and_type(db, student.id, type)
        return ok([
            {
                "id": f.id, "content": f.content,
                "translate": f.translate, "rule": f.rule, "note": f.note,
            }
            for f in items
        ])
    except Exception as e:
        return fail(f"获取收藏列表失败: {e}")


@app.delete("/api/student/favorites/{fav_id}")
def favorites_delete(fav_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        fav = FavoriteCRUD.get_by_id(db, fav_id)
        if not fav:
            return fail("收藏不存在", 404)
        if fav.student_id != student.id:
            return fail("无权操作该收藏", 403)
        FavoriteCRUD.delete(db, fav_id)
        return ok(None, "删除成功")
    except Exception as e:
        return fail(f"删除失败: {e}")


@app.post("/api/student/favorites/ai-extend")
def favorites_ai_extend(req: FavAIExtendReq, request: Request = None, db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        type_prompts = {
            "vocab": f"请对德语词汇「{req.content}」进行扩展：给出词性、复数形式、常用搭配和2个例句。用中文回答。",
            "grammar": f"请对德语语法规则「{req.content}」进行扩展讲解：给出详细说明和3个例句。用中文回答。",
            "sentence": f"请对德语句子「{req.content}」进行分析：逐词翻译、语法结构、类似表达。用中文回答。",
            "note": f"请对学习笔记「{req.content}」进行扩展：补充相关知识点和记忆技巧。用中文回答。",
        }
        prompt = type_prompts.get(req.type, f"请对「{req.content}」进行扩展讲解，用中文回答。")
        extended = _ai_text(prompt, f"暂无法为「{req.content}」生成扩展内容。")
        return ok({"extendContent": extended})
    except Exception as e:
        return fail(f"AI扩展失败: {e}")


# ╔═══════════════════════════════════════════════════════╗
# ║  7-9. 学习进度 (LearningProgress)                    ║
# ╚═══════════════════════════════════════════════════════╝

DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


@app.get("/api/student/learning/progress")
def learning_progress(request: Request, db: Session = Depends(get_db)):
    try:
        student = _current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        total_time = LearningSessionCRUD.total_minutes(db, student.id)
        week_time = LearningSessionCRUD.week_minutes(db, student.id)

        sessions = LearningSessionCRUD.list_by_student(db, student.id)
        module_map: dict[str, int] = {}
        for s in sessions:
            module_map[s.module] = module_map.get(s.module, 0) + s.duration_minutes

        all_modules = ["词汇学习", "语法练习", "情景对话", "听说训练", "写作辅助"]
        max_minutes = max(module_map.values()) if module_map else 1
        modules = [
            {"name": m, "rate": round(module_map.get(m, 0) / max_minutes * 100) if max_minutes else 0}
            for m in all_modules
        ]

        knowledge_list = StudentKnowledgeMasteryCRUD.list_by_student(db, student.id)
        knowledge = [{"name": k.knowledge_name, "level": k.mastery_level} for k in knowledge_list]

        mastered_count = sum(1 for k in knowledge_list if k.mastery_level == "熟练")
        finish_rate = round(mastered_count / len(knowledge_list) * 100) if knowledge_list else 0

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_sessions = [
            s for s in sessions
            if hasattr(s.session_date, 'date')
            and s.session_date.date() >= week_start
            or (isinstance(s.session_date, date) and s.session_date >= week_start)
        ]

        day_map: dict[int, dict] = {}
        for s in week_sessions:
            sd = s.session_date.date() if hasattr(s.session_date, 'date') else s.session_date
            weekday = sd.weekday()
            if weekday not in day_map:
                day_map[weekday] = {"time": 0, "contents": []}
            day_map[weekday]["time"] += s.duration_minutes
            if s.content:
                day_map[weekday]["contents"].append(s.content)

        week_report = [
            {
                "day": DAY_NAMES[i],
                "time": day_map[i]["time"] if i in day_map else 0,
                "content": "、".join(day_map[i]["contents"]) if i in day_map else "",
            }
            for i in range(7)
        ]

        return ok({
            "totalTime": total_time,
            "weekTime": week_time,
            "finishRate": finish_rate,
            "modules": modules,
            "knowledge": knowledge,
            "weekReport": week_report,
        })
    except Exception as e:
        return fail(f"获取学习进度失败: {e}")


# ════════════════════ 8. 根路由 ════════════════════


@app.get("/")
def read_root():
    return {"status": "ok", "message": "SITP German Agent 后端正在运行中! 🚀"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
