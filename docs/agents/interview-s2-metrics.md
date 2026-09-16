# Claims Gate — S2 指标卡（N11）

来源：`docs/user/USER_GUIDE.md` §3.6 / §3.12。旁路分数 **不是** 合门禁。  
档位上下文：面试诚实 **8** 分档；**先剖面后数字**；H4 **deferred**（禁止 grounded / 面试条 9）。

| 项 | 记录 |
|----|------|
| **先剖面后数字** | 面试口头强制：先报测量剖面，再报 Recall / MRR |
| 剖面 A | `demo_seed_eval`；**向量腿关闭**（关键词 / 条款号短路） |
| 剖面 B | `pilot_cloud_embed`；**向量腿开启**（有 embedding Key 时可跑） |
| 种子 | 冻结 Demo 检索种子（**非金标**） |
| **H1**（demo 基线记录） | Recall@1 = **1.00**（n=15）；门槛 ≥ 0.95（条款号子集） |
| **H2**（demo 基线记录） | Recall@5 = **1.00** / MRR ≈ **0.892**（n=20）；门槛 Recall@5 ≥ 0.70 **或** MRR ≥ 0.55 |
| 复现 | `python scripts/run_recall_metrics_s2.py`（默认双剖面；`本项目代码/claims-gate/`） |
| 进默认绿？ | **否**。失败只红质量旁路退出码，不红轨 A |
| vs 合门禁 | 召回分 / 榜分 **≠** `machine_check` |
| **H4** | **deferred**（薄切片 n&lt;10；禁止宣称 grounded） |
| γ | **未上线**；仅当 `pilot_cloud_embed` 上 H2 失败才允许另议 |
| 不是什么 | **禁止**把无剖面标签的短路 1.00 说成语义满分；demo 基线满分 ≠ 语义满分 |

口头：数字有，但是要先说剖面。`demo_seed_eval` 是可复现基线；`pilot_cloud_embed` 才是向量开的 Pilot 语义对照。
