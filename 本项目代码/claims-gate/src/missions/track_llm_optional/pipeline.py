"""轨 B 最小「检索 → 辅助起草」管线。

允许确定性假检索（enable_llm=False，默认）；若调用 LLM 须显式打开且 CI 不依赖。
规则 vs RAG 冲突仍 fail-closed 进人闸；handbook_ops 不得单独支撑对外拒赔。

完整方差预算 / 金标门槛数值化仍属 P2-4；本模块只做最小可跑。
Rewrote from: REF-RAG-CY, REF-MISSIONS, REF-CASE-HYBRID
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from missions.retrieval_profiles import RETRIEVAL_PROFILES

from .config import TrackBConfig
from .retrieval import retrieve_chunks

# 辅助起草立场：仅启发式，不得替代轨 A 裁决
DraftStance = Literal["pay", "deny", "reduce", "unclear"]

_DENY_HINTS = ("责任免除", "除外", "不承担", "不予给付", "拒赔", "剔除")
_PAY_HINTS = ("保险责任", "给付保险金", "承担给付")
_REDUCE_HINTS = ("免赔", "赔付比例", "减赔", "缩小责任")


@dataclass
class DraftAssistResult:
    """轨 B 辅助起草产物；必须标注 inference_track=llm_optional。"""

    inference_track: str
    query: str
    retrieval_profile: str
    citations: list[dict[str, Any]]
    draft_text: str
    used_llm: bool
    suggested_stance: DraftStance = "unclear"
    human_latch_required: bool = False
    conflict_route_id: str | None = None
    can_external_deny: bool = True
    enable_llm: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "inference_track": self.inference_track,
            "query": self.query,
            "retrieval_profile": self.retrieval_profile,
            "citations": self.citations,
            "draft_text": self.draft_text,
            "used_llm": self.used_llm,
            "suggested_stance": self.suggested_stance,
            "human_latch_required": self.human_latch_required,
            "conflict_route_id": self.conflict_route_id,
            "can_external_deny": self.can_external_deny,
            "enable_llm": self.enable_llm,
            "notes": list(self.notes),
        }


def _infer_stance(citations: list[dict[str, Any]], query: str) -> DraftStance:
    """从检索摘录启发式推断辅助立场（假起草，非 LLM）。"""
    blob = query + "\n" + "\n".join(str(c.get("quote") or "") for c in citations)
    deny_hits = sum(1 for h in _DENY_HINTS if h in blob)
    pay_hits = sum(1 for h in _PAY_HINTS if h in blob)
    reduce_hits = sum(1 for h in _REDUCE_HINTS if h in blob)
    # 除外/拒赔词优先于给付词，避免责任条与除外条并存时误判为 pay
    if deny_hits > 0 and deny_hits >= pay_hits:
        return "deny"
    if reduce_hits > 0 and reduce_hits >= pay_hits:
        return "reduce"
    if pay_hits > 0:
        return "pay"
    return "unclear"


def _build_deterministic_draft(
    query: str,
    citations: list[dict[str, Any]],
    stance: DraftStance,
) -> str:
    """无 LLM 时的确定性辅助草稿（模板拼接引用）。"""
    lines = [
        f"[轨 B 辅助起草 · inference_track=llm_optional · 假检索]",
        f"查询: {query}",
        f"建议立场(启发式): {stance}",
        "引用摘录:",
    ]
    if not citations:
        lines.append("- （未命中条款切块）")
    for i, c in enumerate(citations, start=1):
        doc_id = c.get("doc_id") or "?"
        item = c.get("clause_item") or c.get("clause_id") or "?"
        quote = (c.get("quote") or "").replace("\n", " ").strip()[:160]
        lines.append(f"- [{i}] {doc_id} / {item}: {quote}")
    lines.append(
        "说明: 本草稿仅供人闸前辅助，不得替代 Orchestrator 契约与轨 A 裁决；"
        "完整方差预算属 P2-4。"
    )
    return "\n".join(lines)


def _maybe_llm_draft(
    query: str,
    citations: list[dict[str, Any]],
    *,
    enable_llm: bool,
) -> tuple[str | None, bool]:
    """LLM 起草旁路：默认关闭；无 key / 未启用时返回 (None, False)。

    本期不接入真实供应商；显式 enable_llm=True 且无实现时仍回落确定性草稿。
    """
    if not enable_llm:
        return None, False
    # 故意不读环境密钥做真实调用，避免 CI/本地隐式依赖
    return None, False


def draft_assist(
    query: str,
    *,
    kb_root: Path | None = None,
    retrieval_profile: str = "clause_v_current",
    rules_conclusion: DraftStance | None = None,
    intended_external_action: Literal["deny", "pay", "reduce"] | None = None,
    enable_llm: bool = False,
    top_k: int = 3,
    cfg: TrackBConfig | None = None,
) -> DraftAssistResult:
    """检索 → 辅助起草。默认 enable_llm=False（确定性假检索）。"""
    track_cfg = cfg or TrackBConfig()
    citations = retrieve_chunks(
        query,
        kb_root=kb_root,
        retrieval_profile=retrieval_profile,
        top_k=top_k,
    )
    stance = _infer_stance(citations, query)
    llm_text, used_llm = _maybe_llm_draft(query, citations, enable_llm=enable_llm)
    draft_text = llm_text or _build_deterministic_draft(query, citations, stance)

    notes: list[str] = []
    human_latch = False
    conflict_route: str | None = None
    can_external_deny = True

    # handbook_ops：配置位 external_deny_alone=False → 永不可独撑对外拒赔
    profile_meta = RETRIEVAL_PROFILES.get(retrieval_profile) or {}
    if retrieval_profile == "handbook_ops" or profile_meta.get("external_deny_alone") is False:
        can_external_deny = False
        if intended_external_action == "deny" or stance == "deny":
            human_latch = True
            notes.append("handbook_ops 不可单独作为对外拒赔依据，进人闸")
        else:
            notes.append("handbook_ops 不可单独作为对外拒赔依据")

    # 规则 vs RAG 冲突 → fail-closed（与轨 A R-CONFLICT-RULES-RAG 对齐）
    if (
        rules_conclusion is not None
        and stance != "unclear"
        and rules_conclusion != stance
    ):
        human_latch = True
        conflict_route = "R-CONFLICT-RULES-RAG"
        notes.append(
            f"规则结论={rules_conclusion} 与 RAG 辅助立场={stance} 冲突，失败关闭进人闸"
        )

    return DraftAssistResult(
        inference_track=track_cfg.inference_track,
        query=query,
        retrieval_profile=retrieval_profile,
        citations=citations,
        draft_text=draft_text,
        used_llm=used_llm,
        suggested_stance=stance,
        human_latch_required=human_latch,
        conflict_route_id=conflict_route,
        can_external_deny=can_external_deny,
        enable_llm=enable_llm,
        notes=notes,
    )
