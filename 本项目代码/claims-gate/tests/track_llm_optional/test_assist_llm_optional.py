"""真 LLM 网络调用隔离测（默认 CI 不跑；缺 Key 跳过）。

有 Key 的替身契约已在 tests/test_assist_api_degrade_adopt.py 覆盖。
G0 Live：有 Key 时须能跑通 structured draft（Issue 57）。
Rewrote from: REF-COURSE-03, REF-MISSIONS
"""

from __future__ import annotations

import os

import pytest

from missions.track_llm_optional import llm_client
from missions.track_llm_optional.pipeline import draft_assist

pytestmark = pytest.mark.requires_llm

_HAS_LLM_KEY = bool(
    os.environ.get("OPENAI_API_KEY") or os.environ.get("CLAIMS_GATE_LLM_API_KEY")
)


@pytest.mark.skipif(not _HAS_LLM_KEY, reason="无真实 OPENAI_API_KEY，跳过真调用")
def test_live_openai_compatible_chat_completion() -> None:
    """可选：对真实兼容端点打一枪（仅人工/带 Key CI）。"""
    text = llm_client.chat_completion(
        system="用一句话回复：ok",
        user="ping",
        timeout_s=30.0,
    )
    assert isinstance(text, str) and text.strip()


@pytest.mark.skipif(not _HAS_LLM_KEY, reason="无真实 OPENAI_API_KEY，跳过真 Assist")
def test_live_assist_structured_draft_with_key() -> None:
    """G0：有 Key + enable_llm → used_llm 结构化草稿；不签发人闸、不出款就绪。"""
    result = draft_assist(
        "疾病导致的摔伤是否属于责任免除",
        enable_llm=True,
        top_k=3,
    )
    assert result.used_llm is True
    assert result.degraded is False
    assert result.degrade_reason is None
    assert result.enable_llm is True
    assert result.inference_track == "llm_optional"
    assert isinstance(result.draft_text, str) and result.draft_text.strip()
    assert isinstance(result.citations, list)
    for c in result.citations:
        assert "doc_id" in c
        assert "adoptable" in c
        if not c["adoptable"]:
            assert c.get("reject_reason")
    # Assist 永不越权：本结果不得携带出款就绪或人闸令牌字段
    payload = result.to_dict()
    assert payload.get("payout_ready") in (None, False)
    assert payload.get("human_latch_token") in (None, "")
