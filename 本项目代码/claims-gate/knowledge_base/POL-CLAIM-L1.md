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

## POL-CLAIM-003 除外拒赔草案与文书分态人闸
条款项: POL-CLAIM-003

疾病导致摔伤等除外案须产出拒赔草案（reject_draft），责任/除外引用须落库到条款项
（doc_id + clause_item + doc_version）；拒赔文书须含 appeal_path。

文书效力分态：DRAFT_EXPORT 可无人闸供内部预览；升 EXTERNAL_NOTIFY 必须持有有效
human_latch_token，否则 API 拒绝（LATCH_REQUIRED 或 DOCUMENT_STATUS_FORBIDDEN）。
无人闸时 payout_ready 恒为 false；人闸批准后可对外通知语义，但仍不触发银企出款。
人闸驳回后回编辑态可再提。叙事禁止以「秒赔」包装责任争议案。

## POL-CLAIM-004 效力栈减赔与理算步骤
条款项: POL-CLAIM-004

批单缩小责任时须产出减赔草案（reduce），引用服从效力栈：批单优于主险；
每条 citation 须含 doc_id、条款项、版本/生效日与 authority_rank，被覆盖条款须暴露 overridden_by。

免赔额与赔付比例以可复核 calc_steps 呈现；与批单条款冲突则失败关闭，禁止静默改数。
减赔通知 DRAFT_EXPORT 复用 citations 与 calc_steps；未人闸前 payout_ready 必须为 false。
检索画像 endorsement_priority 须先查批单再主险。

## POL-CLAIM-005 Router 确定性策略表与 ledger
条款项: POL-CLAIM-005

Router 为 Missions 硬层确定性策略表，禁止写成独立 LLM 核赔角色。
多路由冲突按 Human > Invest > Rules > RAG > OCR 仲裁；
规则与条款 RAG 结论冲突时失败关闭进人闸，不静默采信一侧。
handbook_ops 不得单独作为对外拒赔唯一依据。
每案 ledger 须记录 route_id、retrieval_profile、decision_type、validator_score；
轨 A 下同一夹具重复跑 Router 结果须可复现。
