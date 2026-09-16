/**
 * 作业壳 HTTP 客户端：直连 Claims API，无 BFF；错误体原样抛出。
 * Rewrote from: REF-MISSIONS, REF-CASE-HYBRID
 */

import type {
  AssistCitation,
  AssistSuggestion,
  ClaimDetail,
  ClaimSummary,
  DecisionDraft,
  DocumentExportResult,
  EvalLeaderboardResult,
  EvalRunListResult,
  EvalRunRecord,
  GoldLabelExportResult,
  GoldLabelImportResult,
  HumanLatchApproveResult,
  HumanLatchRejectResult,
  LatchEventRow,
  LedgerEntry,
  LoginResult,
  MaterialsRegisterResult,
  ProviderConnectionStatus,
  SupplementNotifyResult,
} from "./types";

export type ClaimsApiClientOptions = {
  baseUrl: string;
  getToken: () => string | null;
  fetchImpl?: typeof fetch;
};

export class ApiClientError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, body: unknown) {
    super(`API ${status}`);
    this.name = "ApiClientError";
    this.status = status;
    this.body = body;
  }
}

function trimSlash(url: string): string {
  return url.replace(/\/+$/, "");
}

async function parseBody(resp: Response): Promise<unknown> {
  const text = await resp.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export function createClaimsApiClient(options: ClaimsApiClientOptions) {
  const baseUrl = trimSlash(options.baseUrl);
  const doFetch = options.fetchImpl ?? fetch;

  async function request<T>(
    path: string,
    init: RequestInit & { auth?: boolean } = {},
  ): Promise<T> {
    const headers = new Headers(init.headers);
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    const auth = init.auth !== false;
    if (auth) {
      const token = options.getToken();
      if (token) {
        headers.set("Authorization", `Bearer ${token}`);
      }
    }
    const { auth: _auth, ...rest } = init;
    const resp = await doFetch(`${baseUrl}${path}`, {
      ...rest,
      headers,
    });
    const body = await parseBody(resp);
    if (!resp.ok) {
      throw new ApiClientError(resp.status, body);
    }
    return body as T;
  }

  return {
    async login(username: string, password: string): Promise<LoginResult> {
      return request<LoginResult>("/auth/login", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ username, password }),
      });
    },

    async listClaims(): Promise<ClaimSummary[]> {
      const body = await request<{ items: ClaimSummary[] }>("/claims", {
        method: "GET",
      });
      return body.items;
    },

    async getClaim(caseId: string): Promise<ClaimDetail> {
      return request<ClaimDetail>(`/claims/${encodeURIComponent(caseId)}`, {
        method: "GET",
      });
    },

    async evaluateClaim(caseId: string): Promise<DecisionDraft> {
      return request<DecisionDraft>(
        `/claims/${encodeURIComponent(caseId)}/evaluate`,
        {
          method: "POST",
          body: JSON.stringify({}),
        },
      );
    },

    async registerMaterials(
      caseId: string,
      body: { material_codes: string[]; image_ids?: string[] },
    ): Promise<MaterialsRegisterResult> {
      return request<MaterialsRegisterResult>(
        `/claims/${encodeURIComponent(caseId)}/materials`,
        {
          method: "POST",
          body: JSON.stringify(
            body.image_ids === undefined
              ? { material_codes: body.material_codes }
              : {
                  material_codes: body.material_codes,
                  image_ids: body.image_ids,
                },
          ),
        },
      );
    },

    async notifySupplement(
      caseId: string,
      body: { one_shot_hash: string; missing_item_codes: string[] },
    ): Promise<SupplementNotifyResult> {
      return request<SupplementNotifyResult>(
        `/claims/${encodeURIComponent(caseId)}/supplement/notify`,
        {
          method: "POST",
          body: JSON.stringify({
            one_shot_hash: body.one_shot_hash,
            missing_item_codes: body.missing_item_codes,
          }),
        },
      );
    },

    async getDecision(caseId: string): Promise<DecisionDraft> {
      return request<DecisionDraft>(
        `/claims/${encodeURIComponent(caseId)}/decision`,
        {
          method: "GET",
        },
      );
    },

    async approveHumanLatch(
      caseId: string,
      body: { approved_by: string; second_approver?: string },
    ): Promise<HumanLatchApproveResult> {
      const payload: { approved_by: string; second_approver?: string } = {
        approved_by: body.approved_by,
      };
      if (body.second_approver) {
        payload.second_approver = body.second_approver;
      }
      return request<HumanLatchApproveResult>(
        `/claims/${encodeURIComponent(caseId)}/human-latch/approve`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
    },

    async rejectHumanLatch(
      caseId: string,
      body: { rejected_by: string; reason?: string },
    ): Promise<HumanLatchRejectResult> {
      return request<HumanLatchRejectResult>(
        `/claims/${encodeURIComponent(caseId)}/human-latch/reject`,
        {
          method: "POST",
          body: JSON.stringify({
            rejected_by: body.rejected_by,
            reason: body.reason ?? "",
          }),
        },
      );
    },

    async exportDocument(
      caseId: string,
      body: {
        document_type: string;
        document_status: string;
        human_latch_token?: string;
      },
    ): Promise<DocumentExportResult> {
      const payload: {
        document_type: string;
        document_status: string;
        human_latch_token?: string;
      } = {
        document_type: body.document_type,
        document_status: body.document_status,
      };
      if (body.human_latch_token) {
        payload.human_latch_token = body.human_latch_token;
      }
      return request<DocumentExportResult>(
        `/claims/${encodeURIComponent(caseId)}/documents/export`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
    },

    /** 显式触发 AI 辅助建议；无 Key 时服务端降级，壳不静默调用。 */
    async assistClaim(
      caseId: string,
      body: { query: string; retrieval_profile?: string; top_k?: number },
    ): Promise<AssistSuggestion> {
      const payload: {
        query: string;
        retrieval_profile?: string;
        top_k?: number;
      } = { query: body.query };
      if (body.retrieval_profile !== undefined) {
        payload.retrieval_profile = body.retrieval_profile;
      }
      if (body.top_k !== undefined) {
        payload.top_k = body.top_k;
      }
      return request<AssistSuggestion>(
        `/claims/${encodeURIComponent(caseId)}/assist`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
    },

    /** 采纳辅助建议：携带 citation（Schema 三联槽）；服务端过门后再 evaluate。 */
    async adoptAssist(
      caseId: string,
      body: {
        assist_invocation_id?: string;
        draft_text?: string;
        suggested_stance?: string;
        retrieval_profile?: string;
        citations?: AssistCitation[];
      },
    ): Promise<DecisionDraft> {
      const payload: {
        assist_invocation_id?: string;
        draft_text?: string;
        suggested_stance?: string;
        retrieval_profile?: string;
        citations?: AssistCitation[];
      } = {};
      if (body.assist_invocation_id !== undefined) {
        payload.assist_invocation_id = body.assist_invocation_id;
      }
      if (body.draft_text !== undefined) {
        payload.draft_text = body.draft_text;
      }
      if (body.suggested_stance !== undefined) {
        payload.suggested_stance = body.suggested_stance;
      }
      if (body.retrieval_profile !== undefined) {
        payload.retrieval_profile = body.retrieval_profile;
      }
      if (body.citations !== undefined) {
        payload.citations = body.citations;
      }
      return request<DecisionDraft>(
        `/claims/${encodeURIComponent(caseId)}/assist/adopt`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
    },

    /** 本案流水：evaluate / assist / latch 等关键动作摘要（最新在前）。 */
    async getLedger(caseId: string): Promise<LedgerEntry[]> {
      const body = await request<{ case_id: string; items: LedgerEntry[] }>(
        `/claims/${encodeURIComponent(caseId)}/ledger`,
        { method: "GET" },
      );
      return body.items;
    },

    /** 人闸事件明细（批准/驳回可回放）。 */
    async getLatchEvents(caseId: string): Promise<LatchEventRow[]> {
      const body = await request<{ case_id: string; items: LatchEventRow[] }>(
        `/claims/${encodeURIComponent(caseId)}/latch-events`,
        { method: "GET" },
      );
      return body.items;
    },

    /** 触发评测跑次并持久化（OpenEval 旁路；actor 取自会话）。 */
    async createEvalRun(body: {
      experiment_name?: string;
      dataset_name?: string;
    }): Promise<EvalRunRecord> {
      const payload: { experiment_name?: string; dataset_name?: string } = {};
      if (body.experiment_name !== undefined) {
        payload.experiment_name = body.experiment_name;
      }
      if (body.dataset_name !== undefined) {
        payload.dataset_name = body.dataset_name;
      }
      return request<EvalRunRecord>("/eval/runs", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },

    /** 列出评测跑次；可按 actor_user_id 过滤（多人互不覆盖）。 */
    async listEvalRuns(options?: {
      actor_user_id?: string;
    }): Promise<EvalRunListResult> {
      const qs = new URLSearchParams();
      if (options?.actor_user_id) {
        qs.set("actor_user_id", options.actor_user_id);
      }
      const suffix = qs.toString() ? `?${qs.toString()}` : "";
      return request<EvalRunListResult>(`/eval/runs${suffix}`, {
        method: "GET",
      });
    },

    /** 评测排行榜：本地 eval_runs 真源；可按主指标升降序。 */
    async getEvalLeaderboard(options?: {
      order?: "asc" | "desc";
    }): Promise<EvalLeaderboardResult> {
      const order = options?.order ?? "desc";
      const qs = new URLSearchParams({ order });
      return request<EvalLeaderboardResult>(
        `/eval/leaderboard?${qs.toString()}`,
        { method: "GET" },
      );
    },

    /** 金标数据集导入钩子（须含 case_id；不宣称运营完成）。 */
    async importGoldLabels(body: {
      dataset_id: string;
      records: Array<{
        case_id: string;
        inputs?: Record<string, unknown>;
        expected?: Record<string, unknown>;
        notes?: string;
      }>;
    }): Promise<GoldLabelImportResult> {
      return request<GoldLabelImportResult>("/eval/gold-labels/import", {
        method: "POST",
        body: JSON.stringify(body),
      });
    },

    /** 金标数据集导出钩子；可按 dataset_id / case_id 过滤。 */
    async exportGoldLabels(options?: {
      dataset_id?: string;
      case_id?: string;
    }): Promise<GoldLabelExportResult> {
      const qs = new URLSearchParams();
      if (options?.dataset_id) {
        qs.set("dataset_id", options.dataset_id);
      }
      if (options?.case_id) {
        qs.set("case_id", options.case_id);
      }
      const suffix = qs.toString() ? `?${qs.toString()}` : "";
      return request<GoldLabelExportResult>(
        `/eval/gold-labels/export${suffix}`,
        { method: "GET" },
      );
    },

    /** 只读连接状态：已配置？降级？模型名？永不回显 Key。 */
    async getProviderConnectionStatus(): Promise<ProviderConnectionStatus> {
      return request<ProviderConnectionStatus>("/provider/connection-status", {
        method: "GET",
      });
    },
  };
}

export type ClaimsApiClient = ReturnType<typeof createClaimsApiClient>;
