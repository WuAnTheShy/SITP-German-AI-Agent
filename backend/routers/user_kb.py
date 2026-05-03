"""
user_kb.py - 上传/删除/列表 API
"""
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.deps import require_login_user
from crud.repositories import KnowledgeBaseCRUD
from db.session import get_db
from services.kb_ingest import chunk_text, enrich_chunks_with_embeddings, extract_text

router = APIRouter(prefix="/api/user/kb", tags=["user-kb"])
KB_STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage" / "kb_private"


def _ingest_document_sync(db: Session, doc_id: int) -> None:
    doc = KnowledgeBaseCRUD.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    try:
        source_path = Path(doc["source_path"])
        text = extract_text(source_path, doc.get("mime_type"))
        chunks = chunk_text(text)
        if not chunks:
            KnowledgeBaseCRUD.set_document_status(db, doc_id, "failed", "文档内容为空或解析失败")
            return
        enriched = enrich_chunks_with_embeddings(chunks)
        KnowledgeBaseCRUD.replace_chunks(db, doc_id, enriched)
        KnowledgeBaseCRUD.set_document_status(db, doc_id, "ready", None, chunk_count=len(enriched))
    except Exception as e:
        KnowledgeBaseCRUD.set_document_status(db, doc_id, "failed", str(e)[:500])


@router.get("/docs")
def list_user_docs(db: Session = Depends(get_db), actor=Depends(require_login_user)):
    return KnowledgeBaseCRUD.list_documents(db, scope="private", owner_user_id=actor["user_id"])


@router.post("/upload")
async def upload_user_doc(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor=Depends(require_login_user),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(status_code=400, detail="暂仅支持 pdf/txt/md")
    KB_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f"{actor['user_id']}_{uuid4().hex}{suffix}"
    save_path = KB_STORAGE_DIR / saved_name
    data = await file.read()
    save_path.write_bytes(data)

    doc = KnowledgeBaseCRUD.create_document(
        db=db,
        title=Path(file.filename or "未命名文档").stem,
        source_name=file.filename or saved_name,
        source_path=str(save_path),
        mime_type=file.content_type,
        uploaded_by=actor["user_id"],
        scope="private",
        owner_user_id=actor["user_id"],
    )
    _ingest_document_sync(db, int(doc["id"]))
    return {"id": doc["id"], "status": "processing"}


@router.post("/upload-temporary")
async def upload_user_temp_doc(
    session_key: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor=Depends(require_login_user),
):
    """
    仅本会话资料：
    - 存在向量库中，但仅对当前会话可检索（由 session_key 过滤）
    - 仍归属当前用户，不会被他人检索
    """
    session_key = (session_key or "").strip()
    if not session_key:
        raise HTTPException(status_code=400, detail="session_key 不能为空")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(status_code=400, detail="暂仅支持 pdf/txt/md")
    KB_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f"{actor['user_id']}_{uuid4().hex}{suffix}"
    save_path = KB_STORAGE_DIR / saved_name
    data = await file.read()
    save_path.write_bytes(data)

    doc = KnowledgeBaseCRUD.create_document(
        db=db,
        title=Path(file.filename or "未命名文档").stem,
        source_name=file.filename or saved_name,
        source_path=str(save_path),
        mime_type=file.content_type,
        uploaded_by=actor["user_id"],
        scope="private",
        owner_user_id=actor["user_id"],
        is_temporary=True,
        session_key=session_key,
    )
    _ingest_document_sync(db, int(doc["id"]))
    return {"id": doc["id"], "status": "processing"}


@router.post("/reindex/{doc_id}")
def reindex_user_doc(doc_id: int, db: Session = Depends(get_db), actor=Depends(require_login_user)):
    doc = KnowledgeBaseCRUD.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.get("scope") != "private" or doc.get("owner_user_id") != actor["user_id"]:
        raise HTTPException(status_code=403, detail="无权操作该文档")
    KnowledgeBaseCRUD.set_document_status(db, doc_id, "processing", None)
    _ingest_document_sync(db, doc_id)
    return {"id": doc_id, "status": "processing"}


@router.delete("/docs/{doc_id}")
def delete_user_doc(doc_id: int, db: Session = Depends(get_db), actor=Depends(require_login_user)):
    doc = KnowledgeBaseCRUD.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc.get("scope") != "private" or doc.get("owner_user_id") != actor["user_id"]:
        raise HTTPException(status_code=403, detail="无权删除该文档")
    source_path = Path(doc.get("source_path") or "")
    ok = KnowledgeBaseCRUD.delete_document(db, doc_id)
    if ok and source_path.exists():
        try:
            source_path.unlink(missing_ok=True)
        except Exception:
            pass
    return {"deleted": bool(ok)}
