# Agent Adoption Guide

- Document ID: `adoption`
- Version: `0.1.0`
- Maturity: `design-only`
- Last updated: 2026-07-17

## 1. Purpose

This is the smallest entry point for an Agent that wants to adopt one or more agent-wiki protocols.

Do not load every document by default. Start from [`protocols.yaml`](../protocols.yaml), choose the mechanism that matches the current problem, implement its minimum binding, and read deeper only when the task requires it.

This guide routes protocol reading. It does not grant permission to create files, run services, spend resources, or modify a user's environment.

## 2. Five-step reading path

1. Read [`protocols.yaml`](../protocols.yaml) for protocol ids, versions, maturity, dependencies, artifacts, and usecase evidence.
2. Select one protocol from the problem table below.
3. Read that protocol's metadata, Purpose, Non-goals, core artifact/schema, minimum binding, implementation levels, validation checklist, and Final rule.
4. Read one matching use case and calibrate claims from its `Evidence` and `Validation scope` fields.
5. Read [Composable Agent Cognition Protocols](composable-agent-cognition.md) only when two or more protocols must exchange artifacts.

Before claiming conformance, read the selected protocol document completely. The short path is for selection and bootstrap, not for skipping invariants.

## 3. Select by problem, not novelty

| Current problem | Start with | Minimum level | First artifact/action |
| --- | --- | --- | --- |
| Useful context must survive sessions | [Memory](agent-first-memory.md) | `memory:L0` | Capture one concise, source-aware memory item in a small inbox/store. |
| A corpus needs weak lateral exploration | [Auto-Walk](agent-first-auto-walk.md) | `auto-walk:L0` | Run one manual walk and write hypotheses outside Memory. |
| The wrong information is active during a task | [Active Workspace](agent-first-active-workspace.md) | `active-workspace:L0` | Maintain one bounded in-context goal/evidence/assumption/action snapshot. |
| An Agent needs a short self-guidance cue | [Inner Speech](agent-first-inner-speech.md) | `inner-speech:L0` | Apply one explicit cue with a trigger and expiry condition. |
| A decision needs inspectable competing views | [Council](agent-first-council.md) | `council:L0` | Create a GoalContract, candidates, ConflictMap, and DecisionRecord. |
| One human wants one interface over many executors | [Steward](agent-first-steward.md) | `steward:S1` | Issue one bounded WorkOrder and integrate one ResultEnvelope. |
| Several chosen protocols must cooperate | [Composition guide](composable-agent-cognition.md) | `composition:C1` | Put a shared envelope around the first cross-protocol artifact. |

If the problem is already solved by a simpler checklist, direct tool call, or one Agent response, do not add a protocol.

## 4. Minimal bindings

### 4.1 Memory

Minimum:

1. Choose a durable inbox or item store.
2. Capture only reusable information.
3. Record stable `id`, `kind`, `Source`, and date; add `subject` for `state`.
4. When confidence is recorded, use `epistemic-status-v1` and its closed values.
5. Retrieve skeptically; do not treat stored text as truth.

A single `memory.md` is valid at `memory:L0`. Do not create archive, topics, scheduling, or Autodream until the simpler binding has value.

### 4.2 Auto-Walk

Minimum:

1. Name a bounded corpus.
2. Select one seed and retrieve distant neighbors.
3. Generate several candidate associations and run a critic gate.
4. Store surviving hypotheses in a separate pool with `supporting_refs` and `ordinal-confidence-v1`.
5. Do not write Memory during the walk.

Memory is optional. Any structured corpus with stable references is valid.

### 4.3 Active Workspace

Minimum:

```yaml
goal:
  statement: <current outcome>
  source_refs: []
  success_criteria: []
constraints: []
evidence: []
assumptions: []
conflicts: []
actions: []
```

Keep this in current context if persistence is unnecessary. Separate evidence from assumptions and close/expire it when the task ends.

### 4.4 Inner Speech

Minimum:

```yaml
trigger: <why a cue is needed>
mode: <orientation | goal-maintenance | uncertainty-check | inside-outsider | other documented mode>
cue: <one bounded self-guidance instruction>
recommended_action: <next action>
expires_after: <observation or phase>
```

Silence is valid. Do not emit a cue merely because the protocol exists.

### 4.5 Council

Minimum:

1. Freeze one GoalContract.
2. Produce genuinely separate candidate views; one Agent MAY execute separated phases.
3. Name material conflicts rather than flattening them into consensus.
4. Return one DecisionRecord or an explicit unresolved state.
5. Preserve evidence, dissent, and reversal signals.

Do not add ranking, Elo, multiple providers, or repeated rounds at `council:L0`.

### 4.6 Steward

Minimum:

1. Preserve the Principal's original intent and authority boundary.
2. Decide whether delegation adds value.
3. If it does, create one bounded WorkOrder and AuthorityGrant.
4. Receive a ResultEnvelope with provenance and uncertainty.
5. Verify and return one coherent result to the Principal.

`steward:S0` is a direct `1:1` relationship. `steward:S1` is the minimum level that actually exercises the `1:1:N` topology.

## 5. Record the local binding

A binding SHOULD record what it implemented:

```yaml
binding_id: <local stable id>
protocol: <protocol id>
protocol_version: <version from protocols.yaml>
level: <qualified level such as memory:L0>
storage_or_runtime: <in-context | files | database | service | other>
artifact_locations: []
deviations: []
validation:
  checklist_completed: []
  evidence: <design-example | source-inspected | run-reported | reproduced | field-tested>
  conformance: <proposed | mapped | partially-verified | verified>
  gaps: []
last_reviewed: <date>
```

Use qualified level ids. `memory:L4` and `council:L4` are unrelated capabilities.

## 6. Version and maturity discipline

- `Version` identifies the protocol document and artifact contract, not the Agent model or usecase version.
- Versions below `1.0.0` may change incompatibly. A binding should pin the version it implemented.
- Protocol levels are cumulative conformance ladders. A binding may report an independently tested higher-level capability, but it cannot claim that level while a lower required level remains unsatisfied.
- `design-only` means the protocol is reasoned but lacks a documented binding.
- `practiced` means some levels are informed by a concrete binding or run; read `Evidence scope` before inferring how much.
- `field-tested` does not make a claim true forever. Runtime state and environment-specific conclusions still require current verification.
- A usecase evidence label describes the page's observation boundary; it does not automatically upgrade the protocol's maturity.

## 7. Add composition only when needed

Protocols remain standalone. Compose them through explicit artifacts:

```text
Memory item
  → gated activation into Active Workspace
  → optional Inner Speech cue or Council decision
  → action and observable outcome
  → optional metamemory feedback
```

For every cross-protocol artifact:

1. preserve producer and source references;
2. preserve original status and confidence scheme;
3. name the receiving protocol and admission rule;
4. prevent the receiver from silently mutating the producer;
5. define expiry or durable routing.

Do not install Steward merely to coordinate protocols inside one simple Agent run. Do not install Composition as if it were a runtime.

## 8. Upgrade rule

Move to the next protocol level only when:

- the current level has an observed limitation;
- the next level directly addresses it;
- new state, automation, authority, and failure modes are understood;
- the current level's validation checklist passes;
- rollback or degraded operation remains possible.

Higher levels are not maturity scores and are not inherently better.

## 9. Bootstrap completion checklist

1. The selected problem names one protocol.
2. The binding pins a protocol version and qualified level.
3. Required artifacts exist in the smallest useful form.
4. Confidence and status use declared closed vocabularies.
5. Sources and provenance are inspectable.
6. No optional protocol was made mandatory.
7. The implementation stays within user-granted authority.
8. The protocol-specific checklist passes for the claimed level.
9. Evidence claims match the recorded validation.
10. Another Agent can discover and resume the binding without reading an entire chat history.
