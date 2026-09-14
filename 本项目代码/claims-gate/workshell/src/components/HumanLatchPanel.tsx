import { useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { DecisionDraft, LoginResult } from "../api/types";
import { isReadonlyRole } from "../auth/session";
import { ApiErrorView } from "./ApiErrorView";

type Props = {
  api: ClaimsApiClient;
  session: LoginResult;
  caseId: string;
  draft: DecisionDraft | null;
  onClaimUpdated: () => Promise<void>;
  onTokenIssued: (token: string) => void;
};

/**
 * 人闸批准/驳回：令牌来自 API 响应；adjuster 点击后由服务端拒绝并原样展示。
 * Rewrote from: REF-MISSIONS
 */
export function HumanLatchPanel({
  api,
  session,
  caseId,
  draft,
  onClaimUpdated,
  onTokenIssued,
}: Props) {
  const readonly = isReadonlyRole(session.role);
  const [secondApprover, setSecondApprover] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [okMessage, setOkMessage] = useState<string | null>(null);
  const [issuedToken, setIssuedToken] = useState<string | null>(null);
  const [error, setError] = useState<ApiClientError | Error | null>(null);

  async function runWrite(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    setOkMessage(null);
    try {
      await action();
      await onClaimUpdated();
    } catch (err) {
      setOkMessage(null);
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="action-panel">
      <h2>人闸</h2>
      <p className="muted">
        仅 supervisor 可批准/驳回应闸类型并获得人闸令牌。adjuster 可点批准以演示 API 拒绝；本壳不签发令牌。批准成功不等于出款。
      </p>
      <dl className="detail-grid">
        <dt>human_latch_required</dt>
        <dd>
          <code>{String(draft?.human_latch_required ?? false)}</code>
        </dd>
        <dt>latch_level_label</dt>
        <dd>
          <code>{draft?.latch_level_label ?? "—"}</code>
        </dd>
        <dt>dual_token_required</dt>
        <dd>
          <code>{String(draft?.dual_token_required ?? false)}</code>
        </dd>
        <dt>当前草案令牌</dt>
        <dd>
          <code>{draft?.human_latch_token ?? "—"}</code>
        </dd>
      </dl>
      {okMessage ? (
        <p className="ok-banner" role="status">
          {okMessage}
        </p>
      ) : null}
      {issuedToken ? (
        <p className="ok-banner" role="status">
          人闸令牌（API 返回，非壳内生成）：<code>{issuedToken}</code>
        </p>
      ) : null}
      {error ? (
        <div>
          <p className="error-title">未记为成功</p>
          <ApiErrorView error={error} />
        </div>
      ) : null}
      {readonly ? null : (
        <div className="form-grid">
          <label>
            第二批准人（D 档上浮时由 API 校验）
            <input
              value={secondApprover}
              onChange={(e) => setSecondApprover(e.target.value)}
              disabled={busy}
            />
          </label>
          <label>
            驳回原因
            <input
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              disabled={busy}
            />
          </label>
          <div className="header-actions">
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                runWrite(async () => {
                  const result = await api.approveHumanLatch(caseId, {
                    approved_by: session.username,
                    second_approver: secondApprover.trim() || undefined,
                  });
                  setIssuedToken(result.human_latch_token);
                  onTokenIssued(result.human_latch_token);
                  setOkMessage(
                    `人闸批准已被 API 接受。payout_ready=${String(result.payout_ready)}。`,
                  );
                })
              }
            >
              批准人闸
            </button>
            <button
              type="button"
              className="secondary"
              disabled={busy}
              onClick={() =>
                runWrite(async () => {
                  const result = await api.rejectHumanLatch(caseId, {
                    rejected_by: session.username,
                    reason: rejectReason,
                  });
                  setIssuedToken(null);
                  onTokenIssued("");
                  setOkMessage(
                    `人闸驳回已被 API 接受。gate_status=${result.gate_status}。`,
                  );
                })
              }
            >
              驳回人闸
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
