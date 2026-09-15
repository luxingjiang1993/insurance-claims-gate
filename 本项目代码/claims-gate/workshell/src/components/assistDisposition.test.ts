/**
 * 接缝：辅助拒答 disposition 展示与采纳开关（只读 API 字段）。
 */
import { describe, expect, it } from "vitest";

import {
  canAdoptAssistSuggestion,
  formatAbstainReason,
} from "./assistDisposition";

describe("assistDisposition", () => {
  it("maps abstain_reason enum to user-visible Chinese labels", () => {
    expect(formatAbstainReason("conflict")).toBe("规则与检索冲突");
    expect(formatAbstainReason("handbook_alone")).toBe(
      "手册不得单独对外拒赔",
    );
    expect(formatAbstainReason("low_confidence")).toBe("检索置信不足");
    expect(formatAbstainReason("citation_unfaithful")).toBe(
      "引用无法支撑断言",
    );
  });

  it("disables adopt when assist_disposition is abstain", () => {
    expect(
      canAdoptAssistSuggestion({
        assist_disposition: "abstain",
        hasAdoptableCitation: true,
      }),
    ).toBe(false);
  });

  it("allows adopt only for draft with adoptable citation", () => {
    expect(
      canAdoptAssistSuggestion({
        assist_disposition: "draft",
        hasAdoptableCitation: true,
      }),
    ).toBe(true);
    expect(
      canAdoptAssistSuggestion({
        assist_disposition: "draft",
        hasAdoptableCitation: false,
      }),
    ).toBe(false);
  });
});
