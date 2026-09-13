"""一键入口：从 claims-gate 根目录运行 Solo SC Demo。

用法：python scripts/run_sc_demo.py [--extras]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from claims_api.demo_sc import main

if __name__ == "__main__":
    raise SystemExit(main())
