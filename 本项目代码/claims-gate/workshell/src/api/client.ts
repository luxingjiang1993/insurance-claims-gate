/**
 * 作业壳 HTTP 客户端：直连 Claims API，无 BFF；错误体原样抛出。
 * Rewrote from: REF-MISSIONS, REF-CASE-HYBRID
 */

import type {
  AssistSuggestion,
  ClaimDetail,
  ClaimSummary,
  DecisionDraft,
  DocumentExportResult,
  HumanLatchApproveResult,
  HumanLatchRejectResult,
  LoginResult,
  MaterialsRegisterResult,
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

    /** 采纳辅助建议：唯一权威更新路径为服务端再跑 evaluate。 */
    async adoptAssist(
      caseId: string,
      body: {
        assist_invocation_id?: string;
        draft_text?: string;
        suggested_stance?: string;
        retrieval_profile?: string;
      },
    ): Promise<DecisionDraft> {
      const payload: {
        assist_invocation_id?: string;
        draft_text?: string;
        suggested_stance?: string;
        retrieval_profile?: string;
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
      return request<DecisionDraft>(
        `/claims/${encodeURIComponent(caseId)}/assist/adopt`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
    },
  };
}

export type ClaimsApiClient = ReturnType<typeof createClaimsApiClient>;
