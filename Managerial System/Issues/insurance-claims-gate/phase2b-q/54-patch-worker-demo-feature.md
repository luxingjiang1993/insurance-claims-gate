# 54: Q-A3 Patch-capable Worker + F-Q-DEMO-01

**github_issue:** #41

**Status:** resolved

**Blocked by:** 53

**wave:** 2b-Q

**spec_id:** SPEC-02B-Q-RELAY-A2A3

**ref_id:** REF-MISSIONS

**Rewrote from:** REF-MISSIONS → 宪法 A3（worktree / diff / commit / owns_paths+lock）

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 / 说明 | 看什么 |
|--------|-------------|--------|
| 1 | `project 多agent`（REF-MISSIONS） | Worker 写锁、handoff、VCS 交接 |
| 2 | SPEC-02B-Q「流 Q 待写入」/ Implementation Decisions | `F-Q-DEMO-01` 与 owns_paths 信封 |
| 3 | 现有 `test_missions_empty_loop.py` / OCR 提权测 | 接缝升级点 |

## What to build

把 Worker 升到宪法 **A3**：在 worktree 内真实改文件、可检视 diff、handoff 含非空 `git_commit` 与 `files_touched`；`owns_paths`+写锁 fail-closed。示范单特性 **`F-Q-DEMO-01`**：OCR/备注吸收时 strip 首尾空白，不改人闸/payout 字段。空 diff / `git_commit=null` / 越权路径不得标 `DONE`。实现 harness 能力 ≠ 使命内可改 Orchestrator/Validator。

## Acceptance criteria

- [x] `F-Q-DEMO-01` 跑通：非空 commit；`files_touched` ⊆ owns_paths（Q-S0-B）
- [x] 空 diff / null commit / 硬禁路径 → 不得 DONE
- [x] 写锁争用 fail-closed
- [x] strip 行为可测；既有 OCR 提权负例仍绿（Q-S1）
- [x] worktree 测用临时本地 git，不绑远端、不要求 LLM Key
- [x] 默认 `pytest -q` 仍绿；handoff 含 `Rewrote from:`
- [x] 未改 `track_llm_optional`；未与 P 共用完成旗

## Answer

- 产品：`absorb_user_controlled_text` 对 OCR/备注 `.strip()`（全空白→空串）；人闸/payout 字段不碰。测：`tests/test_user_text_strip.py`；既有 `test_threat_inject_ocr_remark.py` 仍绿。
- Worker A3：`F-Q-DEMO-01` 在 worktree 内对 `user_text` 做 strip 变换 + `git_commit_paths`；handoff 非空 `git_commit` / `files_touched` ⊆ owns_paths；空 diff / null commit / 越权 → `BLOCKED`。硬禁 `owns_paths` → `OwnsPathError`；A3 额外强制允许上界（claims_api + 配对 test_*）；写锁争用 → `WriterLockError`。
- 新增 `missions/git_util.py`、`missions/owns_paths.py`；测：`tests/test_patch_worker_demo.py`（临时本地 git）。脚手架 Worker 路径保持烟雾测（不绑架既有空回路）。
- 默认 `pytest -q`：309 passed。未改 `track_llm_optional`。用户可见：`docs/user/CHANGELOG.md` Unreleased + `USER_GUIDE` OCR/备注 strip 一句。`Rewrote from: REF-MISSIONS`。

## Comments

- 2026-09-16：`/to-spec` 切票；Status=ready-for-agent。
- 2026-09-16：同步 GitHub Issue #41。
- 2026-09-16：`/implement` 落地 A3 Worker + F-Q-DEMO-01；Status=resolved。
