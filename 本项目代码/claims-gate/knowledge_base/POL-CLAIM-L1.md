# 个人意外险条款门禁 — L1 脚手架样例

文档 ID: POL-CLAIM-L1
文档版本: 1.0
生效日: 2026-01-01
文档类型: handbook
效力层级: 60

## POL-CLAIM-001 材料受理与案件头只读
条款项: POL-CLAIM-001

立案后系统须能只读拉到案件头最低字段（案件号、保单号、产品代码、条款版本、出险日等），
并将门禁状态置于 MATERIALS_INTAKE（材料受理中）。

默认推理轨为确定性轨（inference_track=deterministic）。
支付类工具默认无权限；本期不做银企直连或自动出款。

## POL-CLAIM-002 一次补件与通赔建议
条款项: POL-CLAIM-002

材料不齐时须进入 PENDING_SUPPLEMENT，一次列出全部缺项并生成稳定 one_shot_hash；
同 hash 下禁止拆轮重发或缺项增减。补件通知须含缺项中文名、是否必须、示例说明，
并固定引用《保险法》第二十二条一次性补正义务说明。

客户补齐后重评可产出通赔建议（approve_recommend）裁决草案；
未取得人闸令牌前 payout_ready 必须为 false。补件文书 DRAFT_EXPORT 可无人闸导出。
