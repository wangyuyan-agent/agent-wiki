# Kiro Local Active Workspace Use Case

- Use case ID: `active-workspace.kiro-local`
- Protocol: `active-workspace@0.2.0`
- Evidence: `field-tested`
- Conformance: `mapped` — observed durable task-state behavior maps to the protocol, but the current schema and validation checklist were not independently validated
- Validation scope: two ordinary multi-step tasks used durable revisioned records through `active` → `closing` → `closed`; an earlier bounded canary exercised cross-session lifecycle handling
- Reproducibility: `partial` — the lifecycle, behavior classes, defects, and evidence boundary are documented; private task records and session material are omitted
- Level namespace: `active-workspace`
- Deployment status: `retired` — the local Kiro binding was retired on 2026-08-25; this page preserves historical evidence only
- Last reviewed: 2026-08-25

## 1. Context

This use case records a local Active Workspace binding that stored bounded task state outside the agent's live conversation. The binding was used during ordinary work rather than only in a synthetic demonstration: two multi-step tasks kept durable records and reached a closed lifecycle state. An earlier canary separately exercised creation, revision, cross-session reload, closing, and closure.

The records are not published. This page keeps only the smallest behavior classes and defects needed to inform the protocol. It excludes raw YAML, task content, session identifiers, absolute paths, host details, and private evidence.

The binding was retired with its local Kiro runtime. Retirement changes deployment status, not the historical evidence label.

## 2. Observed lifecycle

Across the two ordinary-work records, the binding preserved:

- a source-aware goal and success criteria;
- task constraints and permissions;
- separate collections for evidence, assumptions, risks, and actions;
- a single owner and monotonically revised durable state;
- expiry metadata and explicit task status;
- a visible transition from active work through closing to closed;
- closure notes and references to verification or remaining gaps.

The earlier canary showed that a record could survive a session boundary and resume from its stored revision. That probe supplied bounded lifecycle evidence, while the later two records supplied ordinary-work evidence.

## 3. Mapping to the protocol

| Active Workspace concept | Observed local behavior | Mapping limit |
| --- | --- | --- |
| Anchors | Goal, success criteria, constraints, and authority boundaries were durable | Completeness and source coverage were not checked against every current requirement |
| Evidence vs model | Evidence and assumptions were stored separately | Some confidence and item-status values fell outside the current closed vocabularies |
| Tensions | Risks and unresolved conditions were visible | One record closed with a risk still open rather than explicitly carried forward or dispositioned |
| Actions | Planned and completed work was recorded | Criterion-by-criterion completion evidence was incomplete |
| Revision and ownership | One owner revised a durable record over time | Stale-patch rejection and multi-writer behavior were not tested |
| Lifecycle | Ordinary tasks moved through `active`, `closing`, and `closed` | Closure alone does not prove successful audited completion |
| Audited completion | One record included a separated verification result | Explicit profile enablement, complete scope references, and full finding coverage were not consistently present |

## 4. Negative evidence

The binding exposed defects that prevent a stronger conformance claim:

1. **Confidence vocabulary drift.** At least one factual item used `verified` as a confidence value. `epistemic-status-v1` permits `confirmed`, `observed-once`, `inferred`, or `unknown`; `verified` belongs to neither confidence scheme.
2. **Item-status vocabulary drift.** An assumption used `confirmed`, which is not one of the protocol's assumption statuses. A risk used `resolved`, which is not one of the protocol's risk statuses. Semantically plausible prose does not substitute for the declared closed tokens.
3. **Incomplete audited-completion enablement.** One record carried a separated verification result without a prior attributable decision that explicitly enabled the profile and named its complete scope.
4. **Incomplete high-risk closure evidence.** Another record closed without the canonical audited-completion metadata and without a clean, criterion-by-criterion finding for every in-scope requirement. One risk remained open at closure.
5. **Stale lifecycle state outside the two closed records.** A separate earlier tracker remained active beyond its expiry, showing that persistence alone does not enforce expiry or review.

These are field lessons, not reconstructed fixes. The historical records were not rewritten to appear conformant after the fact.

## 5. What this evidence supports

- A durable Active Workspace record can carry bounded task state through ordinary multi-step work and across session boundaries.
- Separating goal, constraints, evidence, assumptions, risks, and actions improves inspectability even before formal conformance exists.
- Explicit `closing` before `closed` creates a useful place to record outcomes and unresolved gaps.
- Closed vocabularies need validation at write time; otherwise semantically similar tokens drift quickly.
- A verification-shaped block is not enough to establish the optional audited-completion profile. Enablement, scope, fresh evidence, findings, completion status, and integrity status must form one attributable chain.
- These ordinary-work records are enough to move protocol maturity from `design-only` to `practiced` because a real binding both supported work and exposed reusable operational defects.

## 6. What it does not establish

- `active-workspace:L1` or any higher level. A structured durable record is insufficient when required vocabulary and checklist items are not validated.
- Complete conformance with `active-workspace@0.2.0`.
- Correct stale-patch rejection, multi-agent ownership, interrupt admission, Memory/Auto-Walk activation, or feedback-aware behavior.
- A successful end-to-end run of the optional audited-completion profile.
- Current runtime health or continued deployment; the local binding is retired.

## 7. Reusable lessons

1. Validate confidence and status tokens before committing a revision.
2. Treat expiry as an active review obligation, not passive metadata.
3. Keep `closed` separate from `completed`: a task may close with blocked, incomplete, or explicitly carried-forward outcomes.
4. Enable audited completion with an attributable, scope-complete decision before treating verification results as profile evidence.
5. Preserve negative lifecycle evidence. Retrofitting invalid historical records would erase the lesson that the protocol needs enforcement, not merely documentation.

## 8. Historical binding record

```yaml
binding_id: kiro-local-active-workspace-historical
protocol: active-workspace
protocol_version: 0.2.0
deployment_status: retired
level_claim: none
observed_scope:
  ordinary_work_records: 2
  bounded_lifecycle_canary: 1
mapped_components:
  - source-aware goal and constraints
  - separated evidence, assumptions, risks, and actions
  - durable revision and single ownership
  - active-to-closing-to-closed lifecycle
declared_gaps:
  - invalid confidence and item-status tokens
  - incomplete expiry enforcement
  - incomplete audited-completion enablement and findings
  - current validation checklist not executed
validation:
  evidence: field-tested
  conformance: mapped
  privacy: behavior classes only; private records omitted
last_reviewed: 2026-08-25
```
