import json
import os
import requests

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

# 初始化千问 API 配置
MODEL_ID = "qwen-plus"
API_KEY = os.getenv("QWEN_API_KEY")
# 阿里云通义千问兼容模式 API 接口地址
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

print(f"[API] 尝试加载 QWEN_API_KEY: {API_KEY}")
if not API_KEY:
    print("警告: 未找到 QWEN_API_KEY")
else:
    print(f"[API] API Key 已配置: {API_KEY}")

TEACHER_SYSTEM = (
    "你是一个高级教学AI教研助手，负责协助德语教师分析学情、制定教案和出题等。"
    "请用中文与教师进行沟通，提供专业、基于数据的教学建议和德语教学方案。"
)
STUDENT_SYSTEM = (
    "你是同济大学的 AI 德语助教，专门帮助学生学习德语。"
    "你的职责包括：教授德语语法、词汇、发音，提供德语练习和对话练习，纠正德语错误，解释德语文化和习惯。"
    "回复时请使用中德双语：首先用德语回答，然后在括号内给出中文翻译。"
    "保持回答简洁、准确、专业，适合德语学习者理解。"
    "如果用户用中文提问，你也应该用中德双语回答；如果用户用德语提问，你同样用中德双语回答。"
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


def generate_response(messages, system_instruction=None):
    """使用千问模型 API 生成响应"""
    # 构建对话历史
    conversation = []
    
    # 如果有系统指令，作为第一条消息插入
    if system_instruction:
        conversation.append({
            "role": "system",
            "content": system_instruction
        })
        
    for msg in messages:
        if msg["role"] == "system":
            conversation.append({
                "role": "system",
                "content": msg["content"]
            })
        elif msg["role"] == "user":
            conversation.append({
                "role": "user",
                "content": msg["content"]
            })
        elif msg["role"] == "assistant":
            conversation.append({
                "role": "assistant",
                "content": msg["content"]
            })
    
    # OpenAI 兼容模式请求格式
    payload = {
        "model": MODEL_ID,
        "messages": conversation,
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.95
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY.strip() if API_KEY else ''}"
    }
    
    print(f"[API] 请求头: {headers}")
    print(f"[API] 请求URL: {API_URL}")
    print(f"[API] 请求体: {payload}")
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[API] 调用失败: {type(e).__name__}: {str(e)}", flush=True)
        try:
            if response is not None:
                print(f"[API] 响应状态码: {response.status_code}", flush=True)
                print(f"[API] 响应内容: {response.text[:500]}", flush=True)
        except:
            pass
        return ""


def ai_text(prompt: str, fallback: str = "", system_instruction: str = STUDENT_SYSTEM) -> str:
    """安全调用千问模型返回纯文本"""
    try:
        messages = [{"role": "user", "content": prompt}]
        response = generate_response(messages, system_instruction=system_instruction)
        return response.strip()
    except Exception as e:
        try:
            print(f"[AI] {type(e).__name__}", flush=True)
        except Exception:
            print("[AI] error", flush=True)
        return fallback


def ai_json(prompt: str, fallback=None, system_instruction: str = STUDENT_SYSTEM):
    """调用千问模型并尝试解析 JSON，失败返回 fallback"""
    try:
        messages = [{"role": "user", "content": prompt}]
        response = generate_response(messages, system_instruction=system_instruction)
        text = response.strip()
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


def history_to_messages(messages: list, max_turns: int = 12) -> list:
    """将库中 user/assistant 消息转为千问模型的消息格式"""
    slice_msgs = messages[-(max_turns * 2) :] if len(messages) > max_turns * 2 else messages
    out = []
    for m in slice_msgs:
        role = "user" if m.role == "user" else "assistant"
        out.append({"role": role, "content": m.content})
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
        messages = [{"role": "user", "content": prompt}]
        response = generate_response(messages)
        text = (response or "").strip()[:2000]
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
        messages = [{"role": "user", "content": prompt}]
        response = generate_response(messages, system_instruction=TEACHER_SYSTEM)
        text = (response or "").strip()[:2000]
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
    """Return the API configuration for endpoints that need to call generate directly."""
    print(f"[API] get_client called, API_KEY: {API_KEY}")
    return API_KEY, API_URL, MODEL_ID
