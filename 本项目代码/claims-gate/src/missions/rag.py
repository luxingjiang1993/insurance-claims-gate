"""轻量条款 KB：脚手架最小检索。

Rewrote from: REF-MISSIONS（missions/rag.py；内容换理赔条款）
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .models import RagCitation, RoleName

TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]{1,}")


@dataclass
class Chunk:
    doc_id: str
    chunk_id: str
    title: str
    clause_id: str
    text: str
    doc_version: str
    tokens: set[str]


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text) if t.strip()}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


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
            title = path.stem
            parts = re.split(r"\n(?=## )", text)
            for idx, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                heading = re.match(r"^##\s+(.+)$", part, re.MULTILINE)
                clause_id = f"{doc_id}#{idx}"
                if heading:
                    head = heading.group(1).strip()
                    m = re.match(r"(POL-CLAIM-\d+)", head)
                    if m:
                        clause_id = m.group(1)
                chunk_id = f"{doc_id}::chunk-{idx}"
                self.chunks.append(
                    Chunk(
                        doc_id=doc_id,
                        chunk_id=chunk_id,
                        title=title,
                        clause_id=clause_id,
                        text=part,
                        doc_version=version,
                        tokens=_tokenize(part),
                    )
                )

    @staticmethod
    def _extract_field(text: str, label: str) -> str | None:
        m = re.search(rf"{re.escape(label)}\s*[:：]\s*(.+)", text)
        return m.group(1).strip() if m else None

    def get_clause(self, clause_id: str) -> Chunk | None:
        for chunk in self.chunks:
            if chunk.clause_id == clause_id:
                return chunk
        return None

    def retrieve(
        self,
        query: str,
        *,
        role: RoleName,
        profile: str,
        top_k: int = 3,
        clause_hint: str | None = None,
    ) -> list[RagCitation]:
        q_tokens = _tokenize(query)
        if clause_hint:
            q_tokens |= _tokenize(clause_hint)
        effective_k = max(top_k, 5) if profile.startswith("validator") else top_k
        scored: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            score = _jaccard(q_tokens, chunk.tokens)
            if clause_hint and chunk.clause_id == clause_hint:
                score = min(1.0, score + 0.55)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[RagCitation] = []
        for score, chunk in scored[:effective_k]:
            out.append(
                RagCitation(
                    doc_id=chunk.doc_id,
                    chunk_id=chunk.chunk_id,
                    clause_id=chunk.clause_id,
                    quote=chunk.text[:120],
                    score=round(score, 4),
                    title=chunk.title,
                    doc_version=chunk.doc_version,
                    retrieved_by=role,
                    retrieval_profile=profile,
                )
            )
        return out
