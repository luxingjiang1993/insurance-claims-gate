/**
 * 接缝：作业壳独立「评测」导航（不挂在 evaluate 主按钮背后）。
 * Rewrote from: REF-MISSIONS, REF-CASE-EVAL-ADVISOR
 */
import { describe, expect, it } from "vitest";

import { SHELL_NAV_ITEMS, isEvalOpsRoute } from "./appRoutes";

describe("appRoutes eval entry", () => {
  it("exposes an independent 评测 nav item alongside 案件作业", () => {
    const labels = SHELL_NAV_ITEMS.map((i) => i.label);
    expect(labels).toContain("评测");
    expect(labels).toContain("案件作业");
    expect(SHELL_NAV_ITEMS.find((i) => i.label === "评测")?.route).toBe(
      "evalOps",
    );
  });

  it("treats evalOps as a distinct route from claim gate paths", () => {
    expect(isEvalOpsRoute("evalOps")).toBe(true);
    expect(isEvalOpsRoute("list")).toBe(false);
    expect(isEvalOpsRoute("detail")).toBe(false);
  });
});
