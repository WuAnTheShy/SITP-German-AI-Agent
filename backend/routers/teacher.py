import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from statistics import mean
from google.genai import types

from db.session import get_db
from crud.repositories import (
    UserCRUD,
    StudentCRUD,
    ClassroomCRUD,
    StudentAbilityCRUD,
    ScenarioCRUD,
    ScenarioPushCRUD,
    ExamCRUD,
    ExamAssignmentCRUD,
    HomeworkCRUD,
)
from schemas.entities import (
    ScenarioCreate,
    ScenarioPushCreate,
    ExamCreate,
    ExamAssignmentCreate,
)
from core.responses import ok, fail, to_float
from core.deps import require_teacher
from core.seed import _ensure_demo_data
from services.llm import get_client, MODEL_ID

router = APIRouter()


class ScenarioPublishRequest(BaseModel):
    config: dict
    timestamp: str | None = None


class ExamGenerateRequest(BaseModel):
    config: dict
    timestamp: str | None = None


@router.get("/api/teacher/dashboard")
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


@router.post("/api/scenario/publish")
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


@router.post("/api/exam/generate")
def generate_exam(request: ExamGenerateRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        require_teacher(req, db)
        teacher, classroom = _ensure_demo_data(db)
        cfg = request.config or {}

        exam_code = f"EXM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:4]}"
        grammar_count = int(cfg.get("grammarItems", 15))
        writing_count = int(cfg.get("writingItems", 2))

        focus_desc = "、".join(cfg.get("focusAreas", [])) or "综合考察"
        strategy = cfg.get("strategy", "personalized")
        strategy_desc = "个性化差异出题" if strategy == "personalized" else "统一标准出题"

        def _generate_questions_for_student(student_info: str = "") -> list:
            prompt = f"""你是一个专业的德语考试出题系统。请根据以下配置生成德语考试试卷：

- 语法题数量：{grammar_count} 题
- 写作题数量：{writing_count} 题
- 出题策略：{strategy_desc}
- 重点考察领域：{focus_desc}
{student_info}

要求：
1. 每道语法题都必须**不同**，涵盖不同语法考点（如动词变位、格变化、被动语态、虚拟式、从句语序、介词搭配等）
2. 语法题为选择填空题，每题4个选项(A/B/C/D)，需标注正确答案
3. 写作题需要不同的写作场景和主题，字数要求100-150词
4. 题目难度为 B1 水平

请严格按照以下 JSON 格式返回（不要加任何额外文字或markdown）：
[
  {{
    "type": "grammar",
    "id": "G-1",
    "instruction": "语法题描述（说明考察什么语法点）",
    "content": "题目本身，用___表示需要填写的空",
    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
    "answer": "正确答案字母",
    "score": 2
  }},
  {{
    "type": "writing",
    "id": "W-1",
    "instruction": "写作题描述",
    "content": "写作要求和情景说明，字数要求：100-150词。",
    "score": 15
  }}
]

请确保生成 {grammar_count} 道语法题和 {writing_count} 道写作题。"""

            print(f"[试卷生成] 正在调用 AI 生成 {grammar_count} 道语法题 + {writing_count} 道写作题...", flush=True)
            ai_questions = None
            try:
                resp = get_client().models.generate_content(
                    model=MODEL_ID,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="你是专业的德语考试出题助手，只返回JSON格式数据。",
                        http_options={"timeout": 90_000},
                    ),
                )
                text = resp.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                ai_questions = json.loads(text.strip())
                print(f"[试卷生成] AI 成功生成 {len(ai_questions)} 道题目", flush=True)
            except Exception as e:
                try:
                    print(f"[试卷生成] AI 生成失败: {type(e).__name__}", flush=True)
                except Exception:
                    print("[试卷生成] AI 生成失败", flush=True)

            if not ai_questions or not isinstance(ai_questions, list):
                print("[试卷生成] 使用 fallback 基础题目", flush=True)
                ai_questions = []
                grammar_topics = [
                    ("动词变位", "Ich ___ gestern ins Kino gegangen.", ["A. bin", "B. habe", "C. war", "D. wurde"], "A"),
                    ("格变化", "Er gibt ___ Freund ein Buch.", ["A. sein", "B. seinem", "C. seinen", "D. seiner"], "B"),
                    ("被动语态", "Das Haus ___ letztes Jahr gebaut.", ["A. hat", "B. ist", "C. wird", "D. wurde"], "D"),
                    ("虚拟式", "Wenn ich reich ___, würde ich reisen.", ["A. bin", "B. wäre", "C. war", "D. sei"], "B"),
                    ("从句语序", "Ich weiß, dass er morgen nach Berlin ___.", ["A. fahrt", "B. fährt", "C. gefahren", "D. fahren"], "B"),
                    ("介词搭配", "Wir warten ___ den Bus.", ["A. für", "B. auf", "C. an", "D. um"], "B"),
                    ("冠词", "Das ist ___ interessantes Buch.", ["A. ein", "B. eine", "C. einen", "D. einem"], "A"),
                    ("反身动词", "Er ___ sich für Musik.", ["A. interessiert", "B. interessieren", "C. interessiere", "D. interessierst"], "A"),
                ]
                for i in range(grammar_count):
                    t = grammar_topics[i % len(grammar_topics)]
                    ai_questions.append({
                        "type": "grammar", "id": f"G-{i+1}",
                        "instruction": f"语法题 {i+1}（考点：{t[0]}）：请选择正确的选项填空。",
                        "content": t[1], "options": t[2], "answer": t[3], "score": 2
                    })
                writing_topics = [
                    "你的一位德国朋友即将来中国旅行，请给他写一封邮件，推荐几个必去的城市，并说明理由。字数要求：100-150词。",
                    "请描述你理想的大学生活，包括学习、社交和课外活动。字数要求：100-150词。",
                    "请写一篇短文，介绍你最喜欢的一道中国菜的做法和它的文化意义。字数要求：100-150词。",
                ]
                for i in range(writing_count):
                    ai_questions.append({
                        "type": "writing", "id": f"W-{i+1}",
                        "instruction": f"写作题 {i+1}：请根据以下情景进行写作。",
                        "content": writing_topics[i % len(writing_topics)], "score": 15
                    })
            return ai_questions

        students = StudentCRUD.list_by_class(db, classroom.id)

        if strategy != "personalized":
            ai_questions = _generate_questions_for_student()
            exam = ExamCRUD.create(
                db,
                ExamCreate(
                    exam_code=exam_code,
                    teacher_user_id=teacher.id,
                    grammar_items=grammar_count,
                    writing_items=writing_count,
                    strategy=strategy,
                    focus_areas=cfg.get("focusAreas", []),
                    content=ai_questions,
                ),
            )
            for s in students:
                ExamAssignmentCRUD.create_or_get(
                    db,
                    ExamAssignmentCreate(exam_id=exam.id, student_id=s.id, status="assigned"),
                )
        else:
            exam = ExamCRUD.create(
                db,
                ExamCreate(
                    exam_code=exam_code,
                    teacher_user_id=teacher.id,
                    grammar_items=grammar_count,
                    writing_items=writing_count,
                    strategy=strategy,
                    focus_areas=cfg.get("focusAreas", []),
                    content=[],
                ),
            )
            for s in students:
                ability = StudentAbilityCRUD.get_by_student_id(db, s.id)
                student_info = f"\n- 针对学生情况：该学生在【{s.weak_point or '其他'}】有薄弱点。"
                if ability and ability.ai_diagnosis:
                    student_info += f"\n- AI诊断信息：{ability.ai_diagnosis}"
                student_info += "\n**请务必针对该学生的薄弱点设计题目，体现出个性化！**"
                try:
                    print(f"[千人千面] 正在为学生 id={s.id} 生成个性化试卷...", flush=True)
                except Exception:
                    print("[千人千面] 生成个性化试卷...", flush=True)
                personalized_q = _generate_questions_for_student(student_info)
                ExamAssignmentCRUD.create_or_get(
                    db,
                    ExamAssignmentCreate(
                        exam_id=exam.id,
                        student_id=s.id,
                        status="assigned",
                        personalized_content=personalized_q
                    ),
                )

        return ok({"examId": exam.exam_code, "studentCount": len(students)}, "试卷生成成功")
    except Exception as e:
        return fail(f"试卷生成失败: {e}")


@router.get("/api/teacher/scenario/list")
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


@router.get("/api/teacher/exam/list")
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


@router.get("/api/teacher/exam/{exam_id}")
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
            "生成时间": exam.created_at.isoformat(),
            "题目列表": exam.content
        }
        return ok(content)
    except Exception as e:
        return fail(f"获取试卷详情失败: {e}")
