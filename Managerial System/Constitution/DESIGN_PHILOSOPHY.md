# Design Philosophy — Policy-to-Feature Missions (Agent-Native)

**Audience:** coding agents (and humans directing them).  
**Use:** refactor this repo, or greenfield a Missions-style system.  
**Standard:** Silicon Valley production bar — correctness over theater; name the scaffold honestly; upgrade along a clear autonomy ladder.

**Lineage (conflict order):**
1. **Primary:** Factory-style Missions (Orchestrator / Worker / Validator) + prior improvement mandates for *this* repo  
2. **Secondary:** Sabrina Ramonov solo-agentic ops (relay skills, shared brief, graded gate, human approve-before-publish)  
3. **Tertiary influences:** Karpathy (agentic engineering / verifiability), Shopify River–Aquifer (brain≠hands, multiplayer compounding), Anthropic (parallelism rules), Dex Horthy 12-Factor Agents (own the loop / context engineering), Sidekick-style judge calibration — see §14  
4. On conflict → **(1) wins**, then (2). Throughput, parallel fan-out, or vibe speed must not override serial writers, fail-closed gates, or human latch on a shared mutable codebase.

---

## 1. One-sentence doctrine

**Human architects and retains understanding; a small relay of specialized agents executes narrow jobs; a durable ledger (contract, brief, RAG, handoffs) holds memory while harness/context stays disposable and curated; an independent, calibratable judge gates quality; high-risk side effects require a hard human latch; automate where verifiable; throughput is subordinate to correctness.**

---

## 2. Non-negotiable invariants

Coding agents MUST preserve these. Violating them is a design bug, not a style choice.

| ID | Invariant | Rationale |
|----|-----------|-----------|
| I1 | **Role incentive split** | Orchestrator plans; Worker implements; Validator/Grader only judges. Same agent must not create and finally accept its own work. |
| I2 | **Correctness before implementation** | Validation contract (behavioral assertions + citations) exists before feature code. Acceptance must not be reverse-engineered from an implementation. |
| I3 | **Durable ledger + curated context** | Cross-step truth lives in versioned artifacts (contract, features, handoffs, RAG, Mission Control) — not chat memory. Pack **only the next decision’s density** into the model (handoffs are compressions). Prefer durable event/state substrate; treat agent harness/sessions as replaceable. Successful trajectories should **write back** skills/KB (multiplayer compounding), not die in a private window. |
| I4 | **Write serial; parallel by decision rule** | At most one Writer on a shared mutable workspace (`owns_paths` + lock). **Parallel OK:** retrieval, research, independent review, non-contending artifacts. **Parallel NO:** same file/schema, write dependencies, or when coordination/token tax exceeds speedup — fall back to one session. Worktree isolation required before any true parallel writes. |
| I5 | **Fail closed on gates** | Failed tests, failed validation, or failed grade → block progression. Never mark `DONE` when the gate failed. |
| I6 | **Human architect, latch, and understanding** | Humans set specs, trade-offs, budgets, and taste. You may outsource drafting/thinking assist — **not** system understanding or release responsibility. High-risk actions need explicit human approval. Speedup is **agentic engineering** (keep the quality bar), not vibe coding that ships vulnerabilities. |
| I7 | **Honest autonomy level** | If a step is scripted/choreographed, say so in code comments and handoff notes. Do not fake LLM autonomy or fake git commits. |
| I8 | **Narrow success definition first** | Ship one thin vertical slice (e.g. daily limit + audit policy) before adding roles, parallelism, or domains. Prefer slices with **cheap objective verification**. |

---

## 3. Role model (relay team, not swarm)

Keep the cast **small and sharp** (≈3 core roles + optional read-only tools). Prefer 7 crisp skills over 100 vague ones.

### 3.1 Core roles (required)

| Role | Factory name | Sabrina analogue | Owns | Must not |
|------|--------------|------------------|------|----------|
| Planner | Orchestrator | Content coach | Clarify goal; retrieve policy/brand; emit **validation contract** + feature/milestone list; open **fix** features from validator reports | Implement product code; final accept |
| Builder | Worker | Post writer | Fresh context per feature; tests-then-code; real patch + real VCS handoff; respect `owns_paths` | Final compliance/grade accept; hold write lock while another writer runs |
| Judge | Validator | Post grader | Independent retrieve profile/model; scrutinize + black-box checks against **contract**; emit fail report only; aspire to **human-calibrated** judgment | Patch the system under test; “helpfully” weaken the contract |

### 3.2 Optional specialists (read-only or non-conflicting)

- **Hook/Pattern library** / policy clause finder — tool agent, not a second writer on the same files  
- **Repurpose / fan-out** — only when outputs do **not** contend for the same mutable artifact. **Never** fan-out multiple writers into one git branch without locks/worktrees.  
- **Scheduler / publisher / deployer** — execution agent **behind a human approval gate**

### 3.3 Soft orchestration, hard ledger (own the loop)

- Behavioral policy (split / retry / escalate): prompts / skills (soft).  
- Control flow, tool execution, retries, pause/resume, approvals: **deterministic application code** (hard). LLM emits structured intents; the app owns the switch statement.  
- Soft layer may improve with stronger models; hard layer must not rely on model memory.  
- Prefer **brain ≠ hands**: planning/ledger/harness outside the blast radius of sandbox file/shell mutations.

---

## 4. Shared artifacts (memory bus)

All agents read/write through versioned artifacts. Context windows are disposable and **intentionally compacted**.

| Artifact | Contents | Producer | Consumers |
|----------|----------|----------|-----------|
| **Validation contract** | Behavioral assertions, acceptance, `machine_check`, `policy_clause_id`, broadcast constraints | Orchestrator | Worker, Validator, humans |
| **Brand / domain brief** (Sabrina) | Voice, product, audience, non-goals — FinTech maps to **policy + product constraints** in KB | Human + Orchestrator | All roles |
| **Feature list** | Milestone, claims assertions, `owns_paths`, kind=`implement`\|`fix` | Orchestrator | Runner, Worker |
| **RAG knowledge base** | Policies, API docs, audit findings, runbooks; **version + effective dates**; post-pass write-backs | Humans + scrutiny updates | All roles (role-specific retrieval profiles) |
| **Handoff records** | Done / not done, commands + exit codes, citations, process_followed, blocked_for_human — **compressed** for next step | Every role | Runner, Mission Control, next agent, humans |
| **Grade / validation report** | Pass/fail (or score), notes, citations; optional human-spot-check fields | Validator/Grader | Orchestrator (opens fix), humans |
| **Mission Control state** | Phase, role, write lock, budgets, event log, approval latch | Runner | Humans (async oversight) |

### 4.1 Contract quality rules

- Assertions describe **observable behavior**, not implementation.  
- Every assertion cites a KB clause ID; citations include `doc_id`, `chunk_id`, `doc_version`, `retrieved_by`, `retrieval_profile`.  
- Validator judges using contract + **independent** retrieval — not Worker’s notes as sole evidence.  
- Prefer **executing** `machine_check` (API/E2E/script) over hard-coded `A-001` switches.  
- Automate first where verification is cheap and objective (**verifiability economy**); keep humans on low-verifiability judgment.

### 4.2 Grading gate (Sabrina + calibrated judge)

- Explicit threshold (all assertions pass; or score ≥ 9/10).  
- Loop: build → judge → fix → judge, until threshold or **budget exhausted → human**.  
- Cap revise rounds (e.g. 3–5). Correctness budget beats vanity throughput.  
- Long-term: spot-check judge vs human agreement; an independent but uncalibrated judge can still be systematically wrong.

---

## 5. Control flow (canonical loop)

```text
Human goal / policy change
    → Orchestrator: RAG → validation contract + features (+ broadcast constraints)
    → for feature in serial queue:
          acquire write lock
          Worker: narrow RAG → tests → implement → real commit → handoff
          release write lock
    → Validator: independent RAG + scrutiny + black-box vs contract
    → if fail: Orchestrator opens fix features (Worker must not self-merge bypass)
    → if pass: versioned KB/skill write-back (compounding)
    → if high-risk side effect: HUMAN APPROVE → Scheduler/Deployer
    → if blocked: stop for human (no silent infinite retry)
```

**Parallelism decision tree (I4):**  
research/retrieve/review → parallel OK →  
same mutable artifact or write-dep → serial / one owner →  
coordination or token tax > speedup → single session.

---

## 6. Autonomy ladder (do not skip rungs)

Agents implementing this system MUST progress honesty-first:

| Level | Name | Allowed behavior | This repo target |
|-------|------|------------------|------------------|
| L0 | **Choreography** | Deterministic scripts; fixed contract; flag toggles | Historical demo baseline — label clearly |
| L1 | **Gated skeleton** | Real tests fail-closed; real HTTP black-box validator; no fake git; `goal` unused is forbidden | **Minimum bar for further edits** |
| L2 | **Schema-bound agents** | LLM outputs validated by JSON Schema; contract/features parsed not trusted raw | Next |
| L3 | **Patch-capable Worker** | Worker edits a worktree; real diff + commit hash in handoff | **Current repo target (fix path)** |
| L4 | **Contract-driven Judge** | Checks from acceptance/`machine_check`; separate model/provider; path to human calibration | Required for anti-bias story |
| L5 | **Production latch** | Budgets, approvals, tool ACLs, credential proxy, action audit | Interview + real ops bar |

When editing code: **prefer promoting one rung over adding new role theater.**

---

## 7. Tooling philosophy (agent-native product)

- Prefer **stable tools** (APIs, MCP, CLI); tools are structured outputs executed by deterministic code.  
- Auth, rate limits, and docs must be machine-readable.  
- Least privilege per role; **brain/harness** should not share blast radius with sandbox mutations.  
- Support pause/resume and “contact human” as first-class tool outcomes.  
- Mission Control supervises milestones, not token streams.

---

## 8. Model specialization (“Droid whispering”)

- Orchestrator: strongest reasoning / planning.  
- Worker: strong coding, cost-aware.  
- Validator: instruction-strict, skeptical; **prefer different provider or retrieval profile**.  
- Architecture stays model-agnostic; swap models without rewriting the ledger.

---

## 9. Domain default for this repository

**Policy-to-Feature (FinTech compliance)** remains the default vertical:

- Shared brief ≡ policy + API + audit-finding KB.  
- Grader ≡ compliance Validator against POL-XFER-* citations.  
- Publish latch ≡ external money rails / production — demo uses approval flag.

Content-ops metaphors may inspire **rubric shape**, not product scope creep, unless a human changes the vertical.

---

## 10. Anti-patterns (reject in review)

1. One long-running agent that plans, codes, and self-approves.  
2. Marking features `DONE` when tests/validation failed.  
3. Fake commits, fake “owns_paths obeyed,” unused `goal` parameters.  
4. Parallel writers on one branch “for speed.”  
5. Stuffing the whole KB / raw logs into context instead of ranked citations + compacted handoffs.  
6. Validator that patches code “just this once.”  
7. Infinite revise loops without budget or human escalate.  
8. Claiming production multi-agent while staying on autonomy L0.  
9. Exploding to dozens of overlapping agents/skills.  
10. Optimizing post volume / PR count ahead of contract pass rate.  
11. Private-only agent wins that never write back to KB/skills.  
12. Shipping vibe-coded security/correctness regressions to “go faster.”

---

## 11. Implementation checklist for coding agents

Before closing a change, verify:

- [ ] I1–I8 still hold (esp. curated context, parallelism rule, understanding/latch)  
- [ ] New behavior has an artifact or schema, not only prompt text  
- [ ] App owns control flow; LLM outputs are structured intents  
- [ ] Writer path is fail-closed  
- [ ] Validator does not write product code  
- [ ] High-risk side effects gated by human approval field/API  
- [ ] Handoff records commands, citations, exit codes (compact)  
- [ ] Autonomy level documented if still below L3  
- [ ] No new parallel write paths without lock + `owns_paths` (and worktree if true parallel)  
- [ ] RAG citations include version + role profile; consider KB write-back on pass  
- [ ] Mission Control / state JSON reflects phase, lock, gates, approval  

---

## 12. Success metrics (what “good” means)

Primary (Factory-weighted):

- Contract assertion pass rate after milestone validation  
- Fix-feature ratio and validation rounds (expect >1; design for it)  
- Escape defects caught by Validator but missed by Worker tests  
- Citation coverage (% assertions with valid clause versions)  
- Verification cost vs wall-clock (validation budget is expected, not waste)

Secondary (Sabrina / ops-weighted, not overriding primary):

- Human hours per milestone / batch  
- Time-to-gate; approval queue freshness  
- Write-back rate (passes that update KB/skills)  
- Judge–human agreement when spot-checked  

---

## 13. Quotable summary for agents

> Build a **relay**, not a hive.  
> **Contract before code; verify what you automate.**  
> **One writer; many readers; parallel only when cheap.**  
> **Durable ledger; curated context; compound via write-back.**  
> **Independent, calibratable judge; human latch and understanding.**  
> **Own the loop; climb the ladder; correctness compounds.**

---

## 14. Influences (tertiary — do not override § lineage)

Short map from external practice → this doc. Coding agents: use these as *extensions*, not excuses to weaken I1–I8.

| # | Idea | Source (signal) | Where it lands here |
|---|------|-----------------|---------------------|
| 1 | **Verifiability economy** — automate where checks are cheap/objective | Karpathy / Software 3.0 | I8, §4.1 |
| 2 | **Agentic engineering bar** — speed without dropping security/quality | Karpathy | I6, §10.12 |
| 3 | **Brain ≠ hands** — harness/ledger vs sandbox mutations | Shopify Aquifer / River | §3.3, §7 |
| 4 | **Multiplayer compounding** — public write-back beats private chat wins | Tobi Lütke / River | I3, loop KB write-back |
| 5 | **Parallelism decision rule** — research parallel; contended writes serial | Anthropic multi-agent / Agent Teams | I4, §5 |
| 6 | **Context engineering** — pack density for the next decision; compact noise | Dex Horthy / 12-Factor | I3, handoffs |
| 7 | **Own the loop** — structured tool intents + app-owned control flow | 12-Factor Agents | §3.3, §7 |
| 8 | **Calibrated judges** — independent ≠ correct; align with humans | Shopify Sidekick eng. | §3.1 Judge, §4.2 |

Conflict reminder: Shopify-style parallel agents and content fan-out **never** override Factory serial write on one shared branch.

---

## 15. Known gaps (not yet in this philosophy’s implementation bar)

This document is a **working doctrine**, not a finished production bible. Coding agents must **not pretend** these are already solved:

1. **Eval harness** — no Ground-Truth / regression suite for missions; no systematic judge-vs-human κ/agreement tracking.  
2. **Credential proxy & tool gateway** — least privilege is stated; full prod credential isolation, network policy, and action allowlists are not specified as runnable substrate.  
3. **Cost model** — token, wall-clock validation share, and coordination tax are metrics targets, not enforced budgets in code.  
4. **Worktree / branch isolation** — required before true parallel writes; not a default runner mode in the thin demo.  
5. **LLM planning layer** — Orchestrator/Worker are not yet schema-bound live models (ladder L2+); choreography must stay labeled until then.  
6. **Deep understanding tools** — human “understanding not outsourced” lacks concrete artifacts (architecture notes, threat models, ADRs) as mandatory mission inputs.  
7. **Knowledge write-back automation** — compounding is required by I3; durable, reviewed promotion of handoff→KB/skills is still thin.  
8. **Org/multiplayer UX** — Mission Control is single-operator oriented; searchable shared session corpus (River-style) is out of scope for now.

When closing gaps: climb the autonomy ladder one rung; do not add role theater to paper over a missing substrate.
