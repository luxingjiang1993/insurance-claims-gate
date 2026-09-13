"""领域模型：与 schemas/ 下 JSON Schema 对齐。

Rewrote from: REF-MISSIONS（missions/models.py）
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RoleName(str, Enum):
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    VALIDATOR = "validator"


class AssertionStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class FeatureKind(str, Enum):
    IMPLEMENT = "implement"
    FIX = "fix"


class FeatureStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class RagCitation(BaseModel):
    """RAG 引用：断言与验收必须可回溯到知识库片段。"""

    doc_id: str
    chunk_id: str
    clause_id: str
    quote: str
    score: float = Field(ge=0, le=1)
    title: str = ""
    doc_version: str = ""
    retrieved_by: RoleName | str = "orchestrator"
    retrieval_profile: str = "default"


class MachineCheck(BaseModel):
    """可由 Validator 执行的验收步骤（contract 驱动，禁止按 A-ID 写死分支）。"""

    type: str
    params: dict[str, Any] = Field(default_factory=dict)


class Assertion(BaseModel):
    """行为断言：行为文本给人看；machine_check 给 Judge 执行。"""

    id: str
    behavior: str
    policy_clause_id: str
    acceptance: str
    machine_check: MachineCheck
    status: AssertionStatus = AssertionStatus.PENDING
    claimed_by_features: list[str] = Field(default_factory=list)


class ValidationContract(BaseModel):
    mission_id: str
    title: str
    goal: str = ""
    version: str = "1.0.0"
    created_by: RoleName = RoleName.ORCHESTRATOR
    created_at: str = Field(default_factory=utc_now_iso)
    broadcast_constraints: list[str] = Field(default_factory=list)
    assertions: list[Assertion]
    source_citations: list[RagCitation] = Field(default_factory=list)
    grade_threshold: str = "all_assertions_pass"
    max_validation_rounds: int = 5
    # 默认确定性轨：CI/Demo 合门禁不得依赖 LLM 抽样
    inference_track: str = "deterministic"


class MissionFeature(BaseModel):
    feature_id: str
    title: str
    milestone: str
    kind: FeatureKind = FeatureKind.IMPLEMENT
    claims_assertions: list[str] = Field(default_factory=list)
    status: FeatureStatus = FeatureStatus.QUEUED
    owns_paths: list[str] = Field(default_factory=list)
    notes: str = ""


class CommandResult(BaseModel):
    cmd: str
    exit_code: int
    stdout_tail: str = ""


class HandoffRecord(BaseModel):
    """结构化交接：跨天一致性靠文档，不靠模型记忆。"""

    handoff_id: str
    mission_id: str
    role: RoleName
    feature_id: str | None = None
    completed: list[str] = Field(default_factory=list)
    incomplete: list[str] = Field(default_factory=list)
    commands: list[CommandResult] = Field(default_factory=list)
    citations_used: list[RagCitation] = Field(default_factory=list)
    process_followed: bool = True
    process_notes: str = ""
    git_commit: str | None = None
    files_touched: list[str] = Field(default_factory=list)
    broadcast_ack: list[str] = Field(default_factory=list)
    blocked_for_human: bool = False
    block_reason: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)
    # handoff 标注改写来源
    rewrote_from: str = "REF-MISSIONS"


class HumanApproval(BaseModel):
    """高风险侧效应门闩：验证通过后仍需人类批准才能 promote。"""

    required: bool = True
    action: str = "promote_milestone"
    approved: bool = False
    approved_at: str | None = None
    approved_by: str | None = None


class MissionState(BaseModel):
    """Mission Control 可见的外置状态总线。"""

    mission_id: str
    phase: str
    autonomy_level: str = "L1"
    current_role: RoleName | None = None
    current_feature_id: str | None = None
    writer_lock_held_by: str | None = None
    locked_paths: list[str] = Field(default_factory=list)
    contract: ValidationContract | None = None
    features: list[MissionFeature] = Field(default_factory=list)
    handoffs: list[HandoffRecord] = Field(default_factory=list)
    validation_rounds: int = 0
    last_validation_passed: bool | None = None
    human_approval: HumanApproval | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    demo_mode: str = "claims_gate_scaffold"
