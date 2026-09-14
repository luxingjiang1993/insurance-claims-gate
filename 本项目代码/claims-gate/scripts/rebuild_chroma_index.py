"""可重复执行的 Chroma 条款索引重建入口。

用法（在 claims-gate 根目录）:
  python scripts/rebuild_chroma_index.py

环境变量见 .env.example（EMBEDDING_PROVIDER / CHROMA_*）。

Rewrote from: REF-CASE-RECALL, REF-RAG-CY, REF-MISSIONS
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from missions.chroma_index import ChromaIndexConfig, rebuild_index  # noqa: E402


def main() -> int:
    cfg = ChromaIndexConfig.from_env()
    result = rebuild_index(cfg)
    print(
        f"rebuild ok: collection={result.collection_name} "
        f"chunks={result.chunk_count} provider={result.embedding_provider} "
        f"persist={result.persist_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
