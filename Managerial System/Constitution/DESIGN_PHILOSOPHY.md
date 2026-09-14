# Design Philosophy — Policy-to-Feature Missions (Agent-Native)

| Field | Value |
|-------|-------|
| **Status** | **Formal**（正式宪法；本文件为仓库设计真源） |
| **Version** | `1.0` |
| **Effective** | 2026-09-14 |
| **Supersedes** | v0.2（Daisy / Claude Code @ scale）；v0.3 working draft |
| **Audience** | coding agents（以及指挥它们的人类） |
| **Use** | 重构本仓库，或从零搭建 Missions 风格系统 |
| **Standard** | Silicon Valley production bar — correctness over theater; name the scaffold honestly; upgrade along a clear autonomy ladder |
| **Chinese mirror** | `Managerial System/Sources/DESIGN_PHILOSOPHY.zh.md`（冲突以本英文正式版为准） |

**Lineage (conflict order):**
1. **Primary:** Factory-style Missions (Orchestrator / Worker / Validator) + prior improvement mandates for *this* repo  
2. **Secondary:** Sabrina Ramonov solo-agentic ops (relay skills, shared brief, graded gate, human approve-before-publish)  
3. **Tertiary influences:** Karpathy (agentic engineering / verifiability), Shopify River–Aquifer (brain≠hands, multiplayer compounding), Anthropic (parallelism rules; Daisy Hollman / Claude Code — context-tax & work-surface scale), Dex Horthy 12-Factor Agents (own the loop / context engineering), Sidekick-style judge calibration — detail in **Appendix A**  
4. On conflict → **(1) wins**, then (2). Throughput, parallel fan-out, or vibe speed must not override serial writers, fail-closed gates, or human latch on a shared mutable codebase.

---

## 0. Agent load map (context tax)

This file is long by necessity. **Do not treat the whole document as always-on.**

| Load class | Sections | When |
|------------|----------|------|
| **Always-on (constitution)** | §1 doctrine · §2 I1–I8 · §6 autonomy ladder A\* · §10 anti-patterns · §11 checklist (skim) | Every change that touches Missions / gates / agents |
| **Next-decision** | §3 roles · §4–§5 artifacts & loop · §9 domain default | Implementing a feature / opening a mission |
| **On demand** | §7 tooling · §8 models · §12 metrics wire · §14 gaps | Expanding Access, eval, or claiming a higher A-rung |
| **Appendix (never always-on)** | Appendix A influences · Appendix B naming · Appendix C changelog | External-practice conflict; naming disputes; history |

**Rule:** Prefer hooks / tickets / SPEC over re-pasting this bible into the window. If a change only needs I5 + human latch, load those rows — not Appendix A influence tables.

---

## 1. One-sentence doctrine

**Humans architect and retain understanding; a small relay of specialized agents executes narrow jobs; a durable ledger (contract, brief, RAG, handoffs) holds memory while harness/context stays disposable and curated; an independent, calibratable judge gates quality; high-risk side effects require a hard human latch; automate where verifiable; throughput is subordinate to correctness.**

---

## 2. Non-negotiable invariants

Coding agents MUST preserve these. Violating them is a design bug, not a style choice.

| ID | Invariant | Rationale |
|----|-----------|-----------|
| I1 | **Role incentive split** | Orchestrator plans; Worker implements; Validator/Grader only judges. Same agent must not create and finally accept its own work. |
| I2 | **Correctness before implementation** | Validation contract (behavioral assertions + citations) exists before feature code. Acceptance must not be reverse-engineered from an implementation. |
| I3 | **Durable ledger + curated context** | Cross-step truth lives in versioned artifacts (contract, features, handoffs, RAG, Mission Control) — not chat memory. Pack **only the next decision’s density** into the model (handoffs are compressions). Prefer durable event/state substrate; treat agent harness/sessions as replaceable. **Don’t pay for what you don’t use:** prefer lazy / event-triggered loading over always-on dumps; every always-resident string competes with room to work. Context-tax wins never replace **verify-then-DONE** (I5): cheaper context is worthless if failed checks still ship. Distinguish **curated context engineering** (versioned skills/KB/contracts) from **session memory** (model-written scratch) — the latter must not auto-promote. Successful trajectories should **write back** skills/KB (multiplayer compounding), not die in a private window; **promotion requires an explicit reviewer** — default **human latch** for institutional KB/skills; Validator may only propose write-backs or grade candidates, never silently merge them into the ledger. |
| I4 | **Write serial; parallel by decision rule** | At most one Writer on a shared mutable workspace (`owns_paths` + lock). **Parallel OK:** retrieval, research, independent review, non-contending artifacts. **Parallel NO:** same file/schema, write dependencies, or when coordination/token tax exceeds speedup — fall back to one session. Worktree isolation required before any true parallel writes. |
| I5 | **Fail closed on gates** | Failed tests, failed validation, or failed grade → block progression. Never mark `DONE` when the gate failed. |
| I6 | **Human architect, latch, and understanding** | Humans set specs, trade-offs, budgets, and taste. You may outsource drafting/thinking assist — **not** system understanding or release responsibility. High-risk actions need explicit human approval. Speedup is **agentic engineering** (keep the quality bar), not vibe coding that ships vulnerabilities. |
| I7 | **Honest autonomy level** | If a step is scripted/choreographed, say so in code comments and handoff notes. Document the **A\*** rung (§6). Do not fake LLM autonomy or fake git commits. |
| I8 | **Narrow success definition first** | Ship one thin vertical slice (e.g. claims gate SC-01..03 + audit policy) before adding roles, parallelism, or domains. Prefer slices with **cheap objective verification**. |

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
| **Brand / domain brief** | Voice, product, audience, non-goals — this repo: **policy + product constraints** in claims KB (`CONTEXT.md` glossary) | Human + Orchestrator | All roles |
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

### 4.2 Grading gate (calibrated judge)

- Explicit threshold (all assertions pass; or score ≥ 9/10).  
- Loop: build → judge → fix → judge, until threshold or **budget exhausted → human**.  
- Cap revise rounds (e.g. 3–5). Correctness budget beats vanity throughput.  
- Long-term: spot-check judge vs human agreement; an independent but uncalibrated judge can still be systematically wrong.

### 4.3 Context loading policy (does it scale?)

Every customization competes with tokens available to do the job. Before adding a skill, MCP server, or always-on brief section, ask **does it scale?** to monorepo / multi-repo institutional size. Saving tokens does **not** relax I5: acceptance still requires executing gates — **verify-then-DONE**.

| Mechanism | Load cost | Prefer when |
|-----------|-----------|-------------|
| Always-on brief / mega project bible | Highest (pays every turn) | Only hard constraints + map + pointers (keep tiny) — see §0 |
| MCP tool schemas | High if many tools always resident | Multi-client / IDE portability, or no stable CLI; keep tool count small or searchable |
| Skills (short description always; body on demand) | Medium | Repeatable workflows; write descriptions that trigger precisely |
| Sub-agents (separate window → compact summary) | Medium on descriptions; better body isolation | Large read-only research / review that must not pollute writer context |
| Event hooks / scripts (inject only when matched) | Lowest resident tax | Lint, typecheck, contract checks, policy nudges at mistake-time |

Rules:

- Prefer **hooks / deterministic scripts** for “red squiggly” feedback (mistake-time), not deferred full-compile discovery alone. Hooks are **hard-loop signals**: they run in deterministic application/harness code and inject structured results into the controlled loop — **not** a second soft prompt-brain that re-plans outside §3.3.  
- **Internal company harness:** prefer **CLI + skill “when/how to use it”** over proliferating MCP servers. **Exception:** when the audience is a portable IDE / multi-client plugin surface, MCP (or equivalent) is a legitimate portability layer — still keep schemas lean; tool sprawl dilutes selection either way.  
- Do **not** LRU-swap large rule blocks mid-session just to chase relevance if that busts prefix cache and multiplies cost — redesign for stable prefixes + lazy bodies instead.  
- Skill/MCP **descriptions are not free**; thousands of vague descriptions recreate the always-on tax. Cap count; make descriptions decision-ready.

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
    → if pass: propose versioned KB/skill write-back → named reviewer promotes (default human latch; Validator may propose/grade only)
    → if high-risk side effect: HUMAN APPROVE → Scheduler/Deployer
    → if blocked: stop for human (no silent infinite retry)
```

**Parallelism decision tree (I4):**  
research/retrieve/review → parallel OK →  
same mutable artifact or write-dep → serial / one owner →  
coordination or token tax > speedup → single session.

---

## 6. Autonomy ladder (A\* — do not skip rungs)

**Naming:** Use **A0–A5** for *agent/harness autonomy*. Do **not** reuse these letters for product integration levels.

| Product / domain term (Claims Gate) | Meaning | Not the same as |
|-------------------------------------|---------|-----------------|
| **Integration L1** | Read-only case header fields | A1 |
| **Integration L2** | Core write-back simulation (e.g. payout-ready status) | A2 |
| **Integration L3** | Auto payout / bank rails — **Won't** this repo | A3 |

Agents implementing this system MUST progress honesty-first:

| Level | Name | Allowed behavior | This repo target |
|-------|------|------------------|------------------|
| **A0** | **Choreography** | Deterministic scripts; fixed contract; flag toggles | Historical demo baseline — label clearly |
| **A1** | **Gated skeleton** | Real tests fail-closed; real HTTP black-box validator; no fake git; `goal` unused is forbidden | **Minimum bar for further edits** (轨 A `machine_check`) |
| **A2** | **Schema-bound agents** | LLM outputs validated by JSON Schema; contract/features parsed not trusted raw | Next (mission control path) |
| **A3** | **Patch-capable Worker** | Worker edits a worktree; real diff + commit hash in handoff | **Current repo target (fix path)** |
| **A4** | **Contract-driven Judge** | Checks from acceptance/`machine_check`; separate model/provider; path to human calibration | Required for anti-bias story; ties to Issues 10–11 / Phase 2a W2 |
| **A5** | **Production latch** | Budgets, approvals, tool ACLs, credential proxy, action audit | Interview + real ops bar; blocked on §14 #2 |

When editing code: **prefer promoting one A-rung over adding new role theater.**  
UI / 作业壳 completion (Phase 2a W0) is **product surface**, not automatic promotion to A3–A5.

---

## 7. Tooling philosophy (agent-native product)

**Three surfaces the agent needs (Access / Knowledge / Tooling):**

- **Access:** If a human cannot finish a real workday without leaving the repo shell (CI logs, runbooks, internal CLIs, tickets, dashboards), the agent cannot share that job until those surfaces are reachable via stable tools — not paste-into-prompt. Expand the **work surface** before blaming the model. New Access tools must sit behind the same **credential proxy, network policy, and action allowlists** called out in §14 #2 — doctrine Access without a gateway is policy theater. Until §14 #2 exists, label new Access **demo-only** or **human-gated** (Phase 2a W1 LangSmith included).  
- **Knowledge:** Institutional conventions, failed experiments, internal vocabulary, and “changed last week” facts live in the ledger/KB/skills (I3) — they will not appear from training data.  
- **Tooling / feedback:** The fastest local improvement is often a **tighter feedback loop** (post-edit typecheck, lint, contract validate), not a thicker always-on prompt.

**Tool preference order:**

1. Stable **CLI / HTTP APIs** with machine-readable auth, rate limits, docs, and **stdout contracts** (exit codes + structured errors agents can act on).  
2. Short **skills** that teach *when* and *how* to use those CLIs.  
3. **MCP** when (a) portability across IDEs/clients matters, or (b) no CLI exists — keep schemas lean; tool sprawl dilutes selection. For a **single internal harness** with a good CLI, prefer 1–2 over inventing MCP wrappers.  
4. Tools are structured intents executed by **deterministic** code (own the loop).

**Intelligence-scaling tools:**

- Prefer **nudges** (reminders, policy hints injected at event time) that remain useful as models get stronger.  
- Use **hard blocks** sparingly for true blast-radius cases (prod writes, credential exfil, shared-branch parallel writers).  
- Least privilege per role; **brain/harness** must not share blast radius with sandbox mutations.  
- High-risk side effects stay behind the human latch (I6), including any “auto” mode that multiplies sessions.

**Write-back reviewers (ties to I3):**

- Session memory / handoff notes may **propose** KB or skill updates.  
- **Promotion** into versioned institutional skills/KB requires an explicit reviewer: default **human latch**; Validator may score or reject candidates against contract quality but must **not** silently merge write-backs. Worker never self-promotes.

**Operations:**

- Support pause/resume and “contact human” as first-class tool outcomes.  
- Mission Control supervises milestones and gates — not raw token streams. As parallel *read-only* or worktree-isolated sessions grow, optimize for **human attention** (labeled sessions, compact status), never by weakening I4/I5.

---

## 8. Model specialization (“Droid whispering”)

- Orchestrator: strongest reasoning / planning.  
- Worker: strong coding, cost-aware.  
- Validator: instruction-strict, skeptical; **prefer different provider or retrieval profile**.  
- Architecture stays model-agnostic; swap models without rewriting the ledger.

---

## 9. Domain default for this repository

**Claims Gate（条款门禁）** is the default vertical (see root `CONTEXT.md` and `PRD_02_INSURANCE_CLAIMS_GATE.md`):

- Shared brief ≡ policy + clause KB + API + audit-finding constraints (效力栈, citation triple gate).  
- Grader ≡ compliance Validator against versioned clause / `policy_clause_id` citations — primary seam **`machine_check` HTTP black-box**.  
- Publish latch ≡ **人闸令牌** before `PAYOUT_READY` / external notify; demo uses approval flag / token — **no Integration L3 auto-payout**.  
- Inference honesty ≡ deterministic track A default; optional LLM assist (track B) must not enter default green CI.

Content-ops / transfer-demo metaphors may inspire **rubric shape** only. Do not reintroduce `POL-XFER-*` as the product default unless a human changes the vertical.

---

## 10. Anti-patterns (reject in review)

1. One long-running agent that plans, codes, and self-approves.  
2. Marking features `DONE` when tests/validation failed.  
3. Fake commits, fake “owns_paths obeyed,” unused `goal` parameters.  
4. Parallel writers on one branch “for speed.”  
5. Stuffing the whole KB / raw logs into context instead of ranked citations + compacted handoffs.  
6. Validator that patches code “just this once.”  
7. Infinite revise loops without budget or human escalate.  
8. Claiming production multi-agent while staying on autonomy **A0**.  
9. Exploding to dozens of overlapping agents/skills.  
10. Optimizing post volume / PR count ahead of contract pass rate.  
11. Private-only agent wins that never write back to KB/skills.  
12. Shipping vibe-coded security/correctness regressions to “go faster.”  
13. Always-on mega briefs / unconditional plugin-style context dumps that burn the window before work starts (including pasting this entire file).  
14. Sprawl of MCP servers or skill descriptions “for completeness,” so tool/skill selection dilutes and resident tax dominates — without hooks or lazy bodies.  
15. Treating Phase 2a 作业壳 / LangSmith UI completion as proof of **A5** Production latch.

---

## 11. Implementation checklist for coding agents

Before closing a change, verify:

- [ ] I1–I8 still hold (esp. curated context, parallelism rule, understanding/latch)  
- [ ] New behavior has an artifact or schema, not only prompt text  
- [ ] App owns control flow; LLM outputs are structured intents  
- [ ] Writer path is fail-closed  
- [ ] Validator does not write product code  
- [ ] High-risk side effects gated by human approval field/API  
- [ ] Handoff records commands, citations, exit codes (compact); autonomy rung **A\*** named if below A3  
- [ ] No new parallel write paths without lock + `owns_paths` (and worktree if true parallel)  
- [ ] RAG citations include version + role profile; consider KB write-back on pass  
- [ ] Mission Control / state JSON reflects phase, lock, gates, approval  
- [ ] New always-on prompt/skill/MCP pays its tax (§4.3); prefer hook or lazy body when possible  
- [ ] Agent can reach the same non-repo surfaces a human needs for this job, or the gap is escalated — not papered over with pasted logs  
- [ ] New Access tools are behind credential proxy / allowlists (§14 #2) or explicitly human-gated / demo-labeled  
- [ ] Proposed KB/skill write-backs name a reviewer (human latch default; Validator proposes/grades only)  
- [ ] New hooks have an owner for false-positive rate; noisy nudges are tuned or removed  
- [ ] Context-tax changes do not weaken verify-then-DONE (I5)  
- [ ] Did not confuse **A\*** autonomy with Integration L1/L2/L3  

---

## 12. Success metrics (wired — what “good” means)

Primary metrics must be **observable**, not slogan-only. Until a row’s wire exists, treat it as **aspirational** and do not claim ops maturity.

| Metric | Class | Wire (this repo) | Status |
|--------|-------|------------------|--------|
| Contract assertion pass rate after milestone validation | Primary | `pytest -q` 轨 A + SPEC `machine_check` / SC-01..03 | **Wired** |
| Fix-feature ratio and validation rounds | Primary | Issue Answer / handoff revise counts; expect >1 | Manual / ticket |
| Escape defects (Validator caught, Worker tests missed) | Primary | Validator fail reports vs Worker test logs | Manual until Mission Control events |
| Citation coverage (% assertions with valid clause versions) | Primary | Citation triple-gate tests; KB version fields | **Wired** (轨 A) |
| Verification cost vs wall-clock | Primary | CI duration + optional LangSmith/local trace spans | Partial (W0 local trace; W1 LangSmith) |
| Human hours per milestone | Secondary | Operator log / not automated | Aspirational |
| Time-to-gate; approval queue freshness | Secondary | Latch event timestamps in API / SQLite ledger | Partial (W0+) |
| Write-back rate (passes → KB/skills) | Secondary | Reviewed promotion PRs / skill diffs | Thin (§14 #7) |
| Judge–human agreement (κ / spot-check) | Secondary | Issues 10–11 fields; Phase 2a **W2** OpenEval ops | Wave-bound |
| Attention under concurrency | Secondary | Mission Control multi-session UX | Deferred (§14 #10) |
| Hook / nudge false-positive rate | Secondary | Hook owner dashboard / tune log | Aspirational |

Secondary never overrides primary. Do not “fix” attention by skipping locks or fail-closed gates.

---

## 13. Quotable summary for agents

> Build a **relay**, not a hive.  
> **Contract before code; verify what you automate.**  
> **One writer; many readers; parallel only when cheap.**  
> **Durable ledger; curated context; compound via write-back.**  
> **Independent, calibratable judge; human latch and understanding.**  
> **Own the loop; climb the A-ladder; correctness compounds.**  
> **Tax context deliberately; prefer hooks and lazy skills.**  
> **Grow the work surface, not the dump.**  
> **A\* ≠ Integration L\*; 作业壳 ≠ Production latch.**

---

## 14. Known gaps (wave-bound — not yet implementation bar)

This document is **formal doctrine**, not a claim that every substrate row is already shipped. Coding agents must **not pretend** these gaps are solved. Close gaps by climbing **one A-rung**; do not add role theater to paper over missing substrate.

| # | Gap | Bind to | Notes |
|---|-----|---------|-------|
| 1 | **Eval harness** — Ground-Truth / regression for missions; judge–human κ | Phase 1 Issues **10–11**; Phase 2a **W2** | OpenEval UI/leaderboard is W2 product; default CI stays `machine_check` |
| 2 | **Credential proxy & tool gateway** | **Deferred** (post-2a / A5) | Until then: new Access = demo-only or human-gated |
| 3 | **Cost model** — enforced token / wall-clock / coordination budgets | **Deferred**; observe via W1 traces | Metrics targets ≠ budgets in code |
| 4 | **Worktree / branch isolation** default | **Deferred** (solo-dev); required before true parallel writers | I4 still binds |
| 5 | **LLM planning layer** schema-bound (A2+) | Mission path **Next**; product 轨 B ≠ A2 claim | Choreography stays labeled until schema-bound |
| 6 | **Deep understanding tools** — ADR / threat model as mandatory mission inputs | **Deferred**; human architect still owns understanding (I6) | |
| 7 | **Knowledge write-back automation** | Thin now; promote via reviewed PRs; deepen post-W1 | Validator proposes only |
| 8 | **Org/multiplayer UX** (River-style shared corpus) | Phase 2a **W2** (multi-user eval ops) partial; full River **Deferred** | |
| 9 | **Agent work surface (+ gateway)** | **W0–W1** expand product Access (shell, SQLite, optional LangSmith); gateway = §14 #2 | No pretend prod-safe Access |
| 10 | **Attention / fleet UX** | **Deferred**; W2 may add labeled eval sessions only | Never weaken I4/I5 to “fix” attention |

**Phase 2a reminder:** W0 Dev Complete / W1 Pilot Complete / W2 Eval Ops share one product vision with **layered DoD**. Completing a wave does not auto-close every row above.

---

## Appendix A — Influences (tertiary — do not override lineage)

Coding agents: use as *extensions*, not excuses to weaken I1–I8. **Do not load this appendix unless resolving an external-practice conflict.**

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
| 9 | **Context tax / zero-overhead loading** | Daisy Hollman / Claude Code @ scale | I3, §0, §4.3, §10.13–14 |
| 10 | **Work surface = engineer surface** | Daisy Hollman | §7 |
| 11 | **Hooks & mistake-time feedback** | Daisy Hollman / 12-Factor | §4.3, §7 |
| 12 | **CLI+skill before internal MCP sprawl; attention as bottleneck** | Daisy Hollman / Anthropic agent UX | §7, §12, §14 |

Conflict reminder: Shopify-style parallel agents, content fan-out, and Claude-style multi-session fleets **never** override Factory serial write on one shared branch, fail-closed gates, or human latch. Context-engineering tricks never justify stuffing the full KB, bypassing Validator independence, or marking DONE without verification.

---

## Appendix B — Naming glossary

| Term | Use for |
|------|---------|
| **I1–I8** | Non-negotiable design invariants |
| **A0–A5** | Agent/harness autonomy ladder |
| **Integration L1/L2/L3** | Claims product field / core write-back / payout rails |
| **轨 A / 轨 B** | Deterministic green CI vs optional LLM assist |
| **W0 / W1 / W2** | Phase 2a delivery waves (product DoD), not autonomy rungs |

---

## Appendix C — Changelog

| Version | Date | Summary |
|---------|------|---------|
| **1.0** | 2026-09-14 | Formal constitution. Agent load map (§0); autonomy **A0–A5** vs Integration L\*; Claims Gate domain default; metrics wire table; wave-bound known gaps; influences demoted to Appendix A. |
| 0.3 | 2026-09-14 | Working draft incorporating SV panel loadability / naming / gap-wave / metrics-wire (superseded by 1.0). |
| 0.2 | — | Daisy / Claude Code @ scale integration (accepted into lineage). |
