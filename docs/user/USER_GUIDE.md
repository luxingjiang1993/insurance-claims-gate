# Claims Gate User Guide

> **Pilot · Phase 1 shipped (Issues 01–13) · Phase 2a W0 Dev Complete (14–22) · Phase 2a W1 Pilot Complete (23–28) · Phase 2a W2 Eval Ops Preview (29–33) · Phase 2b P-α Assist 证据地基 (34–44)**  
> Last updated: 2026-09-16 · Product code: `本项目代码/claims-gate/`  
> Status badge: **2b-P-α / Assist 证据地基（closed）** — citation 三联门、拒答 disposition、BM25、Demo 检索种子、Provider 清单已交付；默认 `pytest -q` 仍绿。**诚实：** H4=`deferred`（薄切片 n&lt;10，禁止宣称 grounded）；H1/H2 召回有数已以 **S2/nightly 旁路**交付（不进默认绿）；连接状态 UI / γ（rerank·MultiQuery·fan-out）**未上线**；≥300 金标运营 / 真连 L2 仍延后。W2 Eval Ops Preview 仍可用。

条款门禁是个人意外险（含附加意外医疗）理赔的裁决辅助产品：输出结构化草案、条款项级引用、一次补件清单与人闸令牌门；**不替代**持牌核赔终裁，**不触发**银企支付。

---

## 1. Start here

| 你是谁 | 你要做什么 | 跳到 |
|--------|------------|------|
| 个人开发 / 验收 | 5 分钟跑通 SC-01/02/03 | [§3 Quickstart](#3-quickstart) |
| 演示 / 核赔浏览 | 浏览器登录作业壳看案（可无 Key） | [§3.1 作业壳](#31-作业壳w0登录角色规则路径人闸文书ai-降级与本案流水preview) |
| Pilot 验收 | 满配 + 关向量 + 关 LLM（套餐 L） | [§3.2 Pilot / 套餐 L](#32-pilot-completew1演示可无-key-vs-pilot-须-langsmith) |
| 运维 / 换模 | Provider 清单、分 Key、换模检查单 | [§3.4 Provider](#34-provider-清单与密钥面2b-p-α--issue-43) |
| α DoD / H 演示 | H3/H6/H7 可复现；H1 种子存在 | [§3.5 α DoD](#35-assist-证据地基-α-dod2b-p-α--issue-44) |
| H1/H2 召回旁路 | 冻结种子 Recall@K/MRR（S2） | [§3.6 H1/H2](#36-h1h2-召回旁路s2--issue-46) |
| Eval Ops 演示 | 作业壳「评测」跑榜 / 金标钩子（Preview） | [§3.3 Eval Ops](#33-eval-ops-previeww2评测台与门禁主路径区分) |
| 核赔初审 | 材料受理 → 一次补件 / 进入初审 | [§5.1](#51-材料受理与一次补件-sc-01) |
| 核赔员 | 除外拒赔草案 / 效力栈减赔 | [§5.2](#52-除外拒赔与文书分态-sc-02) · [§5.3](#53-批单效力栈减赔-sc-03) |
| 主管 | 人闸批准 / 驳回；出款就绪 | [§5.4](#54-人闸与出款就绪) |
| 调查岗 | 冻决 / 解除冻决 | [§5.5](#55-调查冻决通融与预赔) |
| 联调 / 集成 | HTTP 对照与错误码 | [§7 Reference](#7-reference) |

**诚实边界（读完再操作）：**

- **Phase 1** 交付面以 **HTTP API + Demo 脚本** 为主（已合门禁）。
- **演示可无 Key（W0 地板仍成立）：** 登录 + 三角色 RBAC + SC 规则路径 + 人闸 + 文书分态 + AI 无 Key 降级 + 本地 trace。默认 `pytest -q` **不要求** LLM Key、LangSmith 与 cloud embedding Key。
- **Pilot 须 LangSmith 等（W1 / Pilot Complete）：** 满配验收须配置 LLM Key、独立 embedding Key（`EMBEDDING_PROVIDER=cloud`）、LangSmith（`LANGCHAIN_TRACING_V2` + Key）、可重建 Chroma 索引；混合检索挂 assist、来源摘要、真 span、OpenEval 实验历史对比按套餐 L 验收。详见 [§3.2](#32-pilot-completew1演示可无-key-vs-pilot-须-langsmith)。勿当生产终裁 UI；评测分 **不**替代 `machine_check`。
- **Eval Ops Preview（W2）：** 作业壳独立「评测」入口、排行榜、多人跑次归因、金标导入/导出钩子已交付。操作见 [§3.3](#33-eval-ops-previeww2评测台与门禁主路径区分) 与 [§7.1a](#71a-评测跑次排行榜与金标-io-钩子w2-eval-ops-preview--issues-29–33)。**硬边界：** 排行榜 / 评测分数 ≠ `machine_check` 通过；合规主缝仍是轨 A `machine_check`；故意失败的评测跑次 **不**进入默认 `pytest -q` / S0 必过；**不得**宣称 ≥300 金标运营已达标。
- **Assist 证据地基（2b-P-α closed）：** citation Schema 三联门 + 非法不可采纳（H3）；`assist_disposition` 拒答；BM25 关键词腿；Demo 检索种子 40 条冻结（非金标）；工具环白名单（H6）；默认无 LLM 轨 A 绿（H7）。验收见 [§3.5](#35-assist-证据地基-α-dod2b-p-α--issue-44)。**诚实：** H4=`deferred`；H1/H2 召回有数见 [§3.6](#36-h1h2-召回旁路s2--issue-46)（S2 旁路）；连接状态 / γ **未上线**。
- **尚未上线（勿按已交付操作）：** ≥300 人工金标双标运营；核赔作业 UI 全作业流；真连核心 L2 / 真 OCR；连接状态只读页；rerank / MultiQuery / fan-out / 往榜灌质量主指标（γ，未触发）。
- 裁决结果是 **草案**，不具对外最终效力；AI 辅助建议 **不是** 终裁。
- `PAYOUT_READY` ≠ 已打款；支付仍走核心人工流程。
- 禁止用「秒赔」叙事包装责任争议案。

术语定义以仓库根 [`CONTEXT.md`](../../CONTEXT.md) 为准。

---

## 2. Product at a glance

### 2.1 What you get

```text
案件头（L1 只读）
  → 材料断言 / 一次补件
  → Router → 裁决草案（补件 / 通赔建议 / 减赔 / 拒赔草案 / 调查中 …）
  → 独立校验（失败则失败关闭）
  → 应闸类型 → 人闸令牌
  → 文书导出（补件 / 拒赔 / 减赔）
  → L2：出款就绪回写 / 结案（不自动支付）
```

### 2.2 What you do not get (Won't)

| 不做 | 原因 |
|------|------|
| L3 自动出款 / 银企直连 | 本期 unmet；另立项 |
| 无人最终拒赔 | 对外拒赔须人闸；须可申诉路径 |
| 车险查勘定损、重疾诊断给付 | 薄切片外 |
| 健康/医疗诊断生成 | 非目标 |
| 把内部手册单独撑起对外拒赔 | fail-closed → 人闸 |

### 2.3 Surface maturity

| 能力 | 成熟度 | 备注 |
|------|---------|------|
| 轨 A 确定性裁决 + `machine_check` | Shipped | 默认合门禁 |
| SC-01 / SC-02 / SC-03 HTTP 黑盒 | Shipped | Solo Demo |
| 人闸矩阵（金额档 / 通融 / 预赔 / 调查） | Shipped | 试点默认档 |
| L2 出款就绪 / 结案模拟 | Shipped | 无真连现网 |
| 轨 B 最小 RAG 起草 | Preview | 不挡轨 A |
| Eval 负例旁路 / 合成抽检表 | Preview | 不冒充金标 |
| 作业壳登录 + 案件只读浏览 | Preview（W0） | Issue 16 |
| 作业壳 SC 规则路径（材料 / evaluate / 一次补件 / 草案） | Preview（W0） | Issue 17；无 LLM Key 可点完；语义同 `machine_check` |
| 作业壳人闸 + 文书分态 | Preview（W0） | Issue 18；supervisor 批/驳获令牌；adjuster 批闸被拒；拒赔 DRAFT 可预览；EXTERNAL_NOTIFY 无人闸不假成功 |
| 作业壳 AI 辅助建议区 | Preview（W0→2b-P） | Issue 20 / 39；显式点击才调用；无 Key 降级可见；`assist_disposition` 拒答时禁用采纳；采纳须再过规则 evaluate；UI 标明非终裁 |
| 作业壳 AI 区检索来源摘要 | Preview（W1） | Issue 25；展示 doc/条款项/版本；可采纳 vs 不可采纳诚实标注；壳不持有门禁权威 |
| 作业壳本案流水 + 本地 trace | Preview（W0） | Issue 21；ledger + 人闸事件可回放；本地 JSONL 可配置；无 Key 不阻塞 |
| Chroma / 混合检索挂 assist | Preview（W1） | Issue 24；assist 路径混合检索 + 三联门 `adoptable`；evaluate 不调向量；关向量可降级 |
| 真 LangSmith span + ledger `trace_id` | Preview（W1） | Issue 26；**Pilot 满配须** `LANGCHAIN_TRACING_V2=true` + Key；无 Key 不阻断演示；默认 pytest 不要求；不替代 `machine_check` |
| OpenEval ↔ LangSmith 实验历史对比 | Preview（W1） | Issue 27；`python -m missions.openeval_langsmith`；同 dataset 多 experiment 可历史对比；**不含**排行榜；不替代 `machine_check`；默认 pytest 不要求 Key |
| 套餐 L 验收清单 | Preview（W1） | Issue 28；满配 / 关向量 / 关 LLM；见 `本项目代码/claims-gate/docs/acceptance/package-l.md`；不进默认 pytest |
| OpenEval 评测跑次持久化 + actor | Preview（W2） | Issue 29：`POST /eval/runs` / `GET /eval/runs?actor_user_id=`；复用 W0 演示用户；不替代 `machine_check` |
| OpenEval 评测排行榜（可排序） | Preview（W2） | Issue 30：`GET /eval/leaderboard`；真源本地 SQLite `eval_runs`；主指标 `pass_rate`；**榜分 ≠ 合门禁 / ≠ `machine_check` 通过** |
| 作业壳「评测」独立入口 | Preview（W2） | Issue 31：主导航「评测」；触发跑次 / 排行榜 / 按提交者过滤；与门禁主路径视觉分离；≥2 账号协作演示；拒绝不假成功 |
| 金标导入/导出钩子 | Preview（W2） | Issue 32：`POST /eval/gold-labels/import`、`GET /eval/gold-labels/export`、`python -m missions.gold_label_io`；须关联 `case_id`；**不是** ≥300 金标运营，不得宣称已达标 |
| 金标薄切片协议 | Preview（2b-P-α） | Issue 38：双标 + 第三人裁决（角色占位）；导入导出加深；当前 **H4=`deferred`**（n&lt;10），禁止宣称 grounded；禁止宣称 ≥300 |
| Eval Ops 手册 + 分数≠合门禁文案 | Preview（W2） | Issue 33：本手册 §3.3 / §7.1a；默认 `pytest -q` 仍绿；评测失败不进 S0 必过；金标全量运营仍 Deferred |
| Provider 清单 + `.env` 分区 | Preview（2b-P-α） | Issue 43：§3.4；密钥仅 `claims-gate/.env`；分 Key；OpenAI-compatible；换模检查单指针；**不含**连接状态 UI（β） |
| α DoD 验收（H3/H6/H7 + H1 种子） | Preview（2b-P-α closed） | Issue 44：`本项目代码/claims-gate/docs/acceptance/alpha-dod.md`；H4 仍 deferred；β/γ 未上线 |
| 核赔作业 UI 全作业流 | Deferred | 真连 L2 / 生产壳等后续 |
| 真连核心 L2 / 真 OCR | Deferred | 有干系人后 |
| ≥300 人工金标运营 | Deferred | 机检入口已占位；W2 仅钩子，勿宣称达标 |
| 连接状态只读 / H1·H2 有数 / γ 加深 | Deferred（β/γ） | β 票 45–52；γ 仅触发；勿按已上线操作 |

---

## 3. Quickstart

**推荐：在仓库根目录**（避免 `ModuleNotFoundError: claims_api`——该错误通常是 cwd 不在 `claims-gate` 却用了 `--app-dir src`）：

```bash
pip install -r "本项目代码/claims-gate/requirements.txt"

# 启动 API（默认 http://127.0.0.1:8000）
python scripts/run_api.py

# 另开终端：一键跑通 SC-01/02/03
python scripts/run_sc_demo.py
python scripts/run_sc_demo.py --extras
```

等价写法（须先进入产品目录）：

```bash
cd 本项目代码/claims-gate
pip install -r requirements.txt
uvicorn claims_api.api:app --app-dir src --reload
python scripts/run_sc_demo.py
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
# 或浏览器打开 http://127.0.0.1:8000/ （返回入口 JSON）
# OpenAPI 交互文档：http://127.0.0.1:8000/docs
```

内置验收夹具（服务启动即种子）：

| case_id | 场景 |
|---------|------|
| `CLM-SC01-001` | 缺件 → 一次补件 → 通赔建议 |
| `CLM-SC02-001` | 疾病摔伤除外拒赔 + 人闸 |
| `CLM-SC03-001` | 批单缩责减赔 |

合门禁（开发自检，非用户必跑）：

```bash
pytest -q
```

### 3.1 作业壳（W0）：登录角色、规则路径、人闸、文书、AI 降级与本案流水（Preview）

`Rewrote from: REF-MISSIONS` · Issues 14–22（壳面 16 / 17 / 18 / 20 / 21；手册与 CI 绿 22）

**W0 启动（两进程）：**

1. 先启动 API（见 §3）。规则路径**无需** LLM Key；AI 辅助无 Key 时明确降级，不阻断规则路径。本地 trace / LangSmith **均非**启动前置。
2. 另开终端启动作业壳：

```bash
cd 本项目代码/claims-gate/workshell
npm install
npm run dev
```

3. 浏览器打开 `http://127.0.0.1:5173/`。

**登录角色（用户名=密码）：**

| 角色 | 可做什么 | 不可做什么 |
|------|----------|------------|
| `viewer` | 只读案件列表/详情、草案、人闸字段、本案流水；只读评测跑次/排行榜 | 无写操作入口（含不可触发评测跑次） |
| `adjuster` | 材料登记、evaluate、一次补件、看裁决草案、点 AI 辅助与采纳送交；评测台触发跑次 | 批准人闸 → API `PERMISSION_DENIED`，UI 不记成功 |
| `supervisor` | 上述写路径 + 批准/驳回人闸（获 API 令牌）+ 文书分态；评测台触发跑次 | 壳不自行签发令牌；出款就绪仍走 HTTP L2 |

主导航含「案件作业」与独立「评测」入口（Issue 31）：评测台与门禁 evaluate 主路径分离，详见 [§3.3](#33-eval-ops-previeww2评测台与门禁主路径区分)。

**规则路径（与 `machine_check` 同语义）：** `adjuster` / `supervisor` 在详情页登记材料 → evaluate → 一次补件 → 查看裁决草案。字段来自 API，壳不另立规则。无 LLM Key 即可点完 SC-01/02/03。

**人闸与文书：** `supervisor` 批准后展示 `human_latch_token`。文书须显式选 `DRAFT_EXPORT` 或 `EXTERNAL_NOTIFY`；拒赔草稿可预览；无人闸对外通知失败时 UI **不**升为已通知。

**AI 降级与非终裁：** 「AI 辅助建议」须显式点击；无 Key → 降级提示且 `used_llm=false`。辅助结果区展示**检索来源摘要**（doc / 条款项 / 版本），并以「可采纳 / 不可采纳」诚实标注三联门状态；不可采纳引用不得当作已过门合法 citation。响应含 `assist_disposition`：`draft` 时可在合法 citation 下送交采纳；`abstain`（原因枚举 `conflict` / `handbook_alone` / `low_confidence` / `citation_unfaithful`）时作业壳**禁用采纳**并展示拒答原因；可提示走人闸（`human_latch_suggested`）但 **不会**自动签发 `human_latch_token`。采纳请求须携带过 Schema 槽（`doc_id`+`clause_item`+`doc_version`）且落库通过的 citation；非法 / 缺槽 → `CITATION_NOT_IN_KB` 或校验失败，**不可采纳**；通过后仍走 `assist/adopt`→evaluate。无可用 citation 或 abstain 时作业壳禁用「送交规则校验」。失败拒绝体原样展示。UI 标明**裁决辅助非终裁**，禁止「秒赔」叙事。

**本案流水：** 详情页浏览 ledger / 人闸事件（含 `retrieval_profile`；有上报时含 `trace_id`）。可选 `.env`：`CLAIMS_GATE_LOCAL_TRACE=1` 导出 JSONL；`LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` 后 evaluate/assist/latch 上报 LangSmith；无 Key 不阻塞规则路径。不替代 `machine_check`。

可选：`VITE_CLAIMS_API_BASE`（默认 `http://127.0.0.1:8000`）。LLM / Embedding / 本地 trace / LangSmith 见 [§3.4](#34-provider-清单与密钥面2b-p-α--issue-43) 与 `.env.example`。

### 3.2 Pilot Complete（W1）：演示可无 Key vs Pilot 须 LangSmith

Issues 23–28 · 波次名：**W1 / Pilot Complete**

| 口径 | 何时用 | Key / 云 | 覆盖能力 |
|------|--------|----------|----------|
| **演示可无 Key** | 本地演示、规则路径验收、无云账号 | 可不配 LLM / LangSmith / embedding；AI 区显示降级；CI 可用 `EMBEDDING_PROVIDER=local`（哈希，**非语义**） | W0 地板 + 关 LLM 路径（套餐 L 路径 C） |
| **Pilot 须 LangSmith（等）** | 向试点方宣称 **W1 / Pilot Complete** | **须** LLM Key + LangSmith Key（`LANGCHAIN_TRACING_V2=true`）+ **独立** embedding Key（`EMBEDDING_PROVIDER=cloud`，不得复用 `OPENAI_API_KEY`）；向量索引可重建 | 满配路径 A；另验关向量路径 B |

**套餐 L（人工验收，不进默认 pytest）：** 逐步清单见  
[`本项目代码/claims-gate/docs/acceptance/package-l.md`](../../本项目代码/claims-gate/docs/acceptance/package-l.md)  
（满配 / 关向量 / 关 LLM）。勾选完成后可对照 `spec-2a-w1-pilot-complete.md` DoD。

**本波不做 / 未上线：** ≥300 人工金标运营；真连 L2 / 生产作业壳。W2 Eval Ops Preview 已交付（Issues 29–33）；钩子 **不是** ≥300 金标运营，勿宣称金标已达标。

**默认 CI：** `pytest -q` 仍不要求 LangSmith / LLM / cloud embedding Key；S2 可选测带 `langsmith_integration` / `track_llm_optional` / `eval_bypass` 等标记。CI 重建索引请显式 `EMBEDDING_PROVIDER=local`（确定性哈希，**非语义**，不得宣称语义检索质量）。

**Provider / Key：** 完整清单、分 Key 约定与换模检查单见 [§3.4](#34-provider-清单与密钥面2b-p-α--issue-43)；模板见 `本项目代码/claims-gate/.env.example`。

### 3.3 Eval Ops Preview（W2）：评测台与门禁主路径区分

`Rewrote from: REF-MISSIONS` · Issues 29–33 · 波次名：**W2 / Eval Ops（Developer Preview）**

| 路径 | 入口 | 权威 / 合门禁 |
|------|------|----------------|
| **门禁主路径** | 作业壳「案件作业」→ evaluate / 人闸 / 文书 | 轨 A `machine_check`；默认 `pytest -q` / S0 必过 |
| **Eval Ops 旁路** | 作业壳主导航「评测」（独立页，不在 evaluate 主按钮背后） | 排行榜 / 评测分数 **不是** 合门禁条件；失败跑次不进 S0 |

**硬文案（内审口径）：**

- 排行榜分数 ≠ `machine_check` 通过；`machine_check` 仍是合规主缝。
- 不得用榜分阈值代替人闸或条款门禁。
- 金标导入/导出仅是钩子；**不得**宣称「金标已达标」或 ≥300 运营已完成。
- Phase 2a 可称「Eval Ops 已交付（Preview）」时，仍须诚实标注金标全量运营延后。

**5 分钟演示（两账号协作跑榜）：**

1. 启动 API + 作业壳（同 §3.1）。
2. 以 `adjuster`（用户名=密码）登录 → 点主导航「评测」→ 可选填实验名 →「触发评测跑次」→ 刷新排行榜，确认本账号 `actor` 有行。
3. 退出，以 `supervisor` 登录 → 再次进入「评测」→ 触发另一跑次 → 用「按提交者过滤」分别查看两人结果（互不覆盖）。
4. `viewer` 可只读跑次/排行榜，不可触发跑次；写操作被拒时 UI **不**假成功。
5. （可选）金标钩子：在评测页粘贴含 `case_id` 的 JSON 导入，或导出；响应 `gold_ops_complete` 恒为 false。CLI：`python -m missions.gold_label_io`（见 §7.1a）。

**HTTP 对照：** 同 [§7.1a](#71a-评测跑次排行榜与金标-io-钩子w2-eval-ops-preview--issues-29–33)。无 LangSmith Key 时跑次仍落本地 SQLite，响应可含 `langsmith_degraded=true`。

**默认 CI：** `pytest -q` 排除 `eval_bypass` 等标记；故意失败的评测旁路套件 **不得** 导致轨 A 红。合门禁自检仍用：

```bash
cd 本项目代码/claims-gate
pytest -q
```

### 3.4 Provider 清单与密钥面（2b-P-α · Issue 43）

`Rewrote from: REF-MISSIONS` · P-CFG α（文档清单）；**不含**连接状态 UI（属 β）

| 能力 | 契约 / Provider | 主要环境变量 | Pilot 参照默认 | 缺 Key / 关闭时 |
|------|-----------------|--------------|----------------|-----------------|
| **LLM**（AI 辅助建议） | OpenAI-compatible Chat Completions | `OPENAI_API_KEY`（或 `CLAIMS_GATE_LLM_API_KEY`）、`OPENAI_BASE_URL`、`OPENAI_MODEL` | `gpt-4o-mini`；`BASE_URL` 默认真官方 | assist **明确降级**（`used_llm=false`）；不挡轨 A |
| **Embedding**（语义检索） | OpenAI-compatible `/embeddings`；或 `local` 确定性哈希 | `EMBEDDING_PROVIDER`、`CLAIMS_GATE_EMBEDDING_API_KEY`（或 `EMBEDDING_API_KEY`）、`EMBEDDING_BASE_URL`、`EMBEDDING_MODEL` | `cloud` + `text-embedding-3-small` | **不得**静默复用 LLM Key；CI 用 `local`（**非语义**） |
| **LangSmith**（云 span） | LangSmith tracing | `LANGCHAIN_TRACING_V2`、`LANGCHAIN_API_KEY`（或 `LANGSMITH_*`）、`LANGCHAIN_PROJECT` | 关闭；满配 Pilot 须开 | 无 Key **不阻塞**规则路径；默认 pytest 不要求 |
| **本地 trace**（JSONL 回放） | 本机文件 | `CLAIMS_GATE_LOCAL_TRACE`、`CLAIMS_GATE_LOCAL_TRACE_PATH` | 关闭 | 可选排障；不替代 `machine_check` |
| **Chroma / 混合检索** | 本地持久目录 + 权重 | `CHROMA_PERSIST_DIR`、`KEYWORD_WEIGHT` / `VECTOR_WEIGHT`、`CLAIMS_GATE_VECTOR_ENABLED` | 权重 0.7 / 0.3 | 关向量 → 关键词降级；evaluate **零**向量依赖 |

**密钥与边界（运维必读）：**

1. **唯一写处：** 密钥只写在 `本项目代码/claims-gate/.env`（从 `.env.example` 复制）。作业壳仅 `VITE_CLAIMS_API_BASE`，**不得**持有 API Key；前端不可配置 Key。
2. **分 Key：** LLM 与 Embedding 必须分开配置；一侧缺失时诚实降级，禁止静默互顶。
3. **OpenAI-compatible：** 换国产/他厂端点 = 改 `OPENAI_*` / `EMBEDDING_*` 的 `BASE_URL` + `MODEL` + 对应 Key，不必另开换模大波。
4. **重建索引：** 切换 `EMBEDDING_PROVIDER`（尤其 `local`→`cloud`）或换 embedding 模型后，须先 `python scripts/rebuild_chroma_index.py`，再宣称语义检索。人改条款库 markdown（含过长条款的段落）后同样重建；切块默认一条款项一块，过长按段切并回填父条款项 id，citation 仍用三联门。
5. **本波未交付：** 「连接状态」只读页/API（已配置？降级？模型名？无 Key 回显）属 **phase2b-p-β**，勿按已上线操作。

**换模检查单（指针；不预切票）：**

1. 改 `.env`（分 Key：`OPENAI_*` / `EMBEDDING_*`）。
2. `EMBEDDING_PROVIDER=cloud` 时重建 Chroma。
3. 在冻结 Demo 检索种子 + 金标薄切片上重测 H1–H5（旁路，不进默认绿）。
4. 更新本表与（β 交付后）连接状态展示的模型名。
5. 手册标明当前 Pilot 参照模型；**不得**因换模宣称合门禁 / `machine_check` 升级。

分区模板：[`本项目代码/claims-gate/.env.example`](../../本项目代码/claims-gate/.env.example)（`[B] LLM` / `[C] Embedding` / `[F] 本地 trace` / `[G] LangSmith` 等）。

### 3.5 Assist 证据地基 α DoD（2b-P-α · Issue 44）

`Rewrote from: SPEC-02B-P α DoD` · 验收清单：[`本项目代码/claims-gate/docs/acceptance/alpha-dod.md`](../../本项目代码/claims-gate/docs/acceptance/alpha-dod.md)

**已关闭（2026-09-16）：** H3 非法 citation 不可采纳；H6 工具环不得写 latch/支付/evaluate 权威字段；H7 默认 `pytest -q` 无 LLM/无 LangSmith 仍绿；H1 Demo 检索种子 40 条已冻结（**非金标**）。

**快速复现（无 Key）：**

```bash
cd 本项目代码/claims-gate
pytest -q tests/test_assist_citation_schema_adopt.py   # H3
pytest -q tests/test_assist_tool_acl.py                # H6
pytest -q                                              # H7 / S0
pytest -q tests/test_demo_retrieval_seeds.py           # H1 种子结构
```

**本波未交付 / 勿宣称：** H4 grounded（当前 `deferred`）；连接状态 UI（β）；rerank / MultiQuery / fan-out / 往榜灌质量主指标（γ，未触发）。H1/H2 召回有数见 [§3.6](#36-h1h2-召回旁路s2--issue-46)（S2 旁路，不进默认绿）。

### 3.6 H1/H2 召回旁路（S2 · Issue 46）

`Rewrote from: REF-CASE-RECALL` · 验收：[`本项目代码/claims-gate/docs/acceptance/recall-metrics-s2.md`](../../本项目代码/claims-gate/docs/acceptance/recall-metrics-s2.md)

在冻结 Demo 检索种子上复现 Recall@K / MRR，并对照门槛：**H1** 条款号子集 Recall@1 ≥ 0.95；**H2** 语义难例 Recall@5 ≥ 0.70 **或** MRR ≥ 0.55。失败只影响质量旁路退出码，**不**红轨 A / **不**进 `machine_check`。

```bash
cd 本项目代码/claims-gate
python scripts/run_recall_metrics_s2.py
pytest -m assist_quality -q tests/test_recall_eval_runner.py
```

报告默认写入 `artifacts/reports/recall_metrics_s2.json`。默认 `pytest -q` 排除 `assist_quality`。

---

## 4. Core concepts

| 概念 | 操作含义 |
|------|----------|
| **裁决草案** | 系统建议；须经校验与（应闸时）人闸后才可对外/出款就绪 |
| **一次补件** | 同一缺项清单一次通知完整；`one_shot_hash` 下禁止拆轮重发 |
| **人闸令牌** | `human_latch_token`；无令牌则 `payout_ready` 恒为 false |
| **效力栈** | 批单/批注 → 特别约定 → 附加险 → 主险 → 告知/核保 → 内部手册 |
| **出款就绪** | 门禁态 `PAYOUT_READY`；仅人闸后可置位；不触发支付 |
| **文书分态** | `DRAFT_EXPORT` 可草稿导出；`EXTERNAL_NOTIFY` 对外通知须人闸 |
| **轨 A / 轨 B** | 轨 A = 确定性默认可回归；轨 B = LLM 可选，失败不挡轨 A |
| **AI 辅助建议** | 显式点击才调用；产物非裁决草案；可看来源摘要（doc/条款项/版本与可采纳标注）；`abstain` 时可见拒答原因且禁用采纳（不自动发人闸令牌）；`draft` 且合法 citation 三联槽后方可采纳再 evaluate；UI 标明非终裁 |
| **本案流水** | ledger + 人闸事件可回放；本地 JSONL 可配置；LangSmith Key 配置后含 `trace_id`；无 Key 不阻塞；不替代 `machine_check` |
| **Eval Ops（评测台）** | 独立「评测」入口；跑次归因 + 排行榜；**分数 ≠ 合门禁**；金标 I/O 仅钩子，非 ≥300 运营 |

### 4.1 门禁状态（作业可读）

| 状态 | 含义 | 常见下一步 |
|------|------|------------|
| `MATERIALS_INTAKE` | 材料受理中 | 登记材料 / evaluate |
| `PENDING_SUPPLEMENT` | 待补件 | 通知补件 → 客户补传 → 再 evaluate |
| `PRIMARY_REVIEW` / `ADJUSTING` | 初审 / 理算 | 查看草案与理算步骤 |
| `INVESTIGATING` | 调查冻决 | 解除须人闸；期间不可出款就绪 |
| `HUMAN_LATCH` / `PENDING_APPROVAL` | 待人批 | approve / reject |
| `PAYOUT_READY` | 出款就绪 | 核心支付流程（系统外） |
| `NOTIFIED` | 已通知 | 留存文书与回执字段 |
| `CLOSED` | 已结案 | L2 close；无自动支付指令 |
| `REJECTED_TO_EDIT` | 人闸驳回 | 修改后重评 |

---

## 5. How-to（作业流）

对齐 PRD 七步作业流。HTTP 与作业壳规则路径 / 人闸 / 文书分态映射同一状态机；出款就绪回写仍以 HTTP 为主。

### 5.1 材料受理与一次补件（SC-01）

**目标：** 缺件时一次说清；补齐后产出通赔建议草案（默认 `payout_ready=false`）。

**作业壳（Preview）：** 以 `adjuster` 打开 `CLM-SC01-001` → 触发 evaluate → 用草案清单发起一次补件 → 按清单登记材料 → 再次 evaluate，查看 `approve_recommend` 且 `payout_ready=false`。同 hash 拆轮会在壳内原样展示 API 拒绝。

**HTTP：**

1. 读取案件头  
   `GET /claims/CLM-SC01-001`
2. 运行裁决  
   `POST /claims/CLM-SC01-001/evaluate`  
   - 若缺件 → 响应含补件清单与 `one_shot_hash`，状态进入 `PENDING_SUPPLEMENT`
3. 一次通知补件（须携带完整缺项码，与 hash 一致）  
   `POST /claims/{id}/supplement/notify`
4. 客户补传后登记材料  
   `POST /claims/{id}/materials`  
   Body 示例：`{"material_codes":["INVOICE","ID","ACCIDENT_PROOF"]}`
5. 再次 `evaluate` → 期望 `approve_recommend`，且 **`payout_ready` 仍为 false**（直至人闸 + L2）
6. 需要时导出补件文书草稿  
   `POST /claims/{id}/documents/export`  
   `document_type=supplement_notice`，`document_status=DRAFT_EXPORT`

**失败关闭：** 同一 `one_shot_hash` 下拆轮缺项 → 拒绝（合规：保险法第 22 条一次通知义务）。

### 5.2 除外拒赔与文书分态（SC-02）

**目标：** 除外责任带条款项 citation；对外拒赔须人闸。

**作业壳（Preview）：** 以 `adjuster` 打开 `CLM-SC02-001` → evaluate → 文书选 `reject_notice` + `DRAFT_EXPORT` 预览。以 `supervisor` 登录后批准人闸，再选 `EXTERNAL_NOTIFY` 并填入令牌。无人闸点对外导出时，界面显示 API 拒绝且**不**点亮成功条。

**HTTP：**

1. `POST /claims/CLM-SC02-001/evaluate` → `reject_draft` + citations + `appeal_path`
2. 草稿导出（可无人闸）  
   `documents/export`：`reject_notice` + `DRAFT_EXPORT`
3. 对外通知（须人闸）  
   - 先 `POST .../human-latch/approve` 取得令牌  
   - 再 `documents/export`：`EXTERNAL_NOTIFY` + `human_latch_token`  
   - 无人闸 → `LATCH_REQUIRED`

### 5.3 批单效力栈减赔（SC-03）

**目标：** 批单优先于主险；理算步骤可复核。

1. `POST /claims/CLM-SC03-001/evaluate` → `reduce` / `ADJUSTING`
2. 检查响应中的 `authority_rank` / `overridden_by` / `calc_steps`
3. 导出减赔说明：`reduction_notice`（引用与步骤复用；默认仍非出款就绪）

**失败关闭：** 提出理算与批单冲突 → 不得静默采信。

### 5.4 人闸与出款就绪

**作业壳（Preview）：** 详情页「人闸」区。`supervisor` 批准后可见 API 返回令牌；`adjuster` 批准被拒绝（`PERMISSION_DENIED`）且 UI 标注「未记为成功」。出款就绪回写仍走下方 HTTP（本票不在壳内做 L2）。

**何时必须人闸（试点默认）：**

| 决定类型 | 人闸 |
|----------|------|
| 补件 | 否 |
| 通赔建议 | 按金额档 A–D（见 §6） |
| 减赔 | 按金额档；争议上浮 |
| 拒赔草案 / 通融 / 预赔 | **是** |
| 调查解除冻决 | **是** |

**批准：**

```http
POST /claims/{case_id}/human-latch/approve
{"approved_by":"supervisor_01"}
```

D 档上浮双人：额外传 `second_approver`。

**驳回：**

```http
POST /claims/{case_id}/human-latch/reject
{"rejected_by":"supervisor_01","reason":"..."}
```

**出款就绪（模拟 L2，不支付）：**

```http
POST /claims/{case_id}/l2/payout-ready
{"human_latch_token":"<token>"}
```

无令牌 → `LATCH_REQUIRED`。主数据不一致夹具 `CLM-MISMATCH-001` → `MASTER_DATA_MISMATCH`，禁止出款就绪。

**结案：**

```http
POST /claims/{case_id}/l2/close
```

载荷不含自动支付指令。

### 5.5 调查冻决、通融与预赔

| 动作 | 端点 | 要点 |
|------|------|------|
| 进入调查 | `POST .../investigate/enter` | 自动冻决；`payout_ready=false` |
| 解除冻决 | `POST .../investigate/unfreeze` | **须**人闸令牌 |
| 通融 | `POST .../decisions/exgratia` | 必闸；伪「主险通赔」citation → 校验失败 |
| 预赔 | `POST .../decisions/prepay` | 必闸 |
| 高峰降级 | `POST .../peak-degrade` | 仅补件+人审队列；禁止静默通赔 |

### 5.6 查阅账本与草案

| 目的 | 端点 |
|------|------|
| 案件当前态 | `GET /claims/{id}` |
| 最新裁决草案 | `GET /claims/{id}/decision` |
| 路由 / 校验账本 | `GET /claims/{id}/ledger` |
| 条款引用校验 | `POST /kb/citations/validate` |

---

## 6. Roles & latch tiers

试点金额档（人民币，单次建议赔付额；**上线前须换客户现行制度**）：

| 档 | 区间 | 通赔建议 | 减赔 |
|----|------|----------|------|
| A | ≤ 10,000 | 可直通草案（抽检） | 主管闸 |
| B | 10,001–50,000 | 作业中心主管闸 | 主管闸 |
| C | 50,001–200,000 | 省级核赔负责人闸 | 同左 |
| D | > 200,000 | 总公司授权闸 | 同左 |

**上浮：** 诉讼/信访/媒体、健康敏感争议、首次大额、通融、拒赔 → 至少上浮一档；已是 D 则双人令牌。

硬约束：无 `human_latch_token` → 不得 `payout_ready=true`。

---

## 7. Reference

### 7.1 HTTP map（Phase 1）

| Method | Path | 用途 |
|--------|------|------|
| GET | `/health` | 存活 |
| GET | `/claims/{id}` | 案件头 + 门禁态 |
| POST | `/claims/{id}/evaluate` | 跑门禁裁决 |
| GET | `/claims/{id}/decision` | 读草案 |
| GET | `/claims/{id}/ledger` | 路由与校验账本 |
| POST | `/claims/{id}/materials` | 登记材料 |
| POST | `/claims/{id}/supplement/notify` | 一次补件通知 |
| POST | `/claims/{id}/documents/export` | 文书导出 |
| POST | `/claims/{id}/human-latch/approve` | 人闸批准 |
| POST | `/claims/{id}/human-latch/reject` | 人闸驳回 |
| POST | `/claims/{id}/decisions/exgratia` | 通融 |
| POST | `/claims/{id}/decisions/prepay` | 预赔 |
| POST | `/claims/{id}/investigate/enter` | 进入调查 |
| POST | `/claims/{id}/investigate/unfreeze` | 解除冻决 |
| POST | `/claims/{id}/peak-degrade` | 高峰降级 |
| POST | `/claims/{id}/l2/payout-ready` | 出款就绪回写 |
| POST | `/claims/{id}/l2/close` | 结案回写 |
| POST | `/claims/{id}/assist` | AI 辅助建议（显式触发） |
| POST | `/claims/{id}/assist/adopt` | 采纳：须合法 citation 三联槽，再 evaluate |
| POST | `/kb/citations/validate` | citation 落库门 |

### 7.1a 评测跑次、排行榜与金标 I/O 钩子（W2 Eval Ops Preview · Issues 29–33）

旁路 API，**不**替代 `machine_check` / 人闸。须 Bearer 登录（W0 种子用户）。  
**单一数据真源（跑次/榜）：** 本地 SQLite 表 `eval_runs`（不读 LangSmith 实验 API 驱动榜）。  
**金标钩子真源：** 本地 SQLite 表 `gold_label_records`（每条须有 `case_id`）。

**金标薄切片（Issue 38 / 2b-P-α）：** 在 W2 钩子上加深「外聘核赔顾问双标 + 第三人裁决」协议。角色字段只用占位 id（如 `external_claims_advisor_a` / `external_claims_advisor_b` / `third_party_adjudicator`），**人名不进仓**。导入 schema 可为 `claims-gate-gold-thin-slice-v1`；每条可带 `annotation`。响应含 `h4_status`：α 目标 n≥10，**当前样例不足 → `deferred`，禁止宣称 grounded**；**禁止宣称 ≥300 运营已完成**。验收清单：`本项目代码/claims-gate/docs/acceptance/gold-thin-slice.md`。外形样例：`artifacts/gold_thin_slice/gold_thin_slice.v1.example.json`（非真双标运营）。

| Method | Path | 角色 | 用途 |
|--------|------|------|------|
| POST | `/eval/runs` | `adjuster` / `supervisor` | 触发 OpenEval 旁路跑次并持久化；`actor_user_id` = 当前用户 |
| GET | `/eval/runs` | 已登录（含 `viewer`） | 列出跑次；可选 `?actor_user_id=` 过滤 |
| GET | `/eval/leaderboard` | 已登录（含 `viewer`） | 排行榜：实验名 / 主指标 `pass_rate` / 时间 / 提交者；`?order=desc\|asc` 按主指标排序（稳定） |
| POST | `/eval/gold-labels/import` | `adjuster` / `supervisor` | 导入金标/薄切片；`records[].case_id` 必填；薄切片须 `annotation`；`gold_ops_complete=true` 被拒绝；回执含 `h4_status` |
| GET | `/eval/gold-labels/export` | 已登录（含 `viewer`） | 导出；可选 `?dataset_id=` / `?case_id=`；`gold_ops_complete` 恒 false；含 `h4_status` / 可选 `protocol` |

无 LangSmith Key 时仍落本地表，响应含 `langsmith_degraded=true`。榜上分数 **不是** 条款门禁合门禁条件；**不等于** `machine_check` 通过。

**约定脚本：** 在 `本项目代码/claims-gate/` 执行 `python -m missions.gold_label_io import --file artifacts/gold_thin_slice/gold_thin_slice.v1.example.json`（或 W2 样例 `artifacts/gold_label_dataset_preview.json`）或 `export --file <out.json>`（可用 `--db` / `CLAIMS_GATE_DB`）。默认 `pytest -q` **不要求**金标 I/O / 评测旁路全绿（`-m eval_bypass` 为可选套件）。

**作业壳入口：** 登录后主导航点「评测」（与「案件作业」并列）。操作步骤见 [§3.3](#33-eval-ops-previeww2评测台与门禁主路径区分)。页面标明评测旁路、非终裁、无秒赔、**不宣称金标已达标**。

OpenAPI：启动服务后访问 `/docs`（FastAPI 自动生成）。

### 7.2 常见错误码（操作可读）

| code | 操作者含义 | 你该做什么 |
|------|------------|------------|
| `LATCH_REQUIRED` | 缺人闸令牌 | 走主管批准后再试对外/出款就绪 |
| `CITATION_NOT_IN_KB` | 引用不在条款库 | 修正 doc_id / 条款项 / 版本 |
| `VALIDATION_FAILED` | 独立校验未过 | 按 fail report 修正；不得出款就绪 |
| `MASTER_DATA_MISMATCH` | 主数据不一致 | 对齐保单/条款/批单后再评 |
| （拆轮补件拒绝） | 同 hash 拆轮 | 使用首次完整缺项清单 |

完整表以产品 `error_codes` 与 SPEC 为准。

### 7.3 Demo 夹具一览

| case_id | 用途 |
|---------|------|
| `CLM-SC01-001` | 一次补件 → 通赔建议 |
| `CLM-SC02-001` | 除外拒赔 + 人闸 |
| `CLM-SC03-001` | 效力栈减赔 |
| `CLM-AMT-*` | 金额档人闸差异 |
| `CLM-MISMATCH-001` | 主数据不一致负例 |

---

## 8. Safety checklist（每次对外前）

- [ ] 拒赔 / 减赔是否有 **条款项级** citation（含版本）？
- [ ] 补件清单是否 **一次完整**（未拆轮）？
- [ ] 应闸类型是否已取得有效 **`human_latch_token`**？
- [ ] 对外通知是否使用 `EXTERNAL_NOTIFY` 而非误把草稿当已发？
- [ ] `payout_ready` 是否仅在人闸后为 true，且 **未**假设系统已打款？
- [ ] 叙事是否避免「秒赔」包装争议案？

---

## 9. Support & sources of truth

| 问题类型 | 真源 |
|----------|------|
| 需求 / Won't | `Managerial System/PRD/PRD_02_INSURANCE_CLAIMS_GATE.md` |
| 工程行为契约 | `Managerial System/SPEC/insurance-claims-gate/spec.md` |
| 术语 | `CONTEXT.md` |
| 开发自检命令 | `本项目代码/claims-gate/README.md` |
| 阶段剩余 / 延后项 | `docs/agents/current-phase-remaining.md` |
| 本手册如何随阶段更新 | [`MAINTENANCE.md`](./MAINTENANCE.md) |
| 用户可见变更 | [`CHANGELOG.md`](./CHANGELOG.md) |

---

## 10. Document control

| 字段 | 值 |
|------|----|
| doc_id | `USER-GUIDE-CLAIMS-GATE` |
| phase_covered | Phase 1（01–13）+ Phase 2a W0–W2（14–33）+ Phase 2b P-α（34–44 closed） |
| next_update_trigger | β 用户可见合入 / 金标全量运营 / 真连 L2 / 生产壳交付，或用户可见 API/作业流变更合入 |
| owner | 产品 Owner（人类）；agents 按 `MAINTENANCE.md` 代写修订 |
