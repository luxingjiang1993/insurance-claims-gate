"""接缝 S0/S1：G0 Live Pilot 验收清单契约 — 存在且含双 Key / 双绿 / 旁路；不强制跑实机。

Rewrote from: REF-MISSIONS · SPEC-02C-LIVE-HONEST-SEAMS · Issue 57
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_G0 = ROOT / "docs" / "acceptance" / "live-pilot-g0.md"
PACKAGE_L = ROOT / "docs" / "acceptance" / "package-l.md"


def test_live_pilot_g0_checklist_exists_with_required_sections() -> None:
    """Live 清单须落盘，覆盖双 Key、cloud 重建、连接双绿、Assist 双路径、旁路与默认绿。"""
    assert LIVE_G0.is_file(), f"缺少 G0 Live 清单: {LIVE_G0}"
    text = LIVE_G0.read_text(encoding="utf-8")
    assert "套餐 L" in text or "package-l" in text
    assert "OPENAI_API_KEY" in text
    assert "CLAIMS_GATE_EMBEDDING_API_KEY" in text
    assert "EMBEDDING_PROVIDER=cloud" in text
    assert "rebuild_chroma_index" in text
    assert "connection-status" in text or "连接状态" in text
    assert "永不回显" in text or "不回显" in text
    assert "requires_llm" in text
    assert "track_llm_optional" in text
    assert "pytest -q" in text
    assert "used_llm" in text or "structured draft" in text or "结构化" in text
    # 诚实边界：须声明不宣称；禁止肯定过线措辞
    assert "不宣称" in text or "不得宣称" in text
    assert "面试条 9" in text or "冲 9" in text or "诚实 8" in text
    assert "已过线 grounded" not in text
    assert "H4 已过线" not in text
    assert "已 grounded" not in text
    assert "面试条 9 过线" not in text
    assert "冲 9 已过" not in text


def test_package_l_points_to_live_g0() -> None:
    """套餐 L 须指向 Live 档，避免把 W1 清单误当作 Phase 2c Live。"""
    text = PACKAGE_L.read_text(encoding="utf-8")
    assert "live-pilot-g0" in text or "Live Pilot" in text or "G0 Live" in text
