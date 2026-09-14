# Claims Gate 作业壳（套餐 C · 最小可用面）

`Rewrote from: REF-MISSIONS`

Vite + React + TypeScript 薄客户端，**直连**理赔 HTTP API（无 BFF）。覆盖 Issue 16（登录 + 只读浏览）与 Issue 17（SC 规则路径）。

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

无需 LLM Key 即可走完规则路径。

2. 本目录安装依赖并启动：

```bash
cd 本项目代码/claims-gate/workshell
npm install
npm run dev
```

浏览器打开 `http://127.0.0.1:5173/`。

演示账号（用户名=密码）：`viewer` / `adjuster` / `supervisor`。

可选环境变量：`VITE_CLAIMS_API_BASE`（默认 `http://127.0.0.1:8000`）。

## 本票范围（Issue 17）

- 材料登记、`evaluate`、一次补件通知、裁决草案查看
- SC-01/02/03 语义以服务端 `machine_check` 为准，壳不另立规则
- `viewer` 不展示写操作入口
- API 拒绝体原样展示，不假成功

人闸 / 文书分态 / AI 区留给后续票。

## 自检

```bash
npm test
npm run typecheck
```
