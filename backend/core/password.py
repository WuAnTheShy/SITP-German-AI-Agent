"""密码哈希与校验，统一使用 bcrypt，兼容旧库中的明文密码。"""
from passlib.context import CryptContext

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
_BCRYPT_MAX_BYTES = 72


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
    return _ctx.hash(_truncate_for_bcrypt(plain))


def verify_password(plain: str, stored: str) -> bool:
    """校验密码。stored 可为 bcrypt 哈希或旧数据中的明文（兼容迁移）。"""
    if not stored or not plain:
        return False
    if stored.startswith("$2") and len(stored) > 20:
        return _ctx.verify(_truncate_for_bcrypt(plain), stored)
    return plain == stored
