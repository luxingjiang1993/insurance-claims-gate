/**
 * AI 辅助区：检索来源摘要展示。
 * 可采纳 vs 不可采纳诚实标注；不伪装成终裁合法 citation。
 * Rewrote from: REF-MISSIONS, REF-CASE-HYBRID
 */
import type { AssistCitation } from "../api/types";
import {
  summarizeRetrievalSources,
  type RetrievalSourceRow,
} from "./retrievalSourceSummary";

type Props = {
  citations: AssistCitation[] | undefined;
  retrievalProfile?: string;
};

function adoptTagClass(row: RetrievalSourceRow): string {
  if (row.adoptable === true) {
    return "tag tag-source-adoptable";
  }
  if (row.adoptable === false) {
    return "tag tag-source-rejected";
  }
  return "tag tag-source-unknown";
}

export function RetrievalSourcesPanel({ citations, retrievalProfile }: Props) {
  const rows = summarizeRetrievalSources(citations);

  if (rows.length === 0) {
    return (
      <div className="retrieval-source-summary" aria-labelledby="retrieval-source-title">
        <div className="panel-title-row">
          <h4 id="retrieval-source-title">检索来源摘要</h4>
        </div>
        <p className="muted">本次辅助未返回可展示的检索来源（citations 为空）。</p>
      </div>
    );
  }

  return (
    <div className="retrieval-source-summary" aria-labelledby="retrieval-source-title">
      <div className="panel-title-row">
        <h4 id="retrieval-source-title">检索来源摘要</h4>
        <span className="tag tag-assist">提名 · 非终裁 citation</span>
      </div>
      <p className="muted">
        以下为 assist API 返回的检索提名（doc / 条款项 / 版本）。
        「可采纳」仅表示已过服务端三联门标记；壳不持有门禁权威，亦不等于裁决草案已落库。
        不可采纳引用须诚实展示，禁止当作已过门的合法引用。
        {retrievalProfile ? (
          <>
            {" "}
            当前 profile：<code>{retrievalProfile}</code>。
          </>
        ) : null}
      </p>
      <table className="data-table retrieval-source-table">
        <caption>检索来源（按 API 字段）</caption>
        <thead>
          <tr>
            <th scope="col">doc</th>
            <th scope="col">条款项</th>
            <th scope="col">版本</th>
            <th scope="col">采纳状态</th>
            <th scope="col">摘要</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.docId}-${row.clauseItem}-${row.docVersion}-${index}`}>
              <td>
                <code>{row.docId}</code>
                {row.title !== "—" ? (
                  <div className="muted source-title">{row.title}</div>
                ) : null}
              </td>
              <td>
                <code>{row.clauseItem}</code>
              </td>
              <td>
                <code>{row.docVersion}</code>
              </td>
              <td>
                <span className={adoptTagClass(row)}>{row.adoptLabel}</span>
                {row.rejectReason ? (
                  <div className="muted">
                    原因：<code>{row.rejectReason}</code>
                  </div>
                ) : null}
              </td>
              <td className="source-quote">
                {row.quote !== "—" ? row.quote : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
