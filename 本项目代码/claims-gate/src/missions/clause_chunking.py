"""条款项级切块：默认一块；过长按段切并回填父 clause_item。

Rewrote from: RAGFlow 模板切块协议；REF-CASE-KB（Issue 45）
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 默认上限（字符）；超过则按空行分段并回填父条款项 id
DEFAULT_MAX_CHUNK_CHARS = 400

_HEADING_RE = re.compile(r"^##\s+")
_CLAUSE_ITEM_FIELD_RE = re.compile(r"^条款项\s*[:：]")


@dataclass(frozen=True)
class ClauseChunkPart:
    """单个切块产物；citation 键仍用 clause_item（= 父条款项）。

    子块不另起 clause_item：parent_clause_item 与 clause_item 同值，
    便于三联门与检索共用父条款项 id。
    """

    text: str
    clause_item: str
    parent_clause_item: str
    part_index: int
    part_count: int


def _paragraphs(text: str) -> list[str]:
    """按空行分段；保留非空段。"""
    raw = text.replace("\r\n", "\n").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split("\n\n")]
    return [p for p in parts if p]


def _looks_like_clause_preamble(para: str) -> bool:
    """标题 / 条款项字段段：去掉后几乎无正文则视为前言，须并入下一段。"""
    lines = [ln.strip() for ln in para.splitlines() if ln.strip()]
    if not lines:
        return True
    body_bits: list[str] = []
    for ln in lines:
        if _HEADING_RE.match(ln) or _CLAUSE_ITEM_FIELD_RE.match(ln):
            continue
        body_bits.append(ln)
    return len("".join(body_bits).strip()) < 8


def _merge_preamble_into_body(paras: list[str]) -> list[str]:
    """避免拆段后 part_0 只剩 ## / 条款项 元数据。"""
    out = list(paras)
    while len(out) >= 2 and _looks_like_clause_preamble(out[0]):
        out = [f"{out[0]}\n\n{out[1]}"] + out[2:]
    return out


def split_clause_item_chunks(
    text: str,
    *,
    clause_item: str,
    max_chars: int = DEFAULT_MAX_CHUNK_CHARS,
) -> list[ClauseChunkPart]:
    """默认一 clause_item 一块；过长按段落切，每块回填 parent_clause_item。

    单段仍超长时保持为一段（不硬截断），避免破坏条款语义。
    """
    body = text.strip()
    parent = clause_item
    if not body:
        return [
            ClauseChunkPart(
                text="",
                clause_item=parent,
                parent_clause_item=parent,
                part_index=0,
                part_count=1,
            )
        ]
    if len(body) <= max_chars:
        return [
            ClauseChunkPart(
                text=body,
                clause_item=parent,
                parent_clause_item=parent,
                part_index=0,
                part_count=1,
            )
        ]

    paras = _merge_preamble_into_body(_paragraphs(body))
    if len(paras) <= 1:
        # 无法按段再切：仍回填父 id，整块保留
        return [
            ClauseChunkPart(
                text=body,
                clause_item=parent,
                parent_clause_item=parent,
                part_index=0,
                part_count=1,
            )
        ]

    # 贪心装箱：相邻段合并直至接近 max_chars
    buckets: list[str] = []
    current = paras[0]
    for para in paras[1:]:
        candidate = f"{current}\n\n{para}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            buckets.append(current)
            current = para
    buckets.append(current)

    n = len(buckets)
    return [
        ClauseChunkPart(
            text=bucket,
            clause_item=parent,
            parent_clause_item=parent,
            part_index=i,
            part_count=n,
        )
        for i, bucket in enumerate(buckets)
    ]


def make_chunk_id(
    doc_id: str,
    clause_item: str,
    doc_version: str,
    *,
    part_index: int,
    part_count: int,
) -> str:
    """单块保持历史形 doc::item::v；多段加 ::p{n}。"""
    base = f"{doc_id}::{clause_item}"
    if part_count <= 1:
        return f"{base}::v{doc_version}"
    return f"{base}::p{part_index}::v{doc_version}"
