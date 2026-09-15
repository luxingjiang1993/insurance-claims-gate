"""可重复执行的 Chroma 条款索引重建入口。

用法（在 claims-gate 根目录）:
  python scripts/rebuild_chroma_index.py

环境变量见 .env.example（EMBEDDING_PROVIDER / CHROMA_*）。
Pilot 默认 EMBEDDING_PROVIDER=cloud（需独立 embedding Key）。
CI / 无云 Key：显式 EMBEDDING_PROVIDER=local（哈希向量，非语义）。

Rewrote from: REF-MISSIONS（加深现有 chroma_index；Issue 34）
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
    if cfg.embedding_provider == "local":
        print(
            "提示: EMBEDDING_PROVIDER=local 使用确定性哈希（非语义），"
            "仅适合 CI/rebuild；Pilot 语义检索请用 cloud + 独立 embedding Key。"
        )
    elif cfg.embedding_provider == "cloud" and not cfg.embedding_api_key.strip():
        print(
            "错误: EMBEDDING_PROVIDER=cloud 需要 CLAIMS_GATE_EMBEDDING_API_KEY "
            "（或 EMBEDDING_API_KEY）；不得静默复用 OPENAI_API_KEY。"
            "无 Key 时请设 EMBEDDING_PROVIDER=local（非语义）后再重建。",
            file=sys.stderr,
        )
        return 2
    result = rebuild_index(cfg)
    print(
        f"rebuild ok: collection={result.collection_name} "
        f"chunks={result.chunk_count} provider={result.embedding_provider} "
        f"persist={result.persist_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
