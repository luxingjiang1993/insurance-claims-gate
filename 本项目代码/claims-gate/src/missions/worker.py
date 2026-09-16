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
from .owns_paths import find_hard_banned, find_outside_allow_envelope
from .rag import KnowledgeBase
from .role_profiles import WORKER_MODEL_NAME, WORKER_RETRIEVE_PROFILE
from .store import ArtifactStore

FQ_DEMO_01_ID = "F-Q-DEMO-01"
FQ_DEMO_01_USER_TEXT_REL = "src/claims_api/user_text.py"


def apply_fq_demo_01_strip_transform(source: str) -> str:
    """在 absorb 赋值处补上 .strip()；已具备则原样返回（空 diff）。"""
    out = source
    for lhs, rhs in (
        ("case.ocr_text = str(ocr_text)", "case.ocr_text = str(ocr_text).strip()"),
        (
            "case.customer_remark = str(customer_remark)",
            "case.customer_remark = str(customer_remark).strip()",
        ),
    ):
        if rhs in out:
            continue
        if lhs not in out:
            continue
        out = out.replace(lhs, rhs, 1)
    return out


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
        *,
        retrieve_profile: str = WORKER_RETRIEVE_PROFILE,
        model_name: str = WORKER_MODEL_NAME,
    ) -> None:
        self.kb = kb
        self.store = store
        self.project_root = project_root
        # 与 Validator 可区分的检索画像 / 模型名（Q-A6 对照）
        self.retrieve_profile = retrieve_profile
        self.model_name = model_name

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

        # A3 示范特性：额外强制允许上界（脚手架既有 owns_paths 可含 missions 烟雾面）
        if feature.feature_id == FQ_DEMO_01_ID:
            outside = find_outside_allow_envelope(feature.owns_paths)
            if outside:
                raise OwnsPathError(f"owns_paths 超出允许上界: {outside}")

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
            extra={
                "owns_paths": feature.owns_paths,
                "broadcast_ack": broadcast,
                "retrieval_profile": self.retrieve_profile,
                "model_name": self.model_name,
            },
        )

        citations = self.kb.retrieve(
            feature.title + " " + " ".join(feature.claims_assertions),
            role=RoleName.WORKER,
            profile=self.retrieve_profile,
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

        outside_touched = find_outside_allow_envelope(files_touched)
        if outside_touched:
            return self._block_feature(
                state,
                feature,
                citations=citations,
                broadcast=broadcast,
                commands=commands,
                files_touched=files_touched,
                git_commit=None,
                reason=f"files_touched 超出允许上界: {outside_touched}",
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
        if not path.exists():
            raise OwnsPathError(f"F-Q-DEMO-01 目标不存在: {target}")
        old = path.read_text(encoding="utf-8")
        new = apply_fq_demo_01_strip_transform(old)
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
