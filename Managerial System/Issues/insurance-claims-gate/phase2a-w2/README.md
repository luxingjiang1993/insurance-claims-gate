# Phase 2a · W2 — Eval Ops

实现票 29–33。SPEC：[`spec-2a-w2-eval-ops.md`](../../../SPEC/insurance-claims-gate/spec-2a-w2-eval-ops.md)。  
上级索引：[`../README.md`](../README.md)。

**波次门禁：** 依赖 **28**（W1 DoD，已 resolved）或其传递依赖；frontier 为 **31 / 32**（30 已 resolved）。

## 任务图

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 29 | 评测跑次持久化 + actor 归因（复用 W0 用户） | 28 | resolved |
| 30 | 排行榜：实验名 / 主指标 / 时间 / 提交者 + 可排序 | 28, 29 | resolved |
| 31 | 作业壳「评测」独立入口 + 两账号协作跑榜演示 | 20, 29, 30 | ready-for-agent |
| 32 | 金标运营接口预留（导入/导出 + case_id） | 29 | ready-for-agent |
| 33 | Eval Ops 手册 + 分数≠合门禁文案 + S0 仍绿 | 30, 31, 32 | ready-for-agent |

```text
28 (W1 close)
 ├── 29 ──┬── 30 ──┐
 │        │        ├── 31 ──┐
 │        └── 32 ──────────┼── 33
 └─────────────────────────┘
```

**Frontier（30 resolved 后）：** 31（仍需 20）、32；33 仍 blocked by 30+31+32。

**本波不做：** ≥300 金标运营、Braintrust/Phoenix 换栈、评测分替 `machine_check`/人闸。
