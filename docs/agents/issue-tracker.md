# Issue tracker: Local Markdown（Managerial System 映射）

本仓**不使用** Matt Pocock 默认的 `.scratch/` 路径。Issues 与 SPEC 落在 `Managerial System/` 下，语义对齐 local-markdown tracker（任务图、`Blocked by`、`Status`、frontier）。

日后建立 git remote 并迁 GitHub Issues 时，再运行 `/setup-matt-pocock-skills` 切换；迁移前以本文件为准。

## Conventions

- 一个 feature 一个 slug 目录；首个切片：`insurance-claims-gate`
- SPEC：`Managerial System/SPEC/<feature-slug>/spec.md`
- Implementation tickets：`Managerial System/Issues/<feature-slug>/<NN>-<slug>.md`，自 `01` 起编号；**禁止**把多票写进单一合并文件
- 票首建议字段：`Status:`、`Blocked by:`、`ref_id:`（一个或多个，见 `docs/agents/ref-projects.md`）
- 需求真源 PRD：`Managerial System/PRD/`（本 tracker 不存放 PRD）
- Triage 状态：每个 issue 文件顶部附近一行 `Status:`（词汇见本机 `setup-matt-pocock-skills/triage-labels.md`，若已安装 triage skill）
- 评论：文件末尾 `## Comments` 下追加
- 当前阶段剩余 / 进阶段 2：`docs/agents/current-phase-remaining.md`（与 `Issues/insurance-claims-gate/10`–`13` 对齐）
- 用户操作手册：`docs/user/`（阶段 DoD / 用户可见 Resolve 时必同步）

## When a skill says "publish to the issue tracker"

在 `Managerial System/Issues/<feature-slug>/` 或 `Managerial System/SPEC/<feature-slug>/` 创建文件（目录不存在则创建）。

## When a skill says "fetch the relevant ticket"

读取用户给出的路径或 `NN` 对应文件。

## Wayfinding operations

- **Map**（若使用 wayfinder）：`Managerial System/Issues/<effort>/map.md`
- **Child ticket**：`Managerial System/Issues/<effort>/<NN>-<slug>.md`；`Type:` 为 `research` / `prototype` / `grilling` / `task`；`Status:` 为 `claimed` / `resolved`（实现票也可使用 triage 角色字符串）
- **Blocking**：文件顶部 `Blocked by: NN, NN`；所列文件均为 `resolved` 后才解阻
- **Frontier**：扫描目录中 open、未阻塞、未 claimed 的文件；编号小者优先
- **Claim**：开工前先写 `Status: claimed` 并保存
- **Resolve**：在 `## Answer` 下写结论，`Status: resolved`，并在 map 的 Decisions-so-far 追加指针（若有 map）
- **用户手册（若本票改变用户可见行为）**：按 `docs/user/MAINTENANCE.md` 更新 `USER_GUIDE.md` 与 `CHANGELOG.md` Unreleased；阶段关闭时再折叠进对应 Phase 节。纯内部重构可跳过

## Implement-spec 对齐

`implement-spec` 假定：已有 SPEC，且 tickets 为带阻塞关系的任务图。本仓对应关系：

1. 读 `Managerial System/SPEC/insurance-claims-gate/spec.md`
2. 读 `Managerial System/Issues/insurance-claims-gate/*.md` 作为 ticket 图
3. 实现只写入 `本项目代码/claims-gate/`；不得改 `历史项目代码供参考/` 作为交付
4. 改写前按票内 `ref_id` 打开 `docs/agents/ref-projects.md` 对应文件夹；主中继/合门禁默认 `REF-MISSIONS`
5. 新票 `ref_id` 须落在「本期仍可供改写」或既有占用票路径内；扩面 REF 须先有正式 SPEC/PRD，不得仅凭 `ref-projects-phase2-supplement.md` 切实现票
