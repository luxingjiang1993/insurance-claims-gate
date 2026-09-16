"""Worker owns_paths 信封：允许上界 + 硬禁（SPEC-02B-Q / 流 Q）。

Rewrote from: REF-MISSIONS；宪法 I4
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

# 允许上界（单特性须再收窄为显式列表）
ALLOW_GLOBS: tuple[str, ...] = (
    "src/claims_api/*.py",
    "src/claims_api/**/*.py",
    "tests/test_*.py",
    "tests/**/test_*.py",
)

# 硬禁：出现在 owns_paths 或 files_touched → 失败关闭
HARD_BANNED_EXACT: frozenset[str] = frozenset(
    {
        "src/claims_api/latch_matrix.py",
        "src/claims_api/tools_acl.py",
        "src/claims_api/auth.py",
        "src/missions/validator.py",
        "src/missions/orchestrator.py",
        "AGENTS.md",
        "CONTEXT.md",
    }
)

HARD_BANNED_GLOBS: tuple[str, ...] = (
    ".env",
    ".env.*",
    "src/missions/track_llm_optional/**",
    "Managerial System/**",
    "docs/**",
    "历史项目代码供参考/**",
)


def _norm(rel: str) -> str:
    return rel.replace("\\", "/").lstrip("./")


def _match_any(path: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
        if pattern.endswith("/**"):
            prefix = pattern[:-3]
            if path == prefix or path.startswith(prefix + "/"):
                return True
    return False


def is_within_allow_envelope(rel: str) -> bool:
    """是否落在允许上界（claims_api 源 + 配对 test_*）。"""
    return _match_any(_norm(rel), ALLOW_GLOBS)


def is_hard_banned_path(rel: str) -> bool:
    """路径相对 claims-gate worktree 根；命中硬禁返回 True。"""
    p = _norm(rel)
    if p in HARD_BANNED_EXACT:
        return True
    if p.startswith(".env"):
        return True
    if _match_any(p, HARD_BANNED_GLOBS):
        return True
    name = Path(p).name.lower()
    if "payout" in name or "银企" in p or "bank_rail" in p.lower():
        return True
    return False


def find_hard_banned(paths: list[str]) -> list[str]:
    return sorted({_norm(p) for p in paths if is_hard_banned_path(p)})


def find_outside_allow_envelope(paths: list[str]) -> list[str]:
    return sorted({_norm(p) for p in paths if not is_within_allow_envelope(p)})


def assert_owns_paths_envelope(paths: list[str]) -> None:
    """允许上界 + 硬禁双检；失败抛出说明字符串列表由调用方包装异常。"""
    outside = find_outside_allow_envelope(paths)
    banned = find_hard_banned(paths)
    problems: list[str] = []
    if outside:
        problems.append(f"超出允许上界: {outside}")
    if banned:
        problems.append(f"含硬禁路径: {banned}")
    if problems:
        raise ValueError("; ".join(problems))
