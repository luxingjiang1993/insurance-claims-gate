/**
 * 接缝：作业壳 API 客户端（login / list / detail / SC / 人闸文书 / assist·adopt + 错误原样）。
 * Rewrote from: REF-MISSIONS, REF-CASE-HYBRID
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

  it("assistClaim posts query and returns degraded assist fields as-is", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC02-001",
        assist_invocation_id: "assist-abc123",
        inference_track: "llm_optional",
        query: "疾病摔伤是否除外",
        retrieval_profile: "clause_v_current",
        draft_text: "【辅助建议】仅供人审，非终裁。",
        used_llm: false,
        degraded: true,
        degrade_reason: "未配置 OPENAI_API_KEY，已降级为关键词提名草稿",
        suggested_stance: "deny",
        citations: [{ doc_id: "PA-ACC-2024.1", clause_item: "2.1" }],
        retrieval: { mode: "keyword", vector_enabled: false },
        payout_ready: false,
        human_latch_token: null,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const suggestion = await client.assistClaim("CLM-SC02-001", {
      query: "疾病摔伤是否除外",
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC02-001/assist",
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({ query: "疾病摔伤是否除外" }),
    });
    expect(callHeaders(fetchMock).get("Authorization")).toBe("Bearer sess-adj");
    expect(suggestion.degraded).toBe(true);
    expect(suggestion.used_llm).toBe(false);
    expect(suggestion.assist_invocation_id).toBe("assist-abc123");
    expect(suggestion.payout_ready).toBe(false);
    expect(suggestion.draft_text).toContain("非终裁");
  });

  it("adoptAssist posts invocation id and returns evaluate decision as-is", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC02-001",
        decision_type: "reject_draft",
        gate_status: "HUMAN_LATCH",
        document_status: "DRAFT_EXPORT",
        payout_ready: false,
        inference_track: "deterministic",
        human_latch_token: null,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const draft = await client.adoptAssist("CLM-SC02-001", {
      assist_invocation_id: "assist-abc123",
      draft_text: "【辅助建议】仅供人审，非终裁。",
      suggested_stance: "deny",
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC02-001/assist/adopt",
    );
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({
        assist_invocation_id: "assist-abc123",
        draft_text: "【辅助建议】仅供人审，非终裁。",
        suggested_stance: "deny",
      }),
    });
    expect(draft.decision_type).toBe("reject_draft");
    expect(draft.payout_ready).toBe(false);
  });

  it("getLedger returns case ledger items newest-first", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC02-001",
        items: [
          {
            case_id: "CLM-SC02-001",
            route_id: "LATCH-APPROVE",
            retrieval_profile: "clause_v_current",
            decision_type: "human_latch_approve",
            validator_score: 1.0,
            ts: "2026-09-14T12:00:00+00:00",
          },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-view",
    });
    const items = await client.getLedger("CLM-SC02-001");

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC02-001/ledger",
    );
    expect(callHeaders(fetchMock).get("Authorization")).toBe("Bearer sess-view");
    expect(items).toHaveLength(1);
    expect(items[0]?.decision_type).toBe("human_latch_approve");
  });

  it("getLatchEvents returns latch event rows", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        case_id: "CLM-SC02-001",
        items: [
          {
            case_id: "CLM-SC02-001",
            event_type: "approve",
            actor: "supervisor",
            ts: "2026-09-14T12:00:00+00:00",
            human_latch_token: "HLT-abc",
          },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-view",
    });
    const items = await client.getLatchEvents("CLM-SC02-001");

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/claims/CLM-SC02-001/latch-events",
    );
    expect(items[0]?.event_type).toBe("approve");
    expect(items[0]?.human_latch_token).toBe("HLT-abc");
  });

  it("surfaces adoptAssist API rejection without rewriting message", async () => {
    const detail = {
      error_code: "CITATION_FAILED",
      message: "citation 三联门未通过，不得落库裁决草案",
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(422, { detail }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });

    await expect(
      client.adoptAssist("CLM-SC02-001", {
        assist_invocation_id: "assist-bad",
        draft_text: "幻觉条款",
      }),
    ).rejects.toMatchObject({
      name: "ApiClientError",
      status: 422,
      body: { detail },
    });
  });

  it("createEvalRun posts optional experiment_name and returns actor-attributed run", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        run_id: "eval-abc",
        actor_user_id: "adjuster",
        experiment_name: "exp-adj-1",
        experiment_id: null,
        dataset_name: "claims-gate-openeval-negatives",
        summary: { passed: 2, total: 3 },
        cases: [],
        created_at: "2026-09-15T01:00:00+00:00",
        langsmith_degraded: true,
        gate_role: "bypass_not_machine_check",
        blocks_track_a_gate: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const run = await client.createEvalRun({ experiment_name: "exp-adj-1" });

    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://127.0.0.1:8000/eval/runs");
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({
      method: "POST",
      body: JSON.stringify({ experiment_name: "exp-adj-1" }),
    });
    expect(callHeaders(fetchMock).get("Authorization")).toBe("Bearer sess-adj");
    expect(run.actor_user_id).toBe("adjuster");
    expect(run.run_id).toBe("eval-abc");
    expect(run.langsmith_degraded).toBe(true);
  });

  it("listEvalRuns passes actor_user_id filter and returns runs", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        runs: [
          {
            run_id: "eval-a",
            actor_user_id: "adjuster",
            experiment_name: "exp-a",
            experiment_id: null,
            dataset_name: "claims-gate-openeval-negatives",
            summary: { passed: 1, total: 2 },
            cases: [],
            created_at: "2026-09-15T01:00:00+00:00",
            langsmith_degraded: true,
            gate_role: "bypass_not_machine_check",
            blocks_track_a_gate: false,
          },
        ],
        filter_actor_user_id: "adjuster",
        gate_role: "bypass_not_machine_check",
        blocks_track_a_gate: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const body = await client.listEvalRuns({ actor_user_id: "adjuster" });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/eval/runs?actor_user_id=adjuster",
    );
    expect(body.runs).toHaveLength(1);
    expect(body.runs[0]?.actor_user_id).toBe("adjuster");
    expect(body.filter_actor_user_id).toBe("adjuster");
  });

  it("getEvalLeaderboard returns sortable rows from local eval_runs", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        rows: [
          {
            experiment_name: "exp-high",
            primary_metric: 1,
            primary_metric_name: "pass_rate",
            created_at: "2026-09-15T02:00:00+00:00",
            submitter: "adjuster",
            run_id: "eval-high",
            gate_role: "bypass_not_machine_check",
            blocks_track_a_gate: false,
          },
          {
            experiment_name: "exp-low",
            primary_metric: 0.5,
            primary_metric_name: "pass_rate",
            created_at: "2026-09-15T01:00:00+00:00",
            submitter: "supervisor",
            run_id: "eval-low",
            gate_role: "bypass_not_machine_check",
            blocks_track_a_gate: false,
          },
        ],
        sort_by: "primary_metric",
        order: "desc",
        primary_metric_name: "pass_rate",
        data_source: "local_sqlite_eval_runs",
        gate_role: "bypass_not_machine_check",
        blocks_track_a_gate: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-sup",
    });
    const board = await client.getEvalLeaderboard({ order: "desc" });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/eval/leaderboard?order=desc",
    );
    expect(board.rows).toHaveLength(2);
    expect(board.rows[0]?.submitter).toBe("adjuster");
    expect(board.rows[1]?.submitter).toBe("supervisor");
    expect(board.data_source).toBe("local_sqlite_eval_runs");
  });

  it("surfaces createEvalRun API rejection without fake success", async () => {
    const detail = {
      error_code: "AUTH_FAILED",
      message: "触发评测跑次须登录会话",
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(401, { detail }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => null,
    });

    await expect(client.createEvalRun({})).rejects.toMatchObject({
      name: "ApiClientError",
      status: 401,
      body: { detail },
    });
  });

  it("importGoldLabels posts dataset with case_id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        dataset_id: "preview-hook",
        imported_count: 1,
        gold_ops_complete: false,
        dual_annotation_workflow: false,
        gate_role: "bypass_not_machine_check",
        blocks_track_a_gate: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const result = await client.importGoldLabels({
      dataset_id: "preview-hook",
      records: [{ case_id: "CLM-SC01-001", inputs: {}, expected: {} }],
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/eval/gold-labels/import",
    );
    expect(result.imported_count).toBe(1);
    expect(result.gold_ops_complete).toBe(false);
  });

  it("exportGoldLabels filters by dataset_id and case_id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        dataset_id: "preview-hook",
        records: [{ case_id: "CLM-SC01-001", inputs: {}, expected: {} }],
        gold_ops_complete: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = createClaimsApiClient({
      baseUrl: "http://127.0.0.1:8000",
      getToken: () => "sess-adj",
    });
    const body = await client.exportGoldLabels({
      dataset_id: "preview-hook",
      case_id: "CLM-SC01-001",
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://127.0.0.1:8000/eval/gold-labels/export?dataset_id=preview-hook&case_id=CLM-SC01-001",
    );
    expect(body.records[0]?.case_id).toBe("CLM-SC01-001");
    expect(body.gold_ops_complete).toBe(false);
  });
});
