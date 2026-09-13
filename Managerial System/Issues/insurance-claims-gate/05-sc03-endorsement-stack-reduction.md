# 05: SC-03 效力栈减赔 + 理算步骤

**Status:** ready-for-agent

**Blocked by:** 01, 02

**ref_id:** REF-CASE-KB, REF-MISSIONS, REF-COURSE-04

**Backlog:** P0-2

**Rewrote from:** REF-CASE-KB, REF-MISSIONS, REF-COURSE-04

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/missions/rag.py` | 检索与 `retrieval_profile`；改写成 `endorsement_priority` |
| 2 | `project 多agent/knowledge_base/`（policies 等 md） | 多文档版本化样例；本票换为批单+主险条款 |
| 3 | `project 多agent/src/missions/checks.py` | 效力栈减赔 / `calc_steps` / `authority_rank` 的黑盒检查类型 |
| 4 | `project 多agent/src/transfer_api/service.py` | 领域计算与错误码返回模式（换为理算步骤） |
| 5 | `04_多步流程编排与条件分支/examples/02_triggerflow_meeting.py` | 多步条件分支编排外形 |
| 6 | `04_多步流程编排与条件分支/examples/03_langgraph_meeting.py` | 状态机式多步流（门禁态参考，勿引入重框架替代中继） |
| 7 | `CASE-知识库处理/4-知识库版本管理与性能比较.py` | 批单 vs 主险版本并存时的版本管理灵感 |

## What to build

端到端跑通 SC-03（确定性轨）：批单缩小责任时产出减赔草案；引用按效力栈消解，批单优于主险；每条 citation 含 doc_id、条款项、版本/生效日与 `authority_rank`，冲突时暴露 `overridden_by`；免赔额与赔付比例以可复核 `calc_steps` 呈现，与条款冲突则失败关闭而非静默改数。减赔通知复用 citations 与计算步骤字段。检索侧落实 `endorsement_priority`（先批单后主险）。

## Acceptance criteria

- [ ] SC-03 夹具经 HTTP：批单缩责 → 减赔草案，引用服从效力栈
- [ ] citations 含 `authority_rank`；批单覆盖主险时可观察 `overridden_by`（或等价字段）
- [ ] `calc_steps` 可复核；条款冲突时失败关闭，不静默改金额
- [ ] `endorsement_priority` 画像下先查批单再主险，可被 machine_check / 黑盒路径验证
- [ ] 减赔导出复用 citations 与 calc_steps；金额档人闸细节可留给 06，但无人闸前不得谎称出款就绪
- [ ] SC-03 轨 A machine_check 稳定绿
- [ ] handoff 含 `Rewrote from: REF-CASE-KB, REF-MISSIONS, REF-COURSE-04`

## Comments

- 2026-09-13：to-tickets 批准 defaults 后落盘。
