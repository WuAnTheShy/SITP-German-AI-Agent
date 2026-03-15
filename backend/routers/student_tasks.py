import json
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from crud.repositories import HomeworkCRUD
from models.entities import ExamAssignment, Exam, Homework, Scenario, ScenarioPush
from schemas.entities import HomeworkCreate
from core.responses import ok, fail
from core.deps import current_student

router = APIRouter()


class StudentExamSubmitReq(BaseModel):
    assignment_id: int
    answers: dict


class TaskCompleteReq(BaseModel):
    task_type: str
    task_id: int


@router.get("/api/student/tasks")
def get_student_tasks(request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return fail("请先登录", 401)
    tasks = []
    assignments = db.scalars(
        select(ExamAssignment)
        .where(ExamAssignment.student_id == student.id)
        .order_by(ExamAssignment.assigned_at.desc())
    ).all()
    for a in assignments:
        exam = db.scalar(select(Exam).where(Exam.id == a.exam_id))
        if exam:
            tasks.append({
                "id": f"exam_{a.id}",
                "type": "exam",
                "exam_id": exam.id,
                "assignment_id": a.id,
                "title": f"📝 测验: {exam.exam_code} ({exam.strategy == 'personalized' and '千人千面' or '基础出题'})",
                "createdAt": a.assigned_at.isoformat() if a.assigned_at else None,
                "status": "completed" if a.status == "completed" else "pending",
                "isPersonalized": exam.strategy == "personalized"
            })
    pushes = db.scalars(
        select(ScenarioPush)
        .where(ScenarioPush.student_id == student.id)
        .order_by(ScenarioPush.pushed_at.desc())
    ).all()
    for p in pushes:
        scenario = db.scalar(select(Scenario).where(Scenario.id == p.scenario_id))
        if scenario:
            tasks.append({
                "id": f"scenario_{p.id}",
                "type": "scenario",
                "scenario_id": scenario.id,
                "push_id": p.id,
                "title": f"💬 对话任务: {scenario.theme} - {scenario.persona}",
                "createdAt": p.pushed_at.isoformat() if p.pushed_at else None,
                "status": "completed" if p.push_status == "completed" else "pending",
                "difficulty": scenario.difficulty
            })
    tasks.sort(key=lambda x: x["createdAt"] or "", reverse=True)
    return ok(tasks)


@router.get("/api/student/exam/assignment/{assignment_id}")
def get_exam_for_student(assignment_id: int, request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return fail("未授权", 401)
    assignment = db.scalar(select(ExamAssignment).where(ExamAssignment.id == assignment_id, ExamAssignment.student_id == student.id))
    if not assignment:
        return fail("找不到该试卷分配记录")
    exam = db.scalar(select(Exam).where(Exam.id == assignment.exam_id))
    if not exam:
        return fail("找不到对应试卷")
    content = assignment.personalized_content if assignment.personalized_content else exam.content
    return ok({
        "assignment_id": assignment.id,
        "exam_id": exam.id,
        "exam_code": exam.exam_code,
        "strategy": exam.strategy,
        "content": content,
        "status": assignment.status
    })


@router.post("/api/student/exam/submit")
def submit_exam_answers(req: StudentExamSubmitReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未授权", 401)
        assignment = db.scalar(select(ExamAssignment).where(ExamAssignment.id == req.assignment_id, ExamAssignment.student_id == student.id))
        if not assignment:
            return fail("任务不存在")
        if assignment.status == "completed":
            return fail("该试卷已提交过")
        exam = db.scalar(select(Exam).where(Exam.id == assignment.exam_id))
        content = assignment.personalized_content if assignment.personalized_content else exam.content
        if not content:
            content = []
        earned_score = 0
        ai_comment_lines = []
        for idx, q_data in enumerate(content):
            q_score = q_data.get("score", 0)
            u_ans = req.answers.get(str(idx), "")
            if q_data.get("type") == "grammar":
                correct_ans = str(q_data.get("answer", ""))
                if correct_ans and (u_ans.startswith(correct_ans + '.') or u_ans.startswith(correct_ans + ' ') or u_ans == correct_ans or correct_ans.startswith(u_ans) or u_ans.startswith(correct_ans)):
                    earned_score += q_score
                else:
                    ai_comment_lines.append(f"第 {idx + 1} 题(语法): 答错了，你的答案 [{u_ans}]；正确答案 [{correct_ans}]")
            else:
                ai_comment_lines.append(f"第 {idx + 1} 题(写作): 已记录答案，待教师或AI后续评分。")
        assignment.status = "completed"
        HomeworkCRUD.create(db, HomeworkCreate(
            student_id=student.id,
            title=f"[随堂测验] {exam.exam_code} 的答卷",
            status="已完成",
            submitted_at=datetime.now(),
            score=float(earned_score),
            file_type="json_exam",
            file_url=json.dumps(req.answers, ensure_ascii=False),
            ai_comment="\n".join(ai_comment_lines) if ai_comment_lines else "语法全对！大题待教师评分。",
            exam_assignment_id=assignment.id
        ))
        db.commit()
        return ok({"score": earned_score, "message": "提交成功"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return fail(f"Server error: {str(e)}", 500)


@router.get("/api/student/exam/result/{assignment_id}")
def get_exam_result(assignment_id: int, request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return fail("未授权", 401)
    assignment = db.scalar(select(ExamAssignment).where(ExamAssignment.id == assignment_id, ExamAssignment.student_id == student.id))
    if not assignment:
        return fail("该记录不存在")
    exam = db.scalar(select(Exam).where(Exam.id == assignment.exam_id))
    content = assignment.personalized_content if assignment.personalized_content else exam.content
    homework = db.scalar(select(Homework).where(Homework.exam_assignment_id == assignment_id, Homework.student_id == student.id))
    answers = {}
    if homework and homework.file_url:
        try:
            answers = json.loads(homework.file_url)
        except Exception:
            pass
    return ok({
        "exam_code": exam.exam_code,
        "content": content,
        "answers": answers,
        "score": homework.score if homework else 0,
        "ai_comment": homework.ai_comment if homework else ""
    })


@router.post("/api/student/task/complete")
def complete_task(req: TaskCompleteReq, request: Request, db: Session = Depends(get_db)):
    student = current_student(request, db)
    if not student:
        return fail("未授权", 401)
    if req.task_type == "scenario":
        p = db.scalar(select(ScenarioPush).where(ScenarioPush.id == req.task_id, ScenarioPush.student_id == student.id))
        if p and p.push_status != "completed":
            p.push_status = "completed"
            db.commit()
    return ok()
