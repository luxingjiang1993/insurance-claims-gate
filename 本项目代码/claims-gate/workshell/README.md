# Claims Gate 作业壳（套餐 C · 最小可用面）

`Rewrote from: REF-MISSIONS`

Vite + React + TypeScript 薄客户端，**直连**理赔 HTTP API（无 BFF）。本目录对应 Issue 16：登录 + 案件只读浏览。

## 前置

1. 启动 API（仓库根）：

```bash
python scripts/run_api.py
```

默认 `http://127.0.0.1:8000`。可选持久库：

```bash
set CLAIMS_GATE_DB=本项目代码\claims-gate\data\claims_gate.sqlite
python scripts/run_api.py
```

2. 本目录安装依赖并启动：

```bash
cd 本项目代码/claims-gate/workshell
npm install
npm run dev
```

浏览器打开 `http://127.0.0.1:5173/`。

演示账号（用户名=密码）：`viewer` / `adjuster` / `supervisor`。

可选环境变量：`VITE_CLAIMS_API_BASE`（默认 `http://127.0.0.1:8000`）。

## 本票范围

- 登录、案件列表、案件详情只读字段：`gate_status`、`document_status`、`inference_track`、`payout_ready`
- `viewer` 不展示写操作入口
- API 拒绝体原样展示

后续票（17+）再补 evaluate / 人闸 / 文书 / AI 区等作业动作。

## 自检

```bash
npm test
npm run typecheck
```
