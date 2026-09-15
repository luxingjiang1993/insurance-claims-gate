/**
 * 辅助拒答展示文案：只映射 API 枚举，不发明壳侧权威。
 * Rewrote from: REF-MISSIONS
 */

const ABSTAIN_REASON_LABELS: Record<string, string> = {
  conflict: "规则与检索冲突",
  handbook_alone: "手册不得单独对外拒赔",
  low_confidence: "检索置信不足",
  citation_unfaithful: "引用无法支撑断言",
};

export function formatAbstainReason(
  reason: string | null | undefined,
): string {
  if (!reason) {
    return "原因未返回";
  }
  return ABSTAIN_REASON_LABELS[reason] ?? reason;
}

/** 仅 draft 且存在可采纳 citation 时可点采纳。 */
export function canAdoptAssistSuggestion(input: {
  assist_disposition?: string | null;
  hasAdoptableCitation: boolean;
}): boolean {
  if (input.assist_disposition === "abstain") {
    return false;
  }
  return input.hasAdoptableCitation;
}
