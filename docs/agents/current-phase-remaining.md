# 当前阶段剩余工作（历史说明）

| 字段 | 内容 |
|------|------|
| 状态 | `historical` |
| 日期 | 2026-09-16（原文 2026-09-13；本版改为关账说明） |
| 前提 | Phase **1**（Issues 01–13）+ **2a** W0–W2 + **2b** P-α/P-β + **Q** 已关闭 |
| 真源 | PRD-02、SPEC `insurance-claims-gate`、`docs/user/USER_GUIDE.md` |
| 扩面草案 | `ref-projects-phase2-supplement.md`（**写入 Constitution/PRD/SPEC 前不得按草案放松 I1–I8**） |

本文件 **不再** 作为「进入阶段 2 的下一实现前线」。Issues 10–13 与后继 2a/2b 票已 resolved；Frontier 空。下面只记录 **仍延后、未宣称** 的项，避免把关账读成待开工清单。

---

## 0. 延后项（不是下一波必做票）

无法对接真实保司用户 / 作业中心实测时，下列项保持延后。**未**因此放松 I1–I8，也 **未** 宣称 grounded / A5 / L3。

| 项 | 处置 |
|----|------|
| Week1–4 OUT 基线实测（PRD M4） | **延后** → 有真实干系人时 |
| ≥300 人工金标运营（PRD M3 全量） | **延后**；Demo 检索种子 / 薄切片 **不是** 运营金标 |
| 关闭 Constitution §14 A1–A5（客户签字） | **延后至生产前** |
| 真连核心 L2 / 现网枚举 | **延后** |
| 真实 OCR 供应商 | **延后**（Provider Stub+Recorded 为 Integration-Ready；≠ 生产 OCR 已上线） |
| H4 grounded 宣称 | **deferred**（薄切片 n&lt;10） |
| γ（rerank / MultiQuery / fan-out / 灌榜） | **未上线** |
| Q-A7 / A5 Production latch | **Deferred**（pause/resume、credential proxy；无 Mission Control） |
| 核赔作业 UI 全作业流 | 作业壳为 Preview；不是生产作业台 |

延后项 **不** 构成「再切一批实现票」的口令。扩面须先修宪 / 新 PRD 条目，再消费 N* 草案。

---

## 1. 已关闭的历史 DoD（勿再当待办）

下列在 2026-09-13 曾是「进阶段 2 前必须完成」，现均为历史关账，**不要**再 claim 10–13：

1. Issues **`10`–`13`** `resolved`，轨 A `pytest -q` 绿。  
2. 其后 Phase 2a W0–W2、2b P-α/P-β、2b-Q（Issues 至 56）DoD 已关。  
3. 用户手册与 Changelog 已按波次同步（见 `docs/user/MAINTENANCE.md`）。  
4. §0 延后表仍有效；未假装真实用户实测或 ≥300 金标已完成。

**非必须且仍未交付（保持延后，不是 Frontier）：** 真 L2、真 OCR、Q-A7/A5、H4 grounded、γ、≥300 金标运营。

---

## 2. 任务图（归档）

原 Frontier 10–13（Eval 旁路、合成抽检占位、轨 B 最小检索、Solo Demo）**已实现并关票**。实现只写入 `本项目代码/claims-gate/`。参考仓只读。勿平行重切。

---

## 3. 给未来的你

若要再开工：先读 USER_GUIDE 页眉诚实边界与 `docs/agents/interview-honesty-table.md`，确认缺口仍是延后项而非「阶段 2 入口未做」。新能力仍须 SPEC → Issues，且不得放松 I1–I8。

---

## 5. 修订记录

- 2026-09-13：初稿。联合评估后冻结个人开发路径；真实用户实测延后；切票 10–13。
- 2026-09-14：DoD 增「用户手册已同步」；真源 `docs/user/`。
- 2026-09-16：改为历史说明。Phase 1–2b-Q 已关闭；剩余为延后项（H4、γ、Q-A7/A5、真 L2/OCR、≥300 金标），不再写成「进入阶段 2」。
