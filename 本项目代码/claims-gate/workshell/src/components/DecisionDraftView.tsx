import { ApiClientError } from "../api/client";
import type { DecisionDraft } from "../api/types";
import { ApiErrorView } from "./ApiErrorView";

type Props = {
  draft: DecisionDraft | null;
  loadError: ApiClientError | Error | null;
};

/** 裁决草案只读展示：字段来自 GET /decision 或 evaluate 响应。 */
export function DecisionDraftView({ draft, loadError }: Props) {
  return (
    <section className="action-panel" aria-labelledby="decision-draft-title">
      <div className="panel-title-row">
        <h2 id="decision-draft-title">裁决草案</h2>
        <span className="tag tag-decision">裁决草案 · 规则路径</span>
      </div>
      <p className="muted">
        系统经规则 evaluate 产出的建议，不具对外最终效力；与上方「AI 辅助建议」分标签，权威以服务端门禁与人闸为准。
      </p>
      {!draft && loadError instanceof ApiClientError && loadError.status === 404 ? (
        <p className="muted">尚无裁决草案（请先 evaluate）。</p>
      ) : null}
      {loadError &&
      !(loadError instanceof ApiClientError && loadError.status === 404) ? (
        <ApiErrorView error={loadError} />
      ) : null}
      {draft ? (
        <>
          <dl className="detail-grid">
            <dt>decision_type</dt>
            <dd>
              <code>{draft.decision_type}</code>
            </dd>
            <dt>gate_status</dt>
            <dd>
              <code>{draft.gate_status}</code>
            </dd>
            <dt>document_status</dt>
            <dd>
              <code>{draft.document_status ?? "—"}</code>
            </dd>
            <dt>inference_track</dt>
            <dd>
              <code>{draft.inference_track}</code>
            </dd>
            <dt>payout_ready</dt>
            <dd>
              <code>{String(draft.payout_ready)}</code>
            </dd>
            <dt>one_shot_hash</dt>
            <dd>
              <code>{draft.one_shot_hash ?? "—"}</code>
            </dd>
            <dt>appeal_path</dt>
            <dd>{draft.appeal_path ?? "—"}</dd>
            <dt>reason_summary</dt>
            <dd>{draft.reason_summary ?? "—"}</dd>
          </dl>
          {draft.supplement_checklist && draft.supplement_checklist.length > 0 ? (
            <table className="data-table">
              <caption>supplement_checklist（服务端冻结清单）</caption>
              <thead>
                <tr>
                  <th>code</th>
                  <th>name_zh</th>
                  <th>required</th>
                </tr>
              </thead>
              <tbody>
                {draft.supplement_checklist.map((item) => (
                  <tr key={item.code}>
                    <td>
                      <code>{item.code}</code>
                    </td>
                    <td>{item.name_zh ?? "—"}</td>
                    <td>{item.required === undefined ? "—" : String(item.required)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
          {draft.citations && draft.citations.length > 0 ? (
            <pre className="json-block">{JSON.stringify(draft.citations, null, 2)}</pre>
          ) : null}
          {draft.calc_steps && draft.calc_steps.length > 0 ? (
            <pre className="json-block">{JSON.stringify(draft.calc_steps, null, 2)}</pre>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
