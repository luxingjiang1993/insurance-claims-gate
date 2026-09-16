# Phase 2b · P-α DoD 验收 / 演示记录

`Rewrote from: SPEC-02B-P-ASSIST-QUALITY α DoD` · Issue 44 / GitHub #31

本清单关闭 **Claims Assist 证据地基（α）**。  
**不**宣称：H1/H2 召回有数、H4 grounded、β 三维质量门、γ（rerank / MultiQuery / fan-out / 灌榜）、连接状态 UI、流 Q。

工作目录：`本项目代码/claims-gate/`。默认合门禁：`pytest -q`（无 LLM / 无 LangSmith / 无 cloud embedding Key 仍须绿）。

---

## H1 种子存在（α 只证「有冻结集」，不算 Recall）

| 项 | 证据 |
|----|------|
| 主集 | `artifacts/demo_retrieval_seeds/demo_retrieval_seeds.v1.json` |
| 结构 | 15 `clause_number` + 20 `semantic_hard` + 5 `abstain_conflict` = 40 |
| 诚实 | `is_gold_label=false`；`is_gold_thin_slice=false`；不得称金标 |
| S0 | `pytest -q tests/test_demo_retrieval_seeds.py` |

勾选：`[x] H1 种子集存在（非金标；Recall@K 属 β / 票 46）`

---

## H3 — 采纳路径非法 citation = 0

**可复现（推荐 pytest，无 Key）：**

```text
pytest -q tests/test_assist_citation_schema_adopt.py
```

**期望：** Schema 缺槽 / 库外幻觉三联键 → 采纳拒绝（`CITATION_NOT_IN_KB` / 校验失败）；合法 citation 采纳后仍 `evaluate`（确定性轨）。

**手工对照（可选）：** 登录 `adjuster` → 案件 `CLM-SC02-001` → `POST .../assist/adopt` 携带 `doc_id=PA-GHOST` 等幻觉三联键 → 非 2xx，权威裁决不被静默改写。

勾选：`[x] H3 可演示`

---

## H6 — 工具环越权写入权威字段 = 0

**可复现：**

```text
pytest -q tests/test_assist_tool_acl.py
```

**期望：** 白名单仅 `retrieve` / `validate_citation` / `draft_slots`；latch / 支付 / evaluate 权威写工具名 → `AssistToolAclError`；`human_latch_token` / `payout_ready` / `decision_type` 不被工具环改写。

勾选：`[x] H6 可演示`

---

## H7 — 无 LLM / 无 LangSmith 下轨 A 绿

**可复现（α 合门禁 S0）：**

```text
pytest -q
```

**记录（2026-09-16）：** `235 passed, 20 deselected`（排除 `track_llm_optional` / `eval_bypass` / `requires_llm` / `langsmith_integration`）；无 cloud embedding Key。

**补充：** `tests/test_hybrid_retrieval.py::test_evaluate_modules_still_zero_chroma_dependency` 证 evaluate 零向量依赖。

勾选：`[x] H7 可演示` · `[x] S0 绿`

---

## 手册诚实（γ / Deferred 未假上线）

- USER_GUIDE：H4=`deferred`；连接状态属 β；≥300 金标 / 真连 L2 Deferred；未把 rerank / MultiQuery / fan-out 写成已上线。
- CHANGELOG：α 用户可见项已折叠进 Phase 2b · P-α 节。
- 按 `docs/user/MAINTENANCE.md`：阶段 DoD 关闭时已同步 `USER_GUIDE.md` + `CHANGELOG.md`。

勾选：`[x] 手册诚实` · `[x] 用户手册已同步`

---

## α DoD 总勾选

| SPEC α 项 | 状态 |
|-----------|------|
| Pilot cloud embedding + local 非语义文案 | 票 34 |
| citation Schema + 非法不可采纳 + 仍 evaluate | 票 37 / H3 |
| Demo 检索种子 40 冻结 | 票 36 / H1 种子 |
| 金标薄切片协议；n&lt;10 → H4 deferred | 票 38 |
| assist_disposition + abstain 禁用采纳 | 票 39 |
| 工具环白名单；越权负例 | 票 40 / H6 |
| span 树 + 本地 JSONL 回放 | 票 41 |
| BM25 关键词腿 + 条款号短路 | 票 35 |
| 引用忠实规则/夹具 | 票 42 |
| Provider 清单 + `.env.example` | 票 43 |
| H3 / H6 / H7 可演示；H1 种子存在 | 本文件 |
| 默认 `pytest -q` 绿 | 本文件 H7 |

**关闭后解阻：** `phase2b-p-β`（45–52）与未来 `SPEC-02B-Q`（另页）。
