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

/** API 拒绝体外形（原样展示，不二次包装文案）。 */
export type ApiErrorBody = {
  detail?: unknown;
  [key: string]: unknown;
};
