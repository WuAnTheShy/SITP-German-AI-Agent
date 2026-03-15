import io
import json
import urllib.parse
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from crud.repositories import (
    StudentCRUD,
    StudentAbilityCRUD,
    HomeworkCRUD,
    HomeworkReviewCRUD,
    ExamCRUD,
    ExamAssignmentCRUD,
    ScenarioCRUD,
    ScenarioPushCRUD,
)
from models.entities import ExamAssignment, Exam
from schemas.entities import (
    ScenarioCreate,
    ScenarioPushCreate,
    HomeworkReviewCreate,
)
from core.responses import ok, fail, to_float
from core.deps import require_teacher, get_current_teacher_and_classroom

router = APIRouter()


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


@router.get("/api/student/detail")
def get_student_detail(id: str, request: Request = None, db: Session = Depends(get_db)):
    try:
        _, classroom = get_current_teacher_and_classroom(request, db)
        student = StudentCRUD.get_by_uid(db, id)
        if not student:
            return fail("学生不存在", 404)
        if student.class_id != classroom.id:
            return fail("无权查看该学生", 403)
        ability = StudentAbilityCRUD.get_by_student_id(db, student.id)
        homeworks = HomeworkCRUD.list_by_student(db, student.id)
        exam_assignments = list(db.scalars(
            select(ExamAssignment).where(ExamAssignment.student_id == student.id).order_by(ExamAssignment.assigned_at.desc())
        ))
        exams_data = []
        for ea in exam_assignments:
            exam = ExamCRUD.get_by_id(db, ea.exam_id)
            if exam:
                exams_data.append({
                    "id": ea.id,
                    "examId": exam.id,
                    "examCode": exam.exam_code,
                    "strategy": exam.strategy,
                    "assignedAt": ea.assigned_at.strftime("%Y-%m-%d"),
                    "content": ea.personalized_content if exam.strategy == "personalized" else exam.content,
                })
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
            "exams": exams_data,
        }
        return ok(data)
    except Exception as e:
        return fail(f"获取学生详情失败: {e}")


@router.get("/api/homework/detail")
def get_homework_detail(id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        _, classroom = get_current_teacher_and_classroom(request, db)
        hw = HomeworkCRUD.get_by_id(db, id)
        if not hw:
            return fail("作业不存在", 404)
        student = StudentCRUD.get_by_id(db, hw.student_id)
        if not student or student.class_id != classroom.id:
            return fail("无权查看该作业", 403)
        file_url = hw.file_url
        if hw.file_type == "json_exam":
            file_url = f"/api/homework/download/{hw.id}"
        data = {
            "type": hw.file_type or "text",
            "meta": {
                "fileUrl": file_url,
                "fileName": hw.file_name or f"homework-{hw.id}.txt",
                "fileSize": hw.file_size or "自动生成",
                "uploadTime": (hw.submitted_at or hw.created_at).strftime("%Y-%m-%d %H:%M"),
            },
            "aiComment": hw.ai_comment or "暂无 AI 评价数据。",
        }
        return ok(data)
    except Exception as e:
        return fail(f"获取作业详情失败: {e}")


@router.get("/api/homework/download/{id}")
def download_homework_as_text(id: int, request: Request = None, db: Session = Depends(get_db)):
    try:
        _, classroom = get_current_teacher_and_classroom(request, db)
        hw = HomeworkCRUD.get_by_id(db, id)
        if not hw:
            raise HTTPException(status_code=404, detail="作业不存在")
        student = StudentCRUD.get_by_id(db, hw.student_id)
        if not student or student.class_id != classroom.id:
            raise HTTPException(status_code=403, detail="无权下载该作业")
        if hw.file_type != "json_exam":
            if hw.file_url and hw.file_url.startswith("http"):
                return RedirectResponse(url=hw.file_url)
            raise HTTPException(status_code=400, detail="该作业类型不支持直接下载文本")
        assignment = None
        if hw.exam_assignment_id:
            assignment = db.scalar(select(ExamAssignment).where(ExamAssignment.id == hw.exam_assignment_id))
        if not assignment:
            raise HTTPException(status_code=404, detail="找不到对应的试卷分配记录")
        exam = db.scalar(select(Exam).where(Exam.id == assignment.exam_id))
        if not exam:
            raise HTTPException(status_code=404, detail="找不到对应的原始试卷")
        content = assignment.personalized_content if assignment.personalized_content else exam.content
        answers = {}
        try:
            if hw.file_url:
                answers = json.loads(hw.file_url)
        except Exception:
            pass
        student = StudentCRUD.get_by_id(db, hw.student_id)
        buffer = io.StringIO()
        buffer.write(f"学生姓名: {student.name if student else '未知'}\n")
        buffer.write(f"试卷代码: {exam.exam_code or 'N/A'}\n")
        buffer.write(f"提交时间: {hw.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if hw.submitted_at else '未知'}\n")
        buffer.write(f"最终得分: {hw.score if hw.score is not None else '未评分'}\n")
        buffer.write("=" * 40 + "\n\n")
        for idx, q in enumerate(content or []):
            q_type = q.get('type', '未知')
            buffer.write(f"题目 {idx + 1} [{q_type}]\n")
            buffer.write(f"要求: {q.get('instruction', '')}\n")
            buffer.write(f"内容: {q.get('content', '')}\n")
            if q_type == 'grammar':
                buffer.write("选项:\n")
                for opt in q.get('options', []):
                    buffer.write(f"  - {opt}\n")
                correct_ans = str(q.get('answer', ''))
                student_ans = str(answers.get(str(idx), ''))
                buffer.write(f"正确答案: {correct_ans}\n")
                buffer.write(f"学生答案: {student_ans}\n")
                is_correct = False
                if student_ans.strip().upper() == correct_ans.strip().upper() or \
                   (student_ans.startswith(correct_ans) and (len(student_ans) == len(correct_ans) or student_ans[len(correct_ans):len(correct_ans)+1] in '. ')):
                    is_correct = True
                buffer.write(f"判定: {'正确 ✅' if is_correct else '错误 ❌'}\n")
            else:
                student_ans = answers.get(str(idx), '')
                buffer.write(f"学生回答:\n{student_ans}\n")
            buffer.write("-" * 20 + "\n\n")
        buffer.write("AI 评价与反馈:\n")
        buffer.write(hw.ai_comment or "暂无反馈")
        buffer.write("\n")
        content_str = buffer.getvalue()
        buffer.close()
        student_name = student.name if student else "student"
        exam_code = exam.exam_code or "EXAM"
        filename = f"答卷_{exam_code}_{student_name}.txt"
        encoded_filename = urllib.parse.quote(filename)
        return StreamingResponse(
            io.BytesIO(content_str.encode('utf-8')),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"下载生成失败: {str(e)}")


@router.post("/api/homework/save")
def save_homework_review(request: HomeworkSaveRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        teacher, classroom = get_current_teacher_and_classroom(req, db)
        hw = HomeworkCRUD.get_by_id(db, request.homeworkId)
        if not hw:
            return fail("作业不存在", 404)
        student = StudentCRUD.get_by_id(db, hw.student_id)
        if not student or student.class_id != classroom.id:
            return fail("无权操作该作业", 403)
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


@router.post("/api/student/push-scheme")
def push_student_scheme(request: PushSchemeRequest, req: Request = None, db: Session = Depends(get_db)):
    try:
        teacher, classroom = get_current_teacher_and_classroom(req, db)
        student = StudentCRUD.get_by_uid(db, request.studentId)
        if not student:
            return fail("学生不存在", 404)
        if student.class_id != classroom.id:
            return fail("无权向该学生推送", 403)
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
