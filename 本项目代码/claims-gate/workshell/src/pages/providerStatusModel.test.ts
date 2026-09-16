/**
 * 接缝：连接状态只读映射（不断言 React state；永不假设 Key 字段）。
 * Rewrote from: REF-MISSIONS
 */
import { describe, expect, it } from "vitest";

import type { ProviderConnectionStatus } from "../api/types";
import {
  statusBadgeLabel,
  toProviderStatusRows,
} from "./providerStatusModel";

const SAMPLE: ProviderConnectionStatus = {
  llm: {
    configured: false,
    degraded: true,
    degrade_reason: "missing_openai_api_key",
    model: "gpt-4o-mini",
    base_url: "https://api.openai.com/v1",
  },
  embedding: {
    configured: true,
    degraded: false,
    provider: "local",
    model: "deterministic_local_non_semantic",
    semantic: false,
  },
  langsmith: {
    configured: false,
    enabled: false,
    degraded: false,
    project: "claims-gate",
    tracing_v2: "false",
  },
  hint: "只读连接状态；永不回显 API Key",
};

describe("providerStatusModel", () => {
  it("maps API fields into three readable rows without key fields", () => {
    const rows = toProviderStatusRows(SAMPLE);
    expect(rows).toHaveLength(3);
    expect(rows.map((r) => r.id)).toEqual(["llm", "embedding", "langsmith"]);
    expect(rows[0]?.modelOrProject).toBe("gpt-4o-mini");
    expect(rows[1]?.detail).toContain("非语义");
    expect(rows[2]?.modelOrProject).toBe("claims-gate");
    const blob = JSON.stringify(rows);
    expect(blob).not.toMatch(/"api_key"\s*:/);
    expect(blob).not.toMatch(/sk-/);
    for (const row of rows) {
      expect(row).not.toHaveProperty("api_key");
    }
  });

  it("labels degraded vs configured honestly", () => {
    const rows = toProviderStatusRows(SAMPLE);
    expect(statusBadgeLabel(rows[0]!)).toBe("未配置·降级");
    expect(statusBadgeLabel(rows[1]!)).toBe("已配置");
    expect(statusBadgeLabel(rows[2]!)).toBe("未配置");
  });
});
