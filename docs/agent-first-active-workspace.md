# Agent-first Active Workspace Architecture

- Protocol ID: `active-workspace`
- Version: `0.1.0`
- Maturity: `design-only`
- Evidence scope: no documented binding yet
- Level namespace: `active-workspace:L0`–`active-workspace:L4`
- Last updated: 2026-07-17

## 1. Purpose

An agent with long-term memory can still fail because the wrong information is active at the wrong time. It may load too much history, forget the current success criterion, keep a disproven assumption alive, or let a weak side idea rewrite an otherwise sound task.

Active Workspace is a short-lived, source-aware control surface for the current task. It records what deserves attention now:

- the active goal and success criteria;
- hard constraints and permissions;
- verified facts and their sources;
- assumptions still carrying the plan;
- unresolved conflicts and risks;
- selected memory pointers;
- candidate actions and current commitment;
- bounded interrupts from Inner Speech or Council.

Its product is **attention calibration**.

> Memory asks, "What has been retained?" Active Workspace asks, "What should influence this task now?"

## 2. Inspiration and boundary

[Anthropic's Global Workspace / J-space research](https://www.anthropic.com/research/global-workspace) motivates the engineering idea that a sparse set of currently active representations can influence many downstream computations.

This protocol does not claim to expose that internal latent mechanism. It specifies an external, inspectable workspace inspired by the control function:

```text
Internal J-space:
  a hypothesis about model-internal representation.

Agent-first Active Workspace:
  an explicit task-state artifact with bounded fields and mutation rules.
```

The analogy is useful only while this distinction remains explicit.

## 3. Design goals

1. Keep the active task state small enough to guide action.
2. Separate verified facts, assumptions, conflicts, and weak signals.
3. Preserve provenance for every load-bearing item.
4. Let one agent or several agents share the same protocol.
5. Allow interruption without allowing arbitrary takeover.
6. Expire transient state instead of polluting long-term Memory.
7. Support replay and debugging without requiring private chain-of-thought.
8. Degrade to an in-memory checklist when no persistent runtime exists.

## 4. Non-goals

Active Workspace is not:

- Long-term Memory.
- A raw transcript or tool-call log.
- A hidden chain-of-thought store.
- The final user-facing answer.
- A task scheduler for all agents and tools.
- An autonomous source of truth.
- A place where every retrieved item becomes active.
- A requirement to serialize every intermediate cognition.

It may contain concise rationale and explicit assumptions. It must not require unrestricted private reasoning traces.

## 5. Core model

The workspace has one lifecycle and five item classes.

### 5.1 Lifecycle

```text
initialize
  → activate
  → work
  → update
  → interrupt/reconcile when needed
  → close
  → selectively emit durable artifacts
  → expire
```

### 5.2 Item classes

| Class | Meaning | Example |
| --- | --- | --- |
| Anchor | Goal, success criterion, hard constraint, permission | "Do not modify production" |
| Evidence | Observed fact with a source | "HEAD is abc123" from `git rev-parse` |
| Model | Assumption, hypothesis, prediction, or causal frame | "The failure may be proxy-related" |
| Tension | Conflict, risk, uncertainty, or missing information | "README and runtime disagree" |
| Action | Candidate, committed, blocked, completed, or rolled-back step | "Inspect live config" |

The classes are semantic. A binding may use different field names, but it MUST preserve the distinction between evidence and interpretation.

## 6. Workspace schema

The five semantic item classes map to schema collections as follows:

| Semantic class | Schema location | Mapping rule |
| --- | --- | --- |
| `anchor` | `goal`, `constraints[]` | The goal statement, success criteria, permissions, and hard constraints are anchors. |
| `evidence` | `evidence[]` | Only sourced observations enter this collection. |
| `model` | `assumptions[]`, `weak_signals[]` | Assumptions are actionable models; weak signals remain gated models and retain their originating protocol type. |
| `tension` | `conflicts[]`, `risks[]` | Conflicts, uncertainty, missing information, and material risks are tensions. |
| `action` | `actions[]` | Candidate, committed, blocked, completed, and rolled-back steps are actions. |

`memory_activations[]` stores source pointers rather than a sixth semantic class. `interrupts[]` contains admission proposals; once accepted, their content is mapped into one of the five classes. `decision_log[]` is an audit surface, not an active-item collection.

A minimal workspace snapshot:

```yaml
workspace_id: ws-2026-07-15-001
task_id: task-001
revision: 4
status: active
owner: agent:main
created_at: 2026-07-15T10:00:00+08:00
expires_at: 2026-07-15T18:00:00+08:00

goal:
  statement: "Determine why the deployment is unhealthy"
  source_refs: ["user:current-request"]
  success_criteria:
    - "Root cause is supported by runtime evidence"
    - "No production mutation occurs"

constraints:
  - id: c-001
    statement: "Read-only diagnosis"
    source_refs: ["user:current-request"]
    status: active

evidence:
  - id: e-001
    statement: "Health endpoint returns 503"
    source_refs: ["runtime:curl-2026-07-15T10:03"]
    confidence_scheme: epistemic-status-v1
    confidence: observed-once
    status: active

assumptions:
  - id: a-001
    statement: "The application cannot reach its database"
    source_refs: ["e-001"]
    confidence_scheme: epistemic-status-v1
    confidence: inferred
    status: testing
    falsifier: "A successful database query from the application container"

conflicts: []
risks: []
memory_activations: []
weak_signals: []

actions:
  - id: act-001
    statement: "Inspect application logs"
    status: committed
    depends_on: []

interrupts: []
decision_log: []
```

### 6.1 Required top-level fields

- `workspace_id` — stable within the task.
- `task_id` — links artifacts from other protocols.
- `revision` — monotonically increasing optimistic-concurrency token.
- `status` — `active | paused | closing | closed | expired`.
- `owner` — the only default writer unless a multi-writer contract exists.
- `goal` — source-aware statement and observable success criteria.
- `constraints` — hard task boundaries.
- `evidence` — source-aware observations.
- `assumptions` — interpretations that may be disproven.
- `conflicts` — incompatible evidence, goals, assumptions, or actions.
- `actions` — candidate and committed next steps.

### 6.2 Optional fields

- `memory_activations` — pointers to Memory items, never pasted trust-free.
- `weak_signals` — low-confidence side observations, gated from main action.
- `risks` — harm, irreversibility, or failure conditions.
- `interrupts` — bounded proposals from Inner Speech, Council, monitors, or humans.
- `decision_log` — concise accepted/rejected/deferred decisions.

## 7. Workspace item metadata

Every item that can change an action SHOULD carry:

```yaml
id: <stable within task>
statement: <concise proposition or action>
class: <anchor | evidence | model | tension | action>
source_refs: []
confidence_scheme: <epistemic-status-v1 | ordinal-confidence-v1>  # when the item makes an epistemic or predictive claim
confidence: <closed token from confidence_scheme>
status: <class-specific closed token>
salience: <critical | high | normal | low>
owner: <role or agent>
created_at: <timestamp>
expires_at: <optional timestamp>
```

When an item lives in a typed collection, the collection supplies `class`, so the field MAY be omitted locally; it MUST be restored when the item crosses a protocol boundary. `source_refs` is required for load-bearing claims. `confidence_scheme` and `confidence` are required for factual, causal, predictive, or frame-changing claims, but SHOULD be omitted for pure commands or permissions that make no epistemic claim. Evidence and state-like assertions normally use `epistemic-status-v1`; predictions, risks, recommendations, and imported Walk hypotheses may use `ordinal-confidence-v1`. Receivers preserve the producer's scheme and never convert silently.

Within `epistemic-status-v1`, `confirmed` means authoritative, repeated, or independently corroborated for the stated scope; `observed-once` means one direct bounded observation; `inferred` means derived rather than directly observed; and `unknown` means the evidence cannot support a stronger classification. `confirmed` does not mean permanent.

`salience` determines attention, not truth. A critical inferred assumption is still inferred.

### 7.1 Closed item-status vocabularies

Bindings MAY add a versioned status scheme, but they MUST NOT use free prose for status. The default vocabularies are:

| Collection | Closed values |
| --- | --- |
| `constraints[]` | `active | satisfied | revoked | superseded` |
| `evidence[]` | `active | disputed | superseded | expired` |
| `assumptions[]` | `proposed | testing | supported | disproven | expired` |
| `conflicts[]` | `open | investigating | resolved | escalated` |
| `risks[]` | `open | mitigated | accepted | realized | expired` |
| `weak_signals[]` | `proposed | investigating | rejected | discharged | expired` |
| `actions[]` | `candidate | committed | in-progress | blocked | completed | rolled-back | cancelled` |
| `interrupts[]` | `proposed | accepted | rejected | deferred | expired` |

Imported artifacts preserve their producer status in `origin_status` and use the workspace status vocabulary in `status`. This prevents a Walk's `active` or Council's `decided` token from being silently reinterpreted as workspace state.

## 8. Activation protocol

Workspace activation is selective retrieval, not bulk loading.

### 8.1 Activation sources

Items may enter from:

- the current user request;
- system or task instructions;
- direct tool/runtime observations;
- gated Memory retrieval;
- a Council artifact;
- an Inner Speech control cue;
- a surfaced Auto-Walk hypothesis;
- an explicit human correction.

### 8.2 Admission gate

Before admitting an item, ask:

1. Is it relevant to the active goal or a material risk?
2. Is its source visible?
3. Is it evidence, inference, or a weak hypothesis?
4. What action could it change?
5. When should it expire or be reviewed?

An item that cannot answer question 4 normally remains background rather than active state.

### 8.3 Source-specific rules

- **User/task anchors** enter with high salience but still preserve exact scope.
- **Runtime evidence** enters as evidence, not interpretation.
- **Memory** retains its original `kind`, `Status`, date, `Source`, and `Confidence`. Activation never launders a stale memory into current truth.
- **Auto-Walk** enters only as a labeled weak signal or hypothesis. Preserve the Walk token as `origin_status`, set the workspace-local `status`, and retain its confidence scheme and references. It cannot become an action premise without verification.
- **Council** enters as candidate, dissent, decision, or frame challenge. Consensus count is metadata, not evidence.
- **Inner Speech** enters as a proposed control cue or interrupt, not a fact.

## 9. Attention budget and eviction

An unbounded workspace becomes a second memory dump and loses its control function.

A binding SHOULD set budgets, for example:

- one active goal;
- three to seven success criteria/constraints;
- a small set of load-bearing evidence and assumptions;
- no more than three committed next actions;
- weak signals excluded from the default action view;
- closed items summarized or evicted.

Eviction order:

1. Expired weak signals.
2. Completed actions whose outcome is recorded.
3. Disproven assumptions, retained only in the concise decision log.
4. Low-salience evidence no longer connected to an active assumption.
5. Old conflicts that have an explicit resolution.

Anchors remain until the task closes unless the user or authorized controller changes them.

## 10. Update and reconciliation

Every material change increments `revision` and records a concise delta:

```yaml
- revision: 5
  changed_at: <timestamp>
  actor: agent:main
  operations:
    - "assumption a-001: testing → disproven"
    - "evidence e-004 added"
    - "action act-002 committed"
```

When evidence conflicts:

1. Keep both observations visible with sources.
2. Create a `conflict` item.
3. Stop any action whose safety depends on choosing silently.
4. Define the discriminating observation or ask the user.
5. Resolve the conflict explicitly; do not delete the losing history from the run record.

This mirrors Memory's Reconcile discipline at task scope.

## 11. Interrupt protocol

An interrupt is a request to reconsider attention or action. It is not an override.

```yaml
interrupt_id: int-001
producer: inner-speech:inside-outsider
trigger: "three failed attempts with the same causal frame"
claim: "The task may be framed as an implementation failure when it is a requirement conflict"
evidence_refs: ["act-001", "act-002", "act-003"]
recommended_action: redirect
urgency: high
status: proposed
```

The workspace owner MUST set `status` to:

- `accepted` — updates goal, assumptions, or action;
- `rejected` — records a reason;
- `deferred` — names a review trigger;
- `expired` — no longer relevant.

Interrupt producers cannot directly change anchors or committed actions unless the binding explicitly grants that authority.

## 12. Single-agent execution

A conforming single agent can keep the workspace only in current context:

```text
1. State the goal and success criteria.
2. List hard constraints.
3. Separate evidence from assumptions.
4. Choose at most the next few actions.
5. Update only when new evidence changes the state.
6. Close with outcomes and durable capture candidates.
```

No file or service is required. A Markdown checklist or structured in-context block is a valid `active-workspace:L0` binding.

## 13. Multi-agent execution

Multi-agent workspaces introduce coordination, not a different cognitive protocol.

### 13.1 Default ownership

- One controller owns the canonical revision.
- Participants submit patches, evidence, candidates, or interrupts.
- The owner validates base revision and merges accepted operations.
- Participants do not overwrite the full snapshot.

### 13.2 Patch shape

```yaml
patch_id: patch-reviewer-003
base_revision: 7
producer: role:skeptic
operations:
  - op: add
    collection: risks
    value: {...}
  - op: propose_status
    item_id: a-002
    value: disputed
```

A stale `base_revision` requires rebase or rejection. Last-writer-wins is forbidden for shared goals, constraints, and decisions.

### 13.3 Context isolation

Participants MAY receive different evidence slices or role contracts. The RunRecord must disclose those differences so later disagreement is not mistaken for irrationality.

## 14. Protocol connections

### Memory

Workspace requests memory by trigger or id. It imports metadata and records later outcome feedback with `verdict_scheme: intervention-outcome-v1` and `helpful | misleading | neutral | unknown`. It never edits Memory directly.

### Inner Speech

Inner Speech reads a bounded snapshot and emits a short control cue. The workspace records only cues that materially change or challenge an action.

### Council

Council receives a frozen GoalContract and evidence snapshot. It returns versioned artifacts. The workspace owner decides how the DecisionRecord affects the active plan.

### Auto-Walk

A surfaced hypothesis enters `weak_signals`, not `evidence`. Workspace closure may record whether it was ignored, investigated, rejected, or discharged through the ordinary Walk protocol.

## 15. Close, persistence, and routing

At task completion:

1. Mark the workspace `closing`.
2. Record success criteria outcomes.
3. Resolve or explicitly carry forward open conflicts.
4. Route durable artifacts through their proper protocols.
5. Produce a concise run summary if replay is useful.
6. Mark the workspace `closed`; expire transient items.

Routing rules:

| Workspace content | Destination |
| --- | --- |
| Stable reusable outcome | Memory capture |
| Raw high-value execution evidence | Memory archive or external log system |
| Confirmed behavioral rule candidate | Memory first, then reviewed promotion |
| Weak cross-domain possibility | Auto-Walk candidate, not Memory |
| Council decision and dissent | Council RunRecord; Memory only if reusable |
| Inner Speech cue | Normally expires; capture only its independently reusable result |

## 16. Observability and privacy

A workspace SHOULD be inspectable at the level of state transitions and decision-relevant reasons.

It SHOULD NOT require:

- private token-level reasoning;
- unrestricted internal monologue;
- sensitive content unrelated to the task;
- every considered alternative;
- model-hidden activations.

Recommended visibility layers:

```text
private-ephemeral: bounded control state used inside the run
shared-run: evidence, assumptions, conflicts, and actions shared among participants
durable-audit: decisions, outcomes, and material interventions
public-rationale: concise explanation appropriate for the user
```

## 17. Failure modes

| Failure mode | Symptom | Prevention |
| --- | --- | --- |
| Workspace bloat | Everything is active; nothing guides action | Attention budget and eviction |
| Evidence/assumption collapse | Inference is acted on as fact | Separate item classes and provenance |
| Memory laundering | Stale memory becomes current merely by retrieval | Preserve Memory metadata and reconcile |
| Weak-signal takeover | Auto-Walk idea rewrites the main task | Keep weak signals in a separate gated collection |
| Goal drift | Actions optimize a proxy | Keep goal/success criteria as anchors; use Inside-Outsider trigger |
| Interrupt storm | Participants continuously challenge progress | Materiality threshold, deduplication, cooldown |
| Shared-state race | Agents overwrite one another | Single owner or revision-checked patches |
| Thought dump | Workspace becomes verbose private narration | Store structured state, not chain-of-thought |
| Permanent scratchpad | Transient state leaks into Memory | Close/expiry and explicit routing |
| False objectivity | Workspace is treated as the world itself | Sources, confidence, conflicts, external verification |

## 18. Implementation levels

| Level | Name | Capability |
| --- | --- | --- |
| `active-workspace:L0` | In-context workspace | One agent maintains a bounded checklist during a task. |
| `active-workspace:L1` | Structured snapshot | Stable schema, item classes, revision, and expiry. |
| `active-workspace:L2` | Protocol activation | Gated Memory, Inner Speech, Walk, or Council artifacts can enter. |
| `active-workspace:L3` | Shared workspace | Multi-agent patches, ownership, and conflict handling. |
| `active-workspace:L4` | Feedback-aware | Outcomes emit signals compatible with `memory:L5` metamemory and `council:L5` outcome evaluation. |

Each completed level remains useful without adopting another protocol. Conformance claims are cumulative within the Active Workspace ladder.

## 19. Validation checklist

1. A new task can initialize goal, success criteria, and constraints.
2. Evidence and assumptions are represented separately.
3. Every load-bearing item has a source reference.
4. Retrieved Memory retains its original trust metadata.
5. A Walk hypothesis cannot enter `evidence` without verification.
6. At most one owner mutates the canonical revision by default.
7. A stale multi-agent patch is rejected or rebased.
8. An interrupt is accepted, rejected, deferred, or expired explicitly.
9. Task closure routes durable knowledge through Memory capture.
10. Transient cues and weak signals expire.
11. Replay does not require hidden chain-of-thought.
12. The protocol works in a single-agent, in-context-only binding.

## 20. Final rule

Active Workspace is not another memory store. It is a bounded answer to a momentary question:

```text
Keep the goal visible.
Keep evidence distinct from interpretation.
Activate history skeptically.
Keep conflicts explicit.
Commit only the next useful actions.
Let bounded observers interrupt, never silently take over.
Route durable outcomes through their own protocols.
Then expire the workspace.
```
