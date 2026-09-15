# Phase 2a · W1 — Pilot Complete

实现票 23–28。SPEC：[`spec-2a-w1-pilot-complete.md`](../../../SPEC/insurance-claims-gate/spec-2a-w1-pilot-complete.md)（**closed**）。  
上级索引：[`../README.md`](../README.md)。

**波次门禁：** 全部票 Blocked by **22**（W0 DoD）或其传递依赖；本波 DoD 已于 Issue 28 收口。

## 任务图

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

**本波已关闭。** W2 亦已关闭（29–33）；Phase 2a 波次 frontier 为空。详见 [`../phase2a-w2/`](../phase2a-w2/) 与 [`../README.md`](../README.md)。

**本波不做：** OpenEval 排行榜、多人协作、≥300 金标运营（已由 W2 外形交付 / 金标运营仍延后）。
