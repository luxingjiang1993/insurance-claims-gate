"""真实 git handoff：禁止伪造 commit hash。

Rewrote from: REF-MISSIONS（missions/git_util.py）
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def git_head(project_root: Path) -> str | None:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip() or None


def ensure_git_identity(project_root: Path) -> None:
    """仅在本地缺失时设置仓库级 identity；不碰全局 git config。"""
    for key, value in (
        ("user.email", "mission-demo@local"),
        ("user.name", "Mission Demo"),
    ):
        check = subprocess.run(
            ["git", "config", "--local", key],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if check.returncode != 0 or not (check.stdout or "").strip():
            subprocess.run(
                ["git", "config", "--local", key, value],
                cwd=str(project_root),
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )


def git_commit_paths(
    project_root: Path,
    paths: list[str],
    message: str,
) -> str | None:
    """对指定路径做真实提交；无变更则返回 None（不是假 hash）。"""
    if not paths:
        return None

    ensure_git_identity(project_root)

    for rel in paths:
        abs_path = project_root / rel
        if not abs_path.exists():
            raise FileNotFoundError(f"提交路径不存在: {rel}")
        add = subprocess.run(
            ["git", "add", "--", rel.replace("\\", "/")],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if add.returncode != 0:
            raise RuntimeError(add.stderr or add.stdout or "git add failed")

    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if not (staged.stdout or "").strip():
        return None

    commit = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if commit.returncode != 0:
        raise RuntimeError(commit.stderr or commit.stdout or "git commit failed")
    return git_head(project_root)
