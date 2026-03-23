import json
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from statistics import mean
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
from core.deps import require_teacher, get_current_teacher_and_classrooms
from services.llm import generate_response
from services.metrics import compute_student_interaction_minutes, refresh_student_metrics

router = APIRouter()


class ScenarioPublishRequest(BaseModel):
    config: dict
    timestamp: str | None = None


class ExamGenerateRequest(BaseModel):
    config: dict
    timestamp: str | None = None


class TeacherStudentUpdateBody(BaseModel):
    name: str | None = None
    status: str | None = None
    active_score: int | None = None
    overall_score: float | None = None
    weak_point: str | None = None
    class_id: int | None = None


@router.get("/api/teacher/dashboard")
def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    """教师仪表盘：已关联班级则返回本班学情，未关联则返回空列表与「未关联」标识，教师仍可正常使用 AI 等非班级功能。"""
    try:
        teacher = require_teacher(request, db)
        classrooms = ClassroomCRUD.list_by_teacher(db, teacher.id)
        if not classrooms:
            return ok({
                "teacherName": teacher.display_name,
                "className": "未关联",
                "pendingTasks": 0,
                "stats": {
                    "totalStudents": 0,
                    "totalStudentsTrend": "+0",
                    "avgDuration": 0,
                    "avgDurationTrend": "—",
                    "avgScore": 0,
                    "avgScoreTrend": "—",
                    "completionRate": 0,
                    "completionRateTrend": "—",
                },
                "students": [],
            })

        students_map: dict[int, any] = {}
        for classroom in classrooms:
            for s in StudentCRUD.list_by_class(db, classroom.id):
                students_map[s.id] = s
        students = list(students_map.values())
        class_name_by_id = {c.id: c.class_name for c in classrooms}

        metric_map: dict[int, dict] = {}
        interaction_hours = []
        for s in students:
            metric_map[s.id] = refresh_student_metrics(db, s.id)
            interaction_hours.append(compute_student_interaction_minutes(db, s.id, days=7) / 60)

        all_homeworks = []
        for s in students:
            all_homeworks.extend(HomeworkCRUD.list_by_student(db, s.id))

        avg_score = round(mean([to_float(s.overall_score) for s in students]), 1) if students else 0
        completion_count = sum(1 for h in all_homeworks if h.status == "已完成")
        completion_rate = round((completion_count / len(all_homeworks)) * 100) if all_homeworks else 0
        avg_duration = round(sum(interaction_hours) / len(interaction_hours), 1) if interaction_hours else 0
        pending_count = sum(1 for s in students if s.status == "pending")

        payload = {
            "teacherName": teacher.display_name,
            "className": " / ".join([c.class_name for c in classrooms]),
            "classCode": " / ".join([c.class_code for c in classrooms]),
            "classCount": len(classrooms),
            "pendingTasks": pending_count,
            "stats": {
                "totalStudents": len(students),
                "totalStudentsTrend": "+0",
                "avgDuration": avg_duration,
                "avgDurationTrend": "按近7天统计",
                "avgScore": avg_score,
                "avgScoreTrend": "按当前成绩",
                "completionRate": completion_rate,
                "completionRateTrend": "按作业提交",
            },
            "students": [
                {
                    "name": s.name,
                    "uid": s.uid,
                    "class": " / ".join([class_name_by_id.get(cid, "") for cid in StudentCRUD.list_class_ids(db, s.id) if class_name_by_id.get(cid)]),
                    "active": metric_map.get(s.id, {}).get("active_score", s.active_score),
                    "score": metric_map.get(s.id, {}).get("overall_score", to_float(s.overall_score)),
                    "weak": metric_map.get(s.id, {}).get("weak_point", s.weak_point or "暂无"),
                }
                for s in students
            ],
        }
        return ok(payload)
    except HTTPException:
        raise
    except Exception as e:
        return fail(f"仪表盘加载失败: {e}")


@router.post("/api/scenario/publish")
def publish_scenario(request: ScenarioPublishRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        teacher, classrooms = get_current_teacher_and_classrooms(req, db)
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

        students_map: dict[int, any] = {}
        for classroom in classrooms:
            for s in StudentCRUD.list_by_class(db, classroom.id):
                students_map[s.id] = s

        for s in students_map.values():
            ScenarioPushCRUD.create_or_get(
                db,
                ScenarioPushCreate(scenario_id=scenario.id, student_id=s.id, push_status="pushed"),
            )

        return ok({"scenarioId": scenario.scenario_code}, "任务发布成功")
    except HTTPException:
        raise
    except Exception as e:
        return fail(f"任务发布失败: {e}")


@router.post("/api/exam/generate")
def generate_exam(request: ExamGenerateRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        teacher, classrooms = get_current_teacher_and_classrooms(req, db)
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
                messages = [{"role": "user", "content": prompt}]
                system_instruction = "你是专业的德语考试出题助手，只返回JSON格式数据。"
                text = generate_response(messages, system_instruction=system_instruction)
                text = text.strip()
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

        def _personalize_questions(base_questions: list, weak_point: str | None) -> list:
            """基于基础题快速个性化，避免逐个学生调用 AI 导致超时。"""
            weak = (weak_point or "综合语法").strip() or "综合语法"
            out = []
            for q in base_questions or []:
                item = dict(q)
                if item.get("type") == "grammar":
                    inst = str(item.get("instruction", "")).strip()
                    item["instruction"] = f"{inst}（个性化强化：{weak}）" if inst else f"个性化强化：{weak}"
                elif item.get("type") == "writing":
                    content = str(item.get("content", "")).strip()
                    item["content"] = f"{content}\n\n【个性化要求】请重点体现：{weak}。"
                out.append(item)
            return out

        students_map: dict[int, any] = {}
        for classroom in classrooms:
            for s in StudentCRUD.list_by_class(db, classroom.id):
                students_map[s.id] = s
        students = list(students_map.values())

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
            base_questions = _generate_questions_for_student()
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
                personalized_q = _personalize_questions(base_questions, s.weak_point)
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
    except HTTPException:
        raise
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


@router.get("/api/teacher/pending-students")
def list_pending_students(request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher = require_teacher(request, db)
        students = StudentCRUD.list_pending_by_teacher(db, teacher.id)
        result = [
            {
                "id": s.id,
                "uid": s.uid,
                "name": s.name,
                "class_id": s.class_id,
                "class_ids": StudentCRUD.list_class_ids(db, s.id),
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in students
        ]
        return ok(result)
    except Exception as e:
        return fail(f"获取待审核学生失败: {e}")


@router.get("/api/teacher/students")
def list_class_students(request: Request = None, db: Session = Depends(get_db)):
    try:
        _, classrooms = get_current_teacher_and_classrooms(request, db)
        students_map: dict[int, any] = {}
        class_name_by_id = {c.id: c.class_name for c in classrooms}
        for classroom in classrooms:
            for s in StudentCRUD.list_by_class(db, classroom.id):
                students_map[s.id] = s

        result = []
        for s in students_map.values():
            latest_metrics = refresh_student_metrics(db, s.id)
            class_names = [class_name_by_id.get(cid) for cid in StudentCRUD.list_class_ids(db, s.id)]
            class_names = [x for x in class_names if x]
            result.append(
                {
                    "id": s.id,
                    "uid": s.uid,
                    "name": s.name,
                    "status": s.status,
                    "class_id": s.class_id,
                    "class_ids": StudentCRUD.list_class_ids(db, s.id),
                    "class_name": class_names[0] if class_names else None,
                    "class_names": class_names,
                    "active_score": latest_metrics["active_score"],
                    "overall_score": latest_metrics["overall_score"],
                    "weak_point": latest_metrics["weak_point"],
                    "created_at": s.created_at.isoformat(),
                }
            )
        return ok(result)
    except Exception as e:
        return fail(f"获取班级学生失败: {e}")


@router.put("/api/teacher/students/{student_id}")
def update_class_student(
    student_id: int,
    body: TeacherStudentUpdateBody,
    request: Request = None,
    db: Session = Depends(get_db),
):
    try:
        teacher, classrooms = get_current_teacher_and_classrooms(request, db)
        teacher_class_ids = {c.id for c in classrooms}
        student = StudentCRUD.get_by_id(db, student_id)
        if not student:
            return fail("学生不存在", 404)

        student_class_ids = set(StudentCRUD.list_class_ids(db, student.id))
        if not (student_class_ids & teacher_class_ids):
            return fail("无权操作该学生", 403)

        updates = body.model_dump(exclude_unset=True)
        updates.pop("active_score", None)
        updates.pop("overall_score", None)
        if "status" in updates and updates["status"] not in {"pending", "approved", "rejected"}:
            return fail("学生状态非法", 400)
        if "class_id" in updates:
            new_class_id = updates["class_id"]
            if new_class_id is not None and new_class_id not in teacher_class_ids:
                return fail("仅可调整到您管理的班级", 400)

            new_class_ids = set(student_class_ids)
            if new_class_id is None:
                new_class_ids = new_class_ids - teacher_class_ids
            else:
                new_class_ids.add(new_class_id)
            StudentCRUD.set_classes(db, student, sorted(new_class_ids))

            updates.pop("class_id", None)

        StudentCRUD.update(db, student, **updates)

        user = UserCRUD.get_by_id(db, student.user_id)
        if user:
            if "name" in updates:
                user.display_name = updates["name"]
            if "status" in updates:
                user.status = updates["status"]
            db.commit()

        latest_metrics = refresh_student_metrics(db, student.id)

        return ok(
            {
                "id": student.id,
                "uid": student.uid,
                "name": student.name,
                "status": student.status,
                "class_id": student.class_id,
                "active_score": latest_metrics["active_score"],
                "overall_score": latest_metrics["overall_score"],
                "weak_point": latest_metrics["weak_point"],
            },
            "学生信息更新成功",
        )
    except Exception as e:
        return fail(f"更新学生信息失败: {e}")


@router.delete("/api/teacher/students/{student_id}")
def remove_student_from_class(student_id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher, classrooms = get_current_teacher_and_classrooms(request, db)
        teacher_class_ids = {c.id for c in classrooms}
        student = StudentCRUD.get_by_id(db, student_id)
        if not student:
            return fail("学生不存在", 404)
        student_class_ids = set(StudentCRUD.list_class_ids(db, student.id))
        if not (student_class_ids & teacher_class_ids):
            return fail("无权操作该学生", 403)

        remain_ids = sorted(student_class_ids - teacher_class_ids)
        StudentCRUD.set_classes(db, student, remain_ids)
        return ok(message="学生已移出当前班级")
    except Exception as e:
        return fail(f"移出学生失败: {e}")


@router.put("/api/teacher/students/{student_id}/approve")
def approve_student(student_id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher = require_teacher(request, db)
        student = StudentCRUD.get_by_id(db, student_id)
        if not student:
            return fail("学生不存在", 404)

        teacher_class_ids = {c.id for c in ClassroomCRUD.list_by_teacher(db, teacher.id)}
        student_class_ids = set(StudentCRUD.list_class_ids(db, student.id))
        if not (student_class_ids & teacher_class_ids):
            return fail("无权操作该学生", 403)
        
        StudentCRUD.update_status(db, student_id, "approved")
        UserCRUD.update_status(db, student.user_id, "approved")
        return ok(message="审批通过成功")
    except Exception as e:
        return fail(f"审批学生失败: {e}")


@router.put("/api/teacher/students/{student_id}/reject")
def reject_student(student_id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        teacher = require_teacher(request, db)
        student = StudentCRUD.get_by_id(db, student_id)
        if not student:
            return fail("学生不存在", 404)

        teacher_class_ids = {c.id for c in ClassroomCRUD.list_by_teacher(db, teacher.id)}
        student_class_ids = set(StudentCRUD.list_class_ids(db, student.id))
        if not (student_class_ids & teacher_class_ids):
            return fail("无权操作该学生", 403)
        
        StudentCRUD.update_status(db, student_id, "rejected")
        UserCRUD.update_status(db, student.user_id, "rejected")
        remain_ids = sorted(student_class_ids - teacher_class_ids)
        StudentCRUD.set_classes(db, student, remain_ids)
        return ok(message="已拒绝该生加入班级")
    except Exception as e:
        return fail(f"拒绝学生失败: {e}")
