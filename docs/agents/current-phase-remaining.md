# 当前阶段剩余工作（个人开发 · 进阶段 2 前门禁）

| 字段 | 内容 |
|------|------|
| 状态 | `active` |
| 日期 | 2026-09-13 |
| 前提 | Issues `01`–`09` 已 `resolved`；轨 A 默认 CI 绿 |
| 真源 | PRD-02、SPEC `insurance-claims-gate`、`ref-projects.md` 清单一 |
| 扩面 | `ref-projects-phase2-supplement.md`（**本文件完成前不得按草案放松 I1–I8**） |

---

## 0. 个人开发约束（已确认）

无法对接真实保司用户 / 作业中心实测时：

| 项 | 处置 |
|----|------|
| Week1–4 OUT 基线实测（PRD M4） | **延后** → 阶段 2 之后或有真实干系人时 |
| ≥300 人工金标运营（PRD M3 全量） | **延后**；本期只做机检入口 + 合成抽检占位 |
| 关闭 §14 A1–A5（客户签字） | **延后至生产前**；个人阶段继续沿用 PRD 试点默认 |
| 真连核心 L2 / 现网枚举 | **延后**（SPEC P2-2） |
| 真实 OCR 供应商 | **延后**（Provider Stub+Recorded 为 Integration-Ready；≠ 生产 OCR 已上线；SPEC-02C G3 / 2c closed） |
| 核赔作业 UI 壳 | **延后**；本期用 HTTP + Demo 脚本验收 |

延后项**不**阻塞「当前阶段完成 → 启动阶段 2 工程」。阶段 2 仍须遵守：先修宪 / 新 PRD 条目，再消费 N1–N11。

---

## 1. 进阶段 2 前必须完成（DoD）

全部满足才可宣称「当前阶段剩余关闭」：

1. Issues **`10`、`11`、`12`、`13`** 均为 `resolved`，且轨 A `pytest -q` 全绿（轨 B 标记用例仍可不并入默认绿门）。  
2. SPEC Backlog 中已落地项状态已与代码一致（见 SPEC 修订记录）。  
3. `docs/agents/ref-projects.md`「本期仍可供改写」中本阶段计划消费的 REF 已写入对应票的 `Rewrote from:`。  
4. 本文件 §0 延后表保持有效；未假装已完成真实用户实测。  
5. **用户手册已同步**：`docs/user/USER_GUIDE.md` 与 Phase 1 交付面一致；`docs/user/CHANGELOG.md` 已写入本阶段条目（规则见 `docs/user/MAINTENANCE.md`）。

**非必须（可留阶段 2 / 另票）：** `REF-CASE-RECALL`、`REF-CASE-MCP`/FastMCP、作业壳、真 L2、N* 修宪。

---

## 2. 任务图（你要做的事）

按 Frontier 编号从小到大；每票开工前把该票 `Status:` 改为 `claimed`。

| NN | 票 | 你做什么 | 验收一眼看 |
|----|-----|----------|------------|
| 10 | Eval / 负例入口 | 按票从 `REF-CASE-OPENEVALS` 裁剪评估外形；挂在轨 A 旁路，**不替代** `machine_check` | 负例集可跑；默认 CI 仍只靠 machine_check 绿 |
| 11 | 合成抽检占位 | 按票从 `REF-CASE-EVAL-ADVISOR` 做 Judge–human **字段/表**占位（合成双人分可手填） | 一致率字段存在；不阻塞轨 A |
| 12 | 轨 B 最小检索 | 按票从 `REF-RAG-CY` 补 `track_llm_optional` 检索起草；标注 `inference_track=llm_optional` | `pytest -m track_llm_optional` 可跑；失败不挡轨 A |
| 13 | Solo Demo 脚本 | 一键/脚本跑通 SC-01/02/03 HTTP 黑盒（个人验收） | README 有命令；与 machine_check 语义一致 |

实现只写入 `本项目代码/claims-gate/`。参考仓只读。

---

## 3. 建议操作顺序（个人）

```text
1. 打开 Issues/insurance-claims-gate/README.md → Frontier
2. Claim 10 → 实现 → Resolve（写 Answer + Rewrote from）
3. Claim 11 → …（可与 10 串行；11 Blocked by 10 可选并行若无代码冲突则改票）
4. Claim 12 → …
5. Claim 13 → …
6. 跑：pytest -q
7. 同步 docs/user（USER_GUIDE + CHANGELOG）；勾选本文件 §1 DoD（含手册项）
8. 再开阶段 2：先读 phase2-supplement，由你书面决定修宪范围后再切扩面票
```

---

## 4. 阶段 2 启动口令（给未来的你）

仅当 §1 DoD 满足后：

1. 将 `ref-projects-phase2-supplement.md` 中拟采用的 N* / 入库组合写入 Constitution 附录或新 PRD/SPEC。  
2. 首批扩面仍遵守「至多 2 个新 REF 仓」。  
3. 真实用户基线、金标运营、A1–A5 关闭仍按 §0 延后，除非你已具备真实干系人。

---

## 5. 修订记录

- 2026-09-13：初稿。联合评估后冻结个人开发路径；真实用户实测延后；切票 10–13。
- 2026-09-14：DoD 增「用户手册已同步」；真源 `docs/user/`。
- 2026-09-16：Phase 2c Live Honest Seams DoD closed（Issues 57–62）；§0 真 OCR 行口径与 Integration-Ready 对齐；H4/A5/真连现网仍延后。
