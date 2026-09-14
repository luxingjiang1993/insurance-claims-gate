/** 与 Claims Gate HTTP API 对齐的只读浏览类型。 */

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

/** API 拒绝体外形（原样展示，不二次包装文案）。 */
export type ApiErrorBody = {
  detail?: unknown;
  [key: string]: unknown;
};
