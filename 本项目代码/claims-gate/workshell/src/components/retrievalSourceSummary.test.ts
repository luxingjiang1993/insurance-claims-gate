/**
 * 接缝：AI 辅助区检索来源摘要（doc / 条款项 / 版本 + 可采纳标注）。
 * Rewrote from: REF-MISSIONS, REF-CASE-HYBRID
 */
import { describe, expect, it } from "vitest";

import { summarizeRetrievalSources } from "./retrievalSourceSummary";

describe("summarizeRetrievalSources", () => {
  it("maps API citation fields into visible doc / clause / version rows", () => {
    const rows = summarizeRetrievalSources([
      {
        doc_id: "PA-ACC-2024.1",
        clause_item: "2.1",
        doc_version: "2024.1",
        title: "意外伤害保险条款",
        adoptable: true,
        quote: "因疾病导致的摔伤…",
      },
      {
        doc_id: "FAKE-DOC",
        clause_item: "9.9",
        doc_version: "9.9",
        title: "库外提名",
        adoptable: false,
        reject_reason: "CITATION_NOT_IN_KB",
      },
    ]);

    expect(rows).toHaveLength(2);
    expect(rows[0]).toMatchObject({
      docId: "PA-ACC-2024.1",
      clauseItem: "2.1",
      docVersion: "2024.1",
      title: "意外伤害保险条款",
      adoptable: true,
      adoptLabel: "可采纳（已过三联门）",
      rejectReason: null,
    });
    expect(rows[1]).toMatchObject({
      docId: "FAKE-DOC",
      clauseItem: "9.9",
      docVersion: "9.9",
      adoptable: false,
      adoptLabel: "不可采纳（未过三联门）",
      rejectReason: "CITATION_NOT_IN_KB",
    });
  });

  it("does not treat missing or non-boolean adoptable as adoptable", () => {
    const missing = summarizeRetrievalSources([
      {
        doc_id: "PA-ACC-2024.1",
        clause_item: "3.1",
        doc_version: "2024.1",
      },
    ]);
    expect(missing[0].adoptable).toBeNull();
    expect(missing[0].adoptLabel).toBe("采纳状态未知（勿当作合法引用）");

    const weird = summarizeRetrievalSources([
      {
        doc_id: "PA-ACC-2024.1",
        clause_item: "3.2",
        doc_version: "2024.1",
        adoptable: "yes",
      },
    ]);
    expect(weird[0].adoptable).toBeNull();
    expect(weird[0].adoptLabel).toBe("采纳状态未知（勿当作合法引用）");
  });

  it("returns empty list when citations absent", () => {
    expect(summarizeRetrievalSources(undefined)).toEqual([]);
    expect(summarizeRetrievalSources([])).toEqual([]);
  });

  it("skips non-object entries without inventing fields", () => {
    const rows = summarizeRetrievalSources([null, "x", 1, { doc_id: "D1" }]);
    expect(rows).toHaveLength(1);
    expect(rows[0].docId).toBe("D1");
    expect(rows[0].clauseItem).toBe("—");
    expect(rows[0].docVersion).toBe("—");
  });
});
