import { useMemo, useState } from "react";

import { createClaimsApiClient } from "./api/client";
import type { LoginResult } from "./api/types";
import {
  clearSession,
  loadSession,
  saveSession,
} from "./auth/session";
import { CaseDetailPage } from "./pages/CaseDetailPage";
import { CaseListPage } from "./pages/CaseListPage";
import { LoginPage } from "./pages/LoginPage";

const API_BASE =
  import.meta.env.VITE_CLAIMS_API_BASE?.trim() || "http://127.0.0.1:8000";

type Route =
  | { name: "login" }
  | { name: "list" }
  | { name: "detail"; caseId: string };

export default function App() {
  const [session, setSession] = useState<LoginResult | null>(() => loadSession());
  const [route, setRoute] = useState<Route>(() =>
    loadSession() ? { name: "list" } : { name: "login" },
  );

  const api = useMemo(
    () =>
      createClaimsApiClient({
        baseUrl: API_BASE,
        getToken: () => loadSession()?.session_token ?? null,
      }),
    [],
  );

  function handleLoggedIn(next: LoginResult) {
    saveSession(next);
    setSession(next);
    setRoute({ name: "list" });
  }

  function handleLogout() {
    clearSession();
    setSession(null);
    setRoute({ name: "login" });
  }

  if (!session || route.name === "login") {
    return (
      <main className="app-shell">
        <LoginPage api={api} onLoggedIn={handleLoggedIn} />
      </main>
    );
  }

  if (route.name === "detail") {
    return (
      <main className="app-shell">
        <CaseDetailPage
          api={api}
          session={session}
          caseId={route.caseId}
          onBack={() => setRoute({ name: "list" })}
          onLogout={handleLogout}
        />
      </main>
    );
  }

  return (
    <main className="app-shell">
      <CaseListPage
        api={api}
        session={session}
        onOpenCase={(caseId) => setRoute({ name: "detail", caseId })}
        onLogout={handleLogout}
      />
    </main>
  );
}
