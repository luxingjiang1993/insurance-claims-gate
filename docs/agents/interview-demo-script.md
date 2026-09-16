# Claims Gate — 计时演示脚本（N3）

| 字段 | 内容 |
|------|------|
| 默认路径 | **无 Key 地板**（W0 仍成立；AI 明确降级） |
| Live 分支 | 有双 Key 时：真 Assist + 连接双绿（见下方「Live 分支」）；缺 Key 仍走降级 |
| 建议时长 | 10–12 分钟演示 + 2 分钟缓冲；超时砍「评测」与 pytest 点名 |
| 配套口述 | `interview-talk-track.md`；图 `diagrams/claims-gate.architecture.html`；S2 卡 `interview-s2-metrics.md` |
| 工作目录 | 仓库根启动 API；产品码 `本项目代码/claims-gate/` |
| 档位 | **面试诚实 8 分档** · **Integration-Ready**（Ready ≠ Deployed） |

**开场固定承认（进房前默念）：** H4 **deferred**；不宣称 grounded；不冲面试条 9；L2/OCR 是 Ready 不是 Deployed。

**本脚本默认不覆盖：** γ、真连现网 L2/OCR、≥300 金标。满配 / Live 勾选见 USER_GUIDE §3.2 / §3.14 与 `live-pilot-g0.md`。

---

## 开场前 10 分钟（面试官进房前做完）

1. 确认 `本项目代码/claims-gate/.env`：无 Key 也可演示地板；有 Key 则准备 **Live 分支**（LLM Key 与 Embedding Key **分槽**，`EMBEDDING_PROVIDER=cloud` 已重建索引）。有 Key 时 AI 区可能出草案——改讲三联门 / 拒答，**不要假装无 Key**。  
2. 终端 A（仓库根）：

```text
python scripts/run_api.py
```

3. 终端 B：

```text
cd 本项目代码/claims-gate/workshell
npm run dev
```

4. 浏览器打开 `http://127.0.0.1:5173/` 与 `http://127.0.0.1:8000/health`。  
5. 可选：终端 C 先跑 `cd 本项目代码/claims-gate` → `pytest -q`，绿了把窗口缩小备用，**演示中不要现场等全集**。  
6. 把架构 HTML 放在第二个浏览器窗口，不要挡作业壳。  
7. （可选 Live）打开「连接状态」确认 LLM / Embedding 已配置且无 Key 回显。

登录约定：**用户名 = 密码**（`viewer` / `adjuster` / `supervisor`）。

---

## 时间盒（无 Key 地板）

| 分 | 动作 | 你必须说出口的一句 |
|----|------|--------------------|
| 0:00–0:30 | 开场 + 健康检查 | 「规则路径不依赖大模型。**H4 仍 deferred，不宣称 grounded，也不冲 9。**」 |
| 0:30–2:00 | `adjuster` · SC-01 | 「一次补件；通赔建议仍非出款就绪。」 |
| 2:00–5:00 | `adjuster`→`supervisor` · SC-02 | 「adjuster 批闸失败；supervisor 拿令牌；对外通知须闸。」 |
| 5:00–6:30 | SC-03 一瞥 | 「批单效力栈优先于主险。」 |
| 6:30–8:00 | AI 辅助区 | 「无 Key 降级；辅助不是终裁；不签发人闸。」 |
| 8:00–9:30 | 评测台 **或** S2 剖面一句 | 「榜分不是 `machine_check`。」 / 「**先剖面后数字**。」 |
| 9:30–11:00 | 连接状态 +（可选）pytest 点名 | 「默认绿不要求 Key；L2/OCR 是 Integration-Ready，不是 Deployed。」 |
| 11:00–12:00 | 收 | 读一页纸收尾句 |

有 Key 时：用下方 **Live 分支**替换 6:30–8:00（或加 90s），并口头声明「这是 Live，不是无 Key 地板」。

---

## 逐步点击（失败时怎么办）

### A. SC-01 一次补件（`adjuster`）

1. 登录 `adjuster`。  
2. 打开 `CLM-SC01-001`。  
3. evaluate → 看到缺件 / 补件清单。  
4. 按清单登记材料后再 evaluate。  
5. **指着屏幕说：** `approve_recommend` 可以出现，但 `payout_ready` 仍为 false（直至人闸 + L2）。

卡死：改跑 `python scripts/run_sc_demo.py`（仓库根或 `claims-gate/` 按 USER_GUIDE §3），口头：「HTTP 黑盒与壳同语义。」

### B. SC-02 人闸与文书（本段是主戏）

1. 仍用 `adjuster` 打开 `CLM-SC02-001` → evaluate → 除外拒赔草案 + citation。  
2. 文书：`reject_notice` + `DRAFT_EXPORT`（草稿可无人闸）。  
3. 在人闸区尝试批准 → 期望 `PERMISSION_DENIED`，UI **不**记成功。  
4. 退出，登录 `supervisor`，同一案批准 → 展示 `human_latch_token`。  
5. `EXTERNAL_NOTIFY` 须带令牌；可先口头说明「故意不带令牌会失败且不点亮已通知」——若时间够再点一次失败路径。

**禁句：** 「系统已经拒赔生效 / 已经打款。」正确：**草案 + 对外须闸；支付在核心、本期无 L3。**

### C. SC-03 效力栈（可压缩到 30s）

打开 `CLM-SC03-001` → evaluate → 指 `reduce` / 理算步骤 / 批单优先。不要展开公式。

### D. AI 辅助（无 Key 地板）

案件详情点「AI 辅助建议」（须显式点击）：

- 期望降级提示、`used_llm=false`（或等价文案）。  
- 标明**非终裁**。  
- 若出现 `abstain`：禁用采纳，**没有**自动令牌。

### D′. Live 分支（有双 Key · 可选 90s–2min）

前置：`.env` 中 LLM 与 Embedding Key 分槽；`EMBEDDING_PROVIDER=cloud` 已重建；连接状态双绿。

1. 「连接状态」：指已配置 / 模型名；**无 Key 回显**。  
2. 同一案件点「AI 辅助建议」→ 期望 `used_llm=true`（或等价）与 structured draft。  
3. 指来源摘要「可采纳 / 不可采纳」；非法 citation 不可送交。  
4. **必须说：** 「Live 仍过三联门与人闸；**不是**自动出款；H4 仍 deferred。」  
5. 可选一句检索：若被问召回，**先剖面后数字**——「这是 `demo_seed_eval` 基线 / 或 `pilot_cloud_embed` 语义对照」，再报数字；禁止甩无标签 1.00 冒充语义满分。

卡死：退回 D（无 Key 降级），诚实说「本机 Key 不可用，地板路径仍成立」。

### E. 评测台（W2 Preview）

主导航「评测」→ 触发一次跑次 → 指排行榜：

> 这是 Eval Ops Preview。分数不是合门禁；金标导入只是钩子，**没有** ≥300 运营。

`viewer` 只读、不能触发：时间不够可口述。

### E′. S2 双剖面（口播 30s，可不跑脚本）

> 召回有数，但是 **先剖面后数字**：`demo_seed_eval`（向量关）是可复现基线；`pilot_cloud_embed`（向量开）才是语义对照。旁路分数 **不是** `machine_check`。H4 仍 deferred。

若被要求现场跑：`python scripts/run_recall_metrics_s2.py`（`claims-gate/`），默认双剖面；**不要**只甩短路满分。

### F. 连接状态 + Integration-Ready

打开「连接状态」：已配置 / 降级 / 模型名；**无 Key 回显**。  
口头补一句：L2 / OCR Provider 是 **Integration-Ready**（契约 + Recorded），**Ready ≠ Deployed**，禁止「已接核心 / 生产 OCR 已上线」。

### G. 工程诚实（可选 90s，有备用窗再点）

在 `本项目代码/claims-gate/`：

```text
pytest -q tests/test_assist_citation_schema_adopt.py
pytest -q tests/test_schema_bound_orchestrator.py
pytest -q tests/test_patch_worker_demo.py
```

口述对应：H3 非法 citation 不可采纳；A2 Schema 硬停；A3 真 commit。  
**不要**打开 Mission Control（不存在）。**不要**说 A5 / grounded / 面试条 9。

---

## 超时砍单

1. 先砍 SC-03 与评测台。  
2. 再砍 pytest 点名（改口播「默认 `pytest -q` 无 Key 仍绿」）。  
3. Live 分支可砍回无 Key 降级，但须诚实声明路径切换。  
4. **永不砍** SC-02 人闸三角色与开场 H4 deferred。

---

## 演示后 30 秒收口

> 权威在轨 A + 人闸；Assist 可证伪；中继诚实到 A2/A3；Live + 双剖面 + Integration-Ready；未宣称 A5 / grounded / 面试条 9 / 生产自动出款。Ready 不等于 Deployed。

若被要求「再看检索质量」：声明要切 S2 旁路（`python scripts/run_recall_metrics_s2.py`），**先剖面后数字**，且 **不**进默认绿、**不**等于合门禁；H4 仍 deferred。

---

## 录屏切片（N9 · 须面试者本人录）

本仓库 **不**代录。建议从本脚本剪一条 **3–5 分钟** 短片：SC-02 人闸三角色（adjuster 失败 / supervisor 令牌）+ DRAFT vs EXTERNAL_NOTIFY +（无 Key 降级 **或** Live 真 Assist 一句）+ 开场 H4 deferred。超时先砍 SC-03 与评测台。成片自存，勿把「未录」写成已交付。
