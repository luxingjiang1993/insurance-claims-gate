"""SQLite 案件域持久化：案件/材料/草案/人闸事件/ledger/用户会话。

Rewrote from: REF-MISSIONS（外置状态外形换 SQLite）；演示 RBAC 种子 REF-COURSE-04
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models_domain import ClaimCase, LatchEvent


_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS latch_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    ts TEXT NOT NULL,
    human_latch_token TEXT,
    reason TEXT NOT NULL DEFAULT '',
    second_approver TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);

CREATE TABLE IF NOT EXISTS ledger_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT NOT NULL,
    route_id TEXT NOT NULL,
    retrieval_profile TEXT NOT NULL,
    decision_type TEXT NOT NULL,
    validator_score REAL NOT NULL,
    ts TEXT NOT NULL,
    arbitration_winner TEXT,
    trace_id TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(case_id)
);
"""


class SqliteCaseStore:
    """文件型 SQLite；同路径重开即可续演示案件。"""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)
        self._ensure_ledger_trace_id_column()
        self._conn.commit()

    def _ensure_ledger_trace_id_column(self) -> None:
        """旧库补齐 ledger_summary.trace_id（Issue 26）。"""
        cols = {
            str(r[1])
            for r in self._conn.execute("PRAGMA table_info(ledger_summary)").fetchall()
        }
        if "trace_id" not in cols:
            self._conn.execute(
                "ALTER TABLE ledger_summary ADD COLUMN trace_id TEXT"
            )

    def close(self) -> None:
        self._conn.close()

    def count_cases(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM cases").fetchone()
        return int(row["n"] if row else 0)

    def count_users(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
        return int(row["n"] if row else 0)

    def load_all_cases(self) -> dict[str, ClaimCase]:
        rows = self._conn.execute("SELECT case_id, payload_json FROM cases").fetchall()
        out: dict[str, ClaimCase] = {}
        for row in rows:
            payload = json.loads(row["payload_json"])
            case = ClaimCase.from_dict(payload)
            # 人闸事件唯一权威：latch_events 表
            case.latch_events = self.list_latch_events(case.case_id)
            out[case.case_id] = case
        return out

    def save_case(self, case: ClaimCase) -> None:
        # 人闸事件以 latch_events 表为唯一权威；案件 JSON 不重复写入
        payload = case.to_dict()
        payload.pop("latch_events", None)
        try:
            self._conn.execute("BEGIN")
            self._conn.execute(
                """
                INSERT INTO cases(case_id, payload_json) VALUES(?, ?)
                ON CONFLICT(case_id) DO UPDATE SET payload_json=excluded.payload_json
                """,
                (case.case_id, json.dumps(payload, ensure_ascii=False)),
            )
            self._conn.execute(
                "DELETE FROM ledger_summary WHERE case_id = ?", (case.case_id,)
            )
            for entry in case.ledger:
                self._conn.execute(
                    """
                    INSERT INTO ledger_summary(
                        case_id, route_id, retrieval_profile, decision_type,
                        validator_score, ts, arbitration_winner, trace_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.case_id,
                        entry.route_id,
                        entry.retrieval_profile,
                        entry.decision_type,
                        entry.validator_score,
                        entry.ts,
                        entry.arbitration_winner,
                        entry.trace_id,
                    ),
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def save_all_cases(self, cases: dict[str, ClaimCase]) -> None:
        for case in cases.values():
            self.save_case(case)

    def append_latch_event(self, event: LatchEvent) -> None:
        self._conn.execute(
            """
            INSERT INTO latch_events(
                case_id, event_type, actor, ts, human_latch_token, reason, second_approver
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.case_id,
                event.event_type,
                event.actor,
                event.ts,
                event.human_latch_token,
                event.reason,
                event.second_approver,
            ),
        )
        self._conn.commit()

    def list_latch_events(self, case_id: str) -> list[LatchEvent]:
        rows = self._conn.execute(
            """
            SELECT case_id, event_type, actor, ts, human_latch_token, reason, second_approver
            FROM latch_events WHERE case_id = ? ORDER BY id ASC
            """,
            (case_id,),
        ).fetchall()
        return [
            LatchEvent(
                case_id=str(r["case_id"]),
                event_type=str(r["event_type"]),
                actor=str(r["actor"]),
                ts=str(r["ts"]),
                human_latch_token=r["human_latch_token"],
                reason=str(r["reason"] or ""),
                second_approver=r["second_approver"],
            )
            for r in rows
        ]

    def upsert_user(
        self,
        *,
        username: str,
        password_hash: str,
        role: str,
        display_name: str,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO users(username, password_hash, role, display_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash=excluded.password_hash,
                role=excluded.role,
                display_name=excluded.display_name
            """,
            (username, password_hash, role, display_name),
        )
        self._conn.commit()

    def get_user(self, username: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT username, password_hash, role, display_name FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return None
        return {
            "username": str(row["username"]),
            "password_hash": str(row["password_hash"]),
            "role": str(row["role"]),
            "display_name": str(row["display_name"]),
        }

    def create_session(
        self, *, token: str, username: str, role: str, created_at: str
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO sessions(token, username, role, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, username, role, created_at),
        )
        self._conn.commit()

    def get_session(self, token: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT token, username, role, created_at FROM sessions WHERE token = ?",
            (token,),
        ).fetchone()
        if row is None:
            return None
        return {
            "token": str(row["token"]),
            "username": str(row["username"]),
            "role": str(row["role"]),
            "created_at": str(row["created_at"]),
        }

    def delete_session(self, token: str) -> None:
        self._conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        self._conn.commit()
