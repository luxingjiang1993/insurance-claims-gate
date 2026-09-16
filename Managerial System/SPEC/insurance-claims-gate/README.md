# SPEC — insurance-claims-gate

## 轨 A 门禁（既有）

[`spec.md`](./spec.md)（Status: `ready-for-agent`，修订 `2.4`）— **勿删改作为 2a 交付。**

## Phase 2a — 分层波次（各波独立 SPEC）

| Wave | SPEC | Status |
|------|------|--------|
| 总览索引 | [`spec-2a-runnable-product-floor.md`](./spec-2a-runnable-product-floor.md) | `ready-for-agent` |
| **W0** Dev Complete | [`spec-2a-w0-dev-complete.md`](./spec-2a-w0-dev-complete.md) | `closed` |
| **W1** Pilot Complete | [`spec-2a-w1-pilot-complete.md`](./spec-2a-w1-pilot-complete.md) | `closed` |
| **W2** Eval Ops | [`spec-2a-w2-eval-ops.md`](./spec-2a-w2-eval-ops.md) | `ready-for-agent` |

实现 / 切票：**按波打开对应 W0/W1/W2 文件**；总览仅作导航与跨波约束。

## Phase 2b — Assist / Relay（已关闭）

| 流 | SPEC | Status |
|----|------|--------|
| P Assist Quality | [`spec-2b-p-assist-quality.md`](./spec-2b-p-assist-quality.md) | `closed` |
| Q Relay A2/A3 | [`spec-2b-q-relay-a2a3.md`](./spec-2b-q-relay-a2a3.md) | `closed` |

## Phase 2c — Live Honest Seams（已关闭）

| SPEC | Status | Issues |
|------|--------|--------|
| [`spec-2c-live-honest-seams.md`](./spec-2c-live-honest-seams.md)（`SPEC-02C-LIVE-HONEST-SEAMS`） | `closed` | `phase2c/` 57–62 resolved |

档位：G0+G2+G3 最小（L2+OCR）+G4；不做 G1/H4 过线；Ready≠Deployed。验收：`本项目代码/claims-gate/docs/acceptance/package-live-honest-seams.md`。

## 其他

- 参考项目目录：`docs/agents/ref-projects.md`（主基线 `REF-MISSIONS`）
- 扩面草案：`docs/agents/ref-projects-phase2-supplement.md`（未修宪不得执行）
- 2a 评委会：`docs/agents/phase2a-sv-expert-panel-review.DRAFT.md`
- 切票目录：`Managerial System/Issues/insurance-claims-gate/`（含 `phase2c/` 57–62 closed；票首 `wave:`）
