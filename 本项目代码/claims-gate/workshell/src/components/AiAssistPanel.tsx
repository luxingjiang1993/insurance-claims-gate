import { useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { AssistSuggestion, DecisionDraft } from "../api/types";
import { isReadonlyRole } from "../auth/session";
import { ApiErrorView } from "./ApiErrorView";

type Props = {
  api: ClaimsApiClient;
  role: string;
  caseId: string;
  onDraftUpdated: (draft: DecisionDraft) => void;
  onClaimUpdated: () => Promise<void>;
};

/**
 * AI 辅助建议区：须显式点击才调用；与裁决草案分标签；采纳走规则校验。
 * Rewrote from: REF-MISSIONS, REF-CASE-HYBRID
 */
export function AiAssistPanel({
  api,
  role,
  caseId,
  onDraftUpdated,
  onClaimUpdated,
}: Props) {
  const readonly = isReadonlyRole(role);
  const [query, setQuery] = useState("");
  const [suggestion, setSuggestion] = useState<AssistSuggestion | null>(null);
  const [busy, setBusy] = useState(false);
  const [okMessage, setOkMessage] = useState<string | null>(null);
  const [error, setError] = useState<ApiClientError | Error | null>(null);

  if (readonly) {
    return null;
  }

  async function runAssist() {
    const trimmed = query.trim();
    if (!trimmed) {
      setError(new Error("请先填写查询后再点击「AI 辅助建议」。"));
      return;
    }
    setBusy(true);
    setError(null);
    setOkMessage(null);
    try {
      const next = await api.assistClaim(caseId, { query: trimmed });
      setSuggestion(next);
      if (next.degraded) {
        setOkMessage(null);
      } else {
        setOkMessage("已返回 AI 辅助建议（非终裁）。");
      }
    } catch (err) {
      setOkMessage(null);
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  async function runAdopt() {
    if (!suggestion) {
      return;
    }
    setBusy(true);
    setError(null);
    setOkMessage(null);
    try {
      const draft = await api.adoptAssist(caseId, {
        assist_invocation_id: suggestion.assist_invocation_id,
        draft_text: suggestion.draft_text,
        suggested_stance: suggestion.suggested_stance,
        retrieval_profile: suggestion.retrieval_profile,
      });
      onDraftUpdated(draft);
      await onClaimUpdated();
      setOkMessage(
        "已送交规则校验（采纳）。下方「裁决草案」为 evaluate 权威结果，非辅助原文直写。",
      );
    } catch (err) {
      setOkMessage(null);
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="action-panel" aria-labelledby="assist-panel-title">
      <div className="panel-title-row">
        <h2 id="assist-panel-title">AI 辅助建议</h2>
        <span className="tag tag-assist">辅助建议 · 非终裁</span>
      </div>
      <p className="muted">
        本区为<strong>裁决辅助</strong>，不替代持牌核赔终裁；与下方「裁决草案」分标签展示。
        须显式点击「AI 辅助建议」才会调用；无 Key 时服务端降级提示可见，规则路径仍可用。
        禁止将本区理解为秒赔或无人赔付。
      </p>
      {okMessage ? (
        <p className="ok-banner" role="status">
          {okMessage}
        </p>
      ) : null}
      {error ? (
        <div>
          <p className="error-title">未记为成功</p>
          <ApiErrorView error={error} />
        </div>
      ) : null}

      <div className="form-grid">
        <label>
          辅助查询（关键词提名；不会静默调用）
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={busy}
            rows={3}
            placeholder="例如：疾病导致的摔伤是否属于责任免除"
          />
        </label>
        <div className="header-actions">
          <button type="button" disabled={busy} onClick={() => void runAssist()}>
            AI 辅助建议
          </button>
        </div>
      </div>

      {suggestion ? (
        <div className="assist-result">
          <div className="panel-title-row">
            <h3>本次辅助结果</h3>
            <span className="tag tag-assist">辅助建议</span>
          </div>
          {suggestion.degraded ? (
            <p className="warn-banner" role="status">
              降级
              {suggestion.degrade_reason ? `：${suggestion.degrade_reason}` : ""}
              。规则路径作业区仍可继续 evaluate / 人闸。
            </p>
          ) : null}
          <dl className="detail-grid">
            <dt>assist_invocation_id</dt>
            <dd>
              <code>{suggestion.assist_invocation_id}</code>
            </dd>
            <dt>used_llm</dt>
            <dd>
              <code>{String(suggestion.used_llm)}</code>
            </dd>
            <dt>degraded</dt>
            <dd>
              <code>{String(suggestion.degraded)}</code>
            </dd>
            <dt>suggested_stance</dt>
            <dd>
              <code>{suggestion.suggested_stance ?? "—"}</code>
            </dd>
            <dt>inference_track</dt>
            <dd>
              <code>{suggestion.inference_track}</code>
            </dd>
          </dl>
          <pre className="json-block">{suggestion.draft_text}</pre>
          {suggestion.citations && suggestion.citations.length > 0 ? (
            <pre className="json-block">
              {JSON.stringify(suggestion.citations, null, 2)}
            </pre>
          ) : null}
          <div className="action-row">
            <button
              type="button"
              disabled={busy}
              onClick={() => void runAdopt()}
            >
              送交规则校验（采纳）
            </button>
          </div>
          <p className="muted">
            采纳不会直写权威裁决字段；仅通过服务端再次 evaluate。失败时拒绝体原样展示。
          </p>
        </div>
      ) : (
        <p className="muted">尚未请求辅助建议（无默认静默调用）。</p>
      )}
    </section>
  );
}
