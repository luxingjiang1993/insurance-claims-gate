"""Worker：串行写锁 + owns_paths；不自审自批；脚手架不改产品代码。

Rewrote from: REF-MISSIONS（missions/worker.py）
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .models import (
    CommandResult,
    FeatureKind,
    FeatureStatus,
    HandoffRecord,
    MissionFeature,
    MissionState,
    RoleName,
)
from .rag import KnowledgeBase
from .store import ArtifactStore


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

        # 脚手架：产品实现已预置；Worker 只跑 API 烟雾测，不自做合规终裁
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
            feature.status = FeatureStatus.BLOCKED
            state.writer_lock_held_by = None
            state.locked_paths = []
            handoff = HandoffRecord(
                handoff_id=f"h-worker-{feature.feature_id}-blocked",
                mission_id=state.mission_id,
                role=RoleName.WORKER,
                feature_id=feature.feature_id,
                completed=[],
                incomplete=["测试未通过，fail-closed 阻断"],
                commands=commands,
                citations_used=citations,
                process_followed=True,
                process_notes="测试失败不得标 DONE；Rewrote from: REF-MISSIONS",
                files_touched=[],
                broadcast_ack=broadcast,
                blocked_for_human=True,
                block_reason="pytest 失败，交回人类或开新 fix",
                rewrote_from="REF-MISSIONS",
            )
            self.store.append_handoff(state, handoff)
            return state

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
