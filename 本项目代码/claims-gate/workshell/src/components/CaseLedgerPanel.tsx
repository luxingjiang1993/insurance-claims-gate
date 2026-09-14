import { useCallback, useEffect, useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { LatchEventRow, LedgerEntry } from "../api/types";
import { ApiErrorView } from "./ApiErrorView";

type Props = {
  api: ClaimsApiClient;
  caseId: string;
  /** 父页关键动作后递增，触发重新拉取流水。 */
  refreshKey?: number;
};

/**
 * 本案流水：浏览 ledger 与人闸事件，便于操作回放。
 * Rewrote from: REF-MISSIONS
 */
export function CaseLedgerPanel({ api, caseId, refreshKey = 0 }: Props) {
  const [items, setItems] = useState<LedgerEntry[]>([]);
  const [latchEvents, setLatchEvents] = useState<LatchEventRow[]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<ApiClientError | Error | null>(null);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const [ledger, events] = await Promise.all([
        api.getLedger(caseId),
        api.getLatchEvents(caseId),
      ]);
      setItems(ledger);
      setLatchEvents(events);
    } catch (err) {
      setItems([]);
      setLatchEvents([]);
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }, [api, caseId]);

  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  return (
    <section className="action-panel">
      <h2>本案流水</h2>
      <p className="muted">
        只读回放 evaluate / AI 辅助 / 人闸等关键动作摘要。本地 JSONL
        span 与 LangSmith 由服务端配置开启；本区不替代 machine_check。
      </p>
      <div className="header-actions">
        <button type="button" className="secondary" onClick={() => void load()} disabled={busy}>
          刷新流水
        </button>
      </div>
      {busy ? <p className="muted">加载中…</p> : null}
      {error ? <ApiErrorView error={error} /> : null}
      {!busy && !error && items.length === 0 ? (
        <p className="muted">尚无 ledger 条目。完成 evaluate 后可在此回放。</p>
      ) : null}
      {items.length > 0 ? (
        <table className="data-table">
          <caption>Ledger（最新在前）</caption>
          <thead>
            <tr>
              <th>ts</th>
              <th>decision_type</th>
              <th>route_id</th>
              <th>retrieval_profile</th>
              <th>trace_id</th>
              <th>validator_score</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={`${row.ts}-${row.decision_type}-${row.route_id}`}>
                <td>
                  <code>{row.ts || "—"}</code>
                </td>
                <td>
                  <code>{row.decision_type}</code>
                </td>
                <td>
                  <code>{row.route_id}</code>
                </td>
                <td>
                  <code>{row.retrieval_profile}</code>
                </td>
                <td>
                  <code>{row.trace_id || "—"}</code>
                </td>
                <td>
                  <code>{String(row.validator_score)}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {latchEvents.length > 0 ? (
        <table className="data-table">
          <caption>人闸事件</caption>
          <thead>
            <tr>
              <th>ts</th>
              <th>event_type</th>
              <th>actor</th>
              <th>token / reason</th>
            </tr>
          </thead>
          <tbody>
            {latchEvents.map((ev) => (
              <tr key={`${ev.ts}-${ev.event_type}-${ev.actor}`}>
                <td>
                  <code>{ev.ts || "—"}</code>
                </td>
                <td>
                  <code>{ev.event_type}</code>
                </td>
                <td>{ev.actor}</td>
                <td>
                  <code>
                    {ev.human_latch_token || ev.reason || "—"}
                  </code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
