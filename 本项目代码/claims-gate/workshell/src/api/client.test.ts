/**
 * 接缝：作业壳 API 客户端（login / list / detail / SC 规则路径 + 错误原样）。
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

  it("evaluateClaim posts empty body and returns API decision fields as-is", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC01-001",
        decision_type: "supplement",
        gate_status: "PENDING_SUPPLEMENT",
        document_status: "DRAFT_EXPORT",
        payout_ready: false,
        inference_track: "deterministic",
        one_shot_hash: "hash-sc01",
        supplement_checklist: [
          { code: "ID_CARD", name_zh: "投保人/被保险人身份证件", required: true },
          { code: "CLAIM_FORM", name_zh: "理赔申请书", required: true },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const draft = await client.evaluateClaim("CLM-SC01-001");

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC01-001/evaluate",
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({}),
    });
    expect(callHeaders(fetchMock).get("Authorization")).toBe("Bearer sess-adj");
    expect(draft.decision_type).toBe("supplement");
    expect(draft.gate_status).toBe("PENDING_SUPPLEMENT");
    expect(draft.payout_ready).toBe(false);
    expect(draft.one_shot_hash).toBe("hash-sc01");
    expect(draft.supplement_checklist?.map((i) => i.code)).toEqual([
      "ID_CARD",
      "CLAIM_FORM",
    ]);
  });

  it("registerMaterials posts codes from caller without inventing checklist", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC01-001",
        material_codes: ["ID_CARD", "CLAIM_FORM"],
        image_ids: ["IMG-ID_CARD"],
        gate_status: "PENDING_SUPPLEMENT",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const result = await client.registerMaterials("CLM-SC01-001", {
      material_codes: ["ID_CARD", "CLAIM_FORM"],
      image_ids: ["IMG-ID_CARD"],
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC01-001/materials",
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({
        material_codes: ["ID_CARD", "CLAIM_FORM"],
        image_ids: ["IMG-ID_CARD"],
      }),
    });
    expect(result.material_codes).toEqual(["ID_CARD", "CLAIM_FORM"]);
  });

  it("notifySupplement posts frozen hash and full missing_item_codes from caller", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC01-001",
        document_type: "supplement_notice",
        document_status: "DRAFT_EXPORT",
        one_shot_hash: "hash-sc01",
        legal_basis: "保险法第二十二条",
        missing_items: [{ code: "ID_CARD", name_zh: "身份证件", required: true }],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const notify = await client.notifySupplement("CLM-SC01-001", {
      one_shot_hash: "hash-sc01",
      missing_item_codes: ["ID_CARD", "CLAIM_FORM"],
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC01-001/supplement/notify",
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({
        one_shot_hash: "hash-sc01",
        missing_item_codes: ["ID_CARD", "CLAIM_FORM"],
      }),
    });
    expect(notify.one_shot_hash).toBe("hash-sc01");
    expect(notify.legal_basis).toContain("第二十二条");
  });

  it("getDecision returns latest draft fields", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC02-001",
        decision_type: "reject_draft",
        gate_status: "HUMAN_LATCH",
        document_status: "DRAFT_EXPORT",
        payout_ready: false,
        inference_track: "deterministic",
        appeal_path: "申诉/人工复核",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const draft = await client.getDecision("CLM-SC02-001");

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC02-001/decision",
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({ method: "GET" });
    expect(draft.decision_type).toBe("reject_draft");
    expect(draft.payout_ready).toBe(false);
  });

  it("surfaces evaluate API rejection without rewriting message", async () => {
    const detail = {
      error_code: "VALIDATION_FAILED",
      message: "同 one_shot_hash 禁止拆轮补件：通知清单须与一次完整缺项一致",
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(422, { detail }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });

    await expect(
      client.notifySupplement("CLM-SC01-001", {
        one_shot_hash: "hash-sc01",
        missing_item_codes: ["ID_CARD"],
      }),
    ).rejects.toMatchObject({
      name: "ApiClientError",
      status: 422,
      body: { detail },
    });
  });

  it("approveHumanLatch posts actor and returns human_latch_token as-is", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC02-001",
        human_latch_token: "HLT-deadbeef",
        human_approver: "supervisor",
        payout_ready: false,
        gate_status: "HUMAN_LATCH",
        decision_type: "reject_draft",
        dual_token_required: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-sup",
    });
    const result = await client.approveHumanLatch("CLM-SC02-001", {
      approved_by: "supervisor",
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC02-001/human-latch/approve",
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({ approved_by: "supervisor" }),
    });
    expect(callHeaders(fetchMock).get("Authorization")).toBe("Bearer sess-sup");
    expect(result.human_latch_token).toBe("HLT-deadbeef");
    expect(result.payout_ready).toBe(false);
  });

  it("rejectHumanLatch posts reject payload and returns null token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC02-001",
        gate_status: "PRIMARY_REVIEW",
        human_latch_token: null,
        payout_ready: false,
        rejected_by: "supervisor",
        reason: "需补调查",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-sup",
    });
    const result = await client.rejectHumanLatch("CLM-SC02-001", {
      rejected_by: "supervisor",
      reason: "需补调查",
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC02-001/human-latch/reject",
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({
        rejected_by: "supervisor",
        reason: "需补调查",
      }),
    });
    expect(result.human_latch_token).toBeNull();
    expect(result.gate_status).toBe("PRIMARY_REVIEW");
  });

  it("surfaces adjuster latch approve rejection without rewriting message", async () => {
    const detail = {
      error_code: "PERMISSION_DENIED",
      message: "仅 supervisor 可执行人闸: approve_human_latch",
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(403, { detail }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });

    await expect(
      client.approveHumanLatch("CLM-SC02-001", { approved_by: "adjuster" }),
    ).rejects.toMatchObject({
      name: "ApiClientError",
      status: 403,
      body: { detail },
    });
  });

  it("exportDocument posts DRAFT_EXPORT reject_notice and keeps document_status", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        document_type: "reject_notice",
        document_status: "DRAFT_EXPORT",
        case_id: "CLM-SC02-001",
        decision: "拒绝赔偿/拒绝给付",
        payout_ready: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const doc = await client.exportDocument("CLM-SC02-001", {
      document_type: "reject_notice",
      document_status: "DRAFT_EXPORT",
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC02-001/documents/export",
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({
        document_type: "reject_notice",
        document_status: "DRAFT_EXPORT",
      }),
    });
    expect(doc.document_status).toBe("DRAFT_EXPORT");
    expect(doc.document_type).toBe("reject_notice");
  });

  it("surfaces EXTERNAL_NOTIFY without latch as API rejection as-is", async () => {
    const detail = {
      error_code: "LATCH_REQUIRED",
      message: "拒赔升 EXTERNAL_NOTIFY 须有效人闸令牌",
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(403, { detail }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-sup",
    });

    await expect(
      client.exportDocument("CLM-SC02-001", {
        document_type: "reject_notice",
        document_status: "EXTERNAL_NOTIFY",
      }),
    ).rejects.toMatchObject({
      name: "ApiClientError",
      status: 403,
      body: { detail },
    });
  });
});
