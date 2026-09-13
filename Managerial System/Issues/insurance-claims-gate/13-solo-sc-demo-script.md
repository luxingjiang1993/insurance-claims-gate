# 13: Solo Demo / SC 黑盒一键脚本

**Status:** resolved

**Blocked by:** 08, 09

**ref_id:** REF-MISSIONS

**Backlog:** 个人验收（替代真实作业台 UI）

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/` 中 Demo / TestClient 入口（若有） | HTTP 黑盒串场 |
| 2 | `本项目代码/claims-gate/tests/test_sc0*.py` | SC-01/02/03 已有路径，脚本应复用同一语义 |
| 3 | `本项目代码/claims-gate/README.md` | 运行说明挂载点 |

## What to build

为个人开发提供 **无需真实用户** 的验收脚本：对 SC-01、SC-02、SC-03（及关联人闸/citation 负例可选）走 HTTP TestClient 或等价调用，打印简明 pass/fail。  
可与现有 pytest 并存；脚本是「给人看的 Demo」，合门禁仍以 pytest/machine_check 为准。

## Acceptance criteria

- [x] 存在可执行入口（如 `python -m claims_api.demo_sc` 或 `scripts/run_sc_demo.py`）
- [x] 覆盖 SC-01、SC-02、SC-03 主路径；失败时非零退出码
- [x] README 写明一条命令即可跑
- [x] 不引入 L3/支付；不依赖真实 OCR/核心
- [x] handoff 含 `Rewrote from: REF-MISSIONS`

## Answer

落地 `claims_api.demo_sc` + `scripts/run_sc_demo.py`：复用 `machine_check` 类型
`sc01_one_shot_supplement_approve` / `sc02_exclusion_reject_latch` /
`sc03_endorsement_stack_reduction`；`--extras` 跑拆轮与无人闸负例。
命令：`python scripts/run_sc_demo.py`。测试：`tests/test_demo_sc.py`。

## Comments

- 2026-09-13：current-phase-remaining 切票；个人 Demo 替代作业 UI。
- 2026-09-14：实现并 resolved；Rewrote from REF-MISSIONS（Validator/TestClient 黑盒语义）。
