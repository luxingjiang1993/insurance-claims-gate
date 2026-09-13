# User docs maintenance（阶段完结必更新）

本目录是 **Claims Gate 用户操作手册** 的唯一真源。工程 README、PRD、SPEC 不替代本手册；本手册也不覆盖内部改写细节。

## 何时必须更新

任一下列事件发生后，**同一变更集**内更新用户文档（不得拖到下阶段）：

| 触发 | 最少更新 |
|------|----------|
| 阶段 DoD 关闭（如 `current-phase-remaining.md` §1 勾选完成） | `CHANGELOG.md` 折叠 Unreleased → 新/现有 Phase 节；`USER_GUIDE.md` §2.3 成熟度表 + Quickstart/How-to 与现状一致；页眉 Last updated |
| Issue `resolved` 且改变用户可见行为（新端点、状态、人闸规则、文书分态、Demo 命令、Won't 边界） | `USER_GUIDE.md` 对应 How-to / Reference；`CHANGELOG.md` Unreleased 追加一条 |
| 公开错误码 / 夹具 case_id 增减 | `USER_GUIDE.md` §7 |
| 作业 UI 或真连 L2 首次交付 | 重写 §3 Quickstart 与 §5（从「HTTP 为主」改为「屏 → 动作」）；成熟度徽章升级 |
| PRD Won't / 人闸默认表变更且已入 SPEC | §2.2、§6 与 Safety checklist |

**不需要**为纯内部重构、仅测试、仅 REF 改写备注更新用户手册——除非用户命令或 API 契约变了。

## 完成标准（DoD 片段）

更新算完成，当且仅当：

1. `USER_GUIDE.md` 中操作步骤在当前代码上可执行（或明确标 `Deferred`）。
2. `CHANGELOG.md` 有对应该阶段/Unreleased 的用户可读条目（动词：Added / Changed / Deprecated / Removed）。
3. 手册不声称未交付能力为已上线（禁止用「秒赔」等禁词包装）。
4. 若阶段文件存在：在阶段 DoD 中勾选「用户手册已同步」。

## 写边界

| 可写 | 路径 |
|------|------|
| 用户手册 | `docs/user/**` |

中文正文 UTF-8；结构保持硅谷 docs 习惯：Start here → Quickstart → Concepts → How-to → Reference → Changelog。

## Agent 指针

- 仓库入口：`AGENTS.md`「用户手册」节  
- Resolve 票时：`docs/agents/issue-tracker.md` 用户文档检查项  
- 阶段门禁：`docs/agents/current-phase-remaining.md` DoD
