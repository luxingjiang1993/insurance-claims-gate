import { useEffect, useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { ClaimDetail, LoginResult } from "../api/types";
import { ApiErrorView } from "../components/ApiErrorView";
import { ReadonlyBanner } from "../components/ReadonlyBanner";

type Props = {
  api: ClaimsApiClient;
  session: LoginResult;
  caseId: string;
  onBack: () => void;
  onLogout: () => void;
};

export function CaseDetailPage({
  api,
  session,
  caseId,
  onBack,
  onLogout,
}: Props) {
  const [claim, setClaim] = useState<ClaimDetail | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<ApiClientError | Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setBusy(true);
    setError(null);
    api
      .getClaim(caseId)
      .then((row) => {
        if (!cancelled) {
          setClaim(row);
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
  }, [api, caseId]);

  return (
    <section className="card">
      <header className="page-header">
        <div>
          <h1>案件详情</h1>
          <p className="muted">
            {session.display_name}（{session.role}）· {caseId}
          </p>
        </div>
        <div className="header-actions">
          <button type="button" className="secondary" onClick={onBack}>
            返回列表
          </button>
          <button type="button" className="secondary" onClick={onLogout}>
            退出
          </button>
        </div>
      </header>
      <ReadonlyBanner role={session.role} />
      {busy ? <p className="muted">加载中…</p> : null}
      {error ? <ApiErrorView error={error} /> : null}
      {claim ? (
        <dl className="detail-grid">
          <dt>case_id</dt>
          <dd>
            <code>{claim.case_id}</code>
          </dd>
          <dt>policy_no</dt>
          <dd>{claim.policy_no}</dd>
          <dt>product_code</dt>
          <dd>{claim.product_code}</dd>
          <dt>clause_version</dt>
          <dd>{claim.clause_version}</dd>
          <dt>loss_date</dt>
          <dd>{claim.loss_date}</dd>
          <dt>claim_amount_claimed</dt>
          <dd>{claim.claim_amount_claimed}</dd>
          <dt>gate_status</dt>
          <dd>
            <code>{claim.gate_status}</code>
          </dd>
          <dt>document_status</dt>
          <dd>
            <code>{claim.document_status ?? "—"}</code>
          </dd>
          <dt>inference_track</dt>
          <dd>
            <code>{claim.inference_track}</code>
          </dd>
          <dt>payout_ready</dt>
          <dd>
            <code>{String(claim.payout_ready)}</code>
          </dd>
          <dt>material_codes</dt>
          <dd>
            <code>{claim.material_codes.join(", ") || "—"}</code>
          </dd>
        </dl>
      ) : null}
      {/* 本票范围：只读浏览；写操作（evaluate / 人闸等）留给后续作业壳票 */}
    </section>
  );
}
