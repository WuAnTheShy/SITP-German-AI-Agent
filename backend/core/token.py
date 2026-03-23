import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

_TOKEN_VERSION = 1
_DEFAULT_TTL_HOURS = 12


def _env_flag(name: str, default: bool = False) -> bool:
    value = (os.getenv(name, "") or "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def _is_production() -> bool:
    env = (os.getenv("APP_ENV", "") or "").strip().lower()
    return env in {"prod", "production"}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _get_secret() -> str:
    secret = (os.getenv("AUTH_TOKEN_SECRET", "") or "").strip()
    if secret:
        return secret
    if _is_production():
        raise RuntimeError("AUTH_TOKEN_SECRET is required in production")
    # Development fallback: ephemeral secret per process.
    generated = secrets.token_urlsafe(48)
    return generated


def _ttl_seconds() -> int:
    raw = (os.getenv("AUTH_TOKEN_TTL_HOURS", str(_DEFAULT_TTL_HOURS)) or str(_DEFAULT_TTL_HOURS)).strip()
    try:
        hours = int(raw)
    except ValueError:
        hours = _DEFAULT_TTL_HOURS
    hours = max(1, min(hours, 24 * 30))
    return hours * 3600


def issue_token(role: str, subject: str) -> str:
    now = int(time.time())
    payload = {
        "v": _TOKEN_VERSION,
        "role": role,
        "sub": str(subject),
        "iat": now,
        "exp": now + _ttl_seconds(),
        "jti": secrets.token_urlsafe(12),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload_part = _b64url_encode(payload_bytes)
    signature = hmac.new(_get_secret().encode("utf-8"), payload_part.encode("ascii"), hashlib.sha256).hexdigest()
    return f"v1.{payload_part}.{signature}"


def parse_token(token: str, allow_legacy: bool = False) -> dict[str, Any] | None:
    token = (token or "").strip()
    if not token:
        return None

    if allow_legacy and token.startswith(("teacher-token-", "student-token-", "admin-token-")):
        parts = token.split("-")
        if len(parts) >= 4:
            role = parts[0]
            subject = parts[2]
            return {"role": role, "sub": subject, "legacy": True}

    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        return None

    payload_part = parts[1]
    signature = parts[2]
    expected = hmac.new(_get_secret().encode("utf-8"), payload_part.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None

    try:
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except Exception:
        return None

    if payload.get("v") != _TOKEN_VERSION:
        return None
    role = str(payload.get("role", "")).strip()
    sub = str(payload.get("sub", "")).strip()
    exp = payload.get("exp")
    if not role or not sub:
        return None
    if not isinstance(exp, int):
        return None
    if int(time.time()) >= exp:
        return None
    return payload


def allow_legacy_tokens() -> bool:
    # Development compatibility switch; keep strict by default in production.
    default = not _is_production()
    return _env_flag("ALLOW_LEGACY_TOKENS", default)
