"""演示 RBAC：种子三角色登录与会话。

Rewrote from: REF-MISSIONS（域服务边界 + 会话凭证外形）
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Any

from .error_codes import ErrorCode
from .sqlite_store import SqliteCaseStore

# 演示种子：用户名=密码（无 SSO；仅本地演示）
SEED_USERS: tuple[tuple[str, str, str, str], ...] = (
    ("viewer", "viewer", "viewer", "只读查看员"),
    ("adjuster", "adjuster", "adjuster", "核赔初审员"),
    ("supervisor", "supervisor", "supervisor", "核赔主管"),
)

_PBKDF2_ITERATIONS = 120_000


def hash_password(password: str, *, salt_hex: str | None = None) -> str:
    """口令哈希：salt$iterations$digest（stdlib，无额外依赖）。"""
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return f"{salt.hex()}${_PBKDF2_ITERATIONS}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, iter_s, digest_hex = stored.split("$", 2)
        iterations = int(iter_s)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


class AuthError(Exception):
    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class AuthService:
    """基于 SQLite 的登录与会话；角色供后续 RBAC 票使用。"""

    def __init__(self, store: SqliteCaseStore) -> None:
        self._store = store
        self.ensure_seed_users()

    def ensure_seed_users(self) -> None:
        for username, password, role, display_name in SEED_USERS:
            existing = self._store.get_user(username)
            if existing is None:
                self._store.upsert_user(
                    username=username,
                    password_hash=hash_password(password),
                    role=role,
                    display_name=display_name,
                )

    def login(self, username: str, password: str) -> dict[str, Any]:
        user = self._store.get_user(username)
        if user is None or not verify_password(password, user["password_hash"]):
            raise AuthError(ErrorCode.AUTH_FAILED.value, "用户名或密码错误")
        token = f"sess-{secrets.token_hex(16)}"
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        self._store.create_session(
            token=token,
            username=user["username"],
            role=user["role"],
            created_at=now,
        )
        return {
            "session_token": token,
            "username": user["username"],
            "role": user["role"],
            "display_name": user["display_name"],
        }

    def resolve_session(self, token: str | None) -> dict[str, Any]:
        if not token:
            raise AuthError(ErrorCode.AUTH_FAILED.value, "缺少会话令牌")
        session = self._store.get_session(token)
        if session is None:
            raise AuthError(ErrorCode.AUTH_FAILED.value, "会话无效")
        user = self._store.get_user(session["username"])
        display = user["display_name"] if user else session["username"]
        return {
            "username": session["username"],
            "role": session["role"],
            "display_name": display,
            "session_token": session["token"],
        }

    def logout(self, token: str | None) -> dict[str, Any]:
        if token:
            self._store.delete_session(token)
        return {"ok": True}
