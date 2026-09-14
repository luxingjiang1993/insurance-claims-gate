import { useEffect, useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { DecisionDraft, DocumentExportResult } from "../api/types";
import { isReadonlyRole } from "../auth/session";
import { ApiErrorView } from "./ApiErrorView";

type Props = {
  api: ClaimsApiClient;
  role: string;
  caseId: string;
  draft: DecisionDraft | null;
  latchToken: string;
  onLatchTokenChange: (token: string) => void;
  onClaimUpdated: () => Promise<void>;
};

function defaultDocumentType(draft: DecisionDraft | null): string {
  if (draft?.decision_type === "reject_draft") {
    return "reject_notice";
  }
  if (draft?.decision_type === "reduce") {
    return "reduction_notice";
  }
  if (draft?.decision_type === "supplement") {
    return "supplement_notice";
  }
  return "reject_notice";
}

/**
 * 文书分态：DRAFT_EXPORT 与 EXTERNAL_NOTIFY 分开展示，失败不记成功。
 * Rewrote from: REF-MISSIONS
 */
export function DocumentExportPanel({
  api,
  role,
  caseId,
  draft,
  latchToken,
  onLatchTokenChange,
  onClaimUpdated,
}: Props) {
  const readonly = isReadonlyRole(role);
  const [documentType, setDocumentType] = useState(() =>
    defaultDocumentType(draft),
  );
  const [documentStatus, setDocumentStatus] = useState("DRAFT_EXPORT");

  useEffect(() => {
    setDocumentType(defaultDocumentType(draft));
  }, [draft?.decision_type]);
  const [busy, setBusy] = useState(false);
  const [okMessage, setOkMessage] = useState<string | null>(null);
  const [error, setError] = useState<ApiClientError | Error | null>(null);
  const [exported, setExported] = useState<DocumentExportResult | null>(null);

  async function exportNow() {
    setBusy(true);
    setError(null);
    setOkMessage(null);
    try {
      const result = await api.exportDocument(caseId, {
        document_type: documentType,
        document_status: documentStatus,
        human_latch_token: latchToken.trim() || undefined,
      });
      setExported(result);
      setOkMessage(
        `文书导出已被 API 接受。document_status=${result.document_status}（与请求分态对照，壳未改写）。`,
      );
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
      <h2>文书分态</h2>
      <p className="muted">
        DRAFT_EXPORT 为内部预览；EXTERNAL_NOTIFY 为对外通知。二者不得互相当作已完成。拒赔草稿可无人闸预览；升对外须人闸令牌，否则 API 拒绝且本区不点亮成功。
      </p>
      {okMessage ? (
        <p className="ok-banner" role="status">
          {okMessage}
        </p>
      ) : null}
      {error ? (
        <div>
          <p className="error-title">未记为成功（本次未升对外）</p>
          <ApiErrorView error={error} />
        </div>
      ) : null}
      {readonly ? (
        <p className="muted">viewer 无文书导出入口。</p>
      ) : (
        <div className="form-grid">
          <label>
            document_type
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              disabled={busy}
            >
              <option value="reject_notice">reject_notice</option>
              <option value="supplement_notice">supplement_notice</option>
              <option value="reduction_notice">reduction_notice</option>
            </select>
          </label>
          <label>
            document_status（分态原样提交）
            <select
              value={documentStatus}
              onChange={(e) => setDocumentStatus(e.target.value)}
              disabled={busy}
            >
              <option value="DRAFT_EXPORT">DRAFT_EXPORT（内部预览）</option>
              <option value="EXTERNAL_NOTIFY">EXTERNAL_NOTIFY（对外通知）</option>
            </select>
          </label>
          <label>
            human_latch_token（升 EXTERNAL_NOTIFY 时提交；草稿可空）
            <input
              value={latchToken}
              onChange={(e) => onLatchTokenChange(e.target.value)}
              disabled={busy}
            />
          </label>
          <div className="header-actions">
            <button type="button" disabled={busy} onClick={() => void exportNow()}>
              导出 / 预览文书
            </button>
          </div>
        </div>
      )}
      {exported ? (
        <>
          <p className="muted">
            最近一次成功导出（失败请求不会改写此块，也不把 DRAFT_EXPORT 标成 EXTERNAL_NOTIFY）。
          </p>
          <dl className="detail-grid">
            <dt>API document_type</dt>
            <dd>
              <code>{exported.document_type}</code>
            </dd>
            <dt>API document_status</dt>
            <dd>
              <code>{exported.document_status}</code>
            </dd>
            <dt>payout_ready</dt>
            <dd>
              <code>{String(exported.payout_ready ?? "—")}</code>
            </dd>
          </dl>
          <pre className="json-block">{JSON.stringify(exported, null, 2)}</pre>
        </>
      ) : null}
    </section>
  );
}
