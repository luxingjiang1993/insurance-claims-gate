# 11: Judge–human 合成抽检占位（P1-7）

**Status:** resolved

**Blocked by:** 10

**ref_id:** REF-CASE-EVAL-ADVISOR, REF-MISSIONS

**Backlog:** P1-7

**Rewrote from:** REF-CASE-EVAL-ADVISOR, REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `CASE-投顾AI助手（效果评估）/deepeval_wealth_advisor.py` | 效果评估流水线外形 |
| 2 | `CASE-投顾AI助手（效果评估）/3-run_langsmith_evaluation_example.py` | 跑批 / 报告入口 |
| 3 | `project 多agent/src/missions/validator.py` | Validator 报告字段；可扩展一致率占位 |
| 4 | PRD §9 Golden SOP | 双人标注 / 第三人裁决概念（本期用**合成表**代替真实核赔） |

## What to build

落实 SPEC P1-7：预留 **Judge–human 一致率**字段与可填写的抽检表（markdown 或 JSON），支持个人用合成「标注 A / 标注 B / 裁决」对 SC 夹具做手工对照演练。  
**不**要求真实核赔员；**不**阻塞轨 A 绿门；**不**把合成表冒充 ≥300 金标运营（金标全量仍延后）。

## Acceptance criteria

- [x] 裁决/校验报告或 ledger 可出现 `judge_human_agreement`（或等价）占位字段；缺省可为 null
- [x] 仓库内有抽检表模板（建议 `本项目代码/claims-gate/artifacts/spot_check_template.md` 或 `.json`），含：case_id、系统裁决、合成人标、是否一致、备注
- [x] 至少 1 份基于 SC-01 或 SC-02 的**合成样例行**（演示填法）
- [x] 文档写明：真实用户/金标运营延后；本票仅占位
- [x] handoff 含 `Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS`

## Answer

`ValidationReport.judge_human_agreement`（缺省 null）+ `validation_done` 事件字段；`artifacts/spot_check_template.md` 与 `spot_check_sample_sc01.json`（SC-01 合成样例）；`missions/spot_check.py` 加载/一致率占位。真实用户与 ≥300 金标延后；不阻塞轨 A。Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS。

## Comments

- 2026-09-13：current-phase-remaining 切票；真实用户实测延后，本票用合成抽检。
- 2026-09-14：实现完成；合成抽检占位落地；Rewrote from: REF-CASE-EVAL-ADVISOR, REF-MISSIONS。
