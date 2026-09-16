# Spec — Phase 2b · Q Missions Relay Honesty (A2/A3)

| 字段 | 内容 |
|------|------|
| feature_slug | `insurance-claims-gate` |
| spec_id | `SPEC-02B-Q-RELAY-A2A3` |
| wave | `2b-Q`（实现目录 `phase2b-q/`） |
| Status | `closed` |
| 规划真源 | [`docs/agents/phase2b-depth-planning-backlog.DRAFT.md`](../../../docs/agents/phase2b-depth-planning-backlog.DRAFT.md) §5.2 +「流 Q 待写入」 |
| 前置 | P-α DoD **closed**（本地 44 / GitHub #31；H3/H6/H7 可演示） |
| 并行 | 流 P-β **可并行**；**禁止**与 P 共用「深度完成」旗；本 SPEC **不含** Claims Assist |
| 主测试接缝 | **Q-S0-A/B/C + Q-S1** 进默认绿；**Q-A6** 轻量 S0（profile 差 + 无产品写）；真多模型 Validator 不进默认绿 |
| 术语 | `CONTEXT.md`（Missions 中继、validation contract、handoff、人闸）；自治阶梯 **A ≠ Integration L** |
| 宪法 | `DESIGN_PHILOSOPHY.md` I1–I8；**A2** Schema-bound；**A3** Patch-capable Worker |

**继承声明：** 轨 A `machine_check`、决策 16–18、空回路脚手架继续有效。本 SPEC **仅**把 Missions 工程中继诚实升到 A2/A3（+ 轻量 A4 profile 差）；不宣称 A5 / Production latch。

**明确废弃作 DoD：** 「组件清单覆盖即深度」「假 commit / 空 diff 标 DONE」「与流 P 共用完成旗」。

---

## Problem Statement

P-α 已证明 Assist 质量地基，但工程中继仍停留在脚手架叙事：Orchestrator 规划易退回字符串匹配；Worker 可标 DONE 却 `git_commit=null`、无真实 diff。架构师与面试官无法诚实宣称自治阶梯 **A2/A3**；继续堆角色剧场只会加深「假 multi-agent」质疑。需要在**不绑架轨 A 合门禁、不吞并流 P** 的前提下，把契约 Schema 硬停与单特性真 patch+commit 做成可验收假设 **H8**。

## Solution

交付 **Missions Relay Honesty（流 Q）**：

- **Q-A2（≡A2）：** Orchestrator 产出经 JSON Schema 校验的 validation contract；缺 `goal` / 非法结构入账前硬停；`goal` 必用；去掉以字符串 if/elif 为主规划源的诚实性漏洞  
- **Q-A3（≡A3）：** Worker 在 worktree 内真实改文件、可检视 diff、handoff 含非空 commit hash；遵守 `owns_paths` + 写锁；示范单特性 `F-Q-DEMO-01`（OCR/备注吸收 strip，不改人闸字段）  
- **Q-A6（轻量 A4 预备）：** Validator 使用与 Worker **不同**的 retrieve profile（可配置独立模型名）；**零**产品代码写入；失败只出 fail report  
- **完成旗：** 独立验收件勾选 **H8**；默认 `pytest -q` 仍无 LLM/无 LangSmith 绿（H7 保持，但不把 P 的 α/β 完成态当作 Q 出口）  
- **Deferred：** Q-A7 pause/resume、credential proxy（未做不得称 Production latch / A5）

---

## DoD Checklist

### 无条件（`phase2b-q`）

- [x] Orchestrator 契约入账前 JSON Schema 硬停；缺 `goal` 或非法结构不得开工（Q-S0-A）  
- [x] 规划/契约主路径不以字符串 if/elif 冒充 Schema-bound 契约源  
- [x] Worker 对 `F-Q-DEMO-01`：worktree 内真实 diff；handoff `git_commit` 非空；`files_touched` ⊆ 该特性 `owns_paths`（Q-S0-B）  
- [x] `git_commit=null` / 空 diff / 越权路径 → 不得标 feature `DONE`  
- [x] 写锁串行：争用 `owns_paths` 时 fail-closed  
- [x] `F-Q-DEMO-01` 行为可观察：非空 OCR/备注写入前 strip；全空白→空串；人闸/payout 字段不被用户可控文本改写（Q-S1）  
- [x] Validator：retrieve profile（或可配置模型名）与 Worker 可区分；运行后产品树无 Validator 写入（轻量 Q-S0）  
- [x] 默认 `pytest -q` 无 LLM / 无 LangSmith 仍绿（Q-S0-C / H7）  
- [x] **H8 可演示**；独立验收件存在（建议路径见 Implementation Decisions）  
- [x] 未将 P-α/P-β Issues 或 assist 质量指标标为 Q 完成条件  

### Deferred（附录 · 不切本期实现票）

- [ ] Q-A7：pause/resume；credential proxy（A5 / Production latch）

---

## User Stories

1. As an 架构师, I want Missions 契约经 JSON Schema 硬停, so that 非法合同不能开工。  
2. As an 架构师, I want `goal` 必填且被后续步骤使用, so that 不做未使用参数的剧场。  
3. As an 架构师, I want 去掉字符串 if/elif 主规划冒充, so that 可诚实宣称 A2。  
4. As a Worker（系统角色）, I want 在 worktree 内提交真实 patch, so that handoff 可带 commit hash。  
5. As a Worker, I want 只改 `owns_paths` 允许的文件, so that 写权限可机检（I4）。  
6. As a Worker, I want 持有写锁时拒绝并行争用, so that 不破坏共享工件。  
7. As a Worker, I want 空 diff 或假 commit 无法标 DONE, so that 不违反 I5。  
8. As a Validator（系统角色）, I want 只评判不改产品代码, so that 激励分离（I1）。  
9. As a Validator, I want 与 Worker 不同的 retrieve profile, so that 反偏见故事可讲（轻量 A4）。  
10. As a Validator, I want 失败时只出 fail report, so that Orchestrator 可开 fix 而非自修。  
11. As an Orchestrator, I want 从 Validator 失败开 fix feature, so that Worker 不自审自批。  
12. As a CI Owner, I want 默认 `pytest -q` 不被 Q 的 worktree/git 测绑架到真 LLM, so that H7 成立。  
13. As a CI Owner, I want Schema 与 handoff 诚实测进 S0, so that A2/A3 可回归。  
14. As an 内审, I want 看到非空 `git_commit` 与可检视 diff, so that 不接受脚手架假交付。  
15. As an 面试官, I want 15 分钟讲清 A2 Schema 与 A3 真 patch, so that 不被「假 multi-agent」追问击穿。  
16. As a Demo 讲解人, I want 单特性 `F-Q-DEMO-01` 即可证明 A3, so that 不必堆大重构。  
17. As a 核赔产品维护者, I want 示范特性只做 OCR/备注 strip 且不改人闸规则, so that 不扩大 blast radius。  
18. As a 安全负责人, I want Worker 不能改 latch 矩阵、支付 ACL、auth、密钥文件, so that 越权面关闭。  
19. As a 流 P Owner, I want Q 不得改 `track_llm_optional` 并不得共用深度完成旗, so that Assist 质量账本不被中继票污染。  
20. As a 文档维护者, I want Q 有独立 DoD 验收件, so that 不把 `alpha-dod.md` 当 Q 出口。  
21. As a coding agent, I want 票内 `Rewrote from: REF-MISSIONS`（契约外形可加 `REF-COURSE-03`）, so that 不另起三角色剧场。  
22. As a coding agent, I want 实现中继 harness 与使命内 Worker `owns_paths` 区分清楚, so that 改 runner/worker 能力不等于使命越权。  
23. As a Mission Control 用户, I want 状态机记录 lock、phase、handoff, so that 跨步骤真相在账本不在聊天。  
24. As a 人类架构师, I want Q-A7 明确 Deferred, so that 未做 pause/resume 不得称 Production latch。  
25. As a 合规负责人, I want Validator 永不写入被测产品, so that 合门禁不被实现方污染。  
26. As a 开发者, I want worktree 测使用临时本地 git, so that CI 不依赖远端推送。  
27. As a 产品经理, I want 本 SPEC 不含 Assist / 检索 / disposition, so that 流 P 与流 Q 日程可分开验收。  
28. As an Issue Owner, I want `phase2b-q/` 全局票号 53+ 且 Blocked by 清晰, so that frontier 可扫。  

---

## Reference Projects

| 能力 | ref_id | 备注 |
|------|--------|------|
| 中继 / worktree / handoff / lock | `REF-MISSIONS` | **主基线** |
| 契约 JSON Schema 外形 | `REF-COURSE-03` | 仅外形；不替代 Missions 契约语义 |

禁止：OpenManus / CrewAI / RAGFlow Agent 替中继；用流 P 质量分宣称 A3。

---

## Implementation Decisions

1. **范围：** 仅流 Q（Q-A2 → Q-A3 → Q-A6；Q-A7 Deferred）。不含流 P Assist 任何工项。  
2. **日程：** 串行于 P-α DoD（已满足）；本期必做；可与 P-β 并行开发，**完成旗分离**。  
3. **自治阶梯：** Q-A2≡A2；Q-A3≡A3；Q-A6=独立 profile 的轻量 Judge 预备（未要求真多供应商进 S0）；勿与 Integration L2/L3 混淆。  
4. **主接缝：** 一条 Missions 回路（契约入账 → Worker handoff/git → Validator 黑盒）。产品 strip 与 Schema 负例挂在该回路上。  
5. **契约：** 入账前 Schema 校验；`goal` 必填且须进入 contract/handoff 可观察字段；非法 → 异常/失败关闭，不创建 implement feature。  
6. **示范特性 `F-Q-DEMO-01`：** kind=`implement`；对用户可控 OCR/备注在吸收时 strip 首尾空白；全空白→空串；不得推导或改写人闸/payout/金额档/latch 矩阵输入。  
7. **本特性 owns_paths（已锁）：** 产品吸收模块 + 可选配对 strip 单测；不得扩到 service 主链、assist、error_code 表、人闸/支付 ACL。  
8. **Worker owns_paths 信封（已锁）：**  
   - **允许上界：** 产品 API 域 Python 源；配对 `test_*.py`（含子目录）。单特性必须再收窄为显式列表。  
   - **硬禁：** latch 矩阵、工具/支付 ACL、auth、所有 `.env*`、missions 的 Validator/Orchestrator、轨 B/assist 可选轨包、Managerial System、仓库约定/文档根、历史参考仓、任何支付/L3/银企新建路径。  
   - 出现在 `owns_paths` 或实际 `files_touched` → 该 feature 失败关闭。  
9. **A3 诚实规则：** worktree 隔离；真实 diff；handoff 记录非空 commit 与 `files_touched`；禁止假 commit。  
10. **角色边界：** 实现 Q 中继能力（使 Worker 能 patch）= 按本 SPEC 改 harness 的实现工作；**不等于**使命内 Worker 可改 Orchestrator/Validator。  
11. **Q-A6：** 默认证明 = profile 字段（或可配置模型名）与 Worker 不同 + 文件系统断言无产品写；真多模型调用不进默认 `pytest -q`。可与 P-E5 **共用 κ 叙事**但实现与完成旗分离。  
12. **票夹：** `Managerial System/Issues/insurance-claims-gate/phase2b-q/`；全局编号 **53+**；本波关闭后票 Status=`resolved`，SPEC Status=`closed`。  
13. **验收件：** 独立 Q DoD 文档（建议置于 claims-gate `docs/acceptance/` 下、文件名体现 `q-relay-a2a3`）；**禁止**把 P 的 α DoD 文件或 Issues 44–52 标 resolved 当作 Q 出口。  
14. **用户手册：** 流 Q 默认**用户不可见**；若未改变作业壳行为，可不改 `USER_GUIDE`；若示范特性改变可观察 OCR/备注存储形态，按 `docs/user/MAINTENANCE.md` 补一句诚实说明。  
15. **密钥：** 不新增 Key 面；Worker 不得持写 `.env*`。  

---

## Testing Decisions

1. **好测试：** 只断言外部可观察行为——契约校验抛错/拒绝入账、handoff 字段（`git_commit`、`files_touched`、DONE/阻断）、写锁争用失败、案件头 OCR/备注 strip 结果、人闸字段未被注入翻转、Validator 后产品树无改写、默认 `pytest -q` 绿。不断言 LLM 私有思维链、React state、或「宣称 A3」的文案单测。  
2. **Q-S0-A：** 契约 Schema / 缺 goal / 非法结构硬停（加深既有 contract schema 测）。  
3. **Q-S0-B：** 示范使命回路：非空 commit、路径 ⊆ owns_paths、空 diff 不得 DONE；临时本地 git/worktree，不绑远端。  
4. **Q-S0-C：** 默认 addopts 下全绿；Q 测不得强制 `requires_llm` / `track_llm_optional` / 真 cloud Key。  
5. **Q-S1：** strip 行为 + 既有 OCR 提权负例仍绿。  
6. **Q-A6：** 轻量 S0（profile 差 + 无产品写）；真多模型 / 需 Key → 旁路标记，默认排除。  
7. **Prior art：** `test_contract_schema_hardstop.py`、`test_missions_empty_loop.py`、`test_threat_inject_ocr_remark.py`、轨 B 隔离契约测。  
8. **违规：** 假 commit 标 DONE；默认 CI 因缺 LLM Key 红；用 P 的 H1–H6 或 assist 分代替 H8；Validator 改产品代码「仅此一次」。  

---

## Out of Scope

- 流 P：Assist、检索、disposition、金标薄切片、Provider 连接状态、S2 质量门  
- Q-A7：pause/resume、credential proxy、A5 Production latch  
- L3 出款、银企直连、UI 签发人闸、自审自批  
- OpenManus/CrewAI/RAGFlow Agent 替中继  
- 多 Writer 无 lock 并行；扩大示范特性到 service 主链或 assist 包  
- 宣称「已达硅谷 9 分 / Anthropic 生产档」  
- 评测分进默认绿；向量进 `evaluate`  

---

## Further Notes

### 测试接缝（人类确认 · defaults · 2026-09-16）

| ID | 内容 | 标记 |
|----|------|------|
| Q-S0-A | 契约 Schema 硬停 | 默认 S0 |
| Q-S0-B | handoff 真 commit / owns_paths | 默认 S0 |
| Q-S0-C | 轨 A `pytest -q` 不被 Q 绑架 | 默认 S0 |
| Q-S1 | `F-Q-DEMO-01` strip + 提权负例 | 默认 S0 |
| Q-A6 | profile 差 + 无产品写 | 轻量 S0；真多模型旁路 |

### 依赖

```text
44 (P-α DoD, resolved)
 └── 53 Q-A2 ── 54 Q-A3(+F-Q-DEMO-01) ── 55 Q-A6
                                      └── 56 Q DoD（H8）
```

### 修订记录

- 2026-09-16：`/to-spec`；接缝经人类回复 `defaults` 确认；自 DRAFT §5.2 +「流 Q 待写入」发布。
- 2026-09-16：Issue 56 收口；无条件 DoD 勾选；验收件 `docs/acceptance/q-relay-a2a3-dod.md`；Status=`closed`；Q-A7 仍 Deferred。
