import json
import os

from google import genai
from google.genai import types

from crud.repositories import (
    StudentCRUD,
    UserCRUD,
    ChatMessageCRUD,
    TeacherChatMessageCRUD,
)
from db.session import SessionLocal

# Proxy (same as main)
_proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
if _proxy:
    os.environ.setdefault("HTTP_PROXY", _proxy)
    os.environ.setdefault("HTTPS_PROXY", _proxy)

# 修复 Windows 下 httpx 编码请求头时默认 ascii 导致的中文等非 ASCII 报错（如系统用户名在头里）
# 错误位置：httpx._models._normalize_header_value -> value.encode(encoding or "ascii")
try:
    import httpx._models as _httpx_models
    _orig_normalize = _httpx_models._normalize_header_value

    def _normalize_header_value_utf8(value, encoding):
        return _orig_normalize(value, encoding or "utf-8")

    _httpx_models._normalize_header_value = _normalize_header_value_utf8
except Exception:
    pass

_gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_ID = "gemini-2.5-flash"
TEACHER_SYSTEM = (
    "你是一个高级教学AI教研助手，负责协助德语教师分析学情、制定教案和出题等。"
    "请用中文与教师进行沟通，提供专业、基于数据的教学建议和德语教学方案。"
)
STUDENT_SYSTEM = (
    "你是同济大学的 AI 德语助教，帮助学生学习德语。"
    "回复简洁、准确。除非用户要求中文，否则用德语回答并在括号内给出中文翻译。"
)

MEMORY_REFRESH_EVERY = 16

_MEMORY_SUMMARY_PROMPT = """You maintain a short learner profile (max 400 Chinese characters).
Previous profile (may be empty):
---
{prev}
---
Recent dialogue (latest lines):
---
{dialogue}
---
Output ONLY the updated profile: level, goals, recurring mistakes, current topics. No markdown."""


def ai_text(prompt: str, fallback: str = "") -> str:
    """安全调用 Gemini 返回纯文本"""
    try:
        resp = _gemini_client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=STUDENT_SYSTEM,
            ),
        )
        return resp.text.strip()
    except Exception as e:
        try:
            print(f"[AI] {type(e).__name__}", flush=True)
        except Exception:
            print("[AI] error", flush=True)
        return fallback


def ai_json(prompt: str, fallback=None):
    """调用 Gemini 并尝试解析 JSON，失败返回 fallback"""
    try:
        resp = _gemini_client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=STUDENT_SYSTEM,
            ),
        )
        text = resp.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())
    except Exception as e:
        try:
            print(f"[AI JSON] {type(e).__name__}", flush=True)
        except Exception:
            print("[AI JSON] error", flush=True)
        return fallback


def history_to_gemini_contents(messages: list, max_turns: int = 12) -> list:
    """将库中 user/assistant 消息转为 Gemini contents（每条为 user 或 model）"""
    slice_msgs = messages[-(max_turns * 2) :] if len(messages) > max_turns * 2 else messages
    out = []
    for m in slice_msgs:
        role = "user" if m.role == "user" else "model"
        out.append(types.Content(role=role, parts=[types.Part.from_text(text=m.content)]))
    return out


def refresh_student_memory(student_id: int, session_id: int) -> None:
    db = SessionLocal()
    try:
        st = StudentCRUD.get_by_id(db, student_id)
        if not st:
            return
        msgs = ChatMessageCRUD.list_by_session(db, session_id)
        tail = msgs[-24:] if len(msgs) > 24 else msgs
        dialogue = "\n".join(f"{'U' if m.role == 'user' else 'A'}: {m.content[:500]}" for m in tail)
        prev = (st.long_memory_summary or "")[:1200]
        prompt = _MEMORY_SUMMARY_PROMPT.format(prev=prev, dialogue=dialogue)
        resp = _gemini_client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(http_options={"timeout": 60_000}),
        )
        text = (resp.text or "").strip()[:2000]
        if text:
            StudentCRUD.update_long_memory(db, student_id, text)
    except Exception as e:
        try:
            print(f"[Memory] student refresh skip: {type(e).__name__}", flush=True)
        except Exception:
            print("[Memory] student refresh skip", flush=True)
    finally:
        db.close()


def refresh_teacher_memory(user_id: int, session_id: int) -> None:
    db = SessionLocal()
    try:
        u = UserCRUD.get_by_id(db, user_id)
        if not u:
            return
        msgs = TeacherChatMessageCRUD.list_by_session(db, session_id)
        tail = msgs[-24:] if len(msgs) > 24 else msgs
        dialogue = "\n".join(f"{'U' if m.role == 'user' else 'A'}: {m.content[:500]}" for m in tail)
        prev = (u.long_memory_summary or "")[:1200]
        prompt = (
            "Update a short teaching-assistant context (max 400 Chinese chars) for this teacher. "
            "Previous:\n---\n" + prev + "\n---\nRecent:\n---\n" + dialogue + "\n---\nOutput only the summary."
        )
        resp = _gemini_client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(http_options={"timeout": 60_000}),
        )
        text = (resp.text or "").strip()[:2000]
        if text:
            UserCRUD.update_long_memory(db, user_id, text)
    except Exception as e:
        try:
            print(f"[Memory] teacher refresh skip: {type(e).__name__}", flush=True)
        except Exception:
            print("[Memory] teacher refresh skip", flush=True)
    finally:
        db.close()


def get_client():
    """Return the Gemini client for endpoints that need to call generate_content directly."""
    return _gemini_client
