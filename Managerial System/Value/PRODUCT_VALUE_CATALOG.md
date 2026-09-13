# 我方产品价值主张目录（供需求↔价值映射引用）

**用途：** 模拟客户填写「价值主张映射」时，只能引用本目录中的 `value_prop_id`，不得发明未列出的能力。  
**产品：** Policy-to-Feature Missions（Orchestrator / Worker / Validator + RAG 契约门禁 + 人闸）。  
**权威设计：** 见 `Managerial System/Constitution/DESIGN_PHILOSOPHY.md`。

---

## 使用规则（给模拟 AI）

1. 映射时填写 `value_prop_id`（可多选），并写清映射基数：`1:1` | `1:N` | `N:1` | `N:N`。
2. 每个客户需求至少映射 1 个价值主张；若无法映射，标记 `unmet` 并说明缺口（供后续产品迭代，不编造能力）。
3. 不得把「通用聊天机器人」「无限并行改同一代码库」「Worker 自审自批」写成价值主张。

---

## 价值主张清单

| value_prop_id | 名称 | 对应能力摘要 | 主要不变量 |
|---------------|------|--------------|------------|
| VP-RELAY | 三角色中继协作 | Orchestrator 规划 / Worker 实现 / Validator 只评判，激励分离 | I1 |
| VP-CONTRACT-FIRST | 契约先行 | 先产出 validation contract（行为断言+政策引用），再写功能代码 | I2 |
| VP-LEDGER | 外置账本记忆 | contract / feature list / handoff / Mission Control 持久化，不靠长聊天记忆 | I3 |
| VP-RAG-CITE | 版本化政策 RAG 与引用 | KB 带版本与生效日；断言引用 doc_id/chunk_id/doc_version/retrieval_profile | I3, citation |
| VP-SERIAL-WRITE | 串行写锁 | 共享可变工件上至多一个 Writer；检索/评审可并行 | I4 |
| VP-FAIL-CLOSED | 失败即关闭门禁 | 测试/校验/评分失败不得标 DONE；修订有轮次与预算上限 | I5 |
| VP-HUMAN-LATCH | 高风险人闸 | 资金、对外发布、生产变更等需显式人工批准 | I6 |
| VP-HONEST-AUTONOMY | 诚实自治等级 | L0–L5 可标注；禁止假 commit / 假自治 | I7 |
| VP-THIN-SLICE | 窄垂直切片优先 | 先交付可客观验收的一条薄切片，再扩域 | I8 |
| VP-INDEP-JUDGE | 独立裁判 | Validator 独立检索与黑盒检查；不改被测系统；可换模型/检索画像 | I1, L4 |
| VP-FIX-LOOP | 校验失败开修复单 | Orchestrator 根据 fail report 开 fix feature，禁止 Worker 自绕过 | I1, I5 |
| VP-AUDIT-TRAIL | 全程审计轨迹 | handoff 记录命令、exit code、引用、blocked_for_human | I3, I6 |
| VP-TOOL-ACL | 角色最小权限工具 | Validator 只读/执行检查；Worker 限定 owns_paths；Deployer 无批准令牌不可动 | tooling |
| VP-DOMAIN-SWAP | 同中继换垂直 | 换 KB + contract schema + 人闸动作表即可迁域，ledger 不变 | domain |
| VP-METRICS | 正确性优先指标 | 断言通过率、fix 轮次、逃逸缺陷、引用覆盖率优先于吞吐 | metrics |

---

## 映射记录推荐字段（客户模板中引用）

```yaml
mapping_entry:
  requirement_id: ""          # 对应需求 ID，如 REQ-M-01
  value_prop_ids: []          # 本目录中的 id 列表
  cardinality: ""             # 1:1 | 1:N | N:1 | N:N
  mapping_rationale: ""       # 为何这样映射（1-3 句）
  demo_observable: ""         # 面试/演示时可观察证据（artifact 或门禁行为）
  unmet: false                # true 表示我方当前能力无法覆盖
  unmet_gap: ""               # unmet=true 时必填
```
