# Agent-first Council Architecture

- Protocol ID: `council`
- Version: `0.1.0`
- Maturity: `practiced`
- Evidence scope: one run-reported binding demonstrates `council:L1`-style blind review and selected `council:L2` revision pressure without full lineage/checkpoint validation; one implementation is source-inspected; one field-tested same-runtime role-diverse binding demonstrates selected `council:L0` mechanisms without independent CandidateArtifacts or anonymized peer review
- Level namespace: `council:L0`–`council:L5`
- Last updated: 2026-08-25

## 1. Purpose

Parallel agents can produce more text without producing better judgment. A Council is useful only when it creates independent candidate views, makes disagreement inspectable, targets revisions at consequential weaknesses, and ends with an actionable decision or an explicit unresolved state.

This protocol defines a portable deliberation mechanism that can be executed by:

- one agent in separated phases;
- several isolated sub-agents using one model family;
- heterogeneous models and providers;
- human and agent participants together;
- a standalone runtime, CLI, skill, API, or manual workflow.

Its product is **structured plural deliberation**, not consensus for its own sake.

## 2. Design goals

1. Create useful cognitive diversity rather than cosmetic persona variation.
2. Separate proposal, critique, revision, synthesis, and run control.
3. Preserve provenance while allowing blind review.
4. Keep disagreements, reversal signals, and rejected alternatives visible.
5. Terminate deterministically under time, cost, round, and quality constraints.
6. Use external outcomes when evaluating long-term participant capability.
7. Allow a minimal one-agent binding and richer multi-model bindings.
8. Keep ranking and reputation policies optional and replaceable.
9. Detect when all participants share the same wrong frame.
10. Produce artifacts another agent can read and act on without a Council service.

## 3. Non-goals

Council is not:

- Ordinary parallel task delegation.
- A group chat transcript.
- A vote where majority count creates truth.
- A requirement that every decision has one winner.
- A universal model leaderboard.
- A permanent governing agent.
- A substitute for runtime verification, tests, or human value choices.
- A guarantee of globally optimal decisions.
- A reason to use multiple models for low-risk, easily reversible work.

## 4. When to use Council

Council is appropriate when at least one is true:

- the decision is high-impact or difficult to reverse;
- evidence supports several plausible causal models;
- missing a stakeholder or second-order effect would be costly;
- a single agent has low confidence despite adequate evidence;
- adversarial review can expose material failure modes;
- the user wants explicit alternatives and trade-offs;
- prior attempts show repeated framing or reasoning failures;
- an outcome needs a documented dissent and reversal plan.

Skip or stop Council when:

- the answer is a directly verifiable fact;
- the task is execution rather than judgment;
- the decision is low-risk and cheap to reverse;
- external rules already determine the action;
- participants have no meaningful diversity;
- the real issue is an unprovided human value preference;
- time or budget cannot support the minimum valid profile.

## 5. Diversity model

Council diversity has at least four sources:

```text
role diversity       different responsibilities or evaluative lenses
model diversity      different model families/providers/versions
information diversity different evidence or memory scopes
method diversity     different tools, tests, causal methods, or search strategies
```

The first two form a useful minimum matrix:

| | Same model family | Different model families |
| --- | --- | --- |
| Same role | Repeated sampling / consistency check | Model ensemble / cross-check |
| Different roles | Role-diverse sub-agent Council | Heterogeneous full Council |

None is universally best.

- Same-model roles are cheap and portable but share correlated priors.
- Heterogeneous models may expose different blind spots but add latency, cost, provider failure, and routing complexity.
- Different provider labels do not prove independence; models may share training sources, benchmarks, and dominant narratives.
- Different roles do not create diversity if every role receives the same objective and is rewarded for agreement.

A binding SHOULD record actual rationale overlap, unique evidence contribution, and disagreement rather than treating member count as diversity.

## 6. Council member descriptor

A Council member is an execution identity, not merely a model id:

```yaml
member_id: member-skeptic-01
model_family: <model or unknown>
provider_runtime: <provider/runtime>
model_version: <version when known>
role: skeptic
role_contract: "Expose failure modes and reversal evidence"
context_scope: <full | bounded | named evidence set>
memory_scope: <none | task | project | named items>
tools: [web, shell]
generation_policy: <temperature/effort/profile when relevant>
independence_group: <shared-model-a>
```

`independence_group` discloses correlated execution, such as three roles using the same base model.

Anonymous review hides identity from reviewers but does not erase this provenance from the RunRecord.

## 7. Roles

Roles are capabilities. One participant may hold several in a small binding; larger bindings SHOULD separate conflicting authorities.

| Role | Responsibility |
| --- | --- |
| Controller | Owns GoalContract, rounds, budgets, checkpoints, termination, and RunRecord |
| Proposer | Creates an independent candidate artifact |
| Reviewer | Evaluates candidates against rubric and evidence |
| Reviser | Produces a new candidate version addressing selected reviews |
| Moderator | Identifies the highest-impact conflict and asks bounded follow-ups |
| Frame observer | Runs Inside-Outsider check; can challenge the GoalContract/frame |
| Synthesizer/Chair | Selects, combines, or reframes grounded material into a DecisionRecord |
| Evaluator | Applies tests, outcome metrics, or delayed feedback |
| Human owner | Supplies value judgments, permissions, and decisions that agents cannot infer |

### 7.1 Controller is not Chair

The Controller enforces deterministic process rules. The Chair makes semantic judgments.

```text
Controller:
  "Budget exhausted; use best checkpoint and record unresolved dissent."

Chair:
  "Candidate B best satisfies the goal; incorporate A's rollback plan and retain C's risk warning."
```

A model cannot extend its own run merely by claiming that one more round will produce insight.

## 8. Core artifacts

### 8.1 GoalContract

```yaml
goal_contract_id: gc-001
question: <decision to make>
goal: <desired outcome>
success_criteria: []
constraints: []
non_goals: []
decision_owner: <human or authorized agent>
risk_level: <low | medium | high>
time_horizon: <when outcomes matter>
evidence_set: []
unknowns: []
budget:
  max_rounds: 4
  max_time: 15m
  max_cost: <binding-defined>
  max_tokens: <binding-defined>
```

Council MUST align the issue before comparing answers. If participants are answering different questions, the run returns to the GoalContract rather than interpreting drift as productive disagreement.

### 8.2 CandidateArtifact

```yaml
candidate_id: cand-A-v1
author_member_id: member-builder-01
version: 1
position: <core recommendation>
claims: []
evidence_refs: []
assumptions: []
expected_outcomes: []
risks: []
reversal_signals: []
actions: []
confidence_scheme: ordinal-confidence-v1
confidence: <low | medium | high>
parent_candidate_id: null
```

### 8.3 ReviewArtifact

```yaml
review_id: rev-X-on-A-v1
reviewer_member_id: member-skeptic-01
target_candidate_id: cand-A-v1
rubric_scores:
  evidence: 3
  correctness: 4
  executability: 2
  risk_coverage: 3
strengths: []
material_issues:
  - claim: <specific weakness>
    evidence_refs: []
    severity: high
    revision_request: <testable change>
blind_spot_candidate: <optional>
ranking: <optional>
```

Reviews must target artifacts, not model identities.

### 8.4 RevisionArtifact

A revision is a new CandidateArtifact plus a response map:

```yaml
candidate_id: cand-A-v2
parent_candidate_id: cand-A-v1
responses:
  - review_issue: rev-X-on-A-v1#issue-1
    disposition: accepted
    change: <what changed>
  - review_issue: rev-Y-on-A-v1#issue-2
    disposition: rejected
    reason: <evidence-backed reason>
```

The best checkpoint may be an earlier version. The final artifact is not automatically the last artifact.

### 8.5 ConflictMap

Disagreement SHOULD be classified rather than flattened into prose:

```yaml
conflicts:
  - conflict_id: conflict-01
    type: causal-model
    positions: [cand-A-v2, cand-B-v1]
    description: <precise disagreement>
    discriminating_evidence: <what would resolve it>
    decision_impact: high
    status: unresolved
```

Recommended conflict types:

- `fact`
- `causal-model`
- `information-set`
- `value`
- `risk-preference`
- `time-horizon`
- `resource-constraint`
- `goal/frame`

Value conflicts are not resolved by more model votes. They return to the human owner or authorized decision policy.

### 8.6 DecisionRecord

```yaml
decision_id: decision-001
goal_contract_id: gc-001
selected_path: <candidate, synthesis, or no-decision>
decision: <actionable result>
grounded_in: []
incorporated: []
rejected:
  - artifact: <id>
    reason: <why>
unresolved_dissent: []
actions: []
stop_loss_conditions: []
reversal_signals: []
confidence_scheme: ordinal-confidence-v1
confidence: <low | medium | high>
decision_owner: <id>
```

### 8.7 RunRecord

The RunRecord preserves:

- participants and independence groups;
- GoalContract revisions;
- artifact lineage;
- anonymization mapping (restricted if needed);
- budgets and timing;
- controller decisions;
- failures and degraded modes;
- best checkpoint selection;
- final DecisionRecord;
- later outcome feedback.

## 9. Protocol lifecycle

The complete protocol is a state machine, not a mandatory fixed number of stages.

```text
0. Align GoalContract
1. Assemble panel and diversity profile
2. Produce independent candidates
3. Review artifacts, optionally blind
4. Extract conflicts and frame challenge
5. Select targeted revisions
6. Revise in parallel
7. Evaluate marginal gain and checkpoints
8. Repeat 3–7 or terminate deterministically
9. Synthesize/select/abstain
10. Emit DecisionRecord and RunRecord
11. Observe outcomes later
```

A three-stage `independent answers → anonymous review → Chair synthesis` binding is valid. It is a bounded profile of this lifecycle, not the universal definition of Council.

## 10. Independent proposal

Before seeing peer candidates, each proposer receives the same GoalContract unless information diversity is intentional and disclosed.

Each candidate MUST state:

- its recommendation or position;
- supporting evidence;
- assumptions;
- risks;
- confidence;
- reversal conditions;
- action implications.

The Controller SHOULD prevent early cross-copying. Otherwise the first fluent answer becomes an anchor and later "diversity" is cosmetic.

## 11. Review and anonymity

Blind review can reduce identity and reputation bias, but it creates its own risks.

### 11.1 Blind surface

Reviewers see:

- stable anonymous labels;
- candidate content and sources;
- the common rubric;
- the GoalContract.

They do not see model/provider identity unless it is materially relevant to interpreting evidence or tool capability.

### 11.2 Audit surface

The Controller retains the mapping for:

- conflict-of-interest checks;
- self-review exclusion;
- provider/model analysis;
- capability feedback;
- replay and audit.

### 11.3 Self-review

A proposer SHOULD NOT score its own candidate in comparative aggregation. It MAY respond to reviews during revision.

## 12. Targeted revision

Council should not repeat complete answers merely because another round exists.

The Moderator selects only issues that can materially change:

- the recommendation;
- confidence;
- risk controls;
- action sequence;
- reversal conditions;
- the GoalContract itself.

Each round SHOULD ask a bounded high-impact question and name which conclusion it could change.

Low-impact style disagreements do not justify another round.

## 13. Frame challenge: Inside-Outsider

A Council may disagree richly inside a shared wrong frame. Before final synthesis, a Frame observer MAY run the [Inside-Outsider stance](agent-first-inner-speech.md#11-inside-outsider-stance).

It emits one of:

```text
frame-holds
frame-challenge
```

A `frame-challenge` must include:

- the assumed frame;
- the excluded stakeholder/boundary/timescale/goal;
- evidence or explicit inference;
- a reversal signal;
- a re-entry action.

It is not ranked with candidates.

If accepted, the Controller revises the GoalContract and decides whether existing artifacts remain comparable. If not, the Council restarts proposal from the revised contract.

## 14. Chair and synthesis

The Chair has three legitimate modes:

1. **Select** — one candidate already dominates under the GoalContract.
2. **Bounded synthesis** — combine compatible strengths and preserve conflicts.
3. **Grounded reframing** — derive a new second-order framing from existing evidence and artifacts.

The Chair MAY produce a novel synthesis. It MUST NOT introduce an unreferenced new fact and present it as Council knowledge.

Any new speculation is labeled, sourced if possible, and subject to the same verification rules as a candidate claim.

Chair selection is a binding policy. The top-ranked proposer is not automatically the best synthesizer. Valid choices include:

- a dedicated synthesis role;
- a capability estimate scoped to synthesis;
- rotation;
- human selection;
- current-run evidence plus a tie-break policy;
- an independent model not involved in proposing.

## 15. Evaluation architecture

Council evaluation has four separate layers. A binding MUST NOT collapse them into one score without explanation.

### 15.1 Artifact evaluation

How good is this candidate or review in this run?

Possible signals:

- executable tests;
- factual verification;
- rubric vectors;
- pairwise preference;
- evidence coverage;
- calibration;
- unique useful contribution;
- detected and confirmed failure modes.

### 15.2 Run aggregation

How are current artifacts compared or combined?

Possible policies:

- no ranking; preserve a Pareto frontier;
- Borda count;
- Condorcet/Ranked Pairs/Schulze-style pairwise aggregation;
- Bradley–Terry or Plackett–Luce probability models;
- weighted rubric vectors;
- test-first elimination;
- human decision after conflict mapping.

No method is the protocol default for every task.

### 15.3 Capability estimation

What has history shown about a `model × role × domain × tool profile`?

Longitudinal estimates SHOULD:

- remain contextual rather than one universal number;
- carry uncertainty and observation count;
- distinguish proposer, reviewer, and synthesizer performance;
- handle model-version changes explicitly;
- decay or reset when the underlying model changes materially;
- avoid granting authority merely because peers previously preferred its style.

Elo is a valid optional adapter for stable, outcome-like comparisons. It is not the definition of reputation and should not be treated as truth.

### 15.4 Outcome evaluation

What happened after the decision?

Prefer:

- test results for verifiable tasks;
- observed operational outcomes;
- prediction scoring such as Brier/log loss when applicable;
- user adoption plus explicit satisfaction criteria;
- incident, rollback, or stop-loss signals;
- delayed human review.

Outcome evidence should dominate peer preference when the two conflict.

## 16. Avoiding circular reputation

This loop is unsafe:

```text
Council members prefer fluent model A
  → A gains reputation
  → A receives more weight and becomes Chair
  → A's framing dominates future preferences
  → reputation appears self-confirming
```

Mitigations:

1. Keep current-run artifact score separate from historical capability.
2. Record who reviewed whom.
3. Weight external verification and delayed outcomes more than peer style preference.
4. Carry uncertainty; do not over-update from small samples.
5. Keep role/domain ratings separate.
6. Reserve exploration slots for new or low-observation participants.
7. Audit concentration: who proposes, who is selected, who chairs, and whose dissent survives.

## 17. Convergence and termination

Council cannot guarantee convergence to global truth. It can guarantee bounded termination and a transparent terminal state.

### 17.1 Hard limits

The Controller MUST enforce configured limits:

- maximum rounds;
- maximum elapsed time;
- maximum token/model cost;
- minimum valid quorum;
- per-stage timeout;
- human-interrupt boundary.

### 17.2 Quality signals

A binding MAY stop early when:

- all material review issues are resolved or explicitly retained as dissent;
- marginal gain falls below a threshold for consecutive rounds;
- candidate versions stop changing decision-relevant fields;
- a verifiable test identifies a dominant candidate;
- further progress requires unavailable evidence or a human value choice.

### 17.3 Regression and oscillation

The Controller SHOULD retain best checkpoints and detect:

- quality regression under the agreed rubric;
- A→B→A oscillation;
- repeated objections with no new evidence;
- expanding prose with no artifact change;
- consensus produced by participant failure rather than agreement.

On regression, select the best earlier checkpoint. On oscillation, preserve both positions and expose the discriminating evidence or value choice.

### 17.4 Terminal states

- `decided`
- `decided-with-dissent`
- `abstained-insufficient-evidence`
- `needs-human-value-choice`
- `budget-exhausted-best-checkpoint`
- `failed-below-quorum`

The system always returns a structured state, not an endless request for another round.

## 18. Failure and degraded operation

Participant failure must be visible.

Example policy for a three-perspective run:

- one role fails: continue if quorum holds; label the missing perspective;
- two roles fail: degrade to single-agent pro/con or stop, according to risk;
- all fail: stop and report failure;
- Chair fails: use an authorized fallback or return artifacts without false synthesis;
- external evaluator unavailable: mark outcome as unknown; do not substitute peer confidence.

High-risk bindings SHOULD stop rather than synthesize from a materially incomplete panel.

## 19. Single-agent and multi-agent profiles

### 19.1 Single-agent manual Council

```text
GoalContract
  → independent candidate A
  → reset stance/context summary
  → independent candidate B or critique
  → conflict map
  → bounded revision
  → decision record
```

The agent must preserve phase separation in artifacts. Merely asking itself to "consider multiple perspectives" in one paragraph is not a Council.

### 19.2 Same-model sub-agent Council

Use isolated contexts and explicit role contracts. Record the shared `independence_group`. This is a valid role-diverse Council with correlated model risk.

### 19.3 Heterogeneous Council

Use provider/model adapters, normalize artifact schemas, disclose tool/context differences, and plan for partial provider failure.

### 19.4 Hybrid escalation

Start with same-model roles. Add an external Challenger or verifier only when:

- risk is high;
- confidence remains low;
- rationales are redundant;
- frame challenge is unresolved;
- external verification is provider-specific.

## 20. Connections to other protocols

### Active Workspace

Workspace supplies a frozen GoalContract/evidence snapshot and receives the DecisionRecord. The workspace owner, not Council, commits the next action.

### Inner Speech

Individual roles may use private bounded cues. Inside-Outsider provides the frame-check artifact. Inner Speech does not become an extra voter.

### Memory

Council may cite Memory items with their trust metadata. It cannot update Memory directly. A verified decision or later outcome enters through Memory capture; misleading activations may emit metamemory feedback.

### Auto-Walk

Walk hypotheses may inspire candidates but remain labeled weak evidence. Council agreement cannot discharge a hypothesis without the ordinary external confirmation path.

## 21. Implementation levels

| Level | Name | Capability |
| --- | --- | --- |
| `council:L0` | Structured perspectives | GoalContract, independent candidates, conflict map, decision. |
| `council:L1` | Blind review | Anonymous artifact review and provenance mapping. |
| `council:L2` | Revision loop | Targeted review responses, version lineage, best checkpoints. |
| `council:L3` | Deterministic controller | Budgets, plateau/regression/oscillation handling, terminal states. |
| `council:L4` | Contextual evaluation | Pluggable aggregation and role/domain capability estimates. |
| `council:L5` | Outcome feedback | Delayed external results calibrate artifacts and participant profiles. |

## 22. Validation checklist

Verify the items applicable at the claimed level and under the conditions the binding has enabled; untagged items apply from `council:L0`.

1. The GoalContract names success criteria, constraints, owner, and budget.
2. Initial candidates are produced independently.
3. Member descriptors disclose model, role, context, and independence group when known.
4. (`council:L1+`) Blind review preserves an auditable identity mapping.
5. Reviews identify material issues, not only rankings.
6. (`council:L2+`) Revisions point to parent artifacts and review dispositions.
7. Conflicts are classified and carry discriminating evidence or value ownership.
8. The Frame observer can return `frame-holds` or a sourced challenge.
9. Controller and Chair authorities and their records are separate from `council:L0`; distinct actors hold them from `council:L3`.
10. (`council:L3+`) Hard termination does not depend on model consent.
11. (`council:L2+`) The best checkpoint can precede the last round.
12. Consensus is not treated as external evidence.
13. (`council:L4+`) Historical capability is scoped by role/domain and carries uncertainty.
14. A failed participant or missing perspective is visible.
15. The final output contains decision, dissent, action, and reversal/stop-loss conditions.
16. A single agent can execute `council:L0` without a Council service.

## 23. Practical use cases

- [Multi-Agent Roundtable](../usecases/council/multi-agent-roundtable.md) — `Evidence: run-reported`; `Conformance: mapped`. A four-round, same-runtime sub-agent binding with role diversity, blind review, one high-impact follow-up, and an actionable decision package.
- [Local LLM Council](../usecases/council/llm-council-local.md) — `Evidence: source-inspected`; `Conformance: mapped`. An early heterogeneous-model service binding using independent answers, anonymous peer ranking, Chair synthesis, and optional Elo history.
- [Kiro Local Council](../usecases/council/kiro-local-council.md) — `Evidence: field-tested`; `Conformance: mapped`. A historical retired same-runtime role-diverse review binding covering isolated review, conflict extraction, and synthesis, without claiming complete `council:L0`.

## 24. Final rule

Council is not a machine for manufacturing agreement:

```text
Align the question.
Create independent candidates.
Review artifacts, not identities.
Preserve provenance behind anonymity.
Turn disagreement into a conflict map.
Revise only what can change the decision.
Let an Inside-Outsider challenge the shared frame.
Keep Controller separate from Chair.
Terminate by constitution, not by model appetite.
Prefer external outcomes over peer reputation.
Return a decision, dissent, or honest abstention.
```
