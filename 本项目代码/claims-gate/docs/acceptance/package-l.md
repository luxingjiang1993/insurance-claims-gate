# 套餐 L — W1 Pilot Complete 验收清单

`Rewrote from: REF-MISSIONS` · `spec_id: SPEC-02A-W1-PILOT-COMPLETE` · Issue 28

本清单供人工（或按步骤手工脚本）验收 **Phase 2a · W1 / Pilot Complete**。  
**不写入默认 `pytest -q` 强制执行**；默认 CI 仍须在无 LangSmith、无 LLM 下全绿。

路径末尾的 `[ ]` 勾选由**验收人**填写；本文件交付即满足实现侧「套餐 L 清单完成」（录像可选，不阻塞实现 DoD）。

对外宣称须带波次名 **「W1 / Pilot Complete」**。本清单**不**覆盖、**不**宣称：OpenEval 排行榜、多人协作评测台（属 **W2 Eval Ops**，未上线）。

---

## 前置（各路径共用）

1. 工作目录：`本项目代码/claims-gate/`
2. 依赖已安装：`pip install -r requirements.txt`；作业壳另需 `cd workshell && npm install`
3. 复制 `.env.example` → `.env` 后按下方路径填写
4. 启动 API：仓库根 `python scripts/run_api.py`（勿在错误 cwd 下误用 `--app-dir src`）
5. 启动作业壳（可选，壳面步骤）：`cd workshell && npm run dev` → `http://127.0.0.1:5173/`

种子账号（用户名=密码）：`viewer` / `adjuster` / `supervisor`。

---

## 路径 A — 满配（Pilot 完工标准）

**配置要求（Pilot 须具备，与「演示可无 Key」区分）：**

| 项 | 建议值 |
|----|--------|
| LLM | `OPENAI_API_KEY`（及可选 `OPENAI_BASE_URL` / `OPENAI_MODEL`） |
| LangSmith | `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`（或 `LANGSMITH_API_KEY`） |
| 向量 | 默认 `EMBEDDING_PROVIDER=cloud` + `CLAIMS_GATE_EMBEDDING_API_KEY`；先重建：`python scripts/rebuild_chroma_index.py`（换 provider 后必须重建） |
| 混合检索权重 | 默认 `KEYWORD_WEIGHT=0.7` / `VECTOR_WEIGHT=0.3` |

**步骤与期望：**

1. **三角色差：** `viewer` 无写入口；`adjuster` 可 evaluate / assist，批人闸被拒；`supervisor` 可批/驳人闸。
2. **规则路径：** 用 `CLM-SC01-001` / `CLM-SC02-001` / `CLM-SC03-001` 跑通材料 → evaluate →（应闸时）人闸；`payout_ready` 无人闸恒 false。
3. **AI + 混合检索：** `adjuster` 显式点「AI 辅助建议」；可见检索来源摘要（doc / 条款项 / 版本）与可采纳标注；采纳须再过规则 evaluate。
4. **LangSmith：** 在 LangSmith 项目中可见对应 evaluate / assist / latch span；ledger 有上报时含 `trace_id`。
5. **OpenEval 旁路：** `python -m missions.openeval_langsmith` 跑通；同 dataset 可做实验**历史对比**。  
   **不含**排行榜 / 多人协作外形。

勾选：`[ ] 路径 A 满配通过`

---

## 路径 B — 关向量（关键词降级）

**配置：**

```text
CLAIMS_GATE_VECTOR_ENABLED=0
```

（或制造向量不可用：错误 persist 目录 / 未建索引。）LLM / LangSmith 可仍开启。

**步骤与期望：**

1. 再点 AI 辅助：仍返回可用结果（或明确降级提示），不得整案失败。
2. 查看 **assist 响应**中的检索画像（非 ledger 的 `retrieval_profile` 配置 id）：应体现向量降级，例如 `vector_degraded=true`、`mode` 为 `keyword` / `keyword_degraded`，或带 `degrade_reason`。
3. **规则 evaluate 不依赖向量：** 关向量后 SC 规则路径仍可点完。

勾选：`[ ] 路径 B 关向量降级通过`

---

## 路径 C — 关 LLM（规则路径仍完整）

**配置：**

- 不设 `OPENAI_API_KEY`（及别名 Key）
- LangSmith / 向量均可关；演示降级场景推荐全关云 Key

**步骤与期望：**

1. SC-01/02/03 **规则路径**仍可完整点完（材料 / evaluate / 补件 / 草案 / 人闸）。
2. 点「AI 辅助建议」→ 明确降级（如 `used_llm=false` 或降级文案），**不阻断**规则作业。
3. 默认合门禁仍绿：`pytest -q`（无 LLM、无 LangSmith Key）。

勾选：`[ ] 路径 C 关 LLM 降级通过`

---

## 默认 CI（本清单之外的硬门）

```bash
cd 本项目代码/claims-gate
pytest -q
```

期望：无 LangSmith、无 LLM 仍全绿；S2 可选测带标记（如 `langsmith_integration` / `track_llm_optional` / `eval_bypass`），默认 addopts 排除。

勾选：`[ ] 默认 pytest -q 无 Key 全绿`

---

## 与演示 / Pilot 口径对照

| 场景 | Key 要求 | 宣称 |
|------|----------|------|
| **演示（W0 地板）** | 可无 LLM / 无 LangSmith；规则路径 + AI 降级可见 | 演示可无 Key |
| **Pilot Complete（W1）** | 满配路径须 LLM + LangSmith（及可重建向量索引） | W1 / Pilot Complete |
| **Eval Ops（W2）** | 排行榜 / 多人评测台 | **未上线**；勿用本清单勾选冒充 |

用户手册：`docs/user/USER_GUIDE.md`（诚实边界与 §3.2）。

---

**脚注（套餐 L 的性质）：** 本文件是 **人工 Pilot 验收清单**（W1 / Pilot Complete）。路径勾选由验收人填写，**不**并入默认 `pytest -q`，**不**等于 `machine_check` 合门禁，也 **不**用评测榜分代替人闸。默认 CI 仍须无 LLM / 无 LangSmith 全绿；满配路径 A 是 Pilot 宣称条件，不是轨 A 地板。

---

## Phase 2c · G0 Live（套餐 L 之上）

有 Key 真 Assist / 双 Key cloud 重建 / 连接双绿 / `requires_llm` 旁路：见 **[`live-pilot-g0.md`](./live-pilot-g0.md)**（Live Pilot；不宣称 H4 grounded / 面试条 9）。
