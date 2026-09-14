# 19: AI 辅助建议 API：降级 + 关键词提名 + 采纳再 evaluate

**github_issue:** #6

**Status:** resolved

**Blocked by:** 14

**wave:** W0

**spec_id:** SPEC-02A-W0-DEV-COMPLETE

**ref_id:** REF-MISSIONS, REF-COURSE-03, REF-CASE-HYBRID, REF-RAG-CY

**Rewrote from:** REF-MISSIONS, REF-COURSE-03, REF-CASE-HYBRID

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `03_单次模型请求与结构化输出控制/` | OpenAI-compatible / 结构化输出外形 |
| 2 | `CASE-投顾AI助手（混合式）/` | 规则+模型分治 |
| 3 | `RAG-cy/` | 关键词检索起步（W0 不用向量） |

## What to build

实现真实 OpenAI-compatible「AI 辅助建议」HTTP 路径：有 Key 可调用；无 Key 明确降级且 `used_llm=false`。关键词检索可用于提名（向量留给 W1）；接口预留 retrieval 画像字段。采纳须再过规则 evaluate 才可能更新裁决草案；assist 不得写 `payout_ready`、不得签发人闸令牌。默认 CI 不要求真 LLM。

## Acceptance criteria

- [x] `.env.example` 含 LLM 相关键；无 Key 时 assist 明确降级
- [x] 有 Key 时可返回辅助建议（真调用实现替换空 stub）
- [x] 关键词检索可用于提名；预留 retrieval 画像字段（不做 Chroma）
- [x] 采纳路径必须再过规则 evaluate；不得直接写权威裁决字段绕过门禁
- [x] assist 不写 `payout_ready`、不签发人闸令牌；注入文本不能改 latch 规则
- [x] 默认 `pytest` 无 LLM 仍绿；真调用测试可隔离标记
- [x] handoff 含 `Rewrote from: REF-MISSIONS`（及所用 REF）

## Answer

交付位于 `本项目代码/claims-gate/`：

- `.env.example`：`OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`（及可选 `CLAIMS_GATE_LLM_API_KEY`）
- `missions/track_llm_optional/llm_client.py`：OpenAI-compatible `chat/completions`（httpx）
- `_maybe_llm_draft` 真调用替换空 stub；无 Key → `used_llm=false` + `degraded`
- `POST /claims/{id}/assist`：关键词提名 + 可选 LLM；`retrieval.mode=keyword`、`vector_enabled=false` 预留 W1
- `POST /claims/{id}/assist/adopt`：唯一权威更新路径为再跑 `evaluate`；不采信 `suggested_stance` 直写草案
- ACL：`assist_claim` / `adopt_assist`（viewer 拒绝）
- 测试：`tests/test_assist_api_degrade_adopt.py`（默认 CI，含有 Key 替身与采纳作废旧令牌）；`requires_llm` 真网隔离于 `tests/track_llm_optional/test_assist_llm_optional.py`
- 默认 `pytest -q`：无 LLM / 无 LangSmith 全绿

**Rewrote from: REF-MISSIONS, REF-COURSE-03, REF-CASE-HYBRID, REF-RAG-CY**

## Comments

- 2026-09-14：to-tickets 批准 defaults；落盘于 `phase2a-w0/`。
- 2026-09-14：同步 GitHub Issue #6。
- 2026-09-14：实现完成并 Resolve；作业壳 AI 区留给票 20。
