"""接缝：Solo Demo 脚本 — SC-01/02/03 HTTP 黑盒给人看的 pass/fail。

主缝：claims_api.demo_sc 复用 machine_check 语义；失败非零退出。
合门禁仍以 pytest/machine_check 为准；本入口是个人验收 Demo。
"""

from __future__ import annotations

from claims_api.demo_sc import DemoResult, run_sc_demo


def test_run_sc_demo_main_paths_pass() -> None:
    """SC-01/02/03 主路径全部通过，exit_code=0。"""
    result = run_sc_demo(include_extras=False)
    assert isinstance(result, DemoResult)
    assert result.exit_code == 0
    labels = [row.label for row in result.rows]
    assert labels == ["SC-01", "SC-02", "SC-03"]
    assert all(row.ok for row in result.rows)


def test_run_sc_demo_with_extras_includes_negatives() -> None:
    """可选人闸/拆轮负例一并跑通且仍绿。"""
    result = run_sc_demo(include_extras=True)
    assert result.exit_code == 0
    labels = [row.label for row in result.rows]
    assert "SC-01" in labels and "SC-02" in labels and "SC-03" in labels
    assert "SC-01-split-round" in labels
    assert "SC-02-latch-required" in labels
    assert all(row.ok for row in result.rows)


def test_format_report_is_human_readable() -> None:
    """打印给人看的简明 pass/fail 行。"""
    result = run_sc_demo(include_extras=False)
    text = result.format_report()
    assert "PASS" in text
    assert "SC-01" in text
    assert "SC-02" in text
    assert "SC-03" in text


def test_run_sc_demo_exit_nonzero_when_any_row_fails(monkeypatch) -> None:
    """任一场景失败时 exit_code 非零（验收契约）。"""
    from missions.checks import CheckOutcome
    from missions.models import CommandResult

    def _fail(_client, check):
        return CheckOutcome(
            ok=False,
            detail=f"forced fail for {check.type}",
            command=CommandResult(
                cmd=f"check:{check.type}",
                exit_code=1,
                stdout_tail="forced",
            ),
        )

    monkeypatch.setattr("claims_api.demo_sc.run_machine_check", _fail)
    result = run_sc_demo(include_extras=False)
    assert result.exit_code != 0
    assert not any(row.ok for row in result.rows)
    assert "FAIL" in result.format_report()
