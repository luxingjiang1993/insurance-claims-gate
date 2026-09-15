"""接缝：Demo 检索种子冻结集（票 36 / P-G1）。

S0：结构契约（默认 CI）——恰好 40=15+20+5；不得称金标；造问非主集。
S2 Recall@K / MRR 由后续票（P-R3）承接，本票只冻结人写主集。

Rewrote from: 人写
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS_DIR = ROOT / "artifacts" / "demo_retrieval_seeds"
MAIN_PATH = SEEDS_DIR / "demo_retrieval_seeds.v1.json"
AUGMENT_DIR = SEEDS_DIR / "augment"

FORBIDDEN_CLAIM_PHRASES = (
    "金标薄切片",
    "本集为金标",
    "本数据集是金标",
    "金标已达标",
)


def test_frozen_main_set_exists_and_loads() -> None:
    """接缝：主集文件进仓且可经公开加载器解析。"""
    from missions.demo_retrieval_seeds import load_demo_retrieval_seeds

    assert MAIN_PATH.is_file(), "Demo 检索种子主集须冻结进 git"
    dataset = load_demo_retrieval_seeds(MAIN_PATH)
    assert dataset.schema == "claims-gate-demo-retrieval-seeds-v1"
    assert dataset.label == "Demo 检索种子"
    assert len(dataset.queries) == 40


def test_bucket_counts_are_exactly_15_20_5() -> None:
    """接缝：恰好 15 条款号 + 20 语义难例 + 5 拒答/冲突负例。"""
    from missions.demo_retrieval_seeds import BUCKET_COUNTS, load_demo_retrieval_seeds

    dataset = load_demo_retrieval_seeds(MAIN_PATH)
    counts = dataset.bucket_counts()
    assert counts == BUCKET_COUNTS
    assert counts["clause_number"] == 15
    assert counts["semantic_hard"] == 20
    assert counts["abstain_conflict"] == 5


def test_main_set_must_not_claim_gold_label() -> None:
    """接缝：文案与元数据禁止把 Demo 检索种子称为金标 / 金标薄切片。"""
    from missions.demo_retrieval_seeds import load_demo_retrieval_seeds

    raw = MAIN_PATH.read_text(encoding="utf-8")
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        assert phrase not in raw, f"主集不得出现宣称短语: {phrase}"
    # 允许否定句说明「非金标」
    assert "非金标" in raw or "不是金标" in raw or "不得称金标" in raw

    dataset = load_demo_retrieval_seeds(MAIN_PATH)
    assert dataset.is_gold_label is False
    assert dataset.is_gold_thin_slice is False
    # 元数据键不得伪装成金标集
    payload = dataset.to_dict()
    assert payload.get("is_gold_label") is False
    assert payload.get("is_gold_thin_slice") is False


def test_query_ids_unique_and_human_authored() -> None:
    """接缝：每条有稳定 query_id；主集 authorship=human。"""
    from missions.demo_retrieval_seeds import load_demo_retrieval_seeds

    dataset = load_demo_retrieval_seeds(MAIN_PATH)
    ids = [q.query_id for q in dataset.queries]
    assert len(ids) == len(set(ids))
    assert all(q.authorship == "human" for q in dataset.queries)
    assert all(q.query.strip() for q in dataset.queries)


def test_clause_bucket_has_expected_clause_and_hint_surface() -> None:
    """接缝：条款号子集每条有 expected.relevant_clause_items，且 query 含可短路表面形。"""
    from missions.demo_retrieval_seeds import load_demo_retrieval_seeds
    from missions.track_llm_optional.hybrid_retrieval import extract_clause_item_hint

    dataset = load_demo_retrieval_seeds(MAIN_PATH)
    clause_rows = [q for q in dataset.queries if q.bucket == "clause_number"]
    assert len(clause_rows) == 15
    for row in clause_rows:
        expected = row.expected.get("relevant_clause_items") or []
        assert expected, f"{row.query_id} 须有 relevant_clause_items"
        hint = extract_clause_item_hint(row.query)
        assert hint, f"{row.query_id} 条款号子集 query 须可抽出条款号短路键"
        assert hint.upper() == str(expected[0]).upper() or hint in {
            str(x) for x in expected
        }


def test_semantic_hard_has_no_clause_short_circuit() -> None:
    """接缝：语义难例不得带条款号短路键（否则计入 H1 而非 H2）。"""
    from missions.demo_retrieval_seeds import load_demo_retrieval_seeds
    from missions.track_llm_optional.hybrid_retrieval import extract_clause_item_hint

    dataset = load_demo_retrieval_seeds(MAIN_PATH)
    hard = [q for q in dataset.queries if q.bucket == "semantic_hard"]
    assert len(hard) == 20
    for row in hard:
        assert extract_clause_item_hint(row.query) is None, row.query_id
        expected = row.expected.get("relevant_clause_items") or []
        assert expected, f"{row.query_id} 语义难例须有相关条款期望"


def test_abstain_conflict_rows_declare_disposition() -> None:
    """接缝：拒答/冲突负例预登记 assist_disposition=abstain 与原因枚举。"""
    from missions.demo_retrieval_seeds import ABSTAIN_REASONS, load_demo_retrieval_seeds

    dataset = load_demo_retrieval_seeds(MAIN_PATH)
    neg = [q for q in dataset.queries if q.bucket == "abstain_conflict"]
    assert len(neg) == 5
    reasons = set()
    for row in neg:
        assert row.expected.get("assist_disposition") == "abstain", row.query_id
        reason = row.expected.get("abstain_reason")
        assert reason in ABSTAIN_REASONS, row.query_id
        reasons.add(reason)
    # H5 预登记：五种负例应覆盖多个原因族（至少 3 种）
    assert len(reasons) >= 3


def test_augment_isolated_from_main_set() -> None:
    """接缝：造问增广若存在则隔离在 augment/，不得并入主集计数。"""
    from missions.demo_retrieval_seeds import (
        list_augment_paths,
        load_demo_retrieval_seeds,
    )

    dataset = load_demo_retrieval_seeds(MAIN_PATH)
    assert len(dataset.queries) == 40
    assert AUGMENT_DIR.is_dir(), "须预留 augment/ 污染隔离目录"
    # 主集文件不得位于 augment/
    assert "augment" not in MAIN_PATH.parts or MAIN_PATH.parent == SEEDS_DIR
    for path in list_augment_paths(SEEDS_DIR):
        assert path.parent == AUGMENT_DIR or AUGMENT_DIR in path.parents
        # 增广文件不得被算进主集
        assert path.resolve() != MAIN_PATH.resolve()


def test_module_declares_rewrote_from_human() -> None:
    """handoff：模块声明 Rewrote from: 人写。"""
    path = ROOT / "src" / "missions" / "demo_retrieval_seeds.py"
    text = path.read_text(encoding="utf-8")
    assert "Rewrote from" in text
    assert "人写" in text
    assert "Demo 检索种子" in text
    assert "金标" in text  # 否定语境说明边界
