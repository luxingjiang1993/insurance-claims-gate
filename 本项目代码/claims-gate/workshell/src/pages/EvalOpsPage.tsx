/**
 * 评测台页面：独立触发跑次 / 查看排行榜；与门禁主路径视觉分离。
 * Rewrote from: REF-MISSIONS, REF-CASE-EVAL-ADVISOR
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type {
  EvalLeaderboardRow,
  EvalRunRecord,
  LoginResult,
} from "../api/types";
import { ApiErrorView } from "../components/ApiErrorView";
import { ReadonlyBanner } from "../components/ReadonlyBanner";
import { ShellNav } from "../components/ShellNav";
import {
  DEMO_EVAL_ACTORS,
  GOLD_LABEL_HOOK_NOTE,
  canCreateEvalRun,
  filterLeaderboardBySubmitter,
  filterRunsByActor,
  resolveRunTriggerOutcome,
} from "./evalOpsModel";

type Props = {
  api: ClaimsApiClient;
  session: LoginResult;
  onNavigateHome: () => void;
  onLogout: () => void;
};

export function EvalOpsPage({
  api,
  session,
  onNavigateHome,
  onLogout,
}: Props) {
  const [runs, setRuns] = useState<EvalRunRecord[]>([]);
  const [boardRows, setBoardRows] = useState<EvalLeaderboardRow[]>([]);
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [actorFilter, setActorFilter] = useState("");
  const [experimentName, setExperimentName] = useState("");
  const [busy, setBusy] = useState(true);
  const [triggerBusy, setTriggerBusy] = useState(false);
  const [loadError, setLoadError] = useState<ApiClientError | Error | null>(
    null,
  );
  const [triggerError, setTriggerError] = useState<
    ApiClientError | Error | null
  >(null);
  const [lastRunId, setLastRunId] = useState<string | null>(null);
  const [primaryMetricName, setPrimaryMetricName] = useState("pass_rate");
  const [dataSource, setDataSource] = useState("local_sqlite_eval_runs");
  const [goldJson, setGoldJson] = useState(
    '{\n  "dataset_id": "preview-hook",\n  "records": [{ "case_id": "CLM-SC01-001", "inputs": {}, "expected": {} }]\n}',
  );
  const [goldBusy, setGoldBusy] = useState(false);
  const [goldError, setGoldError] = useState<ApiClientError | Error | null>(
    null,
  );
  const [goldImportCount, setGoldImportCount] = useState<number | null>(null);
  const [goldExportText, setGoldExportText] = useState("");
  const refreshGen = useRef(0);

  const allowTrigger = canCreateEvalRun(session.role);

  const refresh = useCallback(async () => {
    const gen = ++refreshGen.current;
    setBusy(true);
    setLoadError(null);
    try {
      const [runBody, board] = await Promise.all([
        api.listEvalRuns(),
        api.getEvalLeaderboard({ order }),
      ]);
      if (gen !== refreshGen.current) {
        return;
      }
      setRuns(runBody.runs);
      setBoardRows(board.rows);
      setPrimaryMetricName(board.primary_metric_name);
      setDataSource(board.data_source);
    } catch (err) {
      if (gen !== refreshGen.current) {
        return;
      }
      setLoadError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      if (gen === refreshGen.current) {
        setBusy(false);
      }
    }
  }, [api, order]);

  useEffect(() => {
    void refresh();
    return () => {
      refreshGen.current += 1;
    };
  }, [refresh]);

  async function handleTrigger() {
    if (!allowTrigger) {
      return;
    }
    setTriggerBusy(true);
    setTriggerError(null);
    setLastRunId(null);
    try {
      const payload =
        experimentName.trim().length > 0
          ? { experiment_name: experimentName.trim() }
          : {};
      const run = await api.createEvalRun(payload);
      const outcome = resolveRunTriggerOutcome({ ok: true, run });
      if (outcome.kind === "success") {
        setLastRunId(outcome.run.run_id);
      }
      await refresh();
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      const outcome = resolveRunTriggerOutcome({ ok: false, error });
      if (outcome.kind === "failure") {
        setTriggerError(outcome.error);
        setLastRunId(null);
      }
    } finally {
      setTriggerBusy(false);
    }
  }

  async function handleGoldImport() {
    if (!allowTrigger) {
      return;
    }
    setGoldBusy(true);
    setGoldError(null);
    setGoldImportCount(null);
    try {
      const parsed = JSON.parse(goldJson) as {
        dataset_id?: string;
        records?: Array<{
          case_id: string;
          inputs?: Record<string, unknown>;
          expected?: Record<string, unknown>;
          notes?: string;
        }>;
      };
      if (!parsed.dataset_id || !parsed.records) {
        throw new Error("JSON 须含 dataset_id 与 records");
      }
      const result = await api.importGoldLabels({
        dataset_id: parsed.dataset_id,
        records: parsed.records,
      });
      setGoldImportCount(result.imported_count);
    } catch (err) {
      setGoldError(err instanceof Error ? err : new Error(String(err)));
      setGoldImportCount(null);
    } finally {
      setGoldBusy(false);
    }
  }

  async function handleGoldExport() {
    setGoldBusy(true);
    setGoldError(null);
    try {
      const exported = await api.exportGoldLabels({
        dataset_id: "preview-hook",
      });
      setGoldExportText(JSON.stringify(exported, null, 2));
    } catch (err) {
      setGoldError(err instanceof Error ? err : new Error(String(err)));
      setGoldExportText("");
    } finally {
      setGoldBusy(false);
    }
  }

  const visibleRuns = filterRunsByActor(runs, actorFilter);
  const visibleBoard = filterLeaderboardBySubmitter(boardRows, actorFilter);

  return (
    <section className="card eval-ops-card">
      <header className="page-header">
        <div>
          <ShellNav
            active="evalOps"
            onNavigate={(route) => {
              if (route === "list") {
                onNavigateHome();
              }
            }}
          />
          <h1>评测台（Eval Ops）</h1>
          <p className="muted">
            {session.display_name}（{session.username} / {session.role}）
          </p>
        </div>
        <button type="button" className="secondary" onClick={onLogout}>
          退出
        </button>
      </header>

      <div className="eval-ops-banner" role="note">
        <span className="tag tag-eval">评测旁路</span>
        <p>
          本页是 OpenEval 协作跑榜台，<strong>不是</strong>
          条款门禁核赔终裁台。排行榜分数 ≠{" "}
          <code>machine_check</code> 通过；无「秒赔」/自动出款。
        </p>
      </div>

      <ReadonlyBanner role={session.role} />

      <div className="action-panel">
        <div className="panel-title-row">
          <h2>触发评测跑次</h2>
        </div>
        <p className="muted">
          用演示账号 {DEMO_EVAL_ACTORS.join(" / ")}{" "}
          分别登录可各自触发；结果按 actor 归因，互不覆盖。协作演示：切换账号后再刷新本页查看他人榜行。
        </p>
        {allowTrigger ? (
          <div className="form-grid eval-trigger-form">
            <label>
              实验名（可选）
              <input
                value={experimentName}
                onChange={(e) => setExperimentName(e.target.value)}
                placeholder="留空则服务端自动命名"
              />
            </label>
            <div className="action-row">
              <button
                type="button"
                disabled={triggerBusy}
                onClick={() => void handleTrigger()}
              >
                {triggerBusy ? "跑次中…" : "触发评测跑次"}
              </button>
            </div>
          </div>
        ) : (
          <p className="muted">当前角色仅可查看跑次与排行榜，不可触发。</p>
        )}
        {lastRunId ? (
          <div className="ok-banner" role="status">
            跑次已记录：<code>{lastRunId}</code>（旁路落库；非门禁裁决）
          </div>
        ) : null}
        {triggerError ? <ApiErrorView error={triggerError} /> : null}
      </div>

      <div className="action-panel">
        <div className="panel-title-row">
          <h2>排行榜与跑次</h2>
          <button
            type="button"
            className="secondary"
            disabled={busy}
            onClick={() => void refresh()}
          >
            刷新
          </button>
        </div>
        <p className="muted">
          真源 <code>{dataSource}</code> · 主指标{" "}
          <code>{primaryMetricName}</code>
        </p>
        <div className="eval-filter-row form-grid">
          <label>
            按提交者过滤（可看他人结果）
            <select
              value={actorFilter}
              onChange={(e) => setActorFilter(e.target.value)}
            >
              <option value="">全部</option>
              {DEMO_EVAL_ACTORS.map((actor) => (
                <option key={actor} value={actor}>
                  {actor}
                </option>
              ))}
            </select>
          </label>
          <label>
            主指标排序
            <select
              value={order}
              onChange={(e) =>
                setOrder(e.target.value === "asc" ? "asc" : "desc")
              }
            >
              <option value="desc">降序</option>
              <option value="asc">升序</option>
            </select>
          </label>
        </div>

        {busy ? <p className="muted">加载中…</p> : null}
        {loadError ? <ApiErrorView error={loadError} /> : null}

        {!busy && !loadError ? (
          <>
            <table className="data-table">
              <caption>排行榜</caption>
              <thead>
                <tr>
                  <th>实验名</th>
                  <th>主指标</th>
                  <th>时间</th>
                  <th>提交者</th>
                  <th>run_id</th>
                </tr>
              </thead>
              <tbody>
                {visibleBoard.length === 0 ? (
                  <tr>
                    <td colSpan={5}>
                      <span className="muted">暂无榜行</span>
                    </td>
                  </tr>
                ) : (
                  visibleBoard.map((row) => (
                    <tr key={row.run_id}>
                      <td>{row.experiment_name}</td>
                      <td>
                        <code>
                          {row.primary_metric_name}=
                          {row.primary_metric.toFixed(4)}
                        </code>
                      </td>
                      <td>
                        <code>{row.created_at}</code>
                      </td>
                      <td>
                        <code>{row.submitter}</code>
                      </td>
                      <td>
                        <code>{row.run_id}</code>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            <table className="data-table">
              <caption>跑次列表</caption>
              <thead>
                <tr>
                  <th>run_id</th>
                  <th>actor</th>
                  <th>实验名</th>
                  <th>created_at</th>
                  <th>langsmith_degraded</th>
                </tr>
              </thead>
              <tbody>
                {visibleRuns.length === 0 ? (
                  <tr>
                    <td colSpan={5}>
                      <span className="muted">暂无跑次</span>
                    </td>
                  </tr>
                ) : (
                  visibleRuns.map((run) => (
                    <tr key={run.run_id}>
                      <td>
                        <code>{run.run_id}</code>
                      </td>
                      <td>
                        <code>{run.actor_user_id}</code>
                      </td>
                      <td>{run.experiment_name}</td>
                      <td>
                        <code>{run.created_at}</code>
                      </td>
                      <td>
                        <code>{String(run.langsmith_degraded)}</code>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </>
        ) : null}
      </div>

      <div className="action-panel">
        <div className="panel-title-row">
          <h2>金标导入/导出钩子（Preview）</h2>
        </div>
        <p className="muted">{GOLD_LABEL_HOOK_NOTE}</p>
        {allowTrigger ? (
          <label>
            导入 JSON
            <textarea
              rows={6}
              value={goldJson}
              onChange={(e) => setGoldJson(e.target.value)}
            />
          </label>
        ) : (
          <p className="muted">当前角色仅可导出查看，不可导入。</p>
        )}
        <div className="action-row">
          {allowTrigger ? (
            <button
              type="button"
              disabled={goldBusy}
              onClick={() => void handleGoldImport()}
            >
              {goldBusy ? "处理中…" : "导入钩子"}
            </button>
          ) : null}
          <button
            type="button"
            className="secondary"
            disabled={goldBusy}
            onClick={() => void handleGoldExport()}
          >
            导出 preview-hook
          </button>
        </div>
        {goldImportCount !== null ? (
          <div className="ok-banner" role="status">
            已写入 {goldImportCount} 条（钩子落库；非金标运营完成）
          </div>
        ) : null}
        {goldError ? <ApiErrorView error={goldError} /> : null}
        {goldExportText ? (
          <pre className="muted">{goldExportText}</pre>
        ) : null}
      </div>
    </section>
  );
}
