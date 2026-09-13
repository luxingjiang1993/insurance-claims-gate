# Claims Gate User Guide

> **Pilot · Phase 1 shipped (Issues 01–13)**  
> Last updated: 2026-09-14 · Product code: `本项目代码/claims-gate/`  
> Status badge: **Developer Preview** — production UI and live core L2 are deferred.

条款门禁是个人意外险（含附加意外医疗）理赔的裁决辅助产品：输出结构化草案、条款项级引用、一次补件清单与人闸令牌门；**不替代**持牌核赔终裁，**不触发**银企支付。

---

## 1. Start here

| 你是谁 | 你要做什么 | 跳到 |
|--------|------------|------|
| 个人开发 / 验收 | 5 分钟跑通 SC-01/02/03 | [§3 Quickstart](#3-quickstart) |
| 核赔初审 | 材料受理 → 一次补件 / 进入初审 | [§5.1](#51-材料受理与一次补件-sc-01) |
| 核赔员 | 除外拒赔草案 / 效力栈减赔 | [§5.2](#52-除外拒赔与文书分态-sc-02) · [§5.3](#53-批单效力栈减赔-sc-03) |
| 主管 | 人闸批准 / 驳回；出款就绪 | [§5.4](#54-人闸与出款就绪) |
| 调查岗 | 冻决 / 解除冻决 | [§5.5](#55-调查冻决通融与预赔) |
| 联调 / 集成 | HTTP 对照与错误码 | [§7 Reference](#7-reference) |

**诚实边界（读完再操作）：**

- 本期交付面是 **HTTP API + Demo 脚本**，不是核赔作业台 UI。
- 裁决结果是 **草案**，不具对外最终效力。
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

| 能力 | Phase 1 | 备注 |
|------|---------|------|
| 轨 A 确定性裁决 + `machine_check` | Shipped | 默认合门禁 |
| SC-01 / SC-02 / SC-03 HTTP 黑盒 | Shipped | Solo Demo |
| 人闸矩阵（金额档 / 通融 / 预赔 / 调查） | Shipped | 试点默认档 |
| L2 出款就绪 / 结案模拟 | Shipped | 无真连现网 |
| 轨 B 最小 RAG 起草 | Preview | 不挡轨 A |
| Eval 负例旁路 / 合成抽检表 | Preview | 不冒充金标 |
| 核赔作业 UI | Deferred | 阶段 2+ |
| 真连核心 L2 / 真 OCR | Deferred | 有干系人后 |
| ≥300 人工金标运营 | Deferred | 机检入口已占位 |

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

对齐 PRD 七步作业流。当前用 HTTP 完成；未来作业 UI 映射同一状态机。

### 5.1 材料受理与一次补件（SC-01）

**目标：** 缺件时一次说清；补齐后产出通赔建议草案（默认 `payout_ready=false`）。

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
| POST | `/kb/citations/validate` | citation 落库门 |

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
| phase_covered | Phase 1（Issues 01–13） |
| next_update_trigger | 任一阶段 DoD 关闭，或用户可见 API/作业流变更合入 |
| owner | 产品 Owner（人类）；agents 按 `MAINTENANCE.md` 代写修订 |
