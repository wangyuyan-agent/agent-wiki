# Failed Exploration Withdrawal Use Case

- Use case ID: `memory.failed-exploration-withdrawal`
- Protocol: `memory@0.2.0`
- Evidence: `run-reported`
- Conformance: `mapped` — the reported event maps to withdrawal routing and non-admission; no `memory:L0+` level is claimed
- Validation scope: one maintainer-reported private Codex exploration was interrupted after its conclusions became confused and potentially unsafe to reuse; the originating session, file changes, temporary workspace, and Memory store were not independently inspected
- Reproducibility: `private-source` — the event boundary is documented without publishing the private conversation, project, paths, code, or runtime records
- Level namespace: `memory`
- Last reviewed: 2026-08-13

Source: private maintainer report dated 2026-08-13; not independently reproduced.

## 1. Reported event

A user asked an Agent to investigate a problem from a local project. During the run, the exploration became confused and wrong enough that continuing could interfere with the original project. The user stopped the run and asked the Agent to forget what it had just done and learned from that exploration.

The user later clarified that exploratory code may have been created in a temporary workspace or worktree. The report did not establish:

- whether the original project contained uncommitted changes;
- whether a temporary workspace was actually isolated;
- whether any commit or push occurred;
- whether any conclusion entered durable Memory, Conventions, Steering, or another persistent agent artifact;
- whether any workspace, code, memory item, archive segment, backup, or replica was deleted.

Those unknowns are preserved. This page does not reconstruct the private run or promote a reported concern into an observed mutation.

## 2. Boundary exposed by the event

The natural-language request "forget that exploration" was underspecified across three independently governed surfaces:

| Surface | Reported concern | Protocol routing |
| --- | --- | --- |
| Current context / task workspace | Confused exploration could continue to shape the answer | Stop the run, close or redirect Active Workspace, and do not treat prior exploration as an action premise. Do not claim selective model-context erasure unless the runtime exposes and the binding verifies it. |
| External and separately governed persistent effects | Exploratory code might affect an original project or a temporary workspace; a conclusion might also have been promoted into a standing rule | Inspect the original project, temporary location, and known promoted/derived artifacts separately. Rollback, destructive disposal, revision, and revocation are explicit, verified actions outside Memory. |
| Durable Memory | Conclusions might survive into later sessions | If no capture occurred, use non-admission. If a bounded scope was captured, append a `WithdrawalRecord`. Use authorized erasure only after an explicit, scoped request. |

The event therefore supports a routing lesson, not proof that a Memory erasure was needed. The likely safe path is:

```text
stop exploration
  → close or redirect the task workspace
  → inventory original-project and temporary-workspace effects
  → do not admit failed conclusions to Memory
  → append a content-minimal withdrawal control only when a residual influence path exists
  → escalate to destructive cleanup or erasure only with the required authority
```

## 3. Temporary exploration code

Exploratory code in an isolated temporary workspace is normally runtime/workspace state, not a Memory item and not automatically a durable run artifact. Its existence does not justify copying the code or its conclusions into Memory.

The label "temporary" is not proof of isolation. A review distinguishes at least:

- uncommitted files contained only in the temporary location;
- commits contained on a disposable temporary branch;
- commits made on an original-project branch;
- pushed or otherwise propagated effects.

A forget request removes future cognitive influence by default. It does not silently authorize destruction of unique uncommitted work. If unique bytes may exist, the Agent inventories them and obtains the confirmation required for disposal. If effects reached the original project or a remote, deleting the temporary directory is not rollback.

## 4. Content-minimal withdrawal

Safe forgetting may require retaining one small fact: a bounded run or source scope was withdrawn and must not regain current influence. This is a control event, not a summary of the failed exploration.

An appropriate record identifies only:

- the run, item, archive, or source scope;
- the attributable decision and time;
- a non-epistemic reason such as `failed-exploration`;
- the effect `exclude-from-influence`.

It does not repeat the incorrect conclusions or exploratory code. When nothing entered Memory and no residual influence path remains, even this record is optional; Memory stays clean through non-admission.

## 5. Required receipt

A future binding handling the same request should report five lines rather than saying only "forgotten":

```text
Context / Workspace: closed or redirected; no selective context erasure claimed without verified runtime support.
Original project: clean, or exact residual effects and their separately authorized disposition.
Temporary exploration workspace: absent, retained, safely disposable, disposed, or awaiting confirmation for unique work.
Promoted / derived artifacts: none found, exact governed artifacts and disposition, or unevaluated.
Memory: no capture, withdrawn scope, reinstated scope, or authorized erasure receipt.
```

The receipt prevents three silent failures: claiming to erase model context, implying that code was rolled back, and saying that Memory was deleted when it was only excluded from retrieval.

## 6. Contribution to `memory@0.2.0`

This reported event informed:

- the three-surface routing rule for natural-language forget requests;
- explicit separation of original-project and temporary-workspace effects within the execution surface;
- non-admission as the normal outcome for failed exploration that never entered Memory;
- content-minimal, reversible withdrawal controls for retained Memory;
- anti-resurrection requirements across retrieval, Autodream, review, Auto-Walk, migration, and replication;
- a separate, explicitly authorized erasure path.

It did **not** justify adding `withdrawn` to the Memory item `Status` enum. No durable item requiring that status was inspected. `memory@0.2.0` therefore represents withdrawal as a control record and leaves any future item-status materialization for evidence-backed revision.

## 7. What this evidence supports

- A private maintainer reported asking an Agent, in natural language, to stop the future influence of a failed exploration; successful influence removal was not independently verified.
- The phrase is ambiguous across current context, external code effects, and durable Memory.
- A possible temporary workspace makes boundary verification and a per-surface receipt materially useful.
- Non-admission and reversible withdrawal are distinct from project rollback and permanent erasure.

## 8. What it does not establish

- Any `memory:L0+` conformance or implementation of `memory@0.2.0`.
- That durable Memory capture occurred.
- That original-project or temporary-workspace changes existed.
- That rollback, disposal, withdrawal propagation, anti-resurrection, or erasure was executed successfully.
- That one reported incident validates every withdrawal reason, storage binding, backup topology, or replica path.
