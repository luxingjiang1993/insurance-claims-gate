"""轨 B 最小「检索 → 辅助起草」管线。

允许确定性假检索（enable_llm=False，默认）；若调用 LLM 须显式打开且 CI 不依赖。
规则 vs RAG 冲突仍 fail-closed 进人闸；handbook_ops 不得单独支撑对外拒赔。
混合检索仅挂本路径；evaluate 不得调用向量。
检索与草稿槽经 AssistToolRing 白名单调度（H6）；不得写 latch/支付/evaluate 权威字段。

完整方差预算 / 金标门槛数值化仍属 P2-4；本模块只做最小可跑。
Rewrote from: REF-CASE-RECALL, REF-RAG-CY, REF-CASE-HYBRID, REF-MISSIONS, REF-CASE-FC
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from missions.assist_disposition import (
    mark_citations_unadoptable_for_abstain,
    resolve_assist_disposition,
)
from missions.assist_tool_ring import AssistToolRing
from missions.retrieval_profiles import RETRIEVAL_PROFILES

from .config import TrackBConfig
from .llm_client import LlmConfigError, chat_completion, resolve_api_key
from .retrieval import retrieve_chunks

# 辅助起草立场：仅启发式，不得替代轨 A 裁决
DraftStance = Literal["pay", "deny", "reduce", "unclear"]

_DENY_HINTS = ("责任免除", "除外", "不承担", "不予给付", "拒赔", "剔除")
_PAY_HINTS = ("保险责任", "给付保险金", "承担给付")
_REDUCE_HINTS = ("免赔", "赔付比例", "减赔", "缩小责任")

_LLM_SYSTEM = (
    "你是理赔条款辅助起草助手。仅根据给定摘录给出简短中文辅助建议；"
    "不得签发人闸令牌、不得宣布出款就绪、不得改写 latch 规则。"
    "输出须标明「仅供人审辅助，非终裁」。"
)


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
    assist_invocation_id: str = ""
    degraded: bool = False
    degrade_reason: str | None = None
    # W0 关键词画像；W1 可填 vector_* 而不改契约
    retrieval: dict[str, Any] = field(default_factory=dict)
    # Issue 39：辅助拒答 disposition（永不签发人闸令牌）
    assist_disposition: Literal["draft", "abstain"] = "draft"
    abstain_reason: str | None = None
    human_latch_suggested: bool = False

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
            "assist_invocation_id": self.assist_invocation_id,
            "degraded": self.degraded,
            "degrade_reason": self.degrade_reason,
            "retrieval": dict(self.retrieval),
            "assist_disposition": self.assist_disposition,
            "abstain_reason": self.abstain_reason,
            "human_latch_suggested": self.human_latch_suggested,
            # 硬保证：assist 产物永不写出款就绪 / 人闸令牌
            "payout_ready": False,
            "human_latch_token": None,
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
        f"[轨 B 辅助起草 · inference_track=llm_optional · 关键词提名]",
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


def _build_llm_user_prompt(query: str, citations: list[dict[str, Any]]) -> str:
    """组装供模型阅读的用户提示（含关键词提名摘录）。"""
    lines = [f"核赔员查询: {query}", "关键词检索提名摘录:"]
    if not citations:
        lines.append("- （无命中）")
    for i, c in enumerate(citations, start=1):
        doc_id = c.get("doc_id") or "?"
        item = c.get("clause_item") or c.get("clause_id") or "?"
        quote = (c.get("quote") or "").replace("\n", " ").strip()[:240]
        lines.append(f"- [{i}] {doc_id} / {item}: {quote}")
    lines.append("请输出简短中文辅助建议（非终裁）。")
    return "\n".join(lines)


def _maybe_llm_draft(
    query: str,
    citations: list[dict[str, Any]],
    *,
    enable_llm: bool,
) -> tuple[str | None, bool, str | None]:
    """LLM 起草旁路。

    返回 (文本, used_llm, degrade_reason)。
    - enable_llm=False 或无 Key：不调用，degrade_reason 说明原因。
    - 有 Key 且启用：真实 OpenAI-compatible 调用；失败抛 LlmCallError（不静默回落）。
    """
    if not enable_llm:
        return None, False, "llm_disabled"
    if not resolve_api_key():
        return None, False, "missing_openai_api_key"
    try:
        text = chat_completion(
            system=_LLM_SYSTEM,
            user=_build_llm_user_prompt(query, citations),
        )
    except LlmConfigError:
        return None, False, "missing_openai_api_key"
    return text, True, None


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
    """检索 → 辅助起草。默认 enable_llm=False（关键词确定性提名）。"""
    track_cfg = cfg or TrackBConfig()
    # 经白名单工具环调度 retrieve（禁 latch/支付/evaluate 权威写）
    ring = AssistToolRing(
        retrieve_fn=lambda **kw: _ring_retrieve(kb_root=kb_root, **kw),
    )
    retrieved_payload = ring.invoke(
        "retrieve",
        {
            "query": query,
            "retrieval_profile": retrieval_profile,
            "top_k": top_k,
        },
    )
    citations = list(retrieved_payload.get("citations") or [])
    retrieval_portrait = dict(retrieved_payload.get("retrieval") or {})
    stance = _infer_stance(citations, query)
    llm_text, used_llm, degrade_reason = _maybe_llm_draft(
        query, citations, enable_llm=enable_llm
    )
    draft_text = llm_text or _build_deterministic_draft(query, citations, stance)
    # 仅在「本想用 LLM 但未用上」时标降级；显式 enable_llm=False 不算降级
    degraded = bool(enable_llm and not used_llm)
    if not degraded:
        degrade_reason = None

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

    if degraded and degrade_reason:
        notes.append(f"LLM 降级: {degrade_reason}")
    if retrieval_portrait.get("vector_degraded"):
        notes.append(
            f"向量检索降级: {retrieval_portrait.get('degrade_reason') or 'keyword_only'}"
        )

    disposition, abstain_reason, latch_suggested = resolve_assist_disposition(
        query=query,
        conflict_route_id=conflict_route,
        can_external_deny=can_external_deny,
        retrieval_profile=retrieval_profile,
        stance=stance,
        intended_external_action=intended_external_action,
        citations=citations,
    )
    if disposition == "abstain" and abstain_reason:
        mark_citations_unadoptable_for_abstain(citations, abstain_reason)
        human_latch = True
        latch_suggested = True
        notes.append(f"辅助拒答: assist_disposition=abstain reason={abstain_reason}")
        draft_text = (
            f"[辅助拒答 · abstain · {abstain_reason}]\n"
            f"查询: {query}\n"
            "说明: 当前条件不足以形成可采纳的 AI 辅助建议；"
            "可前往人闸由持牌核赔处理，但本路径不会自动签发人闸令牌。\n"
            f"原草稿摘录已收回（不可送交采纳）。\n---\n{draft_text}"
        )

    # draft_slots：仅填建议体槽；硬钉无令牌 / 无出款就绪（H6）
    slots = ring.invoke(
        "draft_slots",
        {
            "query": query,
            "draft_text": draft_text,
            "suggested_stance": stance,
            "citations": citations,
            "notes": notes,
            "retrieval_profile": retrieval_profile,
            "assist_disposition": disposition,
            "abstain_reason": abstain_reason,
            "human_latch_suggested": latch_suggested,
            "human_latch_required": human_latch,
            "degraded": degraded,
            "degrade_reason": degrade_reason if degraded else None,
            "inference_track": track_cfg.inference_track,
        },
    )

    return DraftAssistResult(
        inference_track=track_cfg.inference_track,
        query=query,
        retrieval_profile=retrieval_profile,
        citations=list(slots.get("citations") or citations),
        draft_text=str(slots.get("draft_text") or draft_text),
        used_llm=used_llm,
        suggested_stance=stance,
        human_latch_required=bool(slots.get("human_latch_required", human_latch)),
        conflict_route_id=conflict_route,
        can_external_deny=can_external_deny,
        enable_llm=enable_llm,
        notes=list(slots.get("notes") or notes),
        assist_invocation_id=f"assist-{uuid.uuid4().hex[:16]}",
        degraded=degraded,
        degrade_reason=degrade_reason if degraded else None,
        retrieval=retrieval_portrait,
        assist_disposition=disposition,
        abstain_reason=abstain_reason,
        human_latch_suggested=bool(
            slots.get("human_latch_suggested", latch_suggested)
        ),
    )


def _ring_retrieve(
    *,
    query: str,
    retrieval_profile: str,
    top_k: int,
    kb_root: Path | None = None,
) -> dict[str, Any]:
    """供 AssistToolRing.retrieve 注入：混合检索仅挂 assist。"""
    citations, portrait = retrieve_chunks(
        query,
        kb_root=kb_root,
        retrieval_profile=retrieval_profile,
        top_k=top_k,
        return_portrait=True,
    )
    return {"citations": citations, "retrieval": portrait}
