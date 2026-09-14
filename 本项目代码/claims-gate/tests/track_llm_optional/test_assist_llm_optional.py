"""真 LLM 网络调用隔离测（默认 CI 不跑；缺 Key 跳过）。

有 Key 的替身契约已在 tests/test_assist_api_degrade_adopt.py 覆盖。
Rewrote from: REF-COURSE-03, REF-MISSIONS
"""

from __future__ import annotations

import os

import pytest

from missions.track_llm_optional import llm_client

pytestmark = pytest.mark.requires_llm


@pytest.mark.skipif(
    not (os.environ.get("OPENAI_API_KEY") or os.environ.get("CLAIMS_GATE_LLM_API_KEY")),
    reason="无真实 OPENAI_API_KEY，跳过真调用",
)
def test_live_openai_compatible_chat_completion() -> None:
    """可选：对真实兼容端点打一枪（仅人工/带 Key CI）。"""
    text = llm_client.chat_completion(
        system="用一句话回复：ok",
        user="ping",
        timeout_s=30.0,
    )
    assert isinstance(text, str) and text.strip()
