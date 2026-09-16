"""轻量条款 KB：条款项级切块 + 父条款回填 + 落库门。

Rewrote from: RAGFlow 模板切块协议；REF-CASE-KB, REF-MISSIONS
（missions/rag.py；升到 doc_id+clause_item+doc_version；Issue 45 父条款回填）
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claims_api.error_codes import ErrorCode

from .clause_chunking import make_chunk_id, split_clause_item_chunks
from .models import RagCitation, RoleName
from .retrieval_profiles import RETRIEVAL_PROFILES

TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]{1,}")

# 文档类型 → 默认效力层级（数值越小优先级越高，对齐效力栈）
_DEFAULT_AUTHORITY: dict[str, int] = {
    "endorsement": 10,
    "special_agreement": 20,
    "rider": 30,
    "main_policy": 40,
    "application": 50,
    "handbook": 60,
}


@dataclass
class Chunk:
    doc_id: str
    chunk_id: str
    title: str
    clause_id: str
    clause_item: str
    text: str
    doc_version: str
    effective_date: str
    authority_rank: int
    doc_type: str
    tokens: set[str]
    # 父条款项 id（未拆分时等于 clause_item；拆段后各子块回填同一父 id）
    parent_clause_item: str = ""
    part_index: int = 0
    part_count: int = 1


@dataclass
class CitationGateResult:
    """条款项落库门结果；失败关闭时带 error_code。"""

    ok: bool
    error_code: str | None = None
    detail: str = ""
    chunk: Chunk | None = None


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text) if t.strip()}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _normalize_excerpt(text: str) -> str:
    return re.sub(r"\s+", "", text)


class KnowledgeBase:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.chunks: list[Chunk] = []
        self._load()

    def _load(self) -> None:
        if not self.root.exists():
            return
        for path in sorted(self.root.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            doc_id = self._extract_field(text, "文档 ID") or path.stem
            version = self._extract_field(text, "文档版本") or "1.0"
            effective_date = self._extract_field(text, "生效日") or ""
            doc_type = self._extract_field(text, "文档类型") or "main_policy"
            authority_raw = self._extract_field(text, "效力层级")
            if authority_raw and authority_raw.isdigit():
                authority_rank = int(authority_raw)
            else:
                authority_rank = _DEFAULT_AUTHORITY.get(doc_type, 40)
            title = path.stem
            parts = re.split(r"\n(?=## )", text)
            for idx, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                heading = re.match(r"^##\s+(.+)$", part, re.MULTILINE)
                clause_item = self._extract_field(part, "条款项") or ""
                clause_id = f"{doc_id}#{idx}"
                if heading:
                    head = heading.group(1).strip()
                    m = re.match(r"(POL-CLAIM-\d+)", head)
                    if m:
                        clause_id = m.group(1)
                        if not clause_item:
                            clause_item = clause_id
                if not clause_item:
                    # 无条款项的前言块不入落库索引（仍可检索）
                    clause_item = clause_id
                # 条款项级切块：默认一块；过长按段切并回填父 id
                for piece in split_clause_item_chunks(part, clause_item=clause_item):
                    chunk_id = make_chunk_id(
                        doc_id,
                        clause_item,
                        version,
                        part_index=piece.part_index,
                        part_count=piece.part_count,
                    )
                    self.chunks.append(
                        Chunk(
                            doc_id=doc_id,
                            chunk_id=chunk_id,
                            title=title,
                            clause_id=clause_id,
                            clause_item=piece.clause_item,
                            text=piece.text,
                            doc_version=version,
                            effective_date=effective_date,
                            authority_rank=authority_rank,
                            doc_type=doc_type,
                            tokens=_tokenize(piece.text),
                            parent_clause_item=piece.parent_clause_item,
                            part_index=piece.part_index,
                            part_count=piece.part_count,
                        )
                    )

    @staticmethod
    def _extract_field(text: str, label: str) -> str | None:
        m = re.search(rf"{re.escape(label)}\s*[:：]\s*(.+)", text)
        return m.group(1).strip() if m else None

    def get_clause(self, clause_id: str) -> Chunk | None:
        """兼容旧接口：按 clause_id 或 clause_item 定位（不校验版本）。"""
        for chunk in self.chunks:
            if chunk.clause_id == clause_id or chunk.clause_item == clause_id:
                return chunk
        return None

    def resolve_clause_parts(
        self,
        doc_id: str,
        clause_item: str,
        doc_version: str,
    ) -> list[Chunk]:
        """同一三联键下的全部切块（含按段拆分的子块）。"""
        out: list[Chunk] = []
        for chunk in self.chunks:
            if chunk.doc_id != doc_id or chunk.clause_item != clause_item:
                continue
            if chunk.doc_version == doc_version or (
                chunk.effective_date and chunk.effective_date == doc_version
            ):
                out.append(chunk)
        out.sort(key=lambda c: c.part_index)
        return out

    def resolve_clause(
        self,
        doc_id: str,
        clause_item: str,
        doc_version: str,
    ) -> Chunk | None:
        """条款项级精确命中：doc_id + clause_item + (doc_version 或等价生效日)。

        若已按段拆分，返回 part_index 最小的子块（父条款回填后 clause_item 仍相同）。
        """
        parts = self.resolve_clause_parts(doc_id, clause_item, doc_version)
        return parts[0] if parts else None

    def validate_citation(self, citation: dict[str, Any]) -> CitationGateResult:
        """对外可用 citation 落库门：三联键精确匹配；可选摘录须落在库内条目。

        禁止用全文最大相似冒充通过。版本键可为 doc_version 或等价 effective_date。
        拆段后摘录可落在任一子块或父条款全文拼接上。
        """
        doc_id = str(citation.get("doc_id") or "").strip()
        clause_item = str(citation.get("clause_item") or "").strip()
        doc_version = str(
            citation.get("doc_version") or citation.get("effective_date") or ""
        ).strip()
        quote = str(citation.get("quote") or "").strip()

        if not doc_id or not clause_item or not doc_version:
            return CitationGateResult(
                ok=False,
                error_code=ErrorCode.CITATION_NOT_IN_KB.value,
                detail="缺少 doc_id/clause_item/doc_version(或 effective_date)",
            )

        parts = self.resolve_clause_parts(doc_id, clause_item, doc_version)
        if not parts:
            # 文档存在但条款项/版本不匹配仍失败（非文档级门）
            doc_exists = any(c.doc_id == doc_id for c in self.chunks)
            detail = (
                f"条款项或版本未落库 doc_id={doc_id} clause_item={clause_item} "
                f"doc_version={doc_version} doc_exists={doc_exists}"
            )
            return CitationGateResult(
                ok=False,
                error_code=ErrorCode.CITATION_NOT_IN_KB.value,
                detail=detail,
            )

        primary = parts[0]
        if quote:
            hay = _normalize_excerpt("".join(p.text for p in parts))
            needle = _normalize_excerpt(quote)
            if needle not in hay:
                return CitationGateResult(
                    ok=False,
                    error_code=ErrorCode.CITATION_NOT_IN_KB.value,
                    detail="摘录无法对应库内条目",
                    chunk=primary,
                )

        return CitationGateResult(ok=True, detail="ok", chunk=primary)

    def retrieve(
        self,
        query: str,
        *,
        role: RoleName,
        profile: str,
        top_k: int = 3,
        clause_hint: str | None = None,
    ) -> list[RagCitation]:
        """检索仅用于候选召回；不得替代 validate_citation 落库门。"""
        q_tokens = _tokenize(query)
        if clause_hint:
            q_tokens |= _tokenize(clause_hint)

        profile_cfg = RETRIEVAL_PROFILES.get(profile, {})
        prefer_types = list(profile_cfg.get("prefer_doc_types") or [])
        endorsement_first = bool(profile_cfg.get("endorsement_first"))

        effective_k = max(top_k, 5) if profile.startswith("validator") else top_k
        scored: list[tuple[float, int, Chunk]] = []
        for chunk in self.chunks:
            score = _jaccard(q_tokens, chunk.tokens)
            if clause_hint and (
                chunk.clause_id == clause_hint or chunk.clause_item == clause_hint
            ):
                score = min(1.0, score + 0.55)
            if prefer_types and chunk.doc_type in prefer_types:
                # 配置位加权：不替代精确落库
                type_rank = prefer_types.index(chunk.doc_type)
                score = min(1.0, score + 0.05 * (len(prefer_types) - type_rank))
            else:
                type_rank = len(prefer_types) + 10
            if endorsement_first and chunk.doc_type == "endorsement":
                score = min(1.0, score + 0.08)
                type_rank = 0
            if score > 0:
                # type_rank 越小越优先（endorsement_priority：先批单再主险）
                scored.append((score, type_rank, chunk))
        # 先按 prefer 类型序，再按相似度
        scored.sort(key=lambda x: (x[1], -x[0]))
        out: list[RagCitation] = []
        for score, _type_rank, chunk in scored[:effective_k]:
            out.append(
                RagCitation(
                    doc_id=chunk.doc_id,
                    chunk_id=chunk.chunk_id,
                    clause_id=chunk.clause_id,
                    clause_item=chunk.clause_item,
                    quote=chunk.text[:120],
                    score=round(score, 4),
                    title=chunk.title,
                    doc_version=chunk.doc_version,
                    retrieved_by=role,
                    retrieval_profile=profile,
                )
            )
        return out
