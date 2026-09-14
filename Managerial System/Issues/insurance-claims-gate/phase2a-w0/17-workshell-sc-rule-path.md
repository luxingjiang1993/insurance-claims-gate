# 17: 作业壳：材料 / evaluate / 一次补件 / 裁决草案（SC 规则路径）

**github_issue:** #4

**Status:** resolved

**Blocked by:** 16

**wave:** W0

**spec_id:** SPEC-02A-W0-DEV-COMPLETE

**ref_id:** REF-MISSIONS, REF-COURSE-04

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/missions/checks.py` | SC 机检语义（壳不得另立规则） |
| 2 | `04_多步流程编排与条件分支/` | 多步作业态 |

## What to build

在作业壳内让 adjuster 完成材料登记、规则评估、一次补件与裁决草案查看。SC-01/02/03 在壳内触发的行为与 `machine_check` 语义一致；无 LLM Key 时规则路径仍可点完。壳不持有门禁最终权威。

## Acceptance criteria

- [x] adjuster 可在壳内登记材料、触发 evaluate、发起一次补件并查看裁决草案
- [x] SC-01/02/03 主路径语义与既有 `machine_check` 一致（不另立 UI 规则）
- [x] 无 LLM Key 时规则路径仍可点完
- [x] API 拒绝时 UI 不假成功
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

作业壳详情页对 `adjuster`/`supervisor` 增加规则路径：直连 `POST /materials`、`POST /evaluate`、`POST /supplement/notify` 与 `GET /decision`。清单码与草案字段原样展示 API 响应，壳不计算缺项或裁决类型。`viewer` 仍无写入口。拒绝体经 `ApiErrorView` 展示且不点亮成功条。

`Rewrote from: REF-MISSIONS`

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w0/`。
- 2026-09-14：同步 GitHub Issue #4。
