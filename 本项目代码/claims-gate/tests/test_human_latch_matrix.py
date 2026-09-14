"""接缝：人闸权限矩阵（金额档 / 通融 / 预赔 / 调查冻决 / 敏感上浮 / 峰值降级）。

主缝：HTTP 黑盒 + machine_check（SPEC 已确认）。
Rewrote from: REF-MISSIONS
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from claims_api.api import app, reset_service
from claims_api.error_codes import ErrorCode
from missions.checks import run_machine_check
from missions.models import MachineCheck

CASE_SMALL = "CLM-AMT-A-001"
CASE_LARGE = "CLM-AMT-C-001"
CASE_REDUCE_LARGE = "CLM-AMT-C-REDUCE-001"
CASE_BASE = "CLM-LATCH-BASE-001"


def _client() -> TestClient:
    reset_service()
    return TestClient(app)


def _supervisor_headers(client: TestClient) -> dict[str, str]:
    resp = client.post(
        "/auth/login",
        json={"username": "supervisor", "password": "supervisor"},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['session_token']}"}


def test_approve_small_vs_large_amount_tier_latch_diff() -> None:
    """通赔建议：小额档可直通草案；大额档必闸；均可经 HTTP 区分。"""
    client = _client()

    small = client.post(f"/claims/{CASE_SMALL}/evaluate")
    assert small.status_code == 200, small.text
    s = small.json()
    assert s["decision_type"] == "approve_recommend"
    assert s["amount_tier"] == "A"
    assert s["human_latch_required"] is False
    assert s["payout_ready"] is False

    large = client.post(f"/claims/{CASE_LARGE}/evaluate")
    assert large.status_code == 200, large.text
    L = large.json()
    assert L["decision_type"] == "approve_recommend"
    assert L["amount_tier"] in ("B", "C", "D")
    assert L["human_latch_required"] is True
    assert L["payout_ready"] is False


def test_reduce_small_requires_latch_large_higher_tier() -> None:
    """减赔：小额亦主管闸；大额档 latch_tier 更高。"""
    client = _client()

    # SC-03：理算结果 7600 → 档 A，但减赔仍必闸
    sc03 = client.post("/claims/CLM-SC03-001/evaluate")
    assert sc03.status_code == 200
    r = sc03.json()
    assert r["decision_type"] == "reduce"
    assert r["amount_tier"] == "A"
    assert r["human_latch_required"] is True
    assert r["latch_tier"] == "A"
    assert r["latch_level_label"] == "主管闸"

    big = client.post(f"/claims/{CASE_REDUCE_LARGE}/evaluate")
    assert big.status_code == 200, big.text
    b = big.json()
    assert b["decision_type"] == "reduce"
    assert b["human_latch_required"] is True
    assert b["amount_tier"] == "C"
    assert b["latch_tier"] == "C"
    assert b["recommended_payout_amount"] == 79600


def test_exgratia_and_prepay_require_latch_no_payout() -> None:
    """通融、预赔无人闸不得 payout_ready。"""
    client = _client()

    ex = client.post(
        f"/claims/{CASE_BASE}/decisions/exgratia",
        json={"reason": "客户长期关系通融协商", "recommended_amount": 3000},
    )
    assert ex.status_code == 200, ex.text
    body = ex.json()
    assert body["decision_type"] == "exgratia"
    assert body["human_latch_required"] is True
    assert body["payout_ready"] is False
    assert body.get("human_latch_token") in (None, "")

    pre = client.post(
        f"/claims/{CASE_BASE}/decisions/prepay",
        json={"reason": "重疾住院预赔", "recommended_amount": 5000},
    )
    assert pre.status_code == 200, pre.text
    p = pre.json()
    assert p["decision_type"] == "prepay"
    assert p["human_latch_required"] is True
    assert p["payout_ready"] is False


def test_exgratia_fake_main_policy_approve_citation_rejected() -> None:
    """通融伪「主险条款通赔」citation 负例失败关闭。"""
    client = _client()
    resp = client.post(
        f"/claims/{CASE_BASE}/decisions/exgratia",
        json={
            "reason": "伪装成条款通赔",
            "recommended_amount": 2000,
            "citations": [
                {
                    "doc_id": "PA-ACC-MAIN",
                    "clause_item": "ART-1-COV",
                    "doc_version": "2024.1",
                    "quote": "按主险条款通赔予以全额给付",
                    "as_clause_approve": True,
                    "semantic": "clause_approve",
                }
            ],
        },
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error_code"] == ErrorCode.VALIDATION_FAILED.value


def test_investigate_auto_freeze_unfreeze_requires_latch() -> None:
    """进入调查中自动冻决；解除冻决无人闸失败；冻决期间 payout_ready=false。"""
    client = _client()

    enter = client.post(
        f"/claims/{CASE_BASE}/investigate/enter",
        json={"reason": "事故真实性存疑", "risk_score": 0.92},
    )
    assert enter.status_code == 200, enter.text
    body = enter.json()
    assert body["decision_type"] == "investigating"
    assert body["gate_status"] == "INVESTIGATING"
    assert body["freeze_active"] is True
    assert body["payout_ready"] is False
    assert body["human_latch_required"] is True

    bare = client.post(f"/claims/{CASE_BASE}/investigate/unfreeze", json={})
    assert bare.status_code in (403, 422)
    err = bare.json()["detail"]["error_code"]
    assert err == ErrorCode.LATCH_REQUIRED.value

    # 冻决期间再评仍不得出款就绪
    frozen_ev = client.post(f"/claims/{CASE_BASE}/evaluate")
    assert frozen_ev.status_code == 200
    assert frozen_ev.json()["payout_ready"] is False
    assert frozen_ev.json().get("freeze_active") is True

    appr = client.post(
        f"/claims/{CASE_BASE}/human-latch/approve",
        json={"approved_by": "invest-supervisor"},
        headers=_supervisor_headers(client),
    )
    assert appr.status_code == 200
    token = appr.json()["human_latch_token"]
    assert appr.json()["payout_ready"] is False

    ok = client.post(
        f"/claims/{CASE_BASE}/investigate/unfreeze",
        json={"human_latch_token": token},
    )
    assert ok.status_code == 200, ok.text
    ub = ok.json()
    assert ub["freeze_active"] is False
    assert ub["payout_ready"] is False


def test_sensitivity_uplift_at_least_one_tier() -> None:
    """诉讼等敏感场景上浮至少一档：小额通赔由直通变为必闸。"""
    client = _client()

    plain = client.post(f"/claims/{CASE_SMALL}/evaluate")
    assert plain.status_code == 200
    assert plain.json()["human_latch_required"] is False
    assert plain.json()["amount_tier"] == "A"

    reset_service()
    client = TestClient(app)
    sens = client.post(
        f"/claims/{CASE_SMALL}/evaluate",
        json={"sensitivity_flags": ["litigation"]},
    )
    assert sens.status_code == 200, sens.text
    body = sens.json()
    assert body["amount_tier"] == "A"
    assert body["latch_tier"] == "B"
    assert body["human_latch_required"] is True


def test_peak_degrade_only_supplement_human_queue() -> None:
    """峰值降级仅允许补件+人审队列，禁止静默通赔。"""
    client = _client()
    resp = client.post(
        f"/claims/{CASE_LARGE}/peak-degrade",
        json={"reason": "巨灾峰值容量降级"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["decision_type"] == "supplement"
    assert body["payout_ready"] is False
    assert body["decision_type"] != "approve_recommend"
    assert body.get("peak_degraded") is True
    assert body["gate_status"] in ("PENDING_SUPPLEMENT", "HUMAN_LATCH")
    # 人审队列：须排队人审
    assert body["human_latch_required"] is True or body["gate_status"] == "HUMAN_LATCH"
    assert "supplement_checklist" in body or body["gate_status"] == "HUMAN_LATCH"

    # 降级后再 evaluate 仍不得静默通赔
    again = client.post(f"/claims/{CASE_LARGE}/evaluate")
    assert again.status_code == 200
    assert again.json()["decision_type"] == "supplement"
    assert again.json().get("peak_degraded") is True
    assert again.json()["decision_type"] != "approve_recommend"


def test_dual_token_required_on_d_tier_sensitivity_uplift() -> None:
    """已是 D 档再敏感上浮：保持 D 并要求双人令牌。"""
    client = _client()
    # SC-01 材料补齐后金额 350000 → D
    ev0 = client.post("/claims/CLM-SC01-001/evaluate")
    assert ev0.status_code == 200
    codes = [i["code"] for i in ev0.json()["supplement_checklist"]]
    client.post(
        "/claims/CLM-SC01-001/materials",
        json={"material_codes": codes, "image_ids": [f"IMG-{c}" for c in codes]},
    )
    sens = client.post(
        "/claims/CLM-SC01-001/evaluate",
        json={"sensitivity_flags": ["media"]},
    )
    assert sens.status_code == 200, sens.text
    body = sens.json()
    assert body["amount_tier"] == "D"
    assert body["latch_tier"] == "D"
    assert body["dual_token_required"] is True
    assert body["human_latch_required"] is True

    headers = _supervisor_headers(client)
    bare = client.post(
        "/claims/CLM-SC01-001/human-latch/approve",
        json={"approved_by": "supervisor-a"},
        headers=headers,
    )
    assert bare.status_code in (403, 422)
    assert bare.json()["detail"]["error_code"] == ErrorCode.LATCH_REQUIRED.value

    ok = client.post(
        "/claims/CLM-SC01-001/human-latch/approve",
        json={"approved_by": "supervisor-a", "second_approver": "supervisor-b"},
        headers=headers,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["human_latch_token"]
    assert ok.json()["second_approver"] == "supervisor-b"
    assert ok.json()["payout_ready"] is False


def test_machine_check_latch_amount_tier_diff() -> None:
    outcome = run_machine_check(
        _client(),
        MachineCheck(type="latch_amount_tier_approve_diff", params={}),
    )
    assert outcome.ok, outcome.detail
    outcome_r = run_machine_check(
        _client(),
        MachineCheck(type="latch_amount_tier_reduce_diff", params={}),
    )
    assert outcome_r.ok, outcome_r.detail


def test_machine_check_exgratia_prepay_and_fake_citation() -> None:
    outcome = run_machine_check(
        _client(),
        MachineCheck(type="latch_exgratia_prepay_and_fake_citation", params={}),
    )
    assert outcome.ok, outcome.detail


def test_machine_check_investigate_freeze() -> None:
    outcome = run_machine_check(
        _client(),
        MachineCheck(type="latch_investigate_freeze_unfreeze", params={}),
    )
    assert outcome.ok, outcome.detail


def test_machine_check_sensitivity_and_peak() -> None:
    outcome = run_machine_check(
        _client(),
        MachineCheck(type="latch_sensitivity_uplift", params={}),
    )
    assert outcome.ok, outcome.detail
    outcome2 = run_machine_check(
        _client(),
        MachineCheck(type="latch_peak_degrade_no_silent_approve", params={}),
    )
    assert outcome2.ok, outcome2.detail
