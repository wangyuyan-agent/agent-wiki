# Agent-first Active Workspace Architecture

- Protocol ID: `active-workspace`
- Version: `0.2.0`
- Maturity: `design-only`
- Evidence scope: No documented binding yet. One public study provides run-reported design evidence for the optional audited-completion profile; no `active-workspace@0.2.0` conformance or profile behavior has been validated.
- Level namespace: `active-workspace:L0`–`active-workspace:L4`
- Last updated: 2026-08-13

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

Externally, one public run-reported study ([LongHorizon-Harness, arXiv:2608.01964](https://arxiv.org/abs/2608.01964)) describes an implementation that keeps task state outside execution and gates persistent state updates on environment-grounded audit findings. This protocol adopts only the transferable boundary between a completion claim and completion evidence, as the optional §15.1 profile. It does not adopt the study's benchmark claims, and it does not require distinct manager, executor, or auditor roles.

## 3. Design goals

1. Keep the active task state small enough to guide action.
2. Separate verified facts, assumptions, conflicts, and weak signals.
3. Preserve provenance for every load-bearing item.
4. Let one agent or several agents share the same protocol.
5. Allow interruption without allowing arbitrary takeover.
6. Expire transient state instead of polluting long-term Memory.
7. Support replay and debugging without requiring private chain-of-thought.
8. Degrade to an in-memory checklist when no persistent runtime exists.
9. Optionally gate completion on criterion-appropriate verification without making audit universal.

## 4. Non-goals

Active Workspace is not:

- Long-term Memory.
- A raw transcript or tool-call log.
- A hidden chain-of-thought store.
- The final user-facing answer.
- A task scheduler for all agents and tools.
- A mandatory verifier, multi-agent topology, or independent model.
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

These fields are required for a structured snapshot (`active-workspace:L1+`). An `active-workspace:L0` in-context binding (§12) preserves the same semantic distinctions without the formal schema.

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

Steps 1–6 are the baseline close path and remain valid without any profile. When the optional §15.1 profile is enabled for the task, step 2 and any transition of an in-scope action to `completed` follow the §15.1 verification rules. The profile adds no top-level workspace status: the workspace still uses `active | paused | closing | closed | expired`.

Routing rules:

| Workspace content | Destination |
| --- | --- |
| Stable reusable outcome | Memory capture |
| Raw high-value execution evidence | Memory archive or external log system |
| Confirmed behavioral rule candidate | Memory first, then reviewed promotion |
| Weak cross-domain possibility | Auto-Walk candidate, not Memory |
| Council decision and dissent | Council RunRecord; Memory only if reusable |
| Inner Speech cue | Normally expires; capture only its independently reusable result |

### 15.1 Optional profile: audited task completion

This profile is optional and off by default. The baseline close path remains valid without it, enabling it changes nothing in §18, and using it does not raise any level, maturity, or conformance claim.

**When to enable.** A binding MUST enable the profile when the user or task contract explicitly requires audited completion. It SHOULD enable the profile per task when one or more hold: the task is long or has many dependent steps; its effects are irreversible or persist outside the workspace; failure cost or risk is high; the task has repeatedly failed; or completion is ambiguous from the outputs alone. Short, low-risk, easily repeated tasks SHOULD NOT be audited by default.

Enablement is explicit and scoped. Before verification begins, the workspace records an attributable `decision_log[]` entry naming the trigger and `scope_refs`; those references MUST identify every action whose state may advance and the criteria and constraints used to judge it. A binding MAY enable the profile before execution or after an ambiguous completion claim. This declaration activates only the rules for that scope and creates no new authority. The completed verification records the mode actually used.

**Work contract.** The profile adds no contract fields. `goal.statement`, `goal.success_criteria`, `constraints[]`, and the in-scope committed `actions[]` are the work contract, and `evidence[]` carries its observations. Within this profile, an in-scope `requirement` is a success criterion, a constraint, or an action statement that itself supplies an observable completion condition. Success criteria SHOULD be stated observably before execution starts. Profile metadata refers to these existing fields by stable item id or by a revision-bound pointer such as `goal.success_criteria[0]`; it does not create a parallel GoalContract.

**Completion claims are unverified.** An executor's report that work is done — including this agent's own belief in a single-agent binding — is a completion claim. A completion claim is not evidence: it MUST NOT enter `evidence[]` and MUST NOT by itself advance an in-scope action to `completed` or record a success criterion as satisfied. It MAY be recorded in `decision_log[]` or a patch as a claim awaiting verification.

**Verification.** Verification re-observes the task environment and maps current evidence to the contract:

1. It reads the goal, success criteria, constraints, and declared outputs. It MAY use a concise completion claim to locate outputs, but it MUST NOT treat that claim, the raw interaction trajectory, or private reasoning as completion evidence.
2. It gathers fresh, source-referenced observations appropriate to each requirement: files, runtime state, logs, test output, external systems, or an attributable user or authority response when the criterion is an approval, choice, or permission.
3. It records one finding per in-scope requirement, each with evidence references.
4. It MUST NOT mutate task-relevant state. If an observation step changed the result under inspection or exceeded the declared constraints, `integrity_status` is `violation`, and that verification cannot support `completed`.

**Independence.** Independence means the verification's evidence and verification steps are separate from the completion claim — not necessarily a distinct actor or model. Declared modes express increasing minimum isolation:

- `same-agent-separated-phase` — the same agent verifies in a distinct phase; valid at `active-workspace:L0`. Findings MUST come from fresh environment observations, not from rereading its own report.
- `fresh-context` — a verifier that does not carry the execution conversation state or raw trajectory.
- `heterogeneous-verifier` — a different agent, model, or toolchain operating from a fresh or otherwise bounded verification context that excludes the raw trajectory.

Modes are binding declarations. Provider or model labels do not prove independence; a binding discloses the actual context and evidence boundary. No mode strengthens a conformance claim.

**Verification metadata.** Findings travel in existing artifacts: a `decision_log[]` entry plus sourced `evidence[]` items in a single-agent binding; a §13.2 patch whose operations add evidence and propose status in a shared workspace; or one entry in the `verification[]` field of a [Steward](agent-first-steward.md#106-resultenvelope) ResultEnvelope when the task ran under delegation. The canonical embedded record is the mapping below, without an implied enclosing field. A single-agent decision entry or patch operation MAY carry it under a `verification` member; a Steward binding appends the mapping itself to `ResultEnvelope.verification[]`.

```yaml
profile: active-workspace/audited-completion
workspace_id: ws-2026-07-15-001
base_revision: 7                  # required at active-workspace:L1+ unless supplied by the carrier
scope_refs: ["goal.success_criteria[0]", c-001, act-001]
findings:
  - requirement_ref: "goal.success_criteria[0]"
    result: <met | not-met | undetermined>
    evidence_refs: [e-007, e-008]
completion_status: <complete | incomplete | blocked>
integrity_status: <clean | suspect | violation>
remaining_gaps: []
verifier: <role or agent>
observed_at: <timestamp>
verification_mode: <same-agent-separated-phase | fresh-context | heterogeneous-verifier>
```

At `active-workspace:L0`, an in-context equivalent MAY omit `workspace_id` and `base_revision` while preserving every semantic distinction. At `active-workspace:L1+`, both values are required either in `verification` or in its enclosing carrier; duplicated values MUST match. `base_revision` identifies the contract and task-relevant workspace state that verification observed at `observed_at`. After validating that base, the owner MAY commit the new evidence, verification record, and permitted status transition as one revisioned update; the resulting revision does not make its own verification stale. A stale patch follows §13.2, and findings MUST be re-observed rather than carried through a rebase when task-relevant state may have changed.

The profile-local closed tokens mean:

| Register | Token | Meaning |
| --- | --- | --- |
| Finding | `met` | Current criterion-appropriate evidence supports the referenced requirement. |
| Finding | `not-met` | Current criterion-appropriate evidence shows that the referenced requirement is unsatisfied. |
| Finding | `undetermined` | Available evidence cannot decide the referenced requirement. |
| Completion | `complete` | Every in-scope requirement has a `met` finding. |
| Completion | `incomplete` | At least one in-scope requirement has a `not-met` finding; this result takes precedence if other findings are `undetermined`. |
| Completion | `blocked` | No finding is `not-met`, and at least one is `undetermined` because a named evidence, access, authority, dependency, or environment gap prevents `complete`. |
| Integrity | `clean` | No task-relevant verifier mutation, boundary breach, or unresolved integrity concern was found. |
| Integrity | `suspect` | A possible contamination or boundary problem could not be resolved. |
| Integrity | `violation` | Verification changed task-relevant state or crossed a declared boundary. |

These are protocol-local vocabularies, not confidence schemes. `completion_status` and `integrity_status` are distinct registers, and both are distinct from item `status` and `confidence`: an action's `completed` token records lifecycle, `confidence` records epistemic strength, `completion_status` records whether the contract is satisfied, and `integrity_status` records whether the verification itself stayed clean and inside its boundaries. `completion_status: complete` with an `integrity_status` other than `clean` MUST NOT advance the canonical `completed` state.

`remaining_gaps` MUST reference every `not-met` or `undetermined` requirement and every unresolved integrity concern that affects the verdict. It is empty for a successful verification: all in-scope requirements are `met`, `completion_status` is `complete`, and `integrity_status` is `clean`.

**Authority.** The workspace owner remains the only canonical writer (§13.1). A verifier proposes evidence and status deltas and gains no new authority. One actor MAY hold executor, verifier, and owner roles in `same-agent-separated-phase`, but it MUST record the verification result before applying the owner transition; these operations MAY share the atomic revisioned update described above, but their logical order remains fixed, and role co-location does not merge the completion claim with the evidence record. With the profile enabled, the owner advances an in-scope action to `completed` or records a successful criterion outcome only when `completion_status` is `complete`, every in-scope finding is `met` with criterion-appropriate sourced evidence, and `integrity_status` is `clean`. The workspace MAY still enter its ordinary `closed` status while its decision log records an `incomplete`, `blocked`, or unverified outcome; the Agent MUST disclose that outcome and MUST NOT claim completion.

**Profile non-goals.** The profile does not: audit every task; require a distinct model or agent; define a verifier implementation; create a new authority; retain hidden reasoning or raw trajectories; accept consensus or self-report as evidence (§8.3); or claim that auditing supplies a capability the underlying model lacks.

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
| False completion | An executor claim advances `completed` without criterion-appropriate sourced evidence | §15.1: claims stay unverified; only clean, criterion-appropriate verification supports `completed` |
| Audit theatre | The verifier treats the report or trajectory as evidence instead of re-observing the environment | §15.1 separates the claim from evidence; fresh-context modes exclude the raw trajectory |
| Completion/integrity collapse | "Complete but suspect" is treated as done | Separate `completion_status` and `integrity_status`; non-`clean` cannot advance `completed` |
| Audit cost inversion | Every short, low-risk task pays full verification | §15.1 risk gate; the baseline close path remains valid |

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

Verify the items applicable at the claimed level and under the conditions the binding has enabled; untagged items apply from `active-workspace:L0`.

1. A new task can initialize goal, success criteria, and constraints.
2. Evidence and assumptions are represented separately.
3. Every load-bearing item has a source reference.
4. (`active-workspace:L2+`, when Memory is adopted) Retrieved Memory retains its original trust metadata.
5. (`active-workspace:L2+`, when Auto-Walk is adopted) A Walk hypothesis cannot enter `evidence` without verification.
6. At most one owner mutates the canonical revision by default.
7. (`active-workspace:L3+`) A stale multi-agent patch is rejected or rebased.
8. An interrupt is accepted, rejected, deferred, or expired explicitly.
9. (when Memory is adopted) Task closure routes durable knowledge through Memory capture.
10. Transient cues and weak signals expire.
11. Replay does not require hidden chain-of-thought.
12. The protocol works in a single-agent, in-context-only binding.
13. (when the §15.1 profile is enabled) A completion claim alone cannot enter `evidence[]` or advance `completed`.
14. (when the §15.1 profile is enabled) `completed` is supported by `completion_status: complete`, `integrity_status: clean`, and a `met` finding with criterion-appropriate sourced evidence for every in-scope requirement.
15. (when the §15.1 profile is enabled) A verification that mutated task-relevant state is recorded as a `violation` and does not support `completed`.
16. (when the §15.1 profile is enabled at `active-workspace:L1+`) Verification records the workspace id, base revision, observation time, and declared mode; stale findings are re-observed when task-relevant state may have changed.

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
