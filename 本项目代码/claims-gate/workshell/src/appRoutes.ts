/**
 * 作业壳路由名常量：评测入口独立于门禁 evaluate 主路径。
 * Rewrote from: REF-MISSIONS, REF-CASE-EVAL-ADVISOR
 */

export type AppRouteName =
  | "login"
  | "list"
  | "detail"
  | "evalOps"
  | "providerStatus";

/** 主导航项：评测不得挂在 evaluate 主按钮背后。 */
export const SHELL_NAV_ITEMS: ReadonlyArray<{
  route: Exclude<AppRouteName, "login" | "detail">;
  label: string;
}> = [
  { route: "list", label: "案件作业" },
  { route: "providerStatus", label: "连接状态" },
  { route: "evalOps", label: "评测" },
];

export function isEvalOpsRoute(name: AppRouteName): boolean {
  return name === "evalOps";
}

export function isProviderStatusRoute(name: AppRouteName): boolean {
  return name === "providerStatus";
}
