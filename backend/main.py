import os
from datetime import datetime
from statistics import mean
from uuid import uuid4

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from crud.repositories import (
    ClassroomCRUD,
    ExamAssignmentCRUD,
    ExamCRUD,
    HomeworkCRUD,
    HomeworkReviewCRUD,
    ScenarioCRUD,
    ScenarioPushCRUD,
    StudentAbilityCRUD,
    StudentCRUD,
    UserCRUD,
)
from db.session import get_db
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

# 1. 配置环境
load_dotenv()
# 记得在同级目录的 .env 文件里写上 GOOGLE_API_KEY=你的密钥
if not os.getenv("GOOGLE_API_KEY"):
    print("警告: 未找到 GOOGLE_API_KEY")

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 2. 定义模型和人设
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction="你是一个同济大学SITP项目的AI德语助教。请用德语回答，括号内给出中文解释，并指出用户的语法错误。如果用户说中文，请引导通过德语表达。"
)
chat = model.start_chat(history=[])

app = FastAPI()

# 3. 允许跨域（必须加，否则前端报错）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 定义数据格式
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

# 5. 核心接口
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"收到前端消息: {request.message}") # 终端打印，方便你调试
    
    try:
        response = chat.send_message(request.message)
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
            # 本地 Mock：若用户不存在，自动创建教师账号，便于前端联调
            user = UserCRUD.create(
                db,
                UserCreate(
                    username=request.username,
                    password_hash=request.password,
                    role="teacher",
                    display_name=f"{request.username}老师",
                ),
            )

        token = f"mock-token-{user.id}-{uuid4().hex[:8]}"
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
def teacher_dashboard(db: Session = Depends(get_db)):
    try:
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
def publish_scenario(request: ScenarioPublishRequest, db: Session = Depends(get_db)):
    try:
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
def generate_exam(request: ExamGenerateRequest, db: Session = Depends(get_db)):
    try:
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


@app.get("/api/student/detail")
def get_student_detail(id: str, db: Session = Depends(get_db)):
    try:
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
def get_homework_detail(id: int, db: Session = Depends(get_db)):
    try:
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
def save_homework_review(request: HomeworkSaveRequest, db: Session = Depends(get_db)):
    try:
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
def push_student_scheme(request: PushSchemeRequest, db: Session = Depends(get_db)):
    try:
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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "SITP German Agent 后端正在运行中! 🚀"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)