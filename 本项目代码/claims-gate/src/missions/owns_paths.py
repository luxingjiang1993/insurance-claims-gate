"""Worker owns_paths 硬禁信封（SPEC-02B-Q / 流 Q）。

Rewrote from: REF-MISSIONS；宪法 I4
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

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


def is_hard_banned_path(rel: str) -> bool:
    """路径相对 claims-gate worktree 根；命中硬禁返回 True。"""
    p = _norm(rel)
    if p in HARD_BANNED_EXACT:
        return True
    if p.startswith(".env"):
        return True
    for pattern in HARD_BANNED_GLOBS:
        if fnmatch.fnmatch(p, pattern):
            return True
        # 前缀目录命中（无 ** 时）
        if pattern.endswith("/**"):
            prefix = pattern[:-3]
            if p == prefix or p.startswith(prefix + "/"):
                return True
    name = Path(p).name.lower()
    if "payout" in name or "银企" in p or "bank_rail" in p.lower():
        return True
    return False


def find_hard_banned(paths: list[str]) -> list[str]:
    return sorted({_norm(p) for p in paths if is_hard_banned_path(p)})
