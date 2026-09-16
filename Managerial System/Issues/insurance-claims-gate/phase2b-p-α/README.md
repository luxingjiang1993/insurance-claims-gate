# Phase 2b · P-α — Claims Assist 证据地基

**SPEC：** [spec-2b-p-assist-quality.md](../../../SPEC/insurance-claims-gate/spec-2b-p-assist-quality.md)  
**Status 词汇：** ready-for-agent → claimed → resolved  
**波次门禁：** 无前置波阻塞（2a 已 closed）。**α DoD 票：44 — resolved（2026-09-16）。**  
**验收：** [`本项目代码/claims-gate/docs/acceptance/alpha-dod.md`](../../../../本项目代码/claims-gate/docs/acceptance/alpha-dod.md)

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

```text
34,35,36,37,38,43（可并行）
37 ── 39
37 ── 40 ── 41
37,38 ── 42
全部 ── 44 (α DoD closed) ──→ 解阻 β 与未来 SPEC-Q
```

**本波不做：** γ 触发项；流 Q；≥300 金标运营。  
**诚实：** H4=`deferred`（薄切片 n&lt;10）；H1/H2 有数属 β。
