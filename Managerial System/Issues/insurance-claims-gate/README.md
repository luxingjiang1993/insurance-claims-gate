# Issues — insurance-claims-gate

任务图：`Blocked by` / `Status`。约定见 `docs/agents/issue-tracker.md`。SPEC：`Managerial System/SPEC/insurance-claims-gate/spec.md`。

## Frontier（可立即开工）

| NN | 文件 | Blocked by |
|----|------|------------|
| — | （本期 P0/P1 实现票已清空） | — |

## 全量任务图

| NN | 标题 | Blocked by | Status |
|----|------|------------|--------|
| 01 | Missions 换垂直脚手架 + 理赔 HTTP 空壳 + machine_check 分发器 | — | resolved |
| 02 | 条款 KB 最小集 + citation 条款项落库门 | 01 | resolved |
| 03 | SC-01 一次补件 → 补传 → 通赔建议（轨 A） | 01 | resolved |
| 04 | SC-02 除外拒赔草案 + 文书分态 + 人闸 | 01, 02 | resolved |
| 05 | SC-03 效力栈减赔 + 理算步骤 | 01, 02 | resolved |
| 06 | 人闸权限矩阵扩展（金额档 / 通融 / 预赔 / 调查冻决） | 03, 04, 05 | resolved |
| 07 | Router 确定性策略表 + 冲突 fail-closed + ledger | 03, 04, 05 | resolved |
| 08 | L2 出款就绪回写模拟（无人闸禁放行） | 04, 06 | resolved |
| 09 | 轨 B 隔离占位 + 威胁负例机检 | 03, 04, 05 | resolved |

```text
01
 ├── 03
 └── 02 ──┬── 04 ──┐
          └── 05 ──┼── 06 ── 08
                   ├── 07
                   └── 09
```

实现只写入 `本项目代码/claims-gate/`。每张票含 **优先打开（只读参考）** 表；路径相对于 `历史项目代码供参考/`。开工前将对应票 `Status` 改为 `claimed`。
