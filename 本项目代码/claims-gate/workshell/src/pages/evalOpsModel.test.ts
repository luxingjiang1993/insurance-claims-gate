/**
 * 接缝：作业壳评测台纯逻辑（入口角色 / 提交者过滤 / 触发结果不假成功）。
 * Rewrote from: REF-MISSIONS, REF-CASE-EVAL-ADVISOR
 */
import { describe, expect, it } from "vitest";

import type { EvalLeaderboardRow, EvalRunRecord } from "../api/types";
import {
  DEMO_EVAL_ACTORS,
  canCreateEvalRun,
  filterLeaderboardBySubmitter,
  filterRunsByActor,
  resolveRunTriggerOutcome,
} from "./evalOpsModel";

const sampleRun = (actor: string, runId: string): EvalRunRecord => ({
  run_id: runId,
  actor_user_id: actor,
  experiment_name: `exp-${actor}`,
  experiment_id: null,
  dataset_name: "claims-gate-openeval-negatives",
  summary: { passed: 1, total: 1 },
  cases: [],
  created_at: "2026-09-15T01:00:00+00:00",
  langsmith_degraded: true,
});

const sampleRow = (submitter: string, runId: string): EvalLeaderboardRow => ({
  experiment_name: `exp-${submitter}`,
  primary_metric: 1,
  primary_metric_name: "pass_rate",
  created_at: "2026-09-15T01:00:00+00:00",
  submitter,
  run_id: runId,
});

describe("evalOpsModel", () => {
  it("exposes at least two demo actors for collaboration", () => {
    expect(DEMO_EVAL_ACTORS.length).toBeGreaterThanOrEqual(2);
    expect(DEMO_EVAL_ACTORS).toEqual(
      expect.arrayContaining(["adjuster", "supervisor"]),
    );
  });

  it("allows adjuster/supervisor to trigger runs; viewer read-only", () => {
    expect(canCreateEvalRun("adjuster")).toBe(true);
    expect(canCreateEvalRun("supervisor")).toBe(true);
    expect(canCreateEvalRun("viewer")).toBe(false);
  });

  it("filters runs and leaderboard by actor without dropping other actors from unfiltered view", () => {
    const runs = [
      sampleRun("adjuster", "r1"),
      sampleRun("supervisor", "r2"),
    ];
    const rows = [
      sampleRow("adjuster", "r1"),
      sampleRow("supervisor", "r2"),
    ];

    expect(filterRunsByActor(runs, "")).toHaveLength(2);
    expect(filterRunsByActor(runs, "adjuster").map((r) => r.run_id)).toEqual([
      "r1",
    ]);
    expect(
      filterLeaderboardBySubmitter(rows, "supervisor").map((r) => r.run_id),
    ).toEqual(["r2"]);
  });

  it("marks API rejection as failure, never fake success", () => {
    const ok = resolveRunTriggerOutcome({
      ok: true,
      run: sampleRun("adjuster", "r-ok"),
    });
    expect(ok.kind).toBe("success");
    if (ok.kind === "success") {
      expect(ok.run.run_id).toBe("r-ok");
    }

    const fail = resolveRunTriggerOutcome({
      ok: false,
      error: new Error("API 401"),
    });
    expect(fail.kind).toBe("failure");
    if (fail.kind === "failure") {
      expect(fail.error.message).toBe("API 401");
    }
  });
});
