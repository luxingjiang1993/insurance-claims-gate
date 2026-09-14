"""接缝：套餐 L 验收清单契约 — 存在且含三路径；不强制跑实机。

Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_L = ROOT / "docs" / "acceptance" / "package-l.md"


def test_package_l_checklist_exists_with_three_paths() -> None:
    """套餐 L 清单须落盘，并覆盖满配 / 关向量 / 关 LLM 三路径。"""
    assert PACKAGE_L.is_file(), f"缺少套餐 L 清单: {PACKAGE_L}"
    text = PACKAGE_L.read_text(encoding="utf-8")
    # 中文路径名须可读；禁止乱码
    assert "满配" in text
    assert "关向量" in text or "关闭向量" in text
    assert "关 LLM" in text or "关闭 LLM" in text or "无 LLM" in text
    # 不得暗示 W2 排行榜已上线
    assert "排行榜已上线" not in text
    assert "Eval Ops 已上线" not in text
