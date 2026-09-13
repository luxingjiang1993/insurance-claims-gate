# 04: SC-02 除外拒赔草案 + 文书分态 + 人闸

**Status:** resolved

**Blocked by:** 01, 02

**ref_id:** REF-MISSIONS

**Backlog:** P0-3

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/missions/runner.py` | `approve_promotion`、`blocked_for_human` / `awaiting_human_approval` |
| 2 | `project 多agent/src/missions/models.py` | `HumanApproval`、handoff `blocked_for_human` |
| 3 | `project 多agent/src/missions/validator.py` | 全过仍进入人闸相位的逻辑 |
| 4 | `project 多agent/src/missions/checks.py` | 扩写拒赔 citation / `document_status` / 人闸令牌类检查 |
| 5 | `project 多agent/src/missions/rag.py` + `validator.py`（citation 段） | 除外引用落库门（依赖票 02） |
| 6 | `project 多agent/schemas/citation.schema.json` | 引用外形 |
| 7 | `project 多agent/tests/compliance/test_audit_failures.py` | 合规失败用例写法参考 |

说明：基线人闸是「promote 前批准」；本票须映射为理赔域的 `human_latch_token` + `DRAFT_EXPORT` / `EXTERNAL_NOTIFY` 分态，勿原样照搬转账语义。

## What to build

端到端跑通 SC-02（确定性轨）：疾病导致摔伤案产出拒赔草案，责任/除外必须带可落库条款项引用；拒赔文书草稿含 `appeal_path`。文书效力分态：`DRAFT_EXPORT` 可无人闸供内部预览；升 `EXTERNAL_NOTIFY` 必须持有有效人闸令牌，否则 API 拒绝且 machine_check 失败。无人闸时 `payout_ready` 恒为 false。人闸批准后可进入对外通知语义，但仍不触发银企出款。人闸驳回后可回编辑态再提。

## Acceptance criteria

- [x] SC-02 夹具经 HTTP：疾病摔伤 → 拒赔草案 + 条款项级 citations 通过落库门
- [x] 拒赔草案含 `appeal_path`；缺 citation 或伪 citation 不得对外
- [x] `DRAFT_EXPORT` 可无人闸生成；同案升 `EXTERNAL_NOTIFY` 无人闸必失败（`DOCUMENT_STATUS_FORBIDDEN` 或 `LATCH_REQUIRED`）
- [x] 无人闸时 `payout_ready` 恒 false；批准后发出人闸令牌，驳回可回编辑态
- [x] 对应 machine_check（拒赔引用、文书分态、人闸门）在轨 A 下稳定绿
- [x] 叙事与字段禁止「秒赔」包装责任争议案
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

SC-02 已在轨 A 落地并通过机检：疾病摔伤夹具产出 `reject_draft` + 条款项 citations + `appeal_path`；`DRAFT_EXPORT` 可无人闸，`EXTERNAL_NOTIFY` 须 `human_latch_token`；无人闸/`payout_ready` 恒 false。交付提交：`93c240b`。

## Comments

- 2026-09-13：to-tickets 批准 defaults 后落盘。
- 2026-09-13：实现落地 — `CLM-SC02-001` 确定性除外拒赔；`reject_notice` 文书分态；`/human-latch/approve|reject`；machine_check `sc02_exclusion_reject_latch` / `sc02_external_notify_requires_latch`。Rewrote from: REF-MISSIONS
- 2026-09-13：正式关闭 — Status=resolved；Answer 已写；已随 main 推远程。
