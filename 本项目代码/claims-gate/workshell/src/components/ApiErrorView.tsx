import { ApiClientError } from "../api/client";

/** 原样展示 API 拒绝体，不改写文案。 */
export function ApiErrorView({ error }: { error: ApiClientError | Error }) {
  if (error instanceof ApiClientError) {
    return (
      <div className="error-panel" role="alert">
        <div className="error-title">API 拒绝（HTTP {error.status}）</div>
        <pre className="error-body">{JSON.stringify(error.body, null, 2)}</pre>
      </div>
    );
  }

  return (
    <div className="error-panel" role="alert">
      <div className="error-title">请求失败</div>
      <pre className="error-body">{String(error)}</pre>
    </div>
  );
}
