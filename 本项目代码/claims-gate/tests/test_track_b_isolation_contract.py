"""接缝：轨 B（llm_optional）隔离契约 — 默认 CI 只跑轨 A。

Rewrote from: REF-CASE-HYBRID, REF-MISSIONS
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pytest_ini_excludes_track_llm_optional_from_default() -> None:
    """默认 pytest 配置必须排除 track_llm_optional，轨 B 失败不阻断轨 A。"""
    ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "track_llm_optional" in ini
    assert 'not track_llm_optional' in ini or "not track_llm_optional" in ini.replace(
        '"', ""
    )


def test_track_llm_optional_isolation_dir_exists() -> None:
    """轨 B 测试必须落在隔离目录 tests/track_llm_optional/。"""
    isolated = ROOT / "tests" / "track_llm_optional"
    assert isolated.is_dir()
    py_files = list(isolated.glob("test_*.py"))
    assert py_files, "隔离目录须有至少一条轨 B 占位测试"


def test_track_b_config_independent_and_nonblocking() -> None:
    """轨 B 方差/人闸策略独立配置，且声明不阻断轨 A 合门禁。"""
    from missions.track_llm_optional.config import TrackBConfig

    cfg = TrackBConfig()
    assert cfg.inference_track == "llm_optional"
    assert cfg.blocks_track_a_gate is False
    assert cfg.default_ci_requires_llm is False
