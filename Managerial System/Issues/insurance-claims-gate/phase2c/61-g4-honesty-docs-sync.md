# 61: G4 诚实表 / USER_GUIDE / demo 脚本同步

**github_issue:** #48

**Status:** resolved

**Blocked by:** 57, 58, 59, 60

**wave:** 2c

**spec_id:** SPEC-02C-LIVE-HONEST-SEAMS

**ref_id:** REF-MISSIONS

**Rewrote from:** 既有 interview 包与 `docs/user/MAINTENANCE.md`

## 优先打开（只读参考）

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | `docs/agents/interview-honesty-table.md` | 须与证据翻绿/保持 deferred |
| 2 | `docs/user/MAINTENANCE.md` + USER_GUIDE | 用户可见更新义务 |
| 3 | interview demo / talk-track / S2 指标卡 | Live 分支 + 先剖面后数字 |

## What to build

将 G0/G2/G3 证据同步进诚实表、USER_GUIDE、demo 脚本与 S2 指标卡。开场固定 H4 deferred。对外可用「面试诚实 8 分档」+ 副标题「Integration-Ready」。删除任何「Frontier 空 = 做完 / 已冲 9」暗示。

## Acceptance criteria

- [x] 诚实表：Live / 双剖面 / L2·OCR Adapter Ready 状态正确；H4 仍 deferred；A5/L3/≥300 仍禁宣
- [x] USER_GUIDE + CHANGELOG 按 MAINTENANCE 更新
- [x] demo 脚本含 Live 分支与「先剖面后数字」
- [x] 开场句含 H4 deferred、不宣称 grounded / 面试条 9
- [x] Ready≠Deployed 写清

## Answer

同步 G0/G2/G3 证据到面试包与用户手册（纯文档，无产品代码改动）：

| 工件 | 变更要点 |
|------|----------|
| `docs/agents/interview-honesty-table.md` | 加 G0 Live 行；8 分档 + Integration-Ready；Ready≠Deployed；H4 deferred；禁 A5/L3/≥300/冲 9；Frontier≠做完 |
| `docs/agents/interview-one-pager.md` / `interview-talk-track.md` | 开场含 H4 deferred；删「Frontier 空」暗示；8 分档口径 |
| `docs/agents/interview-demo-script.md` | Live 分支 D′；先剖面后数字 E′；开场 H4 deferred |
| `docs/agents/interview-s2-metrics.md` | 8 分档上下文 + 先剖面后数字强化 |
| `docs/user/USER_GUIDE.md` | 页眉 8 分档；§3.14 2c；成熟度 G0/G2/G3；CHANGELOG Unreleased 含 57–61 |

## Comments

- 2026-09-16：`/to-spec` 切票；Status=ready-for-agent。
- 2026-09-16：同步 GitHub Issue #48。
- 2026-09-16：`/implement` G4 文案同步关闭；Status=resolved。
