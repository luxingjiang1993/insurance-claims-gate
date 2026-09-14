import { useCallback, useEffect, useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { ClaimDetail, DecisionDraft, LoginResult } from "../api/types";
import { AiAssistPanel } from "../components/AiAssistPanel";
import { ApiErrorView } from "../components/ApiErrorView";
import { CaseLedgerPanel } from "../components/CaseLedgerPanel";
import { DecisionDraftView } from "../components/DecisionDraftView";
import { DocumentExportPanel } from "../components/DocumentExportPanel";
import { HumanLatchPanel } from "../components/HumanLatchPanel";
import { ReadonlyBanner } from "../components/ReadonlyBanner";
import { ScRulePanel } from "../components/ScRulePanel";

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
  const [draft, setDraft] = useState<DecisionDraft | null>(null);
  const [draftError, setDraftError] = useState<ApiClientError | Error | null>(
    null,
  );
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<ApiClientError | Error | null>(null);
  const [latchToken, setLatchToken] = useState("");
  const [ledgerRefreshKey, setLedgerRefreshKey] = useState(0);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    setDraftError(null);
    try {
      const row = await api.getClaim(caseId);
      setClaim(row);
      try {
        const nextDraft = await api.getDecision(caseId);
        setDraft(nextDraft);
      } catch (err) {
        setDraft(null);
        setDraftError(err instanceof Error ? err : new Error(String(err)));
      }
      setLedgerRefreshKey((n) => n + 1);
    } catch (err) {
      setClaim(null);
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }, [api, caseId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (draft?.human_latch_token) {
      setLatchToken(draft.human_latch_token);
    }
  }, [draft?.human_latch_token]);

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
        <>
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
          <ScRulePanel
            api={api}
            role={session.role}
            caseId={caseId}
            claim={claim}
            draft={draft}
            onClaimUpdated={setClaim}
            onDraftUpdated={(next) => {
              setDraft(next);
              setDraftError(null);
              setLedgerRefreshKey((n) => n + 1);
            }}
          />
          <AiAssistPanel
            api={api}
            role={session.role}
            caseId={caseId}
            onDraftUpdated={(next) => {
              setDraft(next);
              setDraftError(null);
              setLedgerRefreshKey((n) => n + 1);
            }}
            onClaimUpdated={async () => {
              await load();
            }}
          />
          <DecisionDraftView draft={draft} loadError={draftError} />
          <HumanLatchPanel
            api={api}
            session={session}
            caseId={caseId}
            draft={draft}
            onTokenIssued={setLatchToken}
            onClaimUpdated={async () => {
              await load();
            }}
          />
          <DocumentExportPanel
            api={api}
            role={session.role}
            caseId={caseId}
            draft={draft}
            latchToken={latchToken}
            onLatchTokenChange={setLatchToken}
            onClaimUpdated={async () => {
              await load();
            }}
          />
          <CaseLedgerPanel
            api={api}
            caseId={caseId}
            refreshKey={ledgerRefreshKey}
          />
        </>
      ) : null}
    </section>
  );
}
