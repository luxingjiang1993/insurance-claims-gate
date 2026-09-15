/** 与 Claims Gate HTTP API 对齐的作业壳类型。 */

export type LoginResult = {
  session_token: string;
  username: string;
  role: string;
  display_name: string;
};

export type ClaimSummary = {
  case_id: string;
  policy_no: string;
  product_code: string;
  claim_amount_claimed: number;
  gate_status: string;
  inference_track: string;
  document_status: string | null;
  payout_ready: boolean;
};

export type ClaimDetail = ClaimSummary & {
  clause_version: string;
  endorsement_flags: string[];
  loss_date: string;
  image_ids: string[];
  material_codes: string[];
  ocr_text?: string;
  customer_remark?: string;
};

/** 一次补件清单项（字段以服务端 machine_check / evaluate 响应为准）。 */
export type SupplementItem = {
  code: string;
  name_zh?: string;
  required?: boolean;
  example?: string;
};

/** 裁决草案：规则路径 evaluate / GET decision 的可观察字段。 */
export type DecisionDraft = {
  case_id?: string;
  decision_type: string;
  gate_status: string;
  document_status: string | null;
  payout_ready: boolean;
  inference_track: string;
  one_shot_hash?: string | null;
  supplement_checklist?: SupplementItem[];
  remaining_missing?: SupplementItem[];
  citations?: unknown[];
  calc_steps?: unknown[];
  appeal_path?: string | null;
  reason_summary?: string | null;
  human_latch_required?: boolean;
  human_latch_token?: string | null;
  dual_token_required?: boolean;
  latch_level_label?: string | null;
};

export type MaterialsRegisterResult = {
  case_id: string;
  material_codes: string[];
  image_ids: string[];
  gate_status: string;
  ocr_text?: string | null;
  customer_remark?: string | null;
};

export type SupplementNotifyResult = {
  case_id?: string;
  document_type?: string;
  document_status?: string;
  one_shot_hash?: string;
  legal_basis?: string;
  missing_items?: SupplementItem[];
};

export type HumanLatchApproveResult = {
  case_id: string;
  human_latch_token: string;
  human_approver: string;
  payout_ready: boolean;
  gate_status: string;
  decision_type?: string;
  dual_token_required?: boolean;
  second_approver?: string | null;
};

export type HumanLatchRejectResult = {
  case_id: string;
  gate_status: string;
  human_latch_token: string | null;
  payout_ready: boolean;
  rejected_by: string;
  reason?: string;
};

export type DocumentExportResult = {
  document_type: string;
  document_status: string;
  case_id?: string;
  payout_ready?: boolean;
  [key: string]: unknown;
};

/** assist 返回的检索提名（字段以 API 为准；adoptable 由服务端三联门标记）。 */
export type AssistCitation = {
  doc_id?: string;
  clause_item?: string;
  doc_version?: string;
  title?: string;
  quote?: string;
  adoptable?: boolean;
  reject_reason?: string;
  [key: string]: unknown;
};

/** AI 辅助建议：POST /assist 响应；非裁决草案权威字段。 */
export type AssistSuggestion = {
  case_id?: string;
  assist_invocation_id: string;
  inference_track: string;
  query: string;
  retrieval_profile: string;
  draft_text: string;
  used_llm: boolean;
  degraded: boolean;
  degrade_reason?: string | null;
  suggested_stance?: string;
  citations?: AssistCitation[];
  retrieval?: Record<string, unknown>;
  notes?: string[];
  payout_ready?: boolean;
  human_latch_token?: string | null;
  enable_llm?: boolean;
  human_latch_required?: boolean;
  /** draft=可考虑采纳；abstain=辅助拒答，禁用采纳 */
  assist_disposition?: "draft" | "abstain";
  abstain_reason?:
    | "conflict"
    | "handbook_alone"
    | "low_confidence"
    | "citation_unfaithful"
    | null;
  /** 可提示走人闸，但 API 永不自动签发令牌 */
  human_latch_suggested?: boolean;
};

/** API 拒绝体外形（原样展示，不二次包装文案）。 */
export type ApiErrorBody = {
  detail?: unknown;
  [key: string]: unknown;
};

/** 本案流水 ledger 条目（evaluate / assist / latch 等可回放）。 */
export type LedgerEntry = {
  case_id: string;
  route_id: string;
  retrieval_profile: string;
  decision_type: string;
  validator_score: number;
  ts: string;
  arbitration_winner?: string | null;
  /** LangSmith run/trace id；有上报时存在。 */
  trace_id?: string | null;
};

export type LatchEventRow = {
  case_id: string;
  event_type: string;
  actor: string;
  ts: string;
  human_latch_token?: string | null;
  reason?: string;
  second_approver?: string | null;
};

/** 评测跑次（POST/GET /eval/runs；旁路，非合门禁）。 */
export type EvalRunRecord = {
  run_id: string;
  actor_user_id: string;
  experiment_name: string;
  experiment_id: string | null;
  dataset_name: string;
  summary: Record<string, unknown>;
  cases: unknown[];
  created_at: string;
  langsmith_degraded: boolean;
  gate_role?: string;
  blocks_track_a_gate?: boolean;
};

export type EvalRunListResult = {
  runs: EvalRunRecord[];
  filter_actor_user_id: string | null;
  gate_role?: string;
  blocks_track_a_gate?: boolean;
};

/** 排行榜一行（GET /eval/leaderboard）。 */
export type EvalLeaderboardRow = {
  experiment_name: string;
  primary_metric: number;
  primary_metric_name: string;
  created_at: string;
  submitter: string;
  run_id: string;
  gate_role?: string;
  blocks_track_a_gate?: boolean;
};

export type EvalLeaderboardResult = {
  rows: EvalLeaderboardRow[];
  sort_by: string;
  order: string;
  primary_metric_name: string;
  data_source: string;
  gate_role?: string;
  blocks_track_a_gate?: boolean;
};

/** 金标数据集钩子行（须含 case_id；非双人全量运营）。 */
export type GoldLabelRecord = {
  case_id: string;
  inputs: Record<string, unknown>;
  expected: Record<string, unknown>;
  notes?: string;
};

export type GoldLabelImportResult = {
  dataset_id: string;
  imported_count: number;
  gold_ops_complete: boolean;
  dual_annotation_workflow?: boolean;
  gate_role?: string;
  blocks_track_a_gate?: boolean;
};

export type GoldLabelExportResult = {
  dataset_id: string;
  records: GoldLabelRecord[];
  gold_ops_complete: boolean;
  dual_annotation_workflow?: boolean;
  docs_note?: string;
  schema?: string;
  gate_role?: string;
  blocks_track_a_gate?: boolean;
};
