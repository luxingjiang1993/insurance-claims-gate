/**
 * 评测台纯逻辑：角色写入口、提交者过滤、触发结果语义。
 * Rewrote from: REF-MISSIONS, REF-CASE-EVAL-ADVISOR
 */

import type { EvalLeaderboardRow, EvalRunRecord } from "../api/types";
import { isReadonlyRole } from "../auth/session";

/** 协作跑榜演示账号（与 W0 演示用户一致）。 */
export const DEMO_EVAL_ACTORS = ["adjuster", "supervisor"] as const;

/** 金标 I/O 诚实文案：钩子预留，不得写成已运营完成。 */
export const GOLD_LABEL_HOOK_NOTE =
  "金标 I/O 仅为导入/导出钩子预留（每条须关联 case_id）。双人标注全量与人工金标运营仍延后；本页不把金标运营写成已完成。";

export function canCreateEvalRun(role: string): boolean {
  return !isReadonlyRole(role);
}

export function filterRunsByActor(
  runs: EvalRunRecord[],
  actorUserId: string,
): EvalRunRecord[] {
  const key = actorUserId.trim();
  if (!key) {
    return runs;
  }
  return runs.filter((r) => r.actor_user_id === key);
}

export function filterLeaderboardBySubmitter(
  rows: EvalLeaderboardRow[],
  submitter: string,
): EvalLeaderboardRow[] {
  const key = submitter.trim();
  if (!key) {
    return rows;
  }
  return rows.filter((r) => r.submitter === key);
}

export type RunTriggerOutcome =
  | { kind: "success"; run: EvalRunRecord }
  | { kind: "failure"; error: Error };

/** 将触发结果归一化为成功/失败；失败不得被调用方当成功展示。 */
export function resolveRunTriggerOutcome(
  result:
    | { ok: true; run: EvalRunRecord }
    | { ok: false; error: Error },
): RunTriggerOutcome {
  if (result.ok) {
    return { kind: "success", run: result.run };
  }
  return { kind: "failure", error: result.error };
}
