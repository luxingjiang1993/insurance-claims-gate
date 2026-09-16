"""混合检索（仅 AI assist 路径）：硬过滤 / 条款号短路 / BM25 关键词腿 / 加权融合 / 三联门 / 向量降级。

Rewrote from: REF-CASE-RECALL, REF-CASE-KB, REF-RAG-CY, REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

import jieba
from rank_bm25 import BM25Okapi

from missions.models import RoleName
from missions.rag import KnowledgeBase
from missions.retrieval_profiles import RETRIEVAL_PROFILES

# 明确条款号 / clause_item：优先关键词短路（先于加权融合）
_CLAUSE_ITEM_RE = re.compile(
    r"(?:"
    r"ART-\d+[A-Z0-9\-]*"
    r"|POL-CLAIM-\d+"
    r"|条款项\s*[:：]\s*([A-Za-z0-9_\-]+)"
    r")",
    re.IGNORECASE,
)

# 中文常见停用词（与 REF-CASE-KB BM25 对齐的最小集；勿扩到语义难例连接词）
_STOP_WORDS = frozenset(
    {
        "的",
        "了",
        "在",
        "是",
        "我",
        "有",
        "和",
        "就",
        "不",
        "人",
        "都",
        "一",
        "一个",
        "上",
        "也",
        "很",
        "到",
        "说",
        "要",
        "去",
        "你",
        "会",
        "着",
        "没有",
        "看",
        "好",
        "自己",
        "这",
    }
)


def _tokenize_chinese(text: str) -> list[str]:
    """jieba 中文分词；保留条款号等拉丁标识，过滤停用词与单字噪声。"""
    if not text or not str(text).strip():
        return []
    cleaned = re.sub(r"[^\w\s\-]", " ", str(text), flags=re.UNICODE)
    words = jieba.lcut(cleaned)
    out: list[str] = []
    for w in words:
        token = w.strip().lower()
        if not token or token in _STOP_WORDS:
            continue
        # 保留含字母/数字的标识（如 art-5-excl）；中文词长度>1
        if re.search(r"[a-z0-9]", token) or len(token) > 1:
            out.append(token)
    return out


@dataclass(frozen=True)
class HybridRetrievalConfig:
    """混合检索权重与向量开关；默认 keyword 0.7 / vector 0.3。"""

    keyword_weight: float = 0.7
    vector_weight: float = 0.3
    vector_enabled: bool = True

    @classmethod
    def from_env(
        cls,
        *,
        env: Mapping[str, str] | None = None,
    ) -> HybridRetrievalConfig:
        e = dict(os.environ) if env is None else dict(env)
        kw = float(e.get("KEYWORD_WEIGHT") or "0.7")
        vw = float(e.get("VECTOR_WEIGHT") or "0.3")
        raw = (
            e.get("CLAIMS_GATE_VECTOR_ENABLED") or e.get("VECTOR_ENABLED") or "1"
        ).strip().lower()
        vector_enabled = raw not in ("0", "false", "no", "off")
        return cls(
            keyword_weight=kw,
            vector_weight=vw,
            vector_enabled=vector_enabled,
        )


class VectorSearcher(Protocol):
    """向量检索接缝：可注入假实现；失败由调用方降级。"""

    def search(
        self,
        query: str,
        *,
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """返回含 chunk_id / score / metadata 的提名列表。"""
        ...


def extract_clause_item_hint(query: str) -> str | None:
    """若查询含明确条款号/clause_item，返回该键；否则 None。"""
    m = _CLAUSE_ITEM_RE.search(query or "")
    if not m:
        return None
    if m.lastindex and m.group(1):
        return m.group(1).strip()
    return m.group(0).strip()


def _hard_filter_chunks(
    kb: KnowledgeBase,
    *,
    retrieval_profile: str,
) -> list[Any]:
    """按效力栈/版本/profile 硬过滤；过期或不在 prefer 类型的块不进入提名池。"""
    profile_cfg = RETRIEVAL_PROFILES.get(retrieval_profile) or {}
    prefer_types = list(profile_cfg.get("prefer_doc_types") or [])
    chunks = list(kb.chunks)
    if prefer_types:
        chunks = [c for c in chunks if c.doc_type in prefer_types]
    if profile_cfg.get("version_mode") == "current_effective":
        # 按 (doc_id, clause_item) 取最新版本，保留该版本下全部切块（含按段子块）
        best_ver: dict[tuple[str, str], str] = {}
        for c in chunks:
            key = (c.doc_id, c.clause_item)
            prev = best_ver.get(key)
            if prev is None or c.doc_version >= prev:
                best_ver[key] = c.doc_version
        chunks = [
            c
            for c in chunks
            if best_ver.get((c.doc_id, c.clause_item)) == c.doc_version
        ]
    return chunks


def _citation_from_chunk(
    chunk: Any,
    *,
    score: float,
    retrieval_profile: str,
    role: RoleName = RoleName.ORCHESTRATOR,
) -> dict[str, Any]:
    return {
        "doc_id": chunk.doc_id,
        "chunk_id": chunk.chunk_id,
        "clause_id": chunk.clause_id,
        "clause_item": chunk.clause_item,
        "quote": chunk.text[:120],
        "score": round(float(score), 4),
        "title": chunk.title,
        "doc_version": chunk.doc_version,
        "retrieved_by": role.value if isinstance(role, RoleName) else str(role),
        "retrieval_profile": retrieval_profile,
        "doc_type": chunk.doc_type,
        "authority_rank": chunk.authority_rank,
        "effective_date": chunk.effective_date,
    }


def _keyword_score_chunks(
    query: str,
    chunks: list[Any],
    *,
    clause_hint: str | None,
    profile: str,
) -> list[tuple[float, Any]]:
    """关键词腿：BM25（jieba）+ 条款号加成；保留 profile 类型加权。

    Rewrote from: REF-CASE-RECALL; REF-CASE-KB BM25
    """
    if not chunks:
        return []

    # 仅对非空分词块建 BM25；空块保持 0 分（仍可由条款号精确加成）
    tokenized = [_tokenize_chinese(c.text) for c in chunks]
    nonempty = [(idx, toks) for idx, toks in enumerate(tokenized) if toks]
    norm_scores = [0.0] * len(chunks)

    q_tokens = _tokenize_chinese(query)
    if clause_hint:
        q_tokens = q_tokens + _tokenize_chinese(clause_hint)
        # 条款号本身作为强查询词（jieba 可能切碎）
        hint_key = clause_hint.strip().lower()
        if hint_key and hint_key not in q_tokens:
            q_tokens.append(hint_key)

    if nonempty and q_tokens:
        bm25 = BM25Okapi([toks for _, toks in nonempty])
        raw_scores = list(bm25.get_scores(q_tokens))
        max_raw = max(raw_scores) if raw_scores else 0.0
        if max_raw > 0:
            for (idx, _), raw in zip(nonempty, raw_scores):
                norm_scores[idx] = float(raw) / max_raw

    profile_cfg = RETRIEVAL_PROFILES.get(profile) or {}
    prefer_types = list(profile_cfg.get("prefer_doc_types") or [])
    endorsement_first = bool(profile_cfg.get("endorsement_first"))

    # (score, type_rank, chunk)：type_rank 越小越优先
    scored: list[tuple[float, int, Any]] = []
    for idx, chunk in enumerate(chunks):
        score = norm_scores[idx]
        exact_clause = bool(
            clause_hint
            and (
                chunk.clause_id == clause_hint
                or chunk.clause_item == clause_hint
            )
        )
        if exact_clause:
            # 条款号短路：精确命中加分，且优先于 profile 类型序（否则手册/批单会被主险淹没）
            score = min(1.0, score + 0.55)
        if prefer_types and chunk.doc_type in prefer_types:
            type_rank = prefer_types.index(chunk.doc_type)
            score = min(1.0, score + 0.05 * (len(prefer_types) - type_rank))
        else:
            type_rank = len(prefer_types) + 10
        if endorsement_first and chunk.doc_type == "endorsement":
            score = min(1.0, score + 0.08)
            type_rank = 0
        if exact_clause:
            type_rank = -1
        if score > 0:
            scored.append((score, type_rank, chunk))
    scored.sort(key=lambda x: (x[1], -x[0]))
    return [(score, chunk) for score, _rank, chunk in scored]


def apply_citation_gate(
    kb: KnowledgeBase,
    nominations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """提名须过 doc_id+clause_item+version 三联门才可采纳。"""
    out: list[dict[str, Any]] = []
    for item in nominations:
        gate = kb.validate_citation(
            {
                "doc_id": item.get("doc_id"),
                "clause_item": item.get("clause_item"),
                "doc_version": item.get("doc_version"),
                "quote": item.get("quote"),
            }
        )
        row = dict(item)
        if gate.ok:
            row["adoptable"] = True
            row.pop("reject_reason", None)
        else:
            row["adoptable"] = False
            row["reject_reason"] = gate.detail or gate.error_code or "CITATION_NOT_IN_KB"
        out.append(row)
    return out


def _normalize_scores(pairs: list[tuple[float, str]]) -> dict[str, float]:
    """按 chunk_id 归一化到 [0,1]（除以本腿最大分）。"""
    if not pairs:
        return {}
    max_s = max(s for s, _ in pairs) or 1.0
    return {cid: (s / max_s) for s, cid in pairs}


def hybrid_retrieve(
    query: str,
    *,
    kb_root: Path | None = None,
    retrieval_profile: str = "clause_v_current",
    top_k: int = 3,
    cfg: HybridRetrievalConfig | None = None,
    vector_searcher: VectorSearcher | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """混合检索主入口（仅 assist）。

    流程：硬过滤 → 条款号短路或并行关键词(BM25)+向量 → 线性加权 → 三联门。
    向量关闭/故障时自动关键词降级。

    返回 (citations, retrieval_portrait)。
    """
    if retrieval_profile not in RETRIEVAL_PROFILES:
        raise ValueError(f"未知 retrieval_profile: {retrieval_profile}")

    config = cfg or HybridRetrievalConfig.from_env()
    root = kb_root or (Path(__file__).resolve().parents[3] / "knowledge_base")
    kb = KnowledgeBase(root)
    pool = _hard_filter_chunks(kb, retrieval_profile=retrieval_profile)
    pool_by_id = {c.chunk_id: c for c in pool}

    portrait: dict[str, Any] = {
        "mode": "keyword",
        "top_k": top_k,
        "vector_enabled": False,
        "vector_degraded": False,
        "degrade_reason": None,
        "keyword_weight": config.keyword_weight,
        "vector_weight": config.vector_weight,
        "keyword_leg": "bm25",
        "clause_short_circuit": False,
        "embedding_model": None,
        "chroma_collection": None,
    }

    clause_hint = extract_clause_item_hint(query)
    if clause_hint:
        portrait["mode"] = "keyword_short_circuit"
        portrait["clause_short_circuit"] = True
        scored = _keyword_score_chunks(
            query, pool, clause_hint=clause_hint, profile=retrieval_profile
        )
        nominations = [
            _citation_from_chunk(chunk, score=score, retrieval_profile=retrieval_profile)
            for score, chunk in scored[:top_k]
        ]
        return apply_citation_gate(kb, nominations), portrait

    kw_scored = _keyword_score_chunks(
        query, pool, clause_hint=None, profile=retrieval_profile
    )
    kw_norm = _normalize_scores([(s, c.chunk_id) for s, c in kw_scored])

    vec_norm: dict[str, float] = {}
    vector_used = False
    if config.vector_enabled and vector_searcher is not None:
        try:
            hits = vector_searcher.search(query, top_k=max(top_k * 3, 9))
            vec_pairs: list[tuple[float, str]] = []
            for h in hits:
                cid = str(h.get("chunk_id") or "")
                if cid not in pool_by_id:
                    continue
                vec_pairs.append((float(h.get("score") or 0.0), cid))
            vec_norm = _normalize_scores(vec_pairs)
            vector_used = True
            portrait["vector_enabled"] = True
            portrait["mode"] = "hybrid"
        except Exception as exc:
            portrait["vector_degraded"] = True
            portrait["degrade_reason"] = f"vector_error:{type(exc).__name__}"
            portrait["mode"] = "keyword_degraded"
    elif config.vector_enabled and vector_searcher is None:
        portrait["vector_degraded"] = True
        portrait["degrade_reason"] = "vector_unavailable"
        portrait["mode"] = "keyword_degraded"
    else:
        portrait["mode"] = "keyword"
        portrait["degrade_reason"] = "vector_disabled"

    all_ids = set(kw_norm) | set(vec_norm)
    fused: list[tuple[float, str]] = []
    for cid in all_ids:
        if cid not in pool_by_id:
            continue
        if vector_used:
            score = (
                config.keyword_weight * kw_norm.get(cid, 0.0)
                + config.vector_weight * vec_norm.get(cid, 0.0)
            )
        else:
            score = kw_norm.get(cid, 0.0)
        if score > 0:
            fused.append((score, cid))
    fused.sort(key=lambda x: -x[0])

    nominations = [
        _citation_from_chunk(
            pool_by_id[cid], score=score, retrieval_profile=retrieval_profile
        )
        for score, cid in fused[:top_k]
    ]
    return apply_citation_gate(kb, nominations), portrait
