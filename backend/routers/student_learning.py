from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from crud.repositories import (
    VocabularyCRUD,
    StudentVocabCollectionCRUD,
    FavoriteCategoryCRUD,
    FavoriteCRUD,
    GrammarCategoryCRUD,
    GrammarExerciseCRUD,
    GrammarSubmissionCRUD,
    ErrorBookCategoryCRUD,
    ErrorBookEntryCRUD,
    ListeningMaterialCRUD,
    SpeakingEvaluationCRUD,
    WritingSessionCRUD,
    LearningSessionCRUD,
    StudentKnowledgeMasteryCRUD,
)
from schemas.entities import (
    StudentVocabCollectionCreate,
    VocabularyCreate,
    FavoriteCreate,
    GrammarSubmissionCreate,
    SpeakingEvaluationCreate,
    WritingSessionCreate,
)
from core.responses import ok, fail
from core.deps import require_student, current_student
from services.llm import ai_text, ai_json
from services.metrics import (
    track_learning_activity,
    refresh_student_metrics,
    parse_duration_minutes,
    compute_student_interaction_minutes,
)

router = APIRouter()

DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _track_and_refresh(
    db: Session,
    student_id: int,
    module: str,
    duration_minutes: int,
    content: str | None = None,
) -> None:
    """写入学习行为并刷新积极度；统计失败不影响主流程。"""
    try:
        track_learning_activity(
            db,
            student_id=student_id,
            module=module,
            duration_minutes=duration_minutes,
            content=content,
        )
        refresh_student_metrics(db, student_id)
    except Exception:
        pass


def _get_error_category_id(error_cats: dict[str, int]) -> int | None:
    """获取错题分类ID - 统一使用"全部"分类"""
    return error_cats.get("全部", next(iter(error_cats.values()), None) if error_cats else None)


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
    categoryId: int | None = None
    categoryName: str | None = None


class ErrorMasterReq(BaseModel):
    errorId: int
    categoryId: int | None = None


class FavAIExtendReq(BaseModel):
    content: str
    type: str = "note"


class FavoriteAddReq(BaseModel):
    type: str = "note"
    content: str
    translate: str = ""
    rule: str = ""
    note: str = ""


@router.get("/api/student/vocab/list")
def vocab_list(request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
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


@router.post("/api/student/vocab/collect")
def vocab_collect(req: VocabCollectReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        if req.isCollect:
            StudentVocabCollectionCRUD.collect(
                db, StudentVocabCollectionCreate(student_id=student.id, vocab_id=req.vocabId)
            )
            vocab = VocabularyCRUD.get_by_id(db, req.vocabId)
            vocab_cat = FavoriteCategoryCRUD.get_by_type(db, "vocab")
            if vocab and vocab_cat:
                existing_favs = FavoriteCRUD.list_by_student_and_category(db, student.id, vocab_cat.id)
                already_exists = any(f.content == vocab.german for f in existing_favs)
                if not already_exists:
                    FavoriteCRUD.create(db, FavoriteCreate(
                        student_id=student.id,
                        category_id=vocab_cat.id,
                        content=vocab.german,
                        translate=vocab.chinese,
                        note=vocab.example,
                    ))
            _track_and_refresh(db, student.id, "词汇学习", 2, "词汇收藏")
        else:
            StudentVocabCollectionCRUD.uncollect(db, student.id, req.vocabId)
            vocab = VocabularyCRUD.get_by_id(db, req.vocabId)
            vocab_cat = FavoriteCategoryCRUD.get_by_type(db, "vocab")
            if vocab and vocab_cat:
                existing_favs = FavoriteCRUD.list_by_student_and_category(db, student.id, vocab_cat.id)
                for f in existing_favs:
                    if f.content == vocab.german:
                        FavoriteCRUD.delete(db, f.id)
                        break
        return ok(None, "操作成功")
    except Exception as e:
        return fail(f"收藏操作失败: {e}")


@router.post("/api/student/vocab/generate")
def vocab_generate(req: VocabGenerateReq, db: Session = Depends(get_db)):
    try:
        existing = VocabularyCRUD.list_all(db, level=req.level, topic=req.topic)
        existing_words = [w.german for w in existing]
        prompt = (
            f"请生成5个德语{req.level}级别、主题「{req.topic}」的新词汇。\n"
            f"已有(不要重复): {', '.join(existing_words[:20])}\n"
            f'返回JSON数组: [{{"german":"…","chinese":"…","example":"例句…"}}]\n只返回JSON。'
        )
        words = ai_json(prompt, [])
        
        # 检查AI是否返回了有效结果
        if not words or not isinstance(words, list):
            return fail("AI生成词汇失败，请检查API配置")
        
        saved = []
        for w in words:
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
            except Exception as e:
                print(f"[Vocab] 保存词汇失败: {e}", flush=True)
                pass
        
        if not saved:
            return fail("未能生成有效词汇，请稍后重试")
            
        return ok(saved)
    except Exception as e:
        print(f"[Vocab] 生成词汇失败: {e}", flush=True)
        return fail(f"生成词汇失败: {str(e)}")


@router.get("/api/student/grammar/categories")
def grammar_categories(request: Request, db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        cats = GrammarCategoryCRUD.list_all(db)
        return ok([{"id": c.id, "name": c.name, "desc": c.description or ""} for c in cats])
    except Exception as e:
        return fail(f"获取分类失败: {e}")


@router.get("/api/student/grammar/exercises")
def grammar_exercises(request: Request, categoryId: int = Query(...), db: Session = Depends(get_db)):
    student = require_student(request, db)
    try:
        exs = GrammarExerciseCRUD.list_by_category(db, categoryId)
        # 获取当前学生的历史提交记录映射
        submissions = GrammarSubmissionCRUD.list_by_student_and_exercises(
            db, student.id, [e.id for e in exs]
        )
        submission_map = {s.exercise_id: s for s in submissions}
        
        result = []
        for e in exs:
            item = {"id": e.id, "question": e.question}
            # 如果有历史记录，添加到响应中
            if e.id in submission_map:
                sub = submission_map[e.id]
                item["userAnswer"] = sub.user_answer
                item["isCorrect"] = sub.is_correct
                item["analysis"] = sub.ai_analysis or ""
                item["submittedAt"] = sub.submitted_at.isoformat() if sub.submitted_at else None
                item["hasHistory"] = True
            else:
                item["hasHistory"] = False
            result.append(item)
        
        return ok(result)
    except Exception as e:
        return fail(f"获取练习失败: {e}")


@router.post("/api/student/grammar/submit")
def grammar_submit(req: GrammarSubmitReq, request: Request, db: Session = Depends(get_db)):
    """
    语法题目提交接口
    1. 保存/更新学生答题历史到GrammarSubmission
    2. 答错时同步到错题本，答对时标记为已掌握
    """
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        
        details = []
        correct_count = 0
        error_cats = {c.name: c.id for c in ErrorBookCategoryCRUD.list_all(db)}
        
        for ans in req.answers:
            ex = GrammarExerciseCRUD.get_by_id(db, ans.exerciseId)
            if not ex:
                continue
            
            # 判断答案是否正确（不区分大小写）
            is_correct = ans.userAnswer.strip().lower() == ex.correct_answer.strip().lower()
            if is_correct:
                correct_count += 1
            
            # 生成或获取分析文本
            analysis = ex.analysis or ""
            if not is_correct and not analysis:
                try:
                    analysis = ai_text(
                        f"德语语法题:\n题目:{ex.question}\n学生答:{ans.userAnswer}\n"
                        f"正确答案:{ex.correct_answer}\n请用中文简短解释错误原因(50字以内)。",
                        "请参考正确答案复习。",
                    )
                except Exception as e:
                    print(f"[Grammar] AI解析失败: {e}", flush=True)
                    analysis = "请参考正确答案复习"
            
            # 保存答题历史（UPSERT逻辑）
            last_sub = GrammarSubmissionCRUD.get_last_submission(db, student.id, ans.exerciseId)
            if last_sub:
                # 更新现有记录
                last_sub.user_answer = ans.userAnswer
                last_sub.is_correct = is_correct
                last_sub.ai_analysis = analysis if not is_correct else None
                db.merge(last_sub)
            else:
                # 创建新记录
                GrammarSubmissionCRUD.create(
                    db,
                    GrammarSubmissionCreate(
                        student_id=student.id, exercise_id=ans.exerciseId,
                        user_answer=ans.userAnswer, is_correct=is_correct,
                        ai_analysis=analysis if not is_correct else None,
                    ),
                )
            
            # 【错题本同步逻辑】
            eb_cat_id = _get_error_category_id(error_cats)
            
            if eb_cat_id:
                if not is_correct:
                    # 答错：添加或更新错题本记录
                    try:
                        existing_error = db.scalar(
                            select(ErrorBookEntry).where(
                                (ErrorBookEntry.student_id == student.id) &
                                (ErrorBookEntry.source == "语法练习") &
                                (ErrorBookEntry.question == ex.question)
                            )
                        )
                        if existing_error:
                            # 更新现有错题记录
                            existing_error.user_answer = ans.userAnswer
                            existing_error.correct_answer = ex.correct_answer
                            existing_error.analysis = analysis
                            existing_error.is_mastered = False
                            db.merge(existing_error)
                        else:
                            # 新增错题记录
                            new_error = ErrorBookEntry(
                                student_id=student.id, 
                                category_id=eb_cat_id,
                                source="语法练习", 
                                question=ex.question,
                                user_answer=ans.userAnswer,
                                correct_answer=ex.correct_answer, 
                                analysis=analysis,
                            )
                            db.add(new_error)
                    except Exception as e:
                        print(f"[Grammar] 错题本同步失败: {e}", flush=True)
                else:
                    # 答对：标记错题本中该题为已掌握（如果存在的话）
                    try:
                        existing_error = db.scalar(
                            select(ErrorBookEntry).where(
                                (ErrorBookEntry.student_id == student.id) &
                                (ErrorBookEntry.source == "语法练习") &
                                (ErrorBookEntry.question == ex.question)
                            )
                        )
                        if existing_error:
                            existing_error.is_mastered = True
                            db.merge(existing_error)
                    except Exception as e:
                        print(f"[Grammar] 更新错题本状态失败: {e}", flush=True)
            
            details.append({
                "exerciseId": ex.id, 
                "isCorrect": is_correct,
                "correctAnswer": ex.correct_answer,
                "analysis": analysis if not is_correct else "",
            })
        
        db.commit()  # 提交所有更改
        
        wrong_count = len(req.answers) - correct_count
        _track_and_refresh(
            db,
            student.id,
            "语法练习",
            max(3, len(req.answers) * 2),
            f"语法提交: 正确{correct_count}/{len(req.answers)}",
        )
        
        return ok({
            "totalCount": len(req.answers), 
            "correctCount": correct_count,
            "wrongCount": wrong_count, 
            "detailList": details,
        })
    except Exception as e:
        db.rollback()
        print(f"[Grammar Submit] 错误: {e}", flush=True)
        return fail(f"提交失败: {str(e)}")


@router.get("/api/student/listening/materials")
def listening_materials(db: Session = Depends(get_db)):
    try:
        mats = ListeningMaterialCRUD.list_all(db)
        return ok([
            {"id": m.id, "title": m.title, "level": m.level, "duration": m.duration}
            for m in mats
        ])
    except Exception as e:
        return fail(f"获取听力材料失败: {e}")


@router.get("/api/student/listening/material/detail")
def listening_material_detail(materialId: int = Query(...), db: Session = Depends(get_db)):
    try:
        m = ListeningMaterialCRUD.get_by_id(db, materialId)
        if not m:
            return fail("材料不存在", 404)
        return ok({"audioUrl": m.audio_url, "script": m.script or ""})
    except Exception as e:
        return fail(f"获取详情失败: {e}")


@router.post("/api/student/speaking/evaluate")
def speaking_evaluate(req: SpeakingEvalReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
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
        result = ai_json(prompt, {
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
        duration_minutes = parse_duration_minutes(getattr(material, "duration", None))
        _track_and_refresh(
            db,
            student.id,
            "听说训练",
            duration_minutes,
            f"口语评测: {material.title}",
        )
        return ok(result)
    except Exception as e:
        return fail(f"评估失败: {e}")


@router.post("/api/student/writing/check")
def writing_check(req: WritingReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        prompt = (
            f"请检查以下德语文本的语法和拼写错误:\n\n{req.userText}\n\n"
            f"返回JSON: {{\"errors\":[{{\"position\":\"出错位置\",\"error\":\"错误描述\","
            f"\"suggestion\":\"修改建议\"}}],\"polishedText\":\"修正后完整文本\"}}\n只返回JSON。"
        )
        result = ai_json(prompt, {"errors": [], "polishedText": req.userText})
        if student:
            WritingSessionCRUD.create(
                db,
                WritingSessionCreate(
                    student_id=student.id, session_type="check",
                    user_text=req.userText, result_json=result,
                ),
            )
            writing_minutes = max(2, min(25, len(req.userText.strip()) // 80 + 2))
            _track_and_refresh(db, student.id, "写作辅助", writing_minutes, "写作纠错")
        return ok(result)
    except Exception as e:
        return fail(f"检查失败: {e}")


@router.post("/api/student/writing/generate-sample")
def writing_generate_sample(req: WritingReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        prompt = (
            f"学生正在练习德语写作，主题/草稿如下:\n\n{req.userText}\n\n"
            f"请生成一篇优秀的德语范文(A2-B1水平，150-200词)。\n"
            f'返回JSON: {{"sampleEssay":"范文内容"}}\n只返回JSON。'
        )
        result = ai_json(prompt, {
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
            writing_minutes = max(3, min(30, len(req.userText.strip()) // 70 + 3))
            _track_and_refresh(db, student.id, "写作辅助", writing_minutes, "写作范文")
        return ok(result)
    except Exception as e:
        return fail(f"生成范文失败: {e}")


@router.get("/api/student/error-book/categories")
def error_book_categories(request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        data = ErrorBookEntryCRUD.count_by_category(db, student.id)
        return ok(data)
    except Exception as e:
        return fail(f"获取错题分类失败: {e}")


@router.get("/api/student/error-book/list")
def error_book_list(
    categoryId: int = Query(None), request: Request = None, db: Session = Depends(get_db)
):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        if categoryId:
            entries = ErrorBookEntryCRUD.list_by_student_and_category(db, student.id, categoryId)
        else:
            entries = ErrorBookEntryCRUD.list_by_student(db, student.id)
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


@router.post("/api/student/error-book/start-review")
def error_book_start_review(req: ErrorReviewReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        if req.categoryId:
            entries = ErrorBookEntryCRUD.list_by_student_and_category(db, student.id, req.categoryId)
        else:
            entries = ErrorBookEntryCRUD.list_by_student(db, student.id)
        cat_name = req.categoryName or "所有错题"
        if not entries:
            return ok({"reviewTip": f"🎉 「{cat_name}」没有未掌握的错题，继续保持！"})
        questions_summary = "\n".join(
            [f"- 题目: {e.question} | 学生答: {e.user_answer} | 正确: {e.correct_answer}" for e in entries[:5]]
        )
        prompt = (
            f"学生在「{cat_name}」分类下有以下错题:\n{questions_summary}\n"
            f"请用中文给出针对性的复习建议(100字以内)。"
        )
        tip = ai_text(prompt, f"建议重点复习「{cat_name}」相关语法规则，结合例句反复练习。")
        # 确保返回的提示不为空
        if not tip or tip.strip() == "":
            tip = f"建议重点复习「{cat_name}」相关语法规则，结合例句反复练习。"
        _track_and_refresh(db, student.id, "语法练习", 3, f"错题复盘: {cat_name}")
        return ok({"reviewTip": tip})
    except Exception as e:
        return fail(f"生成复习建议失败: {e}")


@router.post("/api/student/error-book/mark-mastered")
def error_book_mark_mastered(req: ErrorMasterReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
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


@router.delete("/api/student/error-book/delete/{error_id}")
def error_book_delete(error_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
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


@router.get("/api/student/favorites/categories")
def favorites_categories(request: Request, db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        cats = FavoriteCategoryCRUD.list_all(db)
        return ok([{"id": c.id, "type": c.type, "name": c.name} for c in cats])
    except Exception as e:
        return fail(f"获取收藏分类失败: {e}")


@router.get("/api/student/favorites/list")
def favorites_list(
    type: str = Query("all"), request: Request = None, db: Session = Depends(get_db)
):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        result = []
        if type == "all":
            categories = FavoriteCategoryCRUD.list_all(db)
            for c in categories:
                items = FavoriteCRUD.list_by_student_and_type(db, student.id, c.type)
                for f in items:
                    result.append({
                        "id": f.id,
                        "type": c.type,
                        "content": f.content,
                        "translate": f.translate,
                        "rule": f.rule,
                        "note": f.note,
                    })
        else:
            items = FavoriteCRUD.list_by_student_and_type(db, student.id, type)
            for f in items:
                result.append({
                    "id": f.id,
                    "type": type,
                    "content": f.content,
                    "translate": f.translate,
                    "rule": f.rule,
                    "note": f.note,
                })

        return ok(result)
    except Exception as e:
        return fail(f"获取收藏列表失败: {e}")


@router.delete("/api/student/favorites/{fav_id}")
def favorites_delete(fav_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        fav = FavoriteCRUD.get_by_id(db, fav_id)
        if not fav:
            return fail("收藏不存在", 404)
        if fav.student_id != student.id:
            return fail("无权操作该收藏", 403)
        vocab_cat = FavoriteCategoryCRUD.get_by_type(db, "vocab")
        if vocab_cat and fav.category_id == vocab_cat.id:
            all_vocabs = VocabularyCRUD.list_all(db)
            for v in all_vocabs:
                if v.german == fav.content:
                    StudentVocabCollectionCRUD.uncollect(db, student.id, v.id)
                    break
        FavoriteCRUD.delete(db, fav_id)
        return ok(None, "删除成功")
    except Exception as e:
        return fail(f"删除失败: {e}")


@router.post("/api/student/favorites/ai-extend")
def favorites_ai_extend(req: FavAIExtendReq, request: Request = None, db: Session = Depends(get_db)):
    require_student(request, db)
    try:
        # 验证内容是否为空
        if not req.content or req.content.strip() == "":
            return fail("内容不能为空")
        
        # 验证类型是否有效
        valid_types = ["vocab", "grammar", "sentence", "note"]
        if req.type not in valid_types:
            # 尝试根据内容自动判断类型
            content = req.content.strip()
            if any(char.isdigit() for char in content) or len(content.split()) > 10:
                # 包含数字或长文本，可能是笔记
                req.type = "note"
            elif len(content.split()) <= 3 and any(char.isupper() for char in content):
                # 短文本且包含大写字母，可能是词汇
                req.type = "vocab"
            elif "." in content or "，" in content or "!" in content or "?" in content:
                # 包含标点，可能是句子
                req.type = "sentence"
            else:
                # 默认为笔记
                req.type = "note"
        
        type_prompts = {
            "vocab": f"请对德语词汇「{req.content}」进行扩展：给出词性、复数形式、常用搭配和2个例句。用中文回答。",
            "grammar": f"请对德语语法规则「{req.content}」进行扩展讲解：给出详细说明和3个例句。用中文回答。",
            "sentence": f"请对德语句子「{req.content}」进行分析：逐词翻译、语法结构、类似表达。用中文回答。",
            "note": f"请对学习笔记「{req.content}」进行扩展：补充相关知识点和记忆技巧。用中文回答。",
        }
        prompt = type_prompts.get(req.type, f"请对「{req.content}」进行扩展讲解，用中文回答。")
        extended = ai_text(prompt, f"暂无法为「{req.content}」生成扩展内容。")
        # 确保返回的扩展内容不为空
        if not extended or extended.strip() == "":
            extended = f"暂无法为「{req.content}」生成扩展内容。"
        return ok({"extendContent": extended})
    except Exception as e:
        return fail(f"AI扩展失败: {e}")


@router.get("/api/student/learning/progress")
def learning_progress(request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)

        latest_metrics = refresh_student_metrics(db, student.id)
        total_time = LearningSessionCRUD.total_minutes(db, student.id)
        week_time = LearningSessionCRUD.week_minutes(db, student.id)
        interaction_minutes = compute_student_interaction_minutes(db, student.id, days=7)
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
            if (hasattr(s.session_date, 'date') and s.session_date.date() >= week_start)
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
                "time": round((day_map[i]["time"] if i in day_map else 0) / 60, 1),
                "content": "、".join(day_map[i]["contents"]) if i in day_map else "",
            }
            for i in range(7)
        ]

        total_hours = round(total_time / 60, 1)
        week_hours = round(week_time / 60, 1)
        interaction_hours = round(interaction_minutes / 60, 1)
        if week_time > 0:
            insight = (
                f"最近7天累计学习 {week_hours} 小时，互动时长 {interaction_hours} 小时，"
                f"当前积极度 {latest_metrics['active_score']}%，综合评分 {latest_metrics['overall_score']}。"
            )
        else:
            insight = "最近7天暂未记录到学习行为，建议先完成一次词汇或语法练习。"

        return ok({
            "totalTime": total_hours,
            "weekTime": week_hours,
            "finishRate": finish_rate,
            "activeScore": latest_metrics["active_score"],
            "overallScore": latest_metrics["overall_score"],
            "interactionTime": interaction_hours,
            "insight": insight,
            "modules": modules,
            "knowledge": knowledge,
            "weekReport": week_report,
        })
    except Exception as e:
        return fail(f"获取学习进度失败: {e}")


@router.post("/api/student/favorites/add")
def favorites_add(req: FavoriteAddReq, request: Request, db: Session = Depends(get_db)):
    try:
        student = current_student(request, db)
        if not student:
            return fail("未找到学生信息", 401)
        
        # 验证内容是否为空
        if not req.content or req.content.strip() == "":
            return fail("内容不能为空")
        
        # 验证类型是否有效
        valid_types = ["vocab", "grammar", "sentence", "note"]
        if req.type not in valid_types:
            return fail("无效的收藏类型")
        
        # 获取或创建分类
        category = FavoriteCategoryCRUD.get_by_type(db, req.type)
        if not category:
            # 如果分类不存在，创建默认分类
            from schemas.entities import FavoriteCategoryCreate
            category = FavoriteCategoryCRUD.create(
                db,
                FavoriteCategoryCreate(
                    type=req.type,
                    name={
                        "vocab": "词汇",
                        "grammar": "语法",
                        "sentence": "句子",
                        "note": "笔记"
                    }.get(req.type, "笔记")
                )
            )
        
        # 检查是否已存在相同内容的收藏
        existing_favs = FavoriteCRUD.list_by_student_and_category(db, student.id, category.id)
        for fav in existing_favs:
            if fav.content == req.content:
                return fail("该内容已在收藏夹中")
        
        # 创建收藏
        favorite = FavoriteCRUD.create(
            db,
            FavoriteCreate(
                student_id=student.id,
                category_id=category.id,
                content=req.content,
                translate=req.translate,
                rule=req.rule,
                note=req.note
            )
        )
        
        # 记录学习行为
        _track_and_refresh(
            db,
            student.id,
            "收藏",
            1,
            f"添加{category.name}收藏"
        )
        
        return ok({
            "id": favorite.id,
            "type": req.type,
            "content": favorite.content,
            "translate": favorite.translate,
            "rule": favorite.rule,
            "note": favorite.note
        }, "添加收藏成功")
    except Exception as e:
        return fail(f"添加收藏失败: {e}")
