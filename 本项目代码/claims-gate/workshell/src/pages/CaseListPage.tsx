import { useEffect, useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { ClaimSummary, LoginResult } from "../api/types";
import { ApiErrorView } from "../components/ApiErrorView";
import { ReadonlyBanner } from "../components/ReadonlyBanner";
import { ShellNav } from "../components/ShellNav";

type Props = {
  api: ClaimsApiClient;
  session: LoginResult;
  onOpenCase: (caseId: string) => void;
  onOpenEvalOps: () => void;
  onOpenProviderStatus: () => void;
  onLogout: () => void;
};

export function CaseListPage({
  api,
  session,
  onOpenCase,
  onOpenEvalOps,
  onOpenProviderStatus,
  onLogout,
}: Props) {
  const [items, setItems] = useState<ClaimSummary[]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<ApiClientError | Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setBusy(true);
    setError(null);
    api
      .listClaims()
      .then((rows) => {
        if (!cancelled) {
          setItems(rows);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setBusy(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [api]);

  return (
    <section className="card">
      <header className="page-header">
        <div>
          <ShellNav
            active="list"
            onNavigate={(route) => {
              if (route === "evalOps") {
                onOpenEvalOps();
              } else if (route === "providerStatus") {
                onOpenProviderStatus();
              }
            }}
          />
          <h1>案件列表</h1>
          <p className="muted">
            {session.display_name}（{session.username} / {session.role}）
          </p>
        </div>
        <button type="button" className="secondary" onClick={onLogout}>
          退出
        </button>
      </header>
      <ReadonlyBanner role={session.role} />
      {busy ? <p className="muted">加载中…</p> : null}
      {error ? <ApiErrorView error={error} /> : null}
      {!busy && !error ? (
        <table className="data-table">
          <thead>
            <tr>
              <th>案件号</th>
              <th>保单号</th>
              <th>gate_status</th>
              <th>document_status</th>
              <th>inference_track</th>
              <th>payout_ready</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.case_id}>
                <td>
                  <button
                    type="button"
                    className="linkish"
                    onClick={() => onOpenCase(row.case_id)}
                  >
                    {row.case_id}
                  </button>
                </td>
                <td>{row.policy_no}</td>
                <td>
                  <code>{row.gate_status}</code>
                </td>
                <td>
                  <code>{row.document_status ?? "—"}</code>
                </td>
                <td>
                  <code>{row.inference_track}</code>
                </td>
                <td>
                  <code>{String(row.payout_ready)}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
