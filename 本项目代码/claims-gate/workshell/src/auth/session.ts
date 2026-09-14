/** 会话令牌本地持久化（演示用；无 SSO）。 */

import type { LoginResult } from "../api/types";

const STORAGE_KEY = "claims-gate-workshell-session";

export function loadSession(): LoginResult | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as LoginResult;
    if (!parsed.session_token || !parsed.username || !parsed.role) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function saveSession(session: LoginResult): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}

/** viewer 在本票范围内保持只读：壳内不暴露写操作入口。 */
export function isReadonlyRole(role: string): boolean {
  return role === "viewer";
}
