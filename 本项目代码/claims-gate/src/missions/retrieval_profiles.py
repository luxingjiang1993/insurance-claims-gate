"""检索配置位：效力栈相关 profile 占位（内容由后续票消费）。

Rewrote from: REF-CASE-KB, REF-MISSIONS
"""

from __future__ import annotations

from typing import Any

# 配置位须可区分；检索策略细节留给 SC / Router 票
RETRIEVAL_PROFILES: dict[str, dict[str, Any]] = {
    "clause_v_current": {
        "id": "clause_v_current",
        "description": "责任/除外默认：仅当前生效版本，按条款项切块",
        "prefer_doc_types": ["main_policy", "rider"],
        "version_mode": "current_effective",
        "endorsement_first": False,
    },
    "endorsement_priority": {
        "id": "endorsement_priority",
        "description": "批单冲突案：先批单/特约，再主险；须写 authority_rank",
        "prefer_doc_types": ["endorsement", "special_agreement", "main_policy"],
        "version_mode": "as_of_loss_date",
        "endorsement_first": True,
    },
    "handbook_ops": {
        "id": "handbook_ops",
        "description": "对内作业手册；不得单独作为对外拒赔唯一依据",
        "prefer_doc_types": ["handbook"],
        "version_mode": "current_effective",
        "endorsement_first": False,
        "external_deny_alone": False,
    },
}
