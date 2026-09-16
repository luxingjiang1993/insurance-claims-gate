# Issues — insurance-claims-gate

任务图：`Blocked by` / `Status`。约定见 `docs/agents/issue-tracker.md`。

| Phase / Wave | 目录 | SPEC |
|--------------|------|------|
| Phase 1（轨 A 门禁） | [`phase1/`](./phase1/) | [`spec.md`](../../SPEC/insurance-claims-gate/spec.md) |
| Phase 2a · W0 Dev Complete | [`phase2a-w0/`](./phase2a-w0/) | [`spec-2a-w0-dev-complete.md`](../../SPEC/insurance-claims-gate/spec-2a-w0-dev-complete.md) |
| Phase 2a · W1 Pilot Complete | [`phase2a-w1/`](./phase2a-w1/) | [`spec-2a-w1-pilot-complete.md`](../../SPEC/insurance-claims-gate/spec-2a-w1-pilot-complete.md) |
| Phase 2a · W2 Eval Ops | [`phase2a-w2/`](./phase2a-w2/) | [`spec-2a-w2-eval-ops.md`](../../SPEC/insurance-claims-gate/spec-2a-w2-eval-ops.md) |
| Phase 2b · P-α Assist 证据地基 | [`phase2b-p-α/`](./phase2b-p-α/) | [`spec-2b-p-assist-quality.md`](../../SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md) |
| Phase 2b · P-β Assist 可证伪质量 | [`phase2b-p-β/`](./phase2b-p-β/) | 同上（Blocked by 44） |
| Phase 2b · Q Missions Relay A2/A3 | [`phase2b-q/`](./phase2b-q/) | [`spec-2b-q-relay-a2a3.md`](../../SPEC/insurance-claims-gate/spec-2b-q-relay-a2a3.md) |
| Phase 2c · Live Honest Seams | [`phase2c/`](./phase2c/) | [`spec-2c-live-honest-seams.md`](../../SPEC/insurance-claims-gate/spec-2c-live-honest-seams.md) |

父索引：[`spec-2a-runnable-product-floor.md`](../../SPEC/insurance-claims-gate/spec-2a-runnable-product-floor.md)。  
Phase 1 门禁清单（历史）：`docs/agents/current-phase-remaining.md`。

## Frontier（可立即开工）

**2c（当前）：** 57–61 resolved；**仅 62**（2c DoD 收口）可认领（Blocked by 57–61 已解阻）。详见 [`phase2c/`](./phase2c/)。SPEC Status=`ready-for-agent`（DoD 收口前）。  
**本窗口不做：** G1/H4 grounded、KB≥20、A5、真连现网、γ 无条件项。

**W0–W2：** 已关闭（14–33 resolved）。  
**2b-P-α：** **closed**（34–44 resolved；α DoD 2026-09-16）。验收：`本项目代码/claims-gate/docs/acceptance/alpha-dod.md`。  
**2b-P-β：** **closed**（45–52 resolved；β DoD 2026-09-16）。验收：`本项目代码/claims-gate/docs/acceptance/beta-dod.md`。  
**2b-Q：** **closed**（53–56 resolved；Q DoD / H8 2026-09-16）。验收：`本项目代码/claims-gate/docs/acceptance/q-relay-a2a3-dod.md`。SPEC Status=`closed`。完成旗与 P 隔离（仅 H8）；**未**宣称 A5 / Production latch；Q-A7 Deferred。  
γ 触发项与 ≥300 金标 / 真 L2 现网等：勿预切；勿仅凭扩面草案放松 I1–I8。

## Phase 1 任务图（01–13 · 均已 resolved）

见 [`phase1/`](./phase1/)。摘要：

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 01–13 | 轨 A 门禁 + 当前阶段剩余 | 见各票 | resolved |

## Phase 2a · W0 任务图（14–22）

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 14 | SQLite 持久化 + 种子三角色 + 登录会话 | — | resolved |
| 15 | 人闸 RBAC 硬门 + S0 负例机检 | 14 | resolved |
| 16 | 作业壳：登录 + 案件只读浏览 | 14 | resolved |
| 17 | 作业壳：材料 / evaluate / 一次补件 / 裁决草案（SC 规则路径） | 16 | resolved |
| 18 | 作业壳：人闸 + 文书分态诚实展示 | 15, 17 | resolved |
| 19 | AI 辅助建议 API：降级 + 关键词提名 + 采纳再 evaluate | 14 | resolved |
| 20 | 作业壳：AI 辅助区 + 非终裁标注 + 采纳 | 17, 19 | resolved |
| 21 | 本案流水 + 本地 trace 导出 | 14 | resolved |
| 22 | W0 用户手册 + 默认 CI 无 LLM 绿确认 | 18, 20, 21 | resolved |

```text
14 ─┬── 15 ──────┐
    ├── 16 ─ 17 ─┼── 18 ─┐
    ├── 19 ──────┼── 20 ─┼── 22
    └── 21 ──────────────┘
```

## Phase 2a · W1 任务图（23–28）

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 23 | Chroma 索引 + 本地/云 embedding + 可重建 | 22 | resolved |
| 24 | 混合检索挂 assist：硬过滤 / 条款号短路 / 加权融合 / 三联门 / 向量降级 | 22, 23 | resolved |
| 25 | 作业壳 AI 区展示检索来源摘要 | 20, 24 | resolved |
| 26 | 真 LangSmith：evaluate / assist / latch + ledger 对齐 | 22 | resolved |
| 27 | OpenEval 旁路 ↔ LangSmith 实验历史对比 | 26 | resolved |
| 28 | 套餐 L 验收 + Pilot 手册区分 + 默认 CI 仍绿 | 24, 25, 26, 27 | resolved |

```text
22 (W0 close)
 ├── 23 ── 24 ── 25 ──┐
 │              │      │
 └── 26 ── 27 ──┴──────┴── 28 (W1 close)
```

## Phase 2a · W2 任务图（29–33）

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 29 | 评测跑次持久化 + actor 归因（复用 W0 用户） | 28 | resolved |
| 30 | 排行榜：实验名 / 主指标 / 时间 / 提交者 + 可排序 | 28, 29 | resolved |
| 31 | 作业壳「评测」独立入口 + 两账号协作跑榜演示 | 20, 29, 30 | resolved |
| 32 | 金标运营接口预留（导入/导出 + case_id） | 29 | resolved |
| 33 | Eval Ops 手册 + 分数≠合门禁文案 + S0 仍绿 | 30, 31, 32 | resolved |

```text
28 (W1 close)
 ├── 29 ──┬── 30 ──┐
 │        │        ├── 31 ──┐
 │        └── 32 ──────────┼── 33 (W2 close)
 └─────────────────────────┘
```

实现只写入 `本项目代码/claims-gate/`。每张票含 **优先打开（只读参考）** 表；路径相对于 `历史项目代码供参考/`。

**W0 明确不做：** Chroma / 真 LangSmith 完工 / OpenEval 排行榜与多人 —— 属 W1/W2。  
**W1 明确不做：** OpenEval 排行榜、多人协作、≥300 金标运营 —— 属 W2 / 延后。  
**W2 明确不做：** ≥300 金标运营宣称、Braintrust/Phoenix 换栈、评测分替 `machine_check`/人闸。  
**W2 状态：** 29–33 resolved；SPEC `spec-2a-w2-eval-ops.md` Status=`closed`。

## Phase 2b · P-α 任务图（34–44）

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 34 | Pilot 默认 cloud embedding | — | resolved |
| 35 | BM25 关键词腿 | — | resolved |
| 36 | Demo 检索种子 40 | — | resolved |
| 37 | citation Schema 槽 | — | resolved |
| 38 | 金标薄切片 | — | resolved |
| 39 | 辅助拒答 + 壳 | 37 | resolved |
| 40 | 工具环 ACL | 37 | resolved |
| 41 | span 树 | 40 | resolved |
| 42 | 忠实检查（规则） | 37, 38 | resolved |
| 43 | Provider 文档 | — | resolved |
| 44 | α DoD 收口 | 34–43 | resolved |

详见 [`phase2b-p-α/`](./phase2b-p-α/)。**α DoD closed 2026-09-16。**

## Phase 2b · P-β 任务图（45–52）

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 45 | 条款项切块 | 44, 34 | resolved |
| 46 | Recall 指标 S2 | 44, 36, 35 | resolved |
| 47 | 三维 S2 | 44, 46, 42 | resolved |
| 48 | 夜间 S2 告警 | 44, 47 | resolved |
| 49 | 四步步数预算 | 44, 40 | resolved |
| 50 | κ / judge-human | 44, 38 | resolved |
| 51 | 连接状态只读 | 44, 43 | resolved |
| 52 | β DoD 收口 | 45–51 | resolved |

详见 [`phase2b-p-β/`](./phase2b-p-β/)。**β DoD closed 2026-09-16。** 验收：`本项目代码/claims-gate/docs/acceptance/beta-dod.md`。γ 未触发不预切票。

## Phase 2b · Q 任务图（53–56）

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 53 | Q-A2 Schema-bound Orchestrator | 44 | resolved |
| 54 | Q-A3 Patch Worker + F-Q-DEMO-01 | 53 | resolved |
| 55 | Q-A6 Validator 独立 profile | 54 | resolved |
| 56 | Q DoD 收口（H8） | 53, 54, 55 | resolved |

详见 [`phase2b-q/`](./phase2b-q/)。**本波已关闭。** Q-A7 Deferred 不切票。完成旗仅 H8，不与 P 共用；未宣称 A5 / Production latch。

## Phase 2c · Live Honest Seams 任务图（57–62）

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 57 | G0 Live Pilot 路径 + Live 验收 | — | resolved |
| 58 | G2 检索双剖面 | 57 | resolved |
| 59 | G3 L2 Core Adapter + Recorded | — | resolved |
| 60 | G3 OCR Provider + Recorded | — | resolved |
| 61 | G4 诚实表 / 手册 / demo 同步 | 57–60 | resolved |
| 62 | 2c DoD 收口 | 57–61 | ready-for-agent |

详见 [`phase2c/`](./phase2c/)。已同步 GitHub `#44`–`#49`（标签：`ready-for-agent` · `phase-2c` · `wave:2c`）。

## GitHub Issues 映射

本地票 `14`–`33` 已同步到 GitHub（标签：`ready-for-agent` · `phase-2a` · `wave:W0|W1|W2`）。  
本地票 `34`–`52` 已同步到 GitHub（标签：`ready-for-agent` · `phase-2b` · `wave:2b-P-alpha|2b-P-beta`）。  
本地票 `53`–`56` 同步标签：`ready-for-agent` · `phase-2b` · `wave:2b-Q`。  
本地票 `57`–`62` 同步标签：`ready-for-agent` · `phase-2c` · `wave:2c`。  
完整表：[`github-issue-map.json`](./github-issue-map.json)。

| Local | GitHub | Wave |
|-------|--------|------|
| 14–22 | [#1](https://github.com/luxingjiang1993/insurance-claims-gate/issues/1)–[#9](https://github.com/luxingjiang1993/insurance-claims-gate/issues/9) | W0 |
| 23–28 | [#10](https://github.com/luxingjiang1993/insurance-claims-gate/issues/10)–[#15](https://github.com/luxingjiang1993/insurance-claims-gate/issues/15) | W1 |
| 29–33 | [#16](https://github.com/luxingjiang1993/insurance-claims-gate/issues/16)–[#20](https://github.com/luxingjiang1993/insurance-claims-gate/issues/20) | W2 |
| 34–44 | [#21](https://github.com/luxingjiang1993/insurance-claims-gate/issues/21)–[#31](https://github.com/luxingjiang1993/insurance-claims-gate/issues/31) | 2b-P-α |
| 45–52 | [#32](https://github.com/luxingjiang1993/insurance-claims-gate/issues/32)–[#39](https://github.com/luxingjiang1993/insurance-claims-gate/issues/39) | 2b-P-β |
| 53–56 | [#40](https://github.com/luxingjiang1993/insurance-claims-gate/issues/40)–[#43](https://github.com/luxingjiang1993/insurance-claims-gate/issues/43) | 2b-Q |
| 57–62 | [#44](https://github.com/luxingjiang1993/insurance-claims-gate/issues/44)–[#49](https://github.com/luxingjiang1993/insurance-claims-gate/issues/49) | 2c |

各本地票首含 `github_issue: #N`；Issue 正文内 `Blocked by` 已写 GitHub `#` 引用。
