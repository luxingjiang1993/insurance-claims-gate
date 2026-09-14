"""OpenAI-compatible 聊天补全客户端（httpx，无 SDK 强依赖）。

环境变量见仓库根 `.env.example`：
- OPENAI_API_KEY / CLAIMS_GATE_LLM_API_KEY
- OPENAI_BASE_URL（默认 https://api.openai.com/v1）
- OPENAI_MODEL（默认 gpt-4o-mini）

Rewrote from: REF-COURSE-03, REF-MISSIONS
"""

from __future__ import annotations

import os
from typing import Any

import httpx

# 默认兼容端点与模型；可由环境覆盖
_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_DEFAULT_MODEL = "gpt-4o-mini"


class LlmConfigError(RuntimeError):
    """缺少 API Key 等配置错误（调用方应降级，不得冒充已用 LLM）。"""


class LlmCallError(RuntimeError):
    """供应商调用失败（有 Key 时不静默回落确定性草稿）。"""


def resolve_api_key() -> str | None:
    """读取 OpenAI-compatible API Key；无 Key 返回 None。"""
    key = (os.environ.get("OPENAI_API_KEY") or os.environ.get("CLAIMS_GATE_LLM_API_KEY") or "").strip()
    return key or None


def resolve_base_url() -> str:
    """兼容端点根路径（不含末尾 /）。"""
    raw = (os.environ.get("OPENAI_BASE_URL") or _DEFAULT_BASE_URL).strip().rstrip("/")
    return raw or _DEFAULT_BASE_URL


def resolve_model() -> str:
    """模型名。"""
    return (os.environ.get("OPENAI_MODEL") or _DEFAULT_MODEL).strip() or _DEFAULT_MODEL


def chat_completion(
    *,
    system: str,
    user: str,
    timeout_s: float = 60.0,
) -> str:
    """调用 chat/completions；须已配置 Key，失败抛 LlmCallError。"""
    api_key = resolve_api_key()
    if not api_key:
        raise LlmConfigError("缺少 OPENAI_API_KEY / CLAIMS_GATE_LLM_API_KEY")

    url = f"{resolve_base_url()}/chat/completions"
    payload: dict[str, Any] = {
        "model": resolve_model(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise LlmCallError(f"LLM 网络错误: {exc}") from exc

    if resp.status_code >= 400:
        raise LlmCallError(f"LLM HTTP {resp.status_code}: {resp.text[:400]}")

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise LlmCallError(f"LLM 响应外形异常: {exc}") from exc

    text = str(content or "").strip()
    if not text:
        raise LlmCallError("LLM 返回空内容")
    return text
