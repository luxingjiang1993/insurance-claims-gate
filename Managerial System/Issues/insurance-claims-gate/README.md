# Issues — insurance-claims-gate



任务图：`Blocked by` / `Status`。约定见 `docs/agents/issue-tracker.md`。SPEC：`Managerial System/SPEC/insurance-claims-gate/spec.md`。  

当前阶段门禁清单：`docs/agents/current-phase-remaining.md`（进阶段 2 前读）。



## Frontier（可立即开工）



| NN | 文件 | Blocked by |

|----|------|------------|

| 12 | `12-track-b-min-rag.md` | 09（已 resolved） |

| 13 | `13-solo-sc-demo-script.md` | 08, 09（已 resolved） |



**建议顺序：** 12 与 13 可并行（不同目录时注意写锁）。



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

| 10 | Eval / 机检负例入口（不替代 machine_check） | 09 | resolved |

| 11 | Judge–human 合成抽检占位（P1-7） | 10 | resolved |

| 12 | 轨 B 最小检索起草（RAG-CY） | 09 | open |

| 13 | Solo Demo / SC 黑盒一键脚本 | 08, 09 | open |



```text

01–09 （已闭环）

09 ──┬── 10 ── 11

     ├── 12

08 ──┴── 13

```



实现只写入 `本项目代码/claims-gate/`。每张票含 **优先打开（只读参考）** 表；路径相对于 `历史项目代码供参考/`。开工前将对应票 `Status` 改为 `claimed`。



**延后（不进本阶段 Frontier）：** 真实用户 OUT 基线、≥300 金标运营、§14 客户签字关闭、真连 L2、真实 OCR、作业 UI 壳 —— 见 `docs/agents/current-phase-remaining.md` §0。


