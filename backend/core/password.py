"""密码哈希与校验，统一使用 bcrypt，并支持前端 SHA-256 传输哈希。"""
import hashlib
import re

import bcrypt

_BCRYPT_MAX_BYTES = 72
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def _truncate_for_bcrypt(s: str) -> str:
    """bcrypt 只接受最多 72 字节，按 UTF-8 截断避免报错。"""
    if not s:
        return s
    b = s.encode("utf-8")
    if len(b) <= _BCRYPT_MAX_BYTES:
        return s
    return b[:_BCRYPT_MAX_BYTES].decode("utf-8", errors="ignore")


def hash_password(plain: str) -> str:
    """将明文密码哈希后存入数据库。"""
    secret = _truncate_for_bcrypt(plain).encode("utf-8")
    return bcrypt.hashpw(secret, bcrypt.gensalt(rounds=12)).decode("utf-8")


def is_sha256_hex(value: str | None) -> bool:
    if not value:
        return False
    return bool(_SHA256_RE.fullmatch(value.strip()))


def sha256_hex(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def ensure_transport_hash(raw_or_hash: str | None) -> str:
    """把输入统一为 64 位 SHA-256 十六进制字符串。"""
    if raw_or_hash is None:
        return ""
    v = str(raw_or_hash).strip()
    if is_sha256_hex(v):
        return v.lower()
    return sha256_hex(v)


def verify_password(plain: str, stored: str) -> bool:
    """校验密码。stored 可为 bcrypt 哈希或旧数据中的明文（兼容迁移）。"""
    if not stored or not plain:
        return False
    if stored.startswith("$2") and len(stored) > 20:
        try:
            return bcrypt.checkpw(_truncate_for_bcrypt(plain).encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    return plain == stored
