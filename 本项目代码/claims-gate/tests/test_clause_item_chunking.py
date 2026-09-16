"""接缝：条款项级切块 + 父条款回填 + 改后重建 + citation 三联门。

Rewrote from: RAGFlow 模板切块协议；REF-CASE-KB（Issue 45）
"""

from __future__ import annotations

from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = ROOT / "knowledge_base"


def _collection_count(persist_dir: Path, name: str) -> int:
    client = chromadb.PersistentClient(path=str(persist_dir))
    return int(client.get_collection(name).count())


def test_one_clause_item_one_chunk_when_under_max() -> None:
    """接缝 1a：默认一 clause_item 一块（短文本不过切）。"""
    from missions.clause_chunking import DEFAULT_MAX_CHUNK_CHARS, split_clause_item_chunks

    text = "## 第5条\n条款项: ART-5-EXCL\n\n因疾病导致的摔伤不在责任范围。"
    parts = split_clause_item_chunks(text, clause_item="ART-5-EXCL")
    assert len(parts) == 1
    assert parts[0].clause_item == "ART-5-EXCL"
    assert parts[0].parent_clause_item == "ART-5-EXCL"
    assert parts[0].part_index == 0
    assert parts[0].part_count == 1
    assert len(text) < DEFAULT_MAX_CHUNK_CHARS


def test_overlong_clause_splits_by_paragraph_and_backfills_parent() -> None:
    """接缝 1b：过长按段落切；每块回填父 clause_item。"""
    from missions.clause_chunking import split_clause_item_chunks

    para_a = "甲段。" + ("责任范围说明。" * 40)
    para_b = "乙段。" + ("除外情形列举。" * 40)
    text = f"## 第5条\n条款项: ART-LONG\n\n{para_a}\n\n{para_b}"
    parts = split_clause_item_chunks(text, clause_item="ART-LONG", max_chars=200)
    assert len(parts) >= 2
    assert all(p.clause_item == "ART-LONG" for p in parts)
    assert all(p.parent_clause_item == "ART-LONG" for p in parts)
    assert [p.part_index for p in parts] == list(range(len(parts)))
    assert all(p.part_count == len(parts) for p in parts)
    joined = "\n\n".join(p.text for p in parts)
    assert "甲段" in joined and "乙段" in joined
    # part_0 不得只剩标题/条款项元数据
    assert "甲段" in parts[0].text
    assert "责任范围说明" in parts[0].text


def test_kb_resolve_clause_first_part_includes_body(tmp_path: Path) -> None:
    """回归：过长拆段后 resolve_clause 返回含正文的首块，而非仅元数据。"""
    from missions.rag import KnowledgeBase

    doc = tmp_path / "BODY.md"
    long_a = "首段正文锚点AAA。" + ("意外医疗费用理算规则。" * 80)
    long_b = "次段正文锚点BBB。" + ("免赔与赔付比例细则。" * 80)
    doc.write_text(
        "\n".join(
            [
                "# 正文首块",
                "文档 ID: PA-BODY",
                "文档版本: 2024.1",
                "生效日: 2024-01-01",
                "文档类型: main_policy",
                "",
                "## 第9条 长文",
                "条款项: ART-BODY",
                "",
                long_a,
                "",
                long_b,
            ]
        ),
        encoding="utf-8",
    )
    kb = KnowledgeBase(tmp_path)
    parts = [c for c in kb.chunks if c.clause_item == "ART-BODY"]
    assert len(parts) >= 2
    resolved = kb.resolve_clause("PA-BODY", "ART-BODY", "2024.1")
    assert resolved is not None
    assert "首段正文锚点AAA" in resolved.text
    assert resolved.part_index == 0



def test_kb_load_exposes_parent_and_stable_chunk_ids(tmp_path: Path) -> None:
    """接缝 1c：KB 加载后子块带 parent；单块 chunk_id 保持 doc::item::v 形。"""
    from missions.rag import KnowledgeBase

    doc = tmp_path / "LONG-CLAUSE.md"
    long_a = "首段正文。" + ("意外医疗费用理算规则。" * 80)
    long_b = "次段正文。" + ("免赔与赔付比例细则。" * 80)
    doc.write_text(
        "\n".join(
            [
                "# 长条款样例",
                "文档 ID: PA-LONG",
                "文档版本: 2024.1",
                "生效日: 2024-01-01",
                "文档类型: main_policy",
                "效力层级: 40",
                "",
                "## 第9条 长文",
                "条款项: ART-9-LONG",
                "",
                long_a,
                "",
                long_b,
                "",
            ]
        ),
        encoding="utf-8",
    )
    kb = KnowledgeBase(tmp_path)
    long_parts = [c for c in kb.chunks if c.clause_item == "ART-9-LONG"]
    assert len(long_parts) >= 2
    assert all(c.parent_clause_item == "ART-9-LONG" for c in long_parts)
    assert all("::p" in c.chunk_id for c in long_parts)

    # 生产短条款仍为一块、旧 chunk_id 形
    prod = KnowledgeBase(KB_ROOT)
    excl = [c for c in prod.chunks if c.clause_item == "ART-5-EXCL"]
    assert len(excl) == 1
    assert excl[0].chunk_id == "PA-ACC-MAIN::ART-5-EXCL::v2024.1"
    assert excl[0].parent_clause_item == "ART-5-EXCL"


def test_edit_chunk_source_then_rebuild_index(tmp_path: Path) -> None:
    """接缝 2：人改 KB 源（切块输入）后可重建；条数随切块变化。"""
    from missions.chroma_index import ChromaIndexConfig, rebuild_index
    from missions.rag import KnowledgeBase

    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    src = kb_dir / "EDIT.md"
    long_a = "编辑前甲。" + ("条款叙述。" * 80)
    long_b = "编辑前乙。" + ("除外叙述。" * 80)
    src.write_text(
        "\n".join(
            [
                "# 可编辑",
                "文档 ID: PA-EDIT",
                "文档版本: 1.0",
                "生效日: 2024-01-01",
                "文档类型: main_policy",
                "",
                "## 条款",
                "条款项: ART-EDIT",
                "",
                long_a,
                "",
                long_b,
            ]
        ),
        encoding="utf-8",
    )
    persist = tmp_path / "chroma"
    cfg = ChromaIndexConfig(
        kb_root=kb_dir,
        persist_dir=persist,
        collection_name="clauses_edit",
        embedding_provider="local",
    )
    before_parts = [
        c for c in KnowledgeBase(kb_dir).chunks if c.clause_item == "ART-EDIT"
    ]
    before_total = len(KnowledgeBase(kb_dir).chunks)
    assert len(before_parts) >= 2
    first = rebuild_index(cfg)
    assert first.chunk_count == before_total
    assert _collection_count(persist, "clauses_edit") == before_total

    # 人改：删掉第二段，变短 → ART-EDIT 回落到一块
    src.write_text(
        "\n".join(
            [
                "# 可编辑",
                "文档 ID: PA-EDIT",
                "文档版本: 1.0",
                "生效日: 2024-01-01",
                "文档类型: main_policy",
                "",
                "## 条款",
                "条款项: ART-EDIT",
                "",
                "编辑后短文本。",
            ]
        ),
        encoding="utf-8",
    )
    after_kb = KnowledgeBase(kb_dir)
    after_parts = [c for c in after_kb.chunks if c.clause_item == "ART-EDIT"]
    assert len(after_parts) == 1
    second = rebuild_index(cfg)
    assert second.chunk_count == len(after_kb.chunks)
    assert _collection_count(persist, "clauses_edit") == second.chunk_count


def test_citation_triple_gate_holds_across_parent_parts(tmp_path: Path) -> None:
    """接缝 3：拆段后 citation 仍用父 clause_item 三联门；摘录可落在任一段。"""
    from missions.rag import KnowledgeBase

    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "GATE.md").write_text(
        "\n".join(
            [
                "# 门禁长文",
                "文档 ID: PA-GATE",
                "文档版本: 2024.1",
                "生效日: 2024-01-01",
                "文档类型: main_policy",
                "",
                "## 除外",
                "条款项: ART-GATE",
                "",
                "首段：" + ("疾病除外。" * 80),
                "",
                "次段含独特摘录：库内独特锚点XYZ。" + ("责任说明。" * 80),
            ]
        ),
        encoding="utf-8",
    )
    kb = KnowledgeBase(kb_dir)
    assert len([c for c in kb.chunks if c.clause_item == "ART-GATE"]) >= 2

    ok = kb.validate_citation(
        {
            "doc_id": "PA-GATE",
            "clause_item": "ART-GATE",
            "doc_version": "2024.1",
            "quote": "库内独特锚点XYZ",
        }
    )
    assert ok.ok, ok.detail

    bad_item = kb.validate_citation(
        {
            "doc_id": "PA-GATE",
            "clause_item": "ART-HALLUCINATION",
            "doc_version": "2024.1",
            "quote": "库内独特锚点XYZ",
        }
    )
    assert bad_item.ok is False

    # 生产库短条款三联门不回归
    prod = KnowledgeBase(KB_ROOT)
    assert prod.validate_citation(
        {
            "doc_id": "PA-ACC-MAIN",
            "clause_item": "ART-5-EXCL",
            "doc_version": "2024.1",
            "quote": "疾病",
        }
    ).ok


def test_chroma_metadata_includes_parent_clause_item(tmp_path: Path) -> None:
    """接缝 4：重建写入 parent_clause_item 元数据。"""
    from missions.chroma_index import ChromaIndexConfig, rebuild_index

    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "META.md").write_text(
        "\n".join(
            [
                "# meta",
                "文档 ID: PA-META",
                "文档版本: 1.0",
                "生效日: 2024-01-01",
                "文档类型: main_policy",
                "",
                "## 长",
                "条款项: ART-META",
                "",
                "A。" + ("元数据段甲。" * 80),
                "",
                "B。" + ("元数据段乙。" * 80),
            ]
        ),
        encoding="utf-8",
    )
    persist = tmp_path / "chroma"
    cfg = ChromaIndexConfig(
        kb_root=kb_dir,
        persist_dir=persist,
        collection_name="clauses_meta",
        embedding_provider="local",
    )
    rebuild_index(cfg)
    client = chromadb.PersistentClient(path=str(persist))
    col = client.get_collection("clauses_meta")
    got = col.get(include=["metadatas"])
    metas = got["metadatas"] or []
    art_metas = [m for m in metas if m.get("clause_item") == "ART-META"]
    assert art_metas, "须索引到 ART-META 切块"
    assert all(m.get("parent_clause_item") == "ART-META" for m in art_metas)
    assert all(m.get("clause_item") == "ART-META" for m in art_metas)
    assert any(int(m.get("part_count") or 0) >= 2 for m in art_metas)
