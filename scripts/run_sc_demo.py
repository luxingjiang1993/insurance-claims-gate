"""仓库根一键入口：转发到 claims-gate Solo SC Demo。

用法（在仓库根目录）：
  python scripts/run_sc_demo.py
  python scripts/run_sc_demo.py --extras
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_TARGET = (
    Path(__file__).resolve().parents[1]
    / "本项目代码"
    / "claims-gate"
    / "scripts"
    / "run_sc_demo.py"
)

if not _TARGET.is_file():
    raise SystemExit(f"找不到 Demo 脚本: {_TARGET}")

# 保持用户传入的 argv（含 --extras 等）
sys.argv[0] = str(_TARGET)
runpy.run_path(str(_TARGET), run_name="__main__")
