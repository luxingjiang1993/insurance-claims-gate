# 06: 人闸权限矩阵扩展（金额档 / 通融 / 预赔 / 调查冻决）

**Status:** ready-for-agent

**Blocked by:** 03, 04, 05

**ref_id:** REF-MISSIONS

**Backlog:** （PRD §7；消费 SPEC 人闸决策）

**Rewrote from:** REF-MISSIONS

## 优先打开（只读参考）

路径相对于 `历史项目代码供参考/`。交付只写入 `本项目代码/claims-gate/`。

| 优先级 | 路径 | 看什么 |
|--------|------|--------|
| 1 | `project 多agent/src/missions/runner.py` | 人闸批准/阻塞相位扩展点 |
| 2 | `project 多agent/src/missions/models.py` | `HumanApproval` 字段；扩展为金额档/决定类型矩阵 |
| 3 | `project 多agent/src/transfer_api/limits.py` | **档位阈值 + error_code** 表驱动模式（映射核赔金额档） |
| 4 | `project 多agent/src/transfer_api/service.py` | 超限拒绝、状态不变的领域门禁写法 |
| 5 | `project 多agent/src/missions/checks.py` | 通融伪 citation、调查冻决、金额档人闸的新 check types |
| 6 | `project 多agent/src/missions/validator.py` | 校验失败 → 人闸 / 不开完成 |
| 7 | `project 多agent/tests/compliance/test_audit_failures.py` | 负例/合规失败断言风格 |

权限表数值以 PRD §7 为准，不要从转账限额数字照搬。

## What to build

在 SC 人闸基础设施之上落地试点权限表：通赔建议/减赔按金额档决定是否人闸；拒赔对外、通融、预赔默认必闸；诉讼/信访/媒体等敏感场景权限至少上浮一档。通融决定必须人闸，且禁止伪「主险条款通赔」citation。风险超阈进入调查中时自动冻决且不得出款就绪；解除冻决必须人闸。峰值降级只能变为补件+排队人审，禁止静默自动通赔。

## Acceptance criteria

- [ ] 通赔/减赔小额档与大额档对人闸要求的差异可经 HTTP + machine_check 区分验收
- [ ] 通融、预赔无人闸不得 `payout_ready`，通融伪主险通赔 citation 负例失败
- [ ] 进入调查中自动冻决；解除冻决无人闸失败；冻决期间 `payout_ready=false`
- [ ] 敏感场景上浮至少一档可机检（夹具或参数化断言）
- [ ] 峰值降级路径仅允许补件+人审队列，不出现静默通赔
- [ ] handoff 含 `Rewrote from: REF-MISSIONS`

## Comments

- 2026-09-13：to-tickets 批准 defaults 后落盘。
