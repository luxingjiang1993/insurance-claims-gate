/**
 * 作业壳 HTTP 客户端：直连 Claims API，无 BFF；错误体原样抛出。
 * Rewrote from: REF-MISSIONS
 */

import type { ClaimDetail, ClaimSummary, LoginResult } from "./types";

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
  };
}

export type ClaimsApiClient = ReturnType<typeof createClaimsApiClient>;
