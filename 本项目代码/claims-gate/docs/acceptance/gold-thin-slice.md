# 金标薄切片协议验收（Issue 38 / P-E3）

`Rewrote from: REF-CASE-OPENEVALS` · `spec_id: SPEC-02B-P-ASSIST-QUALITY` · GitHub #25

本清单验收 **金标薄切片协议 + 导入导出加深**。  
旁路能力：**不**写入默认 `pytest -q` / `machine_check` 合门禁。

---

## 协议（双标 + 第三人）

| 角色占位（人名不进仓） | 职责 |
|------------------------|------|
| `external_claims_advisor_a` | 外聘核赔顾问独立标注 A |
| `external_claims_advisor_b` | 外聘核赔顾问独立标注 B |
| `third_party_adjudicator` | 第三人裁决分歧；形成 `expected` 终稿 |

硬约束：

1. 每条记录必须有 `case_id`。
2. 薄切片 schema：`claims-gate-gold-thin-slice-v1`；`is_gold_thin_slice=true`。
3. 每条须含 `annotation`（`label_a` / `label_b` / `adjudication` + 三角色占位）。
4. **禁止**真人姓名写入仓库 JSON / SQLite 角色字段。
5. **禁止** `gold_ops_complete=true`、`dual_annotation_workflow=true`（≥300 全量运营仍延后）。
6. α 目标 **n≥10**；不足则 **H4=`deferred`**，**禁止宣称 grounded**。
7. **禁止宣称 ≥300 运营已完成**。

与 Demo 检索种子边界：Demo 种子 **不得称金标**；本薄切片才可绑 H4/H5 主指标（规模与 κ 达标后）。κ 实填见 Issue 50 / `docs/acceptance/judge-human-kappa.md`。

---

## 导入 / 导出

工作目录：`本项目代码/claims-gate/`

```bash
python -m missions.gold_label_io import --file artifacts/gold_thin_slice/gold_thin_slice.v1.example.json
python -m missions.gold_label_io export --file artifacts/gold_thin_slice/_export.json --dataset-id gold-thin-slice-alpha-example
```

HTTP（须登录；`adjuster`/`supervisor` 可导入）：

- `POST /eval/gold-labels/import`
- `GET /eval/gold-labels/export?dataset_id=...&case_id=...`

响应含 `h4_status`；样例 n=1 → `deferred`。`gold_ops_complete` 恒为 false。

---

## 当前诚实状态（α）

| 项 | 状态 |
|----|------|
| 协议 + I/O + `case_id` | 已交付 |
| 冻结外形样例 | `artifacts/gold_thin_slice/gold_thin_slice.v1.example.json`（非真双标运营） |
| 真外聘双标 n≥10 | **未达** → **H4=`deferred`** |
| ≥300 金标运营 | **Deferred**（不得宣称） |

勾选（验收人）：

- [ ] 导入导出 + `case_id` 可用
- [ ] 双标+第三人协议理解与手册一致
- [ ] 确认当前 `h4_status=deferred`（或已注入真双标 n≥10 后另评）
- [ ] 文案无「金标已达标 / ≥300 已完成 / grounded（在 deferred 时）」

---

## 默认 CI

```bash
pytest -q
pytest tests/eval/test_gold_thin_slice.py -q
```

HTTP 薄切片往返可选：`pytest -m eval_bypass`。
