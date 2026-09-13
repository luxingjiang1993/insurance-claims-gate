"""外置状态存储：contract / features / handoff / mission state。

Rewrote from: REF-MISSIONS（missions/store.py）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import HandoffRecord, MissionState, RoleName, utc_now_iso


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "handoffs").mkdir(exist_ok=True)
        self.state_path = self.root / "mission_state.json"
        self.contract_path = self.root / "validation_contract.json"
        self.features_path = self.root / "features.json"

    def save_state(self, state: MissionState) -> None:
        self.state_path.write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )
        if state.contract:
            self.contract_path.write_text(
                state.contract.model_dump_json(indent=2),
                encoding="utf-8",
            )
        self.features_path.write_text(
            json.dumps(
                [f.model_dump(mode="json") for f in state.features],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load_state(self) -> MissionState | None:
        if not self.state_path.exists():
            return None
        return MissionState.model_validate_json(self.state_path.read_text(encoding="utf-8"))

    def append_handoff(self, state: MissionState, handoff: HandoffRecord) -> None:
        state.handoffs.append(handoff)
        path = self.root / "handoffs" / f"{handoff.handoff_id}.json"
        path.write_text(handoff.model_dump_json(indent=2), encoding="utf-8")
        self.save_state(state)

    def emit(
        self,
        state: MissionState,
        *,
        kind: str,
        message: str,
        role: RoleName | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        event = {
            "ts": utc_now_iso(),
            "kind": kind,
            "message": message,
            "role": role.value if role else None,
            **(extra or {}),
        }
        state.events.append(event)
        self.save_state(state)
