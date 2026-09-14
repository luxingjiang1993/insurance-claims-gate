/**
 * 检索来源摘要：把 assist citations 收成可展示行。
 * 壳不持有门禁权威；不可采纳引用须诚实标注，不得伪装成已过三联门。
 * Rewrote from: REF-MISSIONS, REF-CASE-HYBRID
 */

export type RetrievalSourceRow = {
  docId: string;
  clauseItem: string;
  docVersion: string;
  title: string;
  quote: string;
  /** true=可采纳；false=不可采纳；null=API 未给 adoptable，勿当合法引用 */
  adoptable: boolean | null;
  adoptLabel: string;
  rejectReason: string | null;
};

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function fieldOrDash(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  const text = String(value).trim();
  return text.length > 0 ? text : "—";
}

function resolveAdoptState(raw: Record<string, unknown>): {
  adoptable: boolean | null;
  adoptLabel: string;
  rejectReason: string | null;
} {
  if (!("adoptable" in raw) || typeof raw.adoptable !== "boolean") {
    return {
      adoptable: null,
      adoptLabel: "采纳状态未知（勿当作合法引用）",
      rejectReason: null,
    };
  }
  if (raw.adoptable === true) {
    return {
      adoptable: true,
      adoptLabel: "可采纳（已过三联门）",
      rejectReason: null,
    };
  }
  const reason =
    raw.reject_reason === null || raw.reject_reason === undefined
      ? null
      : String(raw.reject_reason);
  return {
    adoptable: false,
    adoptLabel: "不可采纳（未过三联门）",
    rejectReason: reason && reason.trim() ? reason : null,
  };
}

/**
 * 将 API 返回的 citations 归一化为作业壳可见的来源摘要行。
 * 不发明未返回字段；不以壳侧逻辑覆盖 adoptable。
 */
export function summarizeRetrievalSources(
  citations: unknown[] | undefined | null,
): RetrievalSourceRow[] {
  if (!citations || citations.length === 0) {
    return [];
  }
  const rows: RetrievalSourceRow[] = [];
  for (const item of citations) {
    const raw = asRecord(item);
    if (!raw) {
      continue;
    }
    const adopt = resolveAdoptState(raw);
    rows.push({
      docId: fieldOrDash(raw.doc_id),
      clauseItem: fieldOrDash(raw.clause_item),
      docVersion: fieldOrDash(raw.doc_version),
      title: fieldOrDash(raw.title),
      quote: fieldOrDash(raw.quote),
      adoptable: adopt.adoptable,
      adoptLabel: adopt.adoptLabel,
      rejectReason: adopt.rejectReason,
    });
  }
  return rows;
}
