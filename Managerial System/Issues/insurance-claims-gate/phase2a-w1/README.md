# Phase 2a · W1 — Pilot Complete

实现票 23–28。SPEC：[`spec-2a-w1-pilot-complete.md`](../../../SPEC/insurance-claims-gate/spec-2a-w1-pilot-complete.md)。  
上级索引：[`../README.md`](../README.md)。

**波次门禁：** 全部票 Blocked by **22**（W0 DoD）或其传递依赖；W0 未关闭前不以本目录为主实现路径。

## 任务图

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 23 | Chroma 索引 + 本地/云 embedding + 可重建 | 22 | ready-for-agent |
| 24 | 混合检索挂 assist：硬过滤 / 条款号短路 / 加权融合 / 三联门 / 向量降级 | 22, 23 | ready-for-agent |
| 25 | 作业壳 AI 区展示检索来源摘要 | 20, 24 | ready-for-agent |
| 26 | 真 LangSmith：evaluate / assist / latch + ledger 对齐 | 22 | ready-for-agent |
| 27 | OpenEval 旁路 ↔ LangSmith 实验历史对比 | 26 | ready-for-agent |
| 28 | 套餐 L 验收 + Pilot 手册区分 + 默认 CI 仍绿 | 24, 25, 26, 27 | ready-for-agent |

```text
22 (W0 close)
 ├── 23 ── 24 ── 25 ──┐
 │              │      │
 └── 26 ── 27 ──┴──────┴── 28
```

**Frontier（W0 的 22 resolved 后）：** 23、26。

**本波不做：** OpenEval 排行榜、多人协作、≥300 金标运营。
