import { useState } from "react";
import type { FormEvent } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { LoginResult } from "../api/types";
import { ApiErrorView } from "../components/ApiErrorView";

type Props = {
  api: ClaimsApiClient;
  onLoggedIn: (session: LoginResult) => void;
};

export function LoginPage({ api, onLoggedIn }: Props) {
  const [username, setUsername] = useState("viewer");
  const [password, setPassword] = useState("viewer");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiClientError | Error | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const session = await api.login(username.trim(), password);
      onLoggedIn(session);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card login-card">
      <h1>Claims Gate 作业壳</h1>
      <p className="muted">
        Developer Preview — 直连理赔 HTTP API（无 BFF）。演示账号：viewer /
        adjuster / supervisor（用户名=密码）。
      </p>
      <form onSubmit={onSubmit} className="form-grid">
        <label>
          用户名
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label>
          密码
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "登录中…" : "登录"}
        </button>
      </form>
      {error ? <ApiErrorView error={error} /> : null}
    </section>
  );
}
