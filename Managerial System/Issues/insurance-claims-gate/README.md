# Issues — insurance-claims-gate

任务图：`Blocked by` / `Status`。约定见 `docs/agents/issue-tracker.md`。

| Phase / Wave | 目录 | SPEC |
|--------------|------|------|
| Phase 1（轨 A 门禁） | [`phase1/`](./phase1/) | [`spec.md`](../../SPEC/insurance-claims-gate/spec.md) |
| Phase 2a · W0 Dev Complete | [`phase2a-w0/`](./phase2a-w0/) | [`spec-2a-w0-dev-complete.md`](../../SPEC/insurance-claims-gate/spec-2a-w0-dev-complete.md) |
| Phase 2a · W1 Pilot Complete | [`phase2a-w1/`](./phase2a-w1/) | [`spec-2a-w1-pilot-complete.md`](../../SPEC/insurance-claims-gate/spec-2a-w1-pilot-complete.md) |
| Phase 2a · W2 Eval Ops | [`phase2a-w2/`](./phase2a-w2/) | [`spec-2a-w2-eval-ops.md`](../../SPEC/insurance-claims-gate/spec-2a-w2-eval-ops.md) |

父索引：[`spec-2a-runnable-product-floor.md`](../../SPEC/insurance-claims-gate/spec-2a-runnable-product-floor.md)。  
Phase 1 门禁清单（历史）：`docs/agents/current-phase-remaining.md`。

## Frontier（可立即开工）

**W0：** 已关闭（14–22 resolved）。  
**W1：** 已关闭（23–28 resolved；SPEC Status=`closed`）。  
**W2：** 开放；frontier 为 **33**（30–32 resolved）。  
开工前将对应票 `Status` 改为 `claimed`。

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
| 33 | Eval Ops 手册 + 分数≠合门禁文案 + S0 仍绿 | 30, 31, 32 | ready-for-agent |

```text
28 (W1 close)
 ├── 29 ──┬── 30 ──┐
 │        │        ├── 31 ──┐
 │        └── 32 ──────────┼── 33
 └─────────────────────────┘
```

实现只写入 `本项目代码/claims-gate/`。每张票含 **优先打开（只读参考）** 表；路径相对于 `历史项目代码供参考/`。

**W0 明确不做：** Chroma / 真 LangSmith 完工 / OpenEval 排行榜与多人 —— 属 W1/W2。  
**W1 明确不做：** OpenEval 排行榜、多人协作、≥300 金标运营 —— 属 W2 / 延后。  
**W2 明确不做：** ≥300 金标运营宣称、Braintrust/Phoenix 换栈、评测分替 `machine_check`/人闸。

## GitHub Issues 映射（Phase 2a）

本地票 `14`–`33` 已全部同步到 GitHub（标签：`ready-for-agent` · `phase-2a` · `wave:W0|W1|W2`）。完整表：[`github-issue-map.json`](./github-issue-map.json)。

| Local | GitHub | Wave |
|-------|--------|------|
| 14–22 | [#1](https://github.com/luxingjiang1993/insurance-claims-gate/issues/1)–[#9](https://github.com/luxingjiang1993/insurance-claims-gate/issues/9) | W0 |
| 23–28 | [#10](https://github.com/luxingjiang1993/insurance-claims-gate/issues/10)–[#15](https://github.com/luxingjiang1993/insurance-claims-gate/issues/15) | W1 |
| 29–33 | [#16](https://github.com/luxingjiang1993/insurance-claims-gate/issues/16)–[#20](https://github.com/luxingjiang1993/insurance-claims-gate/issues/20) | W2 |

各本地票首含 `github_issue: #N`；Issue 正文内 `Blocked by` 已写 GitHub `#` 引用。
