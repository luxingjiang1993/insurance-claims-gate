# Phase 2c · Live Honest Seams DoD 验收摘要

`Rewrote from: SPEC-02C-LIVE-HONEST-SEAMS DoD Checklist` · Issue 62 / GitHub #49

本清单关闭 **Live Honest Seams（流 2c）**。  
档位：**面试诚实 8 分档** · 副标题 **Integration-Ready**（**Ready ≠ Deployed**）。

**不**宣称：H4 grounded；面试条 9；A5 / Production latch；已接核心 / 生产 OCR 已上线；KB≥20；γ（rerank / MultiQuery / fan-out）；L3；≥300 金标。

工作目录：`本项目代码/claims-gate/`。默认合门禁：`pytest -q`（无 LLM / 无 LangSmith / 无 cloud embedding Key 仍须绿）。

**完成旗隔离：** 本文件是 2c 唯一出口。禁止把 `alpha-dod.md` / `beta-dod.md` / `q-relay-a2a3-dod.md` 或 Issues 34–56 标为 2c 完成条件。附录 H4 另开 SPEC/票。

---

## 证据索引（57–61）

| 工项 | 票 | 证据指针 |
|------|----|----------|
| G0 Live | 57 / #44 | [`live-pilot-g0.md`](./live-pilot-g0.md)；连接状态 / Assist 降级契约测；旁路 `pytest -m requires_llm`（有 Key） |
| G2 双剖面 | 58 / #45 | [`recall-metrics-s2.md`](./recall-metrics-s2.md)；`python scripts/run_recall_metrics_s2.py`（`report_kind=dual_retrieval_profile`）；`tests/test_recall_eval_runner.py` |
| G3 L2 Adapter | 59 / #46 | `tests/test_l2_core_provider_contract.py`；`tests/fixtures/l2_core/recorded_cassette.json`；`tests/test_l2_payout_ready_writeback.py` |
| G3 OCR Provider | 60 / #47 | `tests/test_ocr_provider_contract.py`；`tests/fixtures/ocr/recorded_cassette.json`；`tests/test_threat_inject_ocr_remark.py` |
| G4 文案 | 61 / #48 | `docs/agents/interview-honesty-table.md`；`docs/user/USER_GUIDE.md` §3.14；`docs/agents/interview-demo-script.md` |

---

## G0 — Live Pilot（S1）

| 子项 | 状态 | 证据 |
|------|------|------|
| 双 Key 分区；`EMBEDDING_PROVIDER=cloud` 可重建 | 清单可勾 | `live-pilot-g0.md` 路径 L0；`.env.example` [B] / [C] |
| 连接状态双绿；永不回显 Key | 契约/清单 | L1；既有 connection-status 测 |
| 有 Key → structured draft；缺 Key → 明确降级 | 契约 + 旁路 | L2/L3；`requires_llm` 有 Key 环境实跑 |
| Live 验收清单可勾完 | 交付 | [`live-pilot-g0.md`](./live-pilot-g0.md) |
| 默认 `pytest -q` 无 Key 仍绿 | 本文件 S0 | 见下 |

勾选：`[x] G0`

---

## G2 — 检索双剖面（S2）

**可复现：**

```text
python scripts/run_recall_metrics_s2.py
pytest -q tests/test_recall_eval_runner.py
```

**期望：** 报告并列 `demo_seed_eval` 与 `pilot_cloud_embed`；强制「先剖面后数字」；禁止无标签短路 1.00 冒充语义满分；evaluate 零向量/零 LLM；真云仅旁路。

勾选：`[x] G2`

---

## G3 — L2 / OCR Provider（S3）

**可复现：**

```text
pytest -q tests/test_l2_core_provider_contract.py tests/test_ocr_provider_contract.py
pytest -q tests/test_threat_inject_ocr_remark.py tests/test_l2_payout_ready_writeback.py
```

**期望：**

- L2：InMemory + Recorded；人闸/出款就绪前置仍在核心服务；支付计数不递增；文案 Integration-Ready。
- OCR：Stub + Recorded；规范化文本进既有收纳；注入不得签发人闸 / 单独出款就绪 / 翻 latch。
- 默认 CI 不依赖真保司 / 真 OCR 账号。

勾选：`[x] G3 L2` · `[x] G3 OCR` · `[x] Integration-Ready（非 Deployed）`

---

## G4 — 诚实叙事同步

| 工件 | 与 61 一致 |
|------|------------|
| `docs/agents/interview-honesty-table.md` | 8 分档；H4 deferred；Ready≠Deployed；禁 A5/L3/≥300/冲 9 |
| `docs/user/USER_GUIDE.md` + `CHANGELOG.md` | §3.14；页眉 8 分档；Unreleased→本 DoD 折叠 |
| `docs/agents/interview-demo-script.md` | Live 分支；先剖面后数字；开场 H4 deferred |
| `docs/agents/interview-s2-metrics.md` | 先剖面后数字；禁 grounded / 条 9 |

勾选：`[x] G4` · `[x] 用户手册与诚实表已与 61 一致`

---

## S0 — 默认 `pytest -q` 绿

**可复现：**

```text
pytest -q
```

**记录（2026-09-16 · Issue 62 收口）：** `337 passed, 26 deselected`（排除 `track_llm_optional` / `eval_bypass` / `requires_llm` / `langsmith_integration` 等）；无 cloud embedding Key；无 LangSmith。

勾选：`[x] S0 绿`

---

## 旁路 / 双剖面 / S3 契约定位速查

| 缝 | 命令或路径 |
|----|------------|
| Live 旁路（有 Key） | `pytest -m requires_llm -q`；清单 [`live-pilot-g0.md`](./live-pilot-g0.md) |
| S2 双剖面 | `python scripts/run_recall_metrics_s2.py` → `artifacts/reports/`（含剖面名） |
| S3 L2 | `tests/test_l2_core_provider_contract.py` |
| S3 OCR | `tests/test_ocr_provider_contract.py` + `tests/test_threat_inject_ocr_remark.py` |

勾选：`[x] Live / 双剖面 / S3 证据可定位`

---

## 禁止正面宣称（抽检）

| 禁宣 | 本关闭态度 |
|------|------------|
| grounded / 面试条 9 | **未宣称**；H4=`deferred` |
| A5 / Production latch | **Deferred**（Q-A7） |
| 已接核心 / 生产 OCR 已上线 | **禁止**；仅 Integration-Ready |
| KB≥20 / γ 无条件 | **未做** |
| L3 / ≥300 金标 | **Won't / 延后** |

勾选：`[x] 无 grounded / 条 9 / 已接核心 / A5 正面宣称`

---

## SPEC 本窗口 DoD 总勾选

| SPEC 必做项 | 状态 |
|-------------|------|
| G0 双 Key / cloud 重建 / 连接双绿 | 票 57 / 本文件 G0 |
| G0 有 Key draft / 缺 Key 降级 | 票 57 |
| G0 Live 清单 + `requires_llm` 旁路 + 默认绿 | 票 57 + 本文件 S0 |
| G2 双剖面报告 + 先剖面后数字 + evaluate 零依赖 | 票 58 |
| G3 L2 Provider InMemory+Recorded；人闸不变 | 票 59 |
| G3 OCR Stub+Recorded；威胁不变式 | 票 60 |
| G3 Integration-Ready 文案 | 票 59–61 |
| G4 诚实表 / 手册 / demo / S2 卡 | 票 61 |
| 不宣称 grounded / 条 9 / A5 / L3 / ≥300 | 本文件 |
| 默认 `pytest -q` 绿 | 本文件 S0 |

| 附录（可选 · 非本波） | 状态 |
|----------------------|------|
| H4 真双标 n≥10 + κ + 忠实率 → grounded | **未做**；保持 deferred |

**关闭后：** `phase2c/` Frontier 为空；SPEC-02C Status=`closed`。γ / ≥300 / 真连现网 / A5 / H4 过线仍勿预切为「已交付」。
