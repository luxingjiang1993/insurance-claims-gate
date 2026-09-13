"""Eval / 负例旁路入口：评估器注册外形 + 固定夹具机读报告。

硬约束（旁路，非合门禁主缝）：
- 默认 CI 合门禁仍以 missions.checks.machine_check 为准；
- 本入口失败可告警/另标记，不得改写人闸语义；
- 不得要求 LLM 才能让轨 A 变绿；不引入支付工具。

评估器外形参考 OpenEvals 的注册/调用模式，落地为确定性规则薄封装
（citation 落库门、通融伪 citation、同 hash 拆轮），不依赖 LLM Judge。

Rewrote from: REF-CASE-OPENEVALS, REF-MISSIONS
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from fastapi.testclient import TestClient

from claims_api.error_codes import ErrorCode
from missions.rag import KnowledgeBase

_KB_ROOT = Path(__file__).resolve().parents[2] / "knowledge_base"

# 文档真源：旁路角色字符串，禁止与 machine_check 混称
EVAL_GATE_ROLE = "bypass_not_machine_check"


@dataclass(frozen=True)
class EvalConfig:
    """旁路契约槽位：失败不得阻断轨 A。"""

    gate_role: str = EVAL_GATE_ROLE
    blocks_track_a_gate: bool = False
    requires_llm: bool = False
    docs_note: str = "旁路，非合门禁主缝；合门禁以 machine_check 为准"


@dataclass
class EvalCaseResult:
    """单条负例评估结果（pass/fail 结构）。"""

    id: str
    category: str
    passed: bool
    detail: str
    evaluator: str


@dataclass
class EvalReport:
    """可机读旁路报告。"""

    cases: list[EvalCaseResult] = field(default_factory=list)
    gate_role: str = EVAL_GATE_ROLE
    blocks_track_a_gate: bool = False
    requires_llm: bool = False

    @property
    def summary(self) -> dict[str, int]:
        passed = sum(1 for c in self.cases if c.passed)
        failed = sum(1 for c in self.cases if not c.passed)
        return {"passed": passed, "failed": failed, "total": len(self.cases)}


EvaluatorFn = Callable[[TestClient], EvalCaseResult]


def _error_code(resp: Any) -> str | None:
    if resp.status_code < 400:
        return None
    detail = resp.json().get("detail")
    if isinstance(detail, dict):
        return detail.get("error_code")
    return None


def eval_hallucination_citation(client: TestClient) -> EvalCaseResult:
    """负例：库外/幻觉条款 citation 不得过落库门。

    旁路 pass = 系统正确拒绝（与 OpenEvals hallucination 负例外形对齐）。
    """
    payload = {
        "doc_id": "PA-ACC-MAIN",
        "clause_item": "ART-999-HALLUCINATION",
        "doc_version": "2024.1",
        "quote": "幻觉条款",
    }
    resp = client.post("/kb/citations/validate", json=payload)
    rejected = (
        resp.status_code == 422
        and _error_code(resp) == ErrorCode.CITATION_NOT_IN_KB.value
    )
    # 双重确认：KB 解析亦为空（groundedness 落地）
    chunk = KnowledgeBase(_KB_ROOT).resolve_clause(
        payload["doc_id"], payload["clause_item"], payload["doc_version"]
    )
    grounded_fail = chunk is None
    ok = rejected and grounded_fail
    return EvalCaseResult(
        id="neg-hallucination-citation",
        category="hallucination_citation",
        passed=ok,
        detail=(
            f"status={resp.status_code} error_code={_error_code(resp)} "
            f"kb_miss={grounded_fail}"
        ),
        evaluator="hallucination_citation",
    )


def eval_exgratia_fake_citation(client: TestClient) -> EvalCaseResult:
    """负例：通融伪主险通赔 citation 必须失败关闭。"""
    case_id = "CLM-LATCH-BASE-001"
    resp = client.post(
        f"/claims/{case_id}/decisions/exgratia",
        json={
            "reason": "伪 citation 旁路夹具",
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
    ok = (
        resp.status_code == 422
        and _error_code(resp) == ErrorCode.VALIDATION_FAILED.value
    )
    return EvalCaseResult(
        id="neg-exgratia-fake-citation",
        category="exgratia_fake_citation",
        passed=ok,
        detail=f"status={resp.status_code} error_code={_error_code(resp)}",
        evaluator="exgratia_fake_citation",
    )


def eval_one_shot_split_round(client: TestClient) -> EvalCaseResult:
    """负例：同 one_shot_hash 拆轮补件必须失败（第三类可选夹具）。"""
    case_id = "CLM-SC01-001"
    ev = client.post(f"/claims/{case_id}/evaluate")
    if ev.status_code != 200:
        return EvalCaseResult(
            id="neg-one-shot-split-round",
            category="one_shot_split_round",
            passed=False,
            detail=f"evaluate status={ev.status_code}",
            evaluator="one_shot_split_round",
        )
    body = ev.json()
    one_shot = body.get("one_shot_hash")
    codes = list(body.get("supplement_checklist") or [])
    if isinstance(codes, list) and codes and isinstance(codes[0], dict):
        codes = [c.get("code") for c in codes if c.get("code")]
    if not one_shot or len(codes) < 2:
        return EvalCaseResult(
            id="neg-one-shot-split-round",
            category="one_shot_split_round",
            passed=False,
            detail=f"need hash and >=2 codes, hash={one_shot} codes={codes}",
            evaluator="one_shot_split_round",
        )
    split = client.post(
        f"/claims/{case_id}/supplement/notify",
        json={"one_shot_hash": one_shot, "missing_item_codes": [codes[0]]},
    )
    ok = (
        split.status_code == 422
        and _error_code(split) == ErrorCode.VALIDATION_FAILED.value
    )
    return EvalCaseResult(
        id="neg-one-shot-split-round",
        category="one_shot_split_round",
        passed=ok,
        detail=f"split_status={split.status_code} error_code={_error_code(split)}",
        evaluator="one_shot_split_round",
    )


# OpenEvals 风格：评估器注册表（确定性，无 LLM）
EVALUATORS: dict[str, EvaluatorFn] = {
    "hallucination_citation": eval_hallucination_citation,
    "exgratia_fake_citation": eval_exgratia_fake_citation,
    "one_shot_split_round": eval_one_shot_split_round,
}

# 默认旁路套件：至少 2 类（幻觉 citation + 通融伪 citation）；拆轮作扩展
DEFAULT_EVAL_SUITE: tuple[str, ...] = (
    "hallucination_citation",
    "exgratia_fake_citation",
)


def run_eval_negatives(
    client: TestClient,
    *,
    suite: tuple[str, ...] | list[str] | None = None,
) -> EvalReport:
    """对固定负例夹具跑评估器，产出旁路报告（不替代 machine_check）。"""
    names = tuple(suite) if suite is not None else DEFAULT_EVAL_SUITE
    report = EvalReport(
        gate_role=EVAL_GATE_ROLE,
        blocks_track_a_gate=False,
        requires_llm=False,
    )
    for name in names:
        fn = EVALUATORS.get(name)
        if fn is None:
            report.cases.append(
                EvalCaseResult(
                    id=f"unknown-{name}",
                    category=name,
                    passed=False,
                    detail=f"unknown evaluator: {name}",
                    evaluator=name,
                )
            )
            continue
        report.cases.append(fn(client))
    return report


def to_machine_readable_report(report: EvalReport) -> dict[str, Any]:
    """序列化为可机读 dict（JSON 友好）。"""
    return {
        "gate_role": report.gate_role,
        "blocks_track_a_gate": report.blocks_track_a_gate,
        "requires_llm": report.requires_llm,
        "docs_note": EvalConfig().docs_note,
        "cases": [asdict(c) for c in report.cases],
        "summary": report.summary,
    }


def main() -> None:
    """脚本入口：python -m missions.eval_entry（旁路，非合门禁）。"""
    import json
    import sys

    # 保证可从仓库根或 claims-gate 根运行
    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from claims_api.api import app, reset_service

    reset_service()
    client = TestClient(app)
    report = run_eval_negatives(client)
    payload = to_machine_readable_report(report)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    # 旁路退出码：失败时非零便于告警，但文档声明不并入轨 A 合门禁
    raise SystemExit(0 if payload["summary"]["failed"] == 0 else 2)


if __name__ == "__main__":
    main()
