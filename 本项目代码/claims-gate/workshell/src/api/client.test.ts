/**
 * 接缝：作业壳 API 客户端（login / list / detail + 错误原样）。
 * Rewrote from: REF-MISSIONS
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, createClaimsApiClient } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function callHeaders(fetchMock: ReturnType<typeof vi.fn>, index = 0): Headers {
  const init = fetchMock.mock.calls[index]?.[1] as RequestInit | undefined;
  return new Headers(init?.headers);
}

describe("createClaimsApiClient", () => {
  it("login posts credentials and returns session fields", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        session_token: "sess-abc",
        username: "viewer",
        role: "viewer",
        display_name: "只读查看员",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => null,
    });
    const session = await client.login("viewer", "viewer");

    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://127.0.0.1:8000/auth/login");
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({ username: "viewer", password: "viewer" }),
    });
    expect(callHeaders(fetchMock).get("Content-Type")).toBe("application/json");
    expect(session).toEqual({
      session_token: "sess-abc",
      username: "viewer",
      role: "viewer",
      display_name: "只读查看员",
    });
  });

  it("listClaims sends bearer token and returns items", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        items: [
          {
            case_id: "CLM-SC01-001",
            policy_no: "PA-2026-000188",
            product_code: "PA-ACCIDENT-MED",
            claim_amount_claimed: 350000,
            gate_status: "MATERIALS_INTAKE",
            inference_track: "deterministic",
            document_status: null,
            payout_ready: false,
          },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-abc",
    });
    const items = await client.listClaims();

    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://127.0.0.1:8000/claims");
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({ method: "GET" });
    expect(callHeaders(fetchMock).get("Authorization")).toBe("Bearer sess-abc");
    expect(items).toHaveLength(1);
    expect(items[0]?.case_id).toBe("CLM-SC01-001");
  });

  it("getClaim returns gate_status document_status inference_track payout_ready", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC02-001",
        policy_no: "PA-X",
        product_code: "PA-ACCIDENT-MED",
        clause_version: "PA-ACC-2024.1",
        endorsement_flags: [],
        loss_date: "2026-08-15",
        claim_amount_claimed: 10000,
        image_ids: [],
        material_codes: [],
        gate_status: "HUMAN_LATCH",
        inference_track: "deterministic",
        document_status: "DRAFT_EXPORT",
        payout_ready: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-abc",
    });
    const claim = await client.getClaim("CLM-SC02-001");

    expect(claim.gate_status).toBe("HUMAN_LATCH");
    expect(claim.document_status).toBe("DRAFT_EXPORT");
    expect(claim.inference_track).toBe("deterministic");
    expect(claim.payout_ready).toBe(false);
  });

  it("surfaces API rejection body as-is without rewriting message", async () => {
    const detail = {
      error_code: "AUTH_FAILED",
      message: "用户名或密码错误",
    };
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(jsonResponse(401, { detail })),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => null,
    });

    await expect(client.login("viewer", "bad")).rejects.toMatchObject({
      name: "ApiClientError",
      status: 401,
      body: { detail },
    });

    try {
      await client.login("viewer", "bad");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiClientError);
      const apiErr = err as ApiClientError;
      // 原样：不得改写成「登录失败请重试」之类
      expect(JSON.stringify(apiErr.body)).toContain("用户名或密码错误");
      expect(apiErr.body).toEqual({ detail });
    }
  });
});
