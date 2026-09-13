"""仓库根一键启动 Claims Gate API（uvicorn）。

用法（在仓库根目录）：
  python scripts/run_api.py
  python scripts/run_api.py --port 8000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = (
    Path(__file__).resolve().parents[1]
    / "本项目代码"
    / "claims-gate"
    / "src"
)

if not (_SRC / "claims_api" / "api.py").is_file():
    raise SystemExit(f"找不到 API 入口: {_SRC / 'claims_api' / 'api.py'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="启动 Claims Gate HTTP API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="热重载（默认开；--no-reload 关闭）",
    )
    args, extra = parser.parse_known_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "未安装 uvicorn。请先：pip install -r 本项目代码/claims-gate/requirements.txt"
        ) from exc

    # 工作目录切到 claims-gate，保证相对 KB 路径与 reload 监视范围正确
    gate_root = _SRC.parent
    import os

    os.chdir(gate_root)

    uvicorn.run(
        "claims_api.api:app",
        app_dir=str(_SRC),
        host=args.host,
        port=args.port,
        reload=args.reload,
        # 仅监视产品代码，避免监视整个仓库根
        reload_dirs=[str(_SRC)] if args.reload else None,
    )


if __name__ == "__main__":
    main()
