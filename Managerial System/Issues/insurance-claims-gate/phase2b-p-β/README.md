# Phase 2b · P-β — Claims Assist 可证伪质量

**SPEC：** [spec-2b-p-assist-quality.md](../../../SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md)  
**波次门禁：** α DoD（票 44）已关闭（2026-09-16）；本波可开工。各票仍须满足表内其余 `Blocked by`。

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 45 | 条款项切块 | 44, 34 | resolved |
| 46 | Recall 指标 S2 | 44, 36, 35 | resolved |
| 47 | 三维 S2 | 44, 46, 42 | resolved |
| 48 | 夜间 S2 告警 | 44, 47 | resolved |
| 49 | 四步步数预算 | 44, 40 | resolved |
| 50 | κ / judge-human | 44, 38 | resolved |
| 51 | 连接状态只读 | 44, 43 | resolved |
| 52 | β DoD 收口 | 45–51 | ready-for-agent |

**本波不做：** 未触发的 γ（RRF/rerank/MultiQuery/fan-out/灌榜）；流 Q 实现（另 SPEC）。
