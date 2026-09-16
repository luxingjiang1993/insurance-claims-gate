/**
 * 连接状态只读页：展示 LLM / Embedding / LangSmith 配置与降级；永不回显 Key。
 * Rewrote from: REF-MISSIONS（质询 P-CFG β）
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { LoginResult, ProviderConnectionStatus } from "../api/types";
import { ApiErrorView } from "../components/ApiErrorView";
import { ShellNav } from "../components/ShellNav";
import {
  statusBadgeLabel,
  toProviderStatusRows,
} from "./providerStatusModel";

type Props = {
  api: ClaimsApiClient;
  session: LoginResult;
  onNavigateHome: () => void;
  onOpenEvalOps: () => void;
  onLogout: () => void;
};

export function ProviderStatusPage({
  api,
  session,
  onNavigateHome,
  onOpenEvalOps,
  onLogout,
}: Props) {
  const [status, setStatus] = useState<ProviderConnectionStatus | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<ApiClientError | Error | null>(null);
  const gen = useRef(0);

  const refresh = useCallback(async () => {
    const token = ++gen.current;
    setBusy(true);
    setError(null);
    try {
      const body = await api.getProviderConnectionStatus();
      if (token !== gen.current) {
        return;
      }
      setStatus(body);
    } catch (err) {
      if (token !== gen.current) {
        return;
      }
      setStatus(null);
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      if (token === gen.current) {
        setBusy(false);
      }
    }
  }, [api]);

  useEffect(() => {
    void refresh();
    return () => {
      gen.current += 1;
    };
  }, [refresh]);

  const rows = status ? toProviderStatusRows(status) : [];

  return (
    <section className="card">
      <header className="page-header">
        <div>
          <ShellNav
            active="providerStatus"
            onNavigate={(route) => {
              if (route === "list") {
                onNavigateHome();
              } else if (route === "evalOps") {
                onOpenEvalOps();
              }
            }}
          />
          <h1>连接状态</h1>
          <p className="muted">
            {session.display_name}（{session.role}）· 只读 · 永不回显 API Key
          </p>
        </div>
        <div className="header-actions">
          <button type="button" className="secondary" onClick={() => void refresh()}>
            刷新
          </button>
          <button type="button" className="secondary" onClick={onLogout}>
            退出
          </button>
        </div>
      </header>

      <p className="muted">
        展示当前进程环境是否已配置 LLM / Embedding / LangSmith、是否降级、当前模型名。
        密钥只写在服务端 <code>.env</code>；作业壳不持 Key。改配后点刷新即可。
      </p>

      {busy ? <p className="muted">加载中…</p> : null}
      {error ? <ApiErrorView error={error} /> : null}

      {!busy && !error && status ? (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>能力</th>
                <th>状态</th>
                <th>模型 / 项目</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{row.title}</td>
                  <td>
                    <span
                      className={
                        row.degraded ? "badge badge-warn" : "badge badge-ok"
                      }
                    >
                      {statusBadgeLabel(row)}
                    </span>
                  </td>
                  <td>
                    <code>{row.modelOrProject}</code>
                  </td>
                  <td className="muted">{row.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {status.hint ? <p className="muted">{status.hint}</p> : null}
        </>
      ) : null}
    </section>
  );
}
