# Phase 2b · P-α — Claims Assist 证据地基

**SPEC：** [spec-2b-p-assist-quality.md](../../../SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md)  
**Status 词汇：** 
eady-for-agent → claimed → 
esolved  
**波次门禁：** 无前置波阻塞（2a 已 closed）。**α DoD 票：44。**

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 34 | Pilot 默认 cloud embedding | — | ready-for-agent |
| 35 | BM25 关键词腿 | — | resolved |
| 36 | Demo 检索种子 40 | — | resolved |
| 37 | citation Schema 槽 | — | ready-for-agent |
| 38 | 金标薄切片 | — | ready-for-agent |
| 39 | 辅助拒答 + 壳 | 37 | ready-for-agent |
| 40 | 工具环 ACL | 37 | resolved |
| 41 | span 树 | 40 | ready-for-agent |
| 42 | 忠实检查（规则） | 37, 38 | ready-for-agent |
| 43 | Provider 文档 | — | ready-for-agent |
| 44 | α DoD 收口 | 34–43 | ready-for-agent |

`	ext
34,35,36,37,38,43（可并行）
37 ── 39
37 ── 40 ── 41
37,38 ── 42
全部 ── 44 (α DoD) ──→ 解阻 β 与未来 SPEC-Q
`

**本波不做：** γ 触发项；流 Q；≥300 金标运营。
