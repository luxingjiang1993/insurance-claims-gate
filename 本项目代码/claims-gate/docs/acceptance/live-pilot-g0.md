# G0 Live Pilot — 验收清单（套餐 L 之上）

`Rewrote from: REF-MISSIONS` · `spec_id: SPEC-02C-LIVE-HONEST-SEAMS` · Issue 57 / GitHub #44

本清单供人工（或按步骤手工）验收 **Phase 2c · G0 Live Pilot**。  
建立在 [`package-l.md`](./package-l.md)（W1 Pilot Complete）之上，**不替代**套餐 L；默认 CI 仍须无 Key 全绿。

路径末尾的 `[ ]` 勾选由**验收人**填写；本文件交付即满足实现侧「Live 验收清单完成」（录像可选）。

**诚实边界（开场必读）：** 本窗口为「面试诚实 8 分档」；**不宣称** H4 grounded、**不冲** 面试条 9、不说「已接核心 / 已上线 OCR」。H4 保持 deferred。

---

## 与套餐 L 的关系

| 清单 | 波次 | 用途 |
|------|------|------|
| [`package-l.md`](./package-l.md) | W1 Pilot Complete | 满配 / 关向量 / 关 LLM 三路径 |
| **本文件** | Phase 2c G0 Live | 双 Key 分区、cloud 重建、连接双绿、真 Assist 起草、旁路绿 |

先按套餐 L 路径 C 确认无 Key 规则路径仍完整，再按本清单勾 Live。

---

## 前置

1. 工作目录：`本项目代码/claims-gate/`
2. 依赖已安装：`pip install -r requirements.txt`；作业壳另需 `cd workshell && npm install`
3. 复制 `.env.example` → `.env`；**LLM Key 与 Embedding Key 必须分栏填写**（见下表）
4. 启动 API：`python scripts/run_api.py`（仓库根或本目录约定入口）
5. 可选作业壳：`cd workshell && npm run dev` → `http://127.0.0.1:5173/`

种子账号（用户名=密码）：`viewer` / `adjuster` / `supervisor`。

---

## 路径 L0 — 双 Key 分区 + cloud 索引重建

**配置（`.env` 分区，与 `.env.example` 的 [B] / [C] 一致）：**

| 分区 | 键 | 说明 |
|------|-----|------|
| [B] LLM | `OPENAI_API_KEY`（或 `CLAIMS_GATE_LLM_API_KEY`） | Assist 起草；不得当作 embedding Key |
| [C] Embedding | `CLAIMS_GATE_EMBEDDING_API_KEY` + `EMBEDDING_PROVIDER=cloud` | 向量索引；**不得**静默复用 `OPENAI_API_KEY` |

**步骤与期望：**

1. 确认 `.env` 中 LLM Key 与 Embedding Key **各自非空且不同槽位**（一侧空时另一侧不得被静默复用）。
2. 执行：`python scripts/rebuild_chroma_index.py`（`EMBEDDING_PROVIDER=cloud`）。
3. 期望：退出码 0；索引写入 `data/chroma`（或 `CHROMA_PERSIST_DIR`）；缺 embedding Key 时须失败并提示，不得 silently 用 LLM Key 建索引。

勾选：`[ ] 路径 L0 双 Key + cloud 重建通过`

---

## 路径 L1 — 连接状态双绿（永不回显 Key）

**前置：** L0 已配双 Key；API 已启动。

**步骤与期望：**

1. 登录任意角色（含 `viewer`），打开作业壳「连接状态」，或：
   `GET /provider/connection-status`（带 session）。
2. 期望：`llm` 与 `embedding` 均为可读「已配置 / 可用」类状态（双绿演示路径）；可见模型名或 provider 标签。
3. 期望：响应 JSON / UI **永不**出现 Key 明文或 `sk-` 秘密串；无 `api_key` / `*_KEY` 字段回显。

勾选：`[ ] 路径 L1 连接状态双绿且无 Key 泄漏`

---

## 路径 L2 — 有 Key 真 Assist 结构化起草

**配置：** `OPENAI_API_KEY`（或别名）已填；作业员显式点「AI 辅助建议」（API 侧 `enable_llm=true`）。

**步骤与期望：**

1. `adjuster` 对 `CLM-SC02-001`（或等价除外案）点 AI 辅助 / `POST /claims/{id}/assist`。
2. 期望：`used_llm=true`，`degraded=false`（无降级文案抢戏）；`draft_text` 非空；含 `citations`（含 doc / 条款项 / 版本可采纳标记）；`inference_track=llm_optional`。
3. 期望：响应**不**签发 `human_latch_token`、**不**置 `payout_ready=true`；采纳须再走规则 evaluate。
4. 旁路（有 Key 环境必跑）：
   ```bash
   pytest -m requires_llm -q
   pytest -m track_llm_optional -q
   ```
   期望：旁路绿（缺 Key 时 `requires_llm` 可 skip，不算本路径通过）。

勾选：`[ ] 路径 L2 有 Key structured draft + 旁路绿`

---

## 路径 L3 — 缺 Key 明确降级（回归）

**配置：** 临时去掉 / 不设 `OPENAI_API_KEY` 与 `CLAIMS_GATE_LLM_API_KEY`（可保留 embedding）。

**步骤与期望：**

1. 再点 AI 辅助。
2. 期望：`used_llm=false`，`degraded=true`，`degrade_reason` 可读（如 `missing_openai_api_key`）；规则 evaluate / SC 路径仍可点完。
3. 默认合门禁：
   ```bash
   pytest -q
   ```
   期望：无 LLM / 无云 Key 仍全绿（`requires_llm` / `track_llm_optional` 等默认 addopts 排除）。

勾选：`[ ] 路径 L3 缺 Key 降级 + 默认 pytest -q 绿`

---

## 默认 CI（硬门 · 本清单之外）

```bash
cd 本项目代码/claims-gate
pytest -q
```

期望：无 LangSmith、无 LLM、无 cloud embedding Key 仍全绿。Live / 真网调用只在旁路标记。

勾选：`[ ] 默认 pytest -q 无 Key 全绿`

---

## 口径对照（禁止越线）

| 场景 | Key | 可宣称 |
|------|-----|--------|
| 演示地板 | 可无 Key | 规则路径 + 明确降级 |
| W1 Pilot Complete | 见套餐 L | Pilot Complete（非 grounded） |
| **G0 Live（本清单）** | 双 Key + cloud 重建 + 真 Assist | Live 可演示；**面试诚实 8 分档** |
| H4 / 面试条 9 | 真双标金标等 | **本窗口不做**；不得宣称 grounded |

用户手册与诚实表同步属 G4 票；本清单勾完 ≠ 宣称 grounded。

---

**脚注：** 本文件是 **人工 Live 验收清单**。路径勾选由验收人填写，**不**并入默认 `pytest -q`，**不**等于 `machine_check`。契约测仅断言清单落盘与必备章节（见 `tests/test_live_pilot_checklist_contract.py`）。
