"""Worker：串行写锁 + owns_paths；A3 真 patch/commit；不自审自批。

Rewrote from: REF-MISSIONS（missions/worker.py）
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .git_util import git_commit_paths
from .models import (
    CommandResult,
    FeatureKind,
    FeatureStatus,
    HandoffRecord,
    MissionFeature,
    MissionState,
    RoleName,
)
from .owns_paths import find_hard_banned
from .rag import KnowledgeBase
from .store import ArtifactStore

# F-Q-DEMO-01 目标产物：OCR/备注吸收 strip（与产品交付对齐）
FQ_DEMO_01_USER_TEXT = '''\
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
    """将 OCR/备注写入案件可观察字段（首尾空白 strip；全空白→空串）。

    硬约束：不得从这些文本解析或改写 human_latch_required、payout_ready、
    sensitivity_flags、金额档或任何人闸矩阵输入。
    """
    # F-Q-DEMO-01：写入前 strip；全空白 → 空串；不改人闸/payout 字段
    if ocr_text is not None:
        case.ocr_text = str(ocr_text).strip()
    if customer_remark is not None:
        case.customer_remark = str(customer_remark).strip()
'''

FQ_DEMO_01_ID = "F-Q-DEMO-01"
FQ_DEMO_01_USER_TEXT_REL = "src/claims_api/user_text.py"


class WriterLockError(RuntimeError):
    pass


class OwnsPathError(RuntimeError):
    pass


class Worker:
    def __init__(
        self,
        kb: KnowledgeBase,
        store: ArtifactStore,
        project_root: Path,
    ) -> None:
        self.kb = kb
        self.store = store
        self.project_root = project_root

    def run_feature(self, state: MissionState, feature: MissionFeature) -> MissionState:
        if state.writer_lock_held_by and state.writer_lock_held_by != feature.feature_id:
            raise WriterLockError(
                f"写锁由 {state.writer_lock_held_by} 持有，拒绝并行写"
            )

        contested = set(feature.owns_paths) & set(state.locked_paths)
        if contested and state.writer_lock_held_by not in (None, feature.feature_id):
            raise OwnsPathError(f"路径争用: {sorted(contested)}")

        banned = find_hard_banned(feature.owns_paths)
        if banned:
            raise OwnsPathError(f"owns_paths 含硬禁路径: {banned}")

        state.current_role = RoleName.WORKER
        state.current_feature_id = feature.feature_id
        state.writer_lock_held_by = feature.feature_id
        state.locked_paths = list(feature.owns_paths)
        feature.status = FeatureStatus.IN_PROGRESS

        broadcast = list(state.contract.broadcast_constraints) if state.contract else []
        self.store.emit(
            state,
            kind="worker_start",
            message=f"Worker 开始 {feature.feature_id}: {feature.title}",
            role=RoleName.WORKER,
            extra={"owns_paths": feature.owns_paths, "broadcast_ack": broadcast},
        )

        citations = self.kb.retrieve(
            feature.title + " " + " ".join(feature.claims_assertions),
            role=RoleName.WORKER,
            profile="worker_narrow_top3",
            top_k=3,
        )

        if feature.feature_id == FQ_DEMO_01_ID:
            return self._run_fq_demo_01(
                state,
                feature,
                citations=citations,
                broadcast=broadcast,
            )

        return self._run_scaffold_smoke(
            state,
            feature,
            citations=citations,
            broadcast=broadcast,
        )

    def _run_fq_demo_01(
        self,
        state: MissionState,
        feature: MissionFeature,
        *,
        citations,
        broadcast: list[str],
    ) -> MissionState:
        """A3：worktree 内真实 patch + commit；空 diff / null commit 不得 DONE。"""
        commands: list[CommandResult] = []
        try:
            files_touched = self._apply_fq_demo_01_patch(feature)
        except OwnsPathError as exc:
            return self._block_feature(
                state,
                feature,
                citations=citations,
                broadcast=broadcast,
                commands=commands,
                files_touched=[],
                git_commit=None,
                reason=str(exc),
            )

        overreach = [p for p in files_touched if p not in feature.owns_paths]
        if overreach:
            return self._block_feature(
                state,
                feature,
                citations=citations,
                broadcast=broadcast,
                commands=commands,
                files_touched=files_touched,
                git_commit=None,
                reason=f"files_touched 越权: {overreach}",
            )

        banned_touched = find_hard_banned(files_touched)
        if banned_touched:
            return self._block_feature(
                state,
                feature,
                citations=citations,
                broadcast=broadcast,
                commands=commands,
                files_touched=files_touched,
                git_commit=None,
                reason=f"files_touched 含硬禁路径: {banned_touched}",
            )

        git_hash = git_commit_paths(
            self.project_root,
            files_touched,
            message=f"feat({FQ_DEMO_01_ID}): OCR/remark absorb strip",
        )
        commands.append(
            CommandResult(
                cmd=f"git commit paths={files_touched}",
                exit_code=0 if git_hash else 1,
                stdout_tail=git_hash or "empty diff / null commit",
            )
        )

        if not git_hash or not files_touched:
            return self._block_feature(
                state,
                feature,
                citations=citations,
                broadcast=broadcast,
                commands=commands,
                files_touched=files_touched,
                git_commit=None,
                reason="空 diff 或 git_commit=null，不得标 DONE",
            )

        feature.status = FeatureStatus.DONE
        state.writer_lock_held_by = None
        state.locked_paths = []
        handoff = HandoffRecord(
            handoff_id=f"h-worker-{feature.feature_id}",
            mission_id=state.mission_id,
            role=RoleName.WORKER,
            feature_id=feature.feature_id,
            completed=[
                f"完成 {feature.feature_id}",
                f"owns_paths={feature.owns_paths}",
                f"真实 patch files={files_touched} commit={git_hash}",
            ],
            incomplete=[],
            commands=commands,
            citations_used=citations,
            process_followed=True,
            process_notes=(
                "A3 worktree 真 patch；Worker 不做最终合规验收；"
                "交 Validator 黑盒；Rewrote from: REF-MISSIONS"
            ),
            git_commit=git_hash,
            files_touched=files_touched,
            broadcast_ack=broadcast,
            rewrote_from="REF-MISSIONS",
        )
        self.store.append_handoff(state, handoff)
        self.store.emit(
            state,
            kind="worker_done",
            message=f"Worker 交付 {feature.feature_id}",
            role=RoleName.WORKER,
        )
        return state

    def _apply_fq_demo_01_patch(self, feature: MissionFeature) -> list[str]:
        """仅改 owns_paths 内的示范文件；无变更则返回空列表。"""
        target = FQ_DEMO_01_USER_TEXT_REL
        if target not in feature.owns_paths:
            raise OwnsPathError(f"F-Q-DEMO-01 未拥有路径: {target}")

        path = self.project_root / target
        path.parent.mkdir(parents=True, exist_ok=True)
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        new = FQ_DEMO_01_USER_TEXT
        if old == new:
            return []
        path.write_text(new, encoding="utf-8")
        return [target]

    def _run_scaffold_smoke(
        self,
        state: MissionState,
        feature: MissionFeature,
        *,
        citations,
        broadcast: list[str],
    ) -> MissionState:
        """脚手架：产品实现已预置；Worker 只跑 API 烟雾测，不自做合规终裁。"""
        test_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_claims_api_l1.py",
            "tests/test_error_codes.py",
            "-q",
            "--tb=line",
        ]
        proc = subprocess.run(
            test_cmd,
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        commands = [
            CommandResult(
                cmd=" ".join(test_cmd),
                exit_code=proc.returncode,
                stdout_tail=(proc.stdout or "")[-500:],
            )
        ]

        if proc.returncode != 0:
            return self._block_feature(
                state,
                feature,
                citations=citations,
                broadcast=broadcast,
                commands=commands,
                files_touched=[],
                git_commit=None,
                reason="pytest 失败，交回人类或开新 fix",
            )

        feature.status = FeatureStatus.DONE
        state.writer_lock_held_by = None
        state.locked_paths = []
        completed = [
            f"完成 {feature.feature_id}",
            f"owns_paths={feature.owns_paths}",
            "pytest 烟雾通过（fail-closed）",
        ]
        if feature.kind == FeatureKind.IMPLEMENT:
            completed.append("无文件 delta（脚手架实现预置）；git_commit=null")

        handoff = HandoffRecord(
            handoff_id=f"h-worker-{feature.feature_id}",
            mission_id=state.mission_id,
            role=RoleName.WORKER,
            feature_id=feature.feature_id,
            completed=completed,
            incomplete=[],
            commands=commands,
            citations_used=citations,
            process_followed=True,
            process_notes="Worker 不做最终合规验收；交 Validator 黑盒；Rewrote from: REF-MISSIONS",
            git_commit=None,
            files_touched=[],
            broadcast_ack=broadcast,
            rewrote_from="REF-MISSIONS",
        )
        self.store.append_handoff(state, handoff)
        self.store.emit(
            state,
            kind="worker_done",
            message=f"Worker 交付 {feature.feature_id}",
            role=RoleName.WORKER,
        )
        return state

    def _block_feature(
        self,
        state: MissionState,
        feature: MissionFeature,
        *,
        citations,
        broadcast: list[str],
        commands: list[CommandResult],
        files_touched: list[str],
        git_commit: str | None,
        reason: str,
    ) -> MissionState:
        feature.status = FeatureStatus.BLOCKED
        state.writer_lock_held_by = None
        state.locked_paths = []
        handoff = HandoffRecord(
            handoff_id=f"h-worker-{feature.feature_id}-blocked",
            mission_id=state.mission_id,
            role=RoleName.WORKER,
            feature_id=feature.feature_id,
            completed=[],
            incomplete=[reason],
            commands=commands,
            citations_used=citations,
            process_followed=True,
            process_notes="失败关闭不得标 DONE；Rewrote from: REF-MISSIONS",
            git_commit=git_commit,
            files_touched=files_touched,
            broadcast_ack=broadcast,
            blocked_for_human=True,
            block_reason=reason,
            rewrote_from="REF-MISSIONS",
        )
        self.store.append_handoff(state, handoff)
        return state
