# Multi-Agent Observability & Feedback Framework

## Project Goal

A tool for observing multi-agent (A2A) workflows in production and pre-production,
identifying which agent/step caused a workflow to fail, capturing a fix (from a
human or, later, a reward model), and feeding that fix back into the system so the
same failure — and semantically similar future failures — don't recur. The system
is validated via a regression suite and, eventually, a shadow-mode gate before any
change to agent behavior ships.

This file defines the v1 MVP scope precisely and the v2+ roadmap, so scope
creep during MVP build is easy to catch: if a task isn't listed under "MVP
Build Order," it belongs in "Future Development," not in the first version.

---

## Architecture Overview

```
A2A workflow (instrumented)
        │  
        ▼
     Kafka / Redpanda topic (canonical trace-event schema)
        │
        ├──► Postgres: raw span storage + per-run DAG (parent/child span IDs)
        │
        ▼
  Verifier registry + triage filter
        │
        ├─► deterministic PASS ──────────────► regression case (auto)
        │
        └─► FAIL / needs-human-judgment ──► Review UI (human diagnoses culprit node)
                                                   │
                                                   ▼
                                        Diagnosis: culprit node + correction
                                                   │
                                   ┌───────────────┴───────────────┐
                                   ▼                                ▼
                     Lesson store (pgvector, dedup)         Regression case (judged)
                                   │
                                   ▼
                    Retry loop: inject lesson → re-run task
                                   │
                                   ▼
                 Verifier / human checks retry outcome
                                   │
                                   ▼
             Log outcome tied to lesson ID (which lessons actually work)
```

**Scope for v1: one real A2A workflow, fully wired end to end.** Prove the loop
closes before generalizing to multiple workflows or importing traces from other
tools (LangSmith, etc.).

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Event streaming | Kafka (or Redpanda for lighter ops) | Standard for high-throughput trace ingestion; decouples producers (agents) from consumers (graph builder, verifiers) |
| Trace + graph storage | Postgres | Per-run graphs are small (tens of nodes) — parent/child span IDs in Postgres are enough. No dedicated graph DB needed at MVP scale. |
| Lesson/embedding store | Postgres + `pgvector` | Avoids running a separate vector DB service for MVP volume |
| Analytical trace store (deferred) | ClickHouse | Only bring in once running dashboards/aggregate queries across enough volume that Postgres shows strain. Has a native Kafka table engine (subscribes to a topic directly, no custom consumer needed) — cheap to adopt later. |
| Backend | Python (FastAPI) | Consumers, verifier registry, retry orchestrator, REST API for the frontend |
| Frontend | Svelte + SvelteKit | Component-scoped styling (no global CSS fights), lighter mental model than React for this team's stated priorities |
| Component library | shadcn-svelte | Pre-styled Radix-based components; styling reduces to Tailwind utility classes for layout only, no custom CSS/visual design work |
| Graph visualization | Svelte Flow (xyflow) | Native Svelte library (same team as React Flow); nodes are plain Svelte components, so click-to-diagnose UI is written like any other UI, not imperative canvas code |
| Instrumentation | OpenTelemetry | Standard span/trace format; wraps the A2A message bus |

---

## Data Model (v1) (Not finalized, save for later after deciding, do not build this yet)

### Canonical trace event (Kafka message schema)
```
{
  run_id: string,
  span_id: string,
  parent_span_id: string | null,
  agent_id: string,
  agent_role: string,
  task_type: string,
  event_type: "message" | "tool_call" | "state_change",
  payload: object,
  timestamp: datetime,
  status: "in_progress" | "completed" | "failed" | "timed_out"
}
```

### Graph node/edge (Postgres)
- `nodes`: `run_id, span_id, agent_id, agent_role, payload_summary, status, started_at, ended_at`
- `edges`: `run_id, parent_span_id, child_span_id`

### Diagnosis (from Review UI)
```
{
  run_id, culprit_span_id, diagnosis_text, correction_text,
  reviewer_id, created_at, task_type
}
```

### Lesson (pgvector)
```
{
  lesson_id, embedding, task_type, failure_summary, correction_text,
  source_diagnosis_id, created_at
}
```

### Regression case
```
{
  case_id, task_type, lane: "deterministic" | "judged",
  input_snapshot, expected_outcome (for deterministic),
  verifier_fn_ref (for deterministic), source_diagnosis_id (for judged),
  last_run_status, last_run_at
}
```

### Retry outcome log
```
{
  retry_id, original_run_id, lesson_ids_injected: [lesson_id],
  outcome: "success" | "fail", checked_by: "verifier" | "human",
  created_at
}
```

---

## MVP Build Order

### Phase 1 — Instrument one workflow into Kafka
- Pick one real A2A workflow.
- OTel interceptor on the A2A message bus emitting spans per the canonical schema above.
- Kafka producer; confirm events land on the topic in order per `run_id`.

### Phase 2 — Build the graph layer in Postgres
- Kafka consumer groups spans by `run_id`/`parent_span_id` into `nodes`/`edges` tables.
- Minimal internal viewer (can be a debug endpoint before the real UI exists) to confirm the DAG is correct for a few sample runs.

### Phase 3 — Verifier registry + triage filter
- Registry: `task_type -> validator_fn` (exact match, numeric tolerance, JSON schema check).
- Triage filter (pure logic, no ML): classify each completed run as `pass`, `verified_fail`, or `needs_human_judgment` based on verifier result, terminal status, or budget/turn-count overrun.
- Verifiers should return a graded score, not just boolean, where feasible (e.g., % of required JSON fields present) — near-misses shouldn't look identical to total failures.

### Phase 4 — Human review UI (Svelte + shadcn-svelte + Svelte Flow)
- Queue view: list of runs needing human judgment.
- Run view: Svelte Flow graph of the run's DAG; clicking a node opens a diagnosis form (culprit confirmation + correction text).
- Submitting writes a `Diagnosis` record.

### Phase 5 — Lesson store with dedup
- On new diagnosis: embed `failure_summary + correction_text`.
- Check cosine similarity against existing lessons for the same `task_type`; merge/skip insert if above threshold, else insert new lesson.
- Retrieval endpoint: given a new task's context, embed and return top-k similar lessons.

### Phase 6 — Retry loop with outcome logging
- On confirmed diagnosis (or verified_fail with an existing relevant lesson), retrieve top-k lessons, inject into the task's context, re-run the workflow for that task.
- Check outcome via verifier (deterministic) or a follow-up human check (judged).
- Log the retry outcome tied to the specific `lesson_id`(s) injected — this is what lets you later tell which lessons actually help vs. sit unused or actively hurt.

### Phase 7 — Regression runner
- Every confirmed diagnosis (deterministic or judged) becomes a permanent `RegressionCase`.
- Deterministic cases: runner replays them automatically on any prompt/config change, using the verifier — no human cost.
- Judged cases: queue for periodic human spot-check rather than full automation in v1.
- This is the MVP stand-in for full shadow-mode gating (see below).

**Definition of done for v1:** point the system at the chosen workflow, watch a failed run land in the review queue, have a human diagnose and fix it, see the fix retrieved and injected on a semantically similar future task, watch the retry succeed, and run a regression suite of 20–50 real captured failures automatically on every change with all deterministic cases staying green.

---

## Explicitly Out of Scope for v1

- Automated causal attribution (counterfactual replay / Shapley-based blame assignment)
- Any reward model (LLM-as-judge or trained)
- LoRA fine-tuning or any policy weight updates
- Dedicated graph database (Neo4j etc.)
- Full production-traffic shadow-mode replay with statistical gating
- Multi-source trace imports (LangSmith, etc.) — native A2A only for v1
- ClickHouse — only adopt once Postgres shows strain on aggregate queries

---

## Future Development (v2+)

### Automated failure attribution
- Model each run as a structural causal model; resample candidate steps (multiple resamples per candidate for stability against LLM stochasticity) and measure outcome shift.
- Use Monte Carlo permutation sampling for Shapley-style credit assignment (exact Shapley is intractable — O(2^n) over steps).
- Reference implementation to study first: Causal Agent Replay (github.com/jaineet17/causal-agent-replay) — handles the "locus" confound between an upstream error and a downstream failure it didn't actually cause.
- Treat output as a confidence-scored ranked shortlist, not ground truth — route top candidates to the reward model / human review, same as v1's triage step, rather than replacing it outright.
- Every confirmed human diagnosis becomes labeled training data for improving this algorithm over time (a domain-specific version of the "Who&When" benchmark, specific to this system's actual workflows).

### Reward model
- **v2a — LLM-as-judge (generative reward model).** No training infra needed. Use a model different from (ideally stronger than) the agents being judged, to avoid self-preference bias. Rubric + chain-of-thought before verdict. Randomize answer order to avoid position bias. Sample a subset for human double-check to measure calibration.
- **v2b — Trained reward model / Process Reward Model (PRM).** Once enough confirmed preference pairs exist (thousands), train a scalar reward model (Bradley-Terry loss on preference pairs) or, better fit for multi-agent step-level attribution, a PRM that scores each agent turn's contribution to the outcome (see AgentPRM-style TD/GAE value estimation). A trained PRM and the causal attribution engine answer the same underlying question from two angles (learned value function vs. causal replay) — consider using attribution engine output as bootstrap training data for the PRM.
- Watch for reward hacking once this feeds any RL/optimization loop — mitigate with a KL penalty against a reference policy, ensembling multiple judges, and periodic recalibration against fresh human labels.

### Policy update mechanisms
- v1 uses retrieval-augmented lesson injection only (no weight changes).
- v2: once enough preference pairs/lessons accumulate, move to LoRA fine-tuning on the underlying policy model, or treat agent prompts as optimizable parameters via a DSPy-style prompt optimizer.
- Both must pass through the shadow-mode gate (below) before promotion.

### Shadow-mode gate (full version)
- Before promoting any updated policy (new lesson set, LoRA weights, or optimized prompts), replay the full regression suite plus a sample of recent production traffic against the candidate version, with no production side effects.
- Gate promotion on a statistically significant success-rate improvement (not just "did it pass"), since LLM outputs are stochastic.

### Other later additions
- Dedicated graph DB (Neo4j) once cross-run graph pattern mining is needed at scale (e.g., "find all workflows with this failure shape").
- ClickHouse for trace storage once aggregate/dashboard query volume justifies it — has a native Kafka table engine, so adoption is a swap-out, not a redesign.
- Multi-source trace import adapters (LangSmith, etc.) — requires a normalization layer mapping each source's schema into the canonical event schema before it reaches the graph builder.
- Cytoscape.js as a secondary visualization for large-scale, non-hierarchical graph views once Svelte Flow's DOM-based rendering becomes a bottleneck (hundreds+ of nodes).
