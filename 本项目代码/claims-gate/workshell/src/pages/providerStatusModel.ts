/**
 * Provider 连接状态：纯展示映射（作业壳只依赖 API 字段）。
 * Rewrote from: REF-MISSIONS（质询 P-CFG β）
 */

import type {
  ProviderConnectionStatus,
  ProviderServiceStatus,
} from "../api/types";

export type ProviderStatusRow = {
  id: "llm" | "embedding" | "langsmith";
  title: string;
  configured: boolean;
  degraded: boolean;
  modelOrProject: string;
  detail: string;
};

function serviceDetail(
  id: ProviderStatusRow["id"],
  svc: ProviderServiceStatus,
  status: ProviderConnectionStatus,
): string {
  const parts: string[] = [];
  if (id === "embedding") {
    parts.push(`provider=${status.embedding.provider}`);
    if (status.embedding.semantic === false) {
      parts.push("非语义（local 哈希）");
    } else if (status.embedding.semantic === true) {
      parts.push("语义 cloud");
    }
  }
  if (id === "langsmith") {
    parts.push(`enabled=${String(svc.enabled ?? false)}`);
    if (svc.tracing_v2) {
      parts.push(`tracing_v2=${svc.tracing_v2}`);
    }
  }
  if (svc.degrade_reason) {
    parts.push(`原因: ${svc.degrade_reason}`);
  }
  if (svc.base_url) {
    parts.push(`base_url=${svc.base_url}`);
  }
  return parts.join(" · ") || "—";
}

/** 将 API 肖像压成三行只读表；不含 Key。 */
export function toProviderStatusRows(
  status: ProviderConnectionStatus,
): ProviderStatusRow[] {
  const specs: Array<{
    id: ProviderStatusRow["id"];
    title: string;
    svc: ProviderServiceStatus;
    modelOrProject: string;
  }> = [
    {
      id: "llm",
      title: "LLM",
      svc: status.llm,
      modelOrProject: status.llm.model || "—",
    },
    {
      id: "embedding",
      title: "Embedding",
      svc: status.embedding,
      modelOrProject: status.embedding.model || "—",
    },
    {
      id: "langsmith",
      title: "LangSmith",
      svc: status.langsmith,
      modelOrProject: status.langsmith.project || "—",
    },
  ];
  return specs.map((s) => ({
    id: s.id,
    title: s.title,
    configured: Boolean(s.svc.configured),
    degraded: Boolean(s.svc.degraded),
    modelOrProject: s.modelOrProject,
    detail: serviceDetail(s.id, s.svc, status),
  }));
}

/** 状态徽章文案（已配置 / 降级）。 */
export function statusBadgeLabel(row: ProviderStatusRow): string {
  if (row.degraded) {
    return row.configured ? "已配置·降级" : "未配置·降级";
  }
  return row.configured ? "已配置" : "未配置";
}
