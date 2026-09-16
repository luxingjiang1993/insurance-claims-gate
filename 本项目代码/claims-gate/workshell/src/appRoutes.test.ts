/**
 * 接缝：作业壳独立「评测」与「连接状态」导航。
 * Rewrote from: REF-MISSIONS, REF-CASE-EVAL-ADVISOR
 */
import { describe, expect, it } from "vitest";

import {
  SHELL_NAV_ITEMS,
  isEvalOpsRoute,
  isProviderStatusRoute,
} from "./appRoutes";

describe("appRoutes shell nav", () => {
  it("exposes 案件作业 / 连接状态 / 评测 as independent items", () => {
    const labels = SHELL_NAV_ITEMS.map((i) => i.label);
    expect(labels).toContain("评测");
    expect(labels).toContain("案件作业");
    expect(labels).toContain("连接状态");
    expect(SHELL_NAV_ITEMS.find((i) => i.label === "评测")?.route).toBe(
      "evalOps",
    );
    expect(
      SHELL_NAV_ITEMS.find((i) => i.label === "连接状态")?.route,
    ).toBe("providerStatus");
  });

  it("treats evalOps and providerStatus as distinct from claim gate paths", () => {
    expect(isEvalOpsRoute("evalOps")).toBe(true);
    expect(isEvalOpsRoute("list")).toBe(false);
    expect(isEvalOpsRoute("detail")).toBe(false);
    expect(isProviderStatusRoute("providerStatus")).toBe(true);
    expect(isProviderStatusRoute("evalOps")).toBe(false);
  });
});
