"""接缝 Q-S0-B：A3 Patch-capable Worker + F-Q-DEMO-01（真 commit / owns_paths / 写锁）。

Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from missions.models import (
    FeatureKind,
    FeatureStatus,
    MissionFeature,
    MissionState,
    RoleName,
)
from missions.rag import KnowledgeBase
from missions.store import ArtifactStore
from missions.worker import (
    FQ_DEMO_01_USER_TEXT,
    OwnsPathError,
    Worker,
    WriterLockError,
)

# 工作树内「未 strip」起点（与产品已交付 strip 形成可检视 diff）
_USER_TEXT_NO_STRIP = '''\
"""用户可控文本（OCR / 客户备注）吸收：可观察收纳，永不改写人闸规则。

Rewrote from: REF-MISSIONS（transfer 用户字段不得改限额）；REF-CASE-HYBRID
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models_domain import ClaimCase


def absorb_user_controlled_text(
    case: "ClaimCase",
    *,
    ocr_text: str | None = None,
    customer_remark: str | None = None,
) -> None:
    """将 OCR/备注写入案件可观察字段。"""
    if ocr_text is not None:
        case.ocr_text = str(ocr_text)
    if customer_remark is not None:
        case.customer_remark = str(customer_remark)
'''

# 已与 Worker 目标产物字节级一致 → 空 diff
_USER_TEXT_WITH_STRIP = FQ_DEMO_01_USER_TEXT

F_Q_DEMO_OWNS = (
    "src/claims_api/user_text.py",
    "tests/test_user_text_strip.py",
)


def _git(cwd: Path, *args: str) -> None:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"git {' '.join(args)} failed")


def _init_local_worktree(tmp_path: Path, *, user_text: str) -> Path:
    """临时本地 git worktree：不绑远端、不要求 LLM Key。"""
    root = tmp_path / "wt"
    (root / "src" / "claims_api").mkdir(parents=True)
    (root / "tests").mkdir(parents=True)
    (root / "knowledge_base").mkdir(parents=True)
    (root / "src" / "claims_api" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "claims_api" / "user_text.py").write_text(user_text, encoding="utf-8")
    (root / "tests" / "test_user_text_strip.py").write_text(
        "# placeholder paired test\n", encoding="utf-8"
    )
    _git(root, "init")
    _git(root, "config", "user.email", "mission-demo@local")
    _git(root, "config", "user.name", "Mission Demo")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init worktree")
    return root


def _worker(root: Path, artifacts: Path) -> Worker:
    return Worker(
        KnowledgeBase(root / "knowledge_base"),
        ArtifactStore(artifacts),
        root,
    )


def _demo_feature() -> MissionFeature:
    return MissionFeature(
        feature_id="F-Q-DEMO-01",
        title="OCR/备注吸收时 strip 首尾空白（不改人闸字段）",
        milestone="M-q-demo",
        kind=FeatureKind.IMPLEMENT,
        claims_assertions=["A-Q-DEMO"],
        status=FeatureStatus.QUEUED,
        owns_paths=list(F_Q_DEMO_OWNS),
    )


def _state(mission_id: str = "m-q-demo") -> MissionState:
    return MissionState(mission_id=mission_id, phase="implementation")


def test_fq_demo_01_real_commit_and_files_touched_subset(tmp_path: Path) -> None:
    """F-Q-DEMO-01：非空 commit；files_touched ⊆ owns_paths。"""
    root = _init_local_worktree(tmp_path, user_text=_USER_TEXT_NO_STRIP)
    worker = _worker(root, tmp_path / "artifacts")
    feature = _demo_feature()
    state = _state()

    state = worker.run_feature(state, feature)

    assert feature.status == FeatureStatus.DONE
    handoff = state.handoffs[-1]
    assert handoff.git_commit
    assert len(handoff.git_commit) >= 7
    assert handoff.files_touched
    assert set(handoff.files_touched) <= set(feature.owns_paths)
    assert "src/claims_api/user_text.py" in handoff.files_touched
    assert "Rewrote from:" in (handoff.process_notes or "")
    assert handoff.rewrote_from.startswith("REF-MISSIONS")
    # 可检视 diff：HEAD 相对父提交有变更
    show = subprocess.run(
        ["git", "show", "--stat", "HEAD"],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    assert "user_text.py" in (show.stdout or "")


def test_empty_diff_must_not_done(tmp_path: Path) -> None:
    """空 diff / 已是目标态 → 不得 DONE。"""
    root = _init_local_worktree(tmp_path, user_text=_USER_TEXT_WITH_STRIP)
    worker = _worker(root, tmp_path / "artifacts")
    feature = _demo_feature()
    state = _state("m-empty")

    state = worker.run_feature(state, feature)

    assert feature.status != FeatureStatus.DONE
    assert feature.status == FeatureStatus.BLOCKED
    handoff = state.handoffs[-1]
    assert handoff.git_commit is None
    assert handoff.blocked_for_human is True


def test_hard_banned_owns_paths_must_not_done(tmp_path: Path) -> None:
    """硬禁路径出现在 owns_paths → 不得 DONE。"""
    root = _init_local_worktree(tmp_path, user_text=_USER_TEXT_NO_STRIP)
    worker = _worker(root, tmp_path / "artifacts")
    feature = _demo_feature()
    feature.owns_paths = [
        "src/claims_api/user_text.py",
        "src/claims_api/latch_matrix.py",
    ]
    state = _state("m-ban")

    with pytest.raises(OwnsPathError):
        worker.run_feature(state, feature)
    assert feature.status != FeatureStatus.DONE


def test_write_lock_contention_fail_closed(tmp_path: Path) -> None:
    """写锁争用 fail-closed。"""
    root = _init_local_worktree(tmp_path, user_text=_USER_TEXT_NO_STRIP)
    worker = _worker(root, tmp_path / "artifacts")
    feature = _demo_feature()
    state = _state("m-lock")
    state.writer_lock_held_by = "F-OTHER"
    state.locked_paths = ["src/claims_api/user_text.py"]

    with pytest.raises(WriterLockError):
        worker.run_feature(state, feature)
    assert feature.status != FeatureStatus.DONE
    assert state.writer_lock_held_by == "F-OTHER"


def test_files_touched_outside_owns_paths_must_not_done(tmp_path: Path) -> None:
    """越权路径（files_touched 超出 owns_paths）→ 不得 DONE。"""
    root = _init_local_worktree(tmp_path, user_text=_USER_TEXT_NO_STRIP)
    worker = _worker(root, tmp_path / "artifacts")
    feature = _demo_feature()
    # 故意收窄 owns_paths，使示范 patch 必越权
    feature.owns_paths = ["tests/test_user_text_strip.py"]
    state = _state("m-overreach")

    state = worker.run_feature(state, feature)

    assert feature.status != FeatureStatus.DONE
    assert feature.status == FeatureStatus.BLOCKED
