# Multi-Agent Roundtable Use Case

- Use case ID: `council.multi-agent-roundtable`
- Protocol: `council@0.1.0`
- Evidence: `run-reported`
- Conformance: `mapped` — the public report maps to `council:L1` and parts of `council:L2`; this repository did not independently validate it
- Validation scope: public source report documents blind review and targeted follow-up; candidate lineage and best-checkpoint behavior required for complete `council:L2` are not demonstrated, and this repository did not independently reproduce the run
- Reproducibility: `public-source`
- Level namespace: `council`
- Last reviewed: 2026-07-17

## 1. Context

This use case records a role-diverse Council executed with OpenClaw sub-agents. It is based on the contributed field report [Multi-Agent Roundtable: from multiple viewpoints to an actionable decision](https://github.com/wangyuyan-agent/claw-info/blob/usecases/multi-agent-roundtable/usecases/multi-agent-roundtable.md).

The source report includes a real four-round run from 2026-03-13. The question was how a documentation project should allocate limited contribution capacity between release notes and use cases.

The binding demonstrates that a Council does not require heterogeneous model providers or a dedicated Council service. One runtime can create useful role separation through isolated sub-agent sessions and explicit artifact hand-offs.

It is a practical `council:L1` profile with selected `council:L2`-style revision pressure, not a verified implementation of complete `council:L2` or higher.

## 2. What this binding is for

The Roundtable is for judgment under competing considerations:

- several approaches are plausible;
- blind spots matter more than execution speed;
- an actionable decision and stop-loss plan are required;
- the problem benefits from controlled disagreement;
- a human value choice can be identified rather than guessed.

It is not used for direct factual lookup, routine execution, low-risk reversible decisions, or issues already fixed by external policy.

## 3. Execution topology

```text
Main session
  = Controller + Moderator

Isolated sub-agent A
  = Builder

Isolated sub-agent B
  = Skeptic

Isolated sub-agent C
  = Systems thinker

Final isolated sub-agent
  = Chair/Synthesizer
```

The source implementation used `sessions_spawn` with isolated sub-agent runs. All roles may share one underlying model family/runtime, so the binding provides role diversity but does not claim model-family independence.

In protocol terms:

```yaml
diversity_profile:
  role_diversity: high
  model_diversity: unknown-or-low
  context_isolation: per-sub-agent
  information_diversity: common initial brief
  method_diversity: role-contract based
```

## 4. Role contracts

| Role | Primary lens | Failure it is meant to expose |
| --- | --- | --- |
| Moderator | Goal alignment and highest-impact conflict | Discussion drift and too many follow-ups |
| Builder | Feasibility, path, speed | Analysis with no executable route |
| Skeptic | Risk, counterexample, boundary | Fluent but fragile recommendations |
| Systems | Long-term and second-order effects | Local optimization |
| Chair | Grounded selection/synthesis | A pile of answers with no decision |

The source report recommends starting with three roles for ordinary decisions and adding Systems and a separate Chair for high-impact or difficult-to-reverse issues.

## 5. Four-round lifecycle

### Round 0: brief alignment

The main session creates a shared brief:

```yaml
topic: <what is being decided>
goal: <desired outcome>
constraints: []
success_criteria: []
time_window: <decision horizon>
```

This is the binding's GoalContract. If the issue is not aligned, the Roundtable does not begin.

### Round 1: independent proposals

Builder, Skeptic, and Systems answer independently without seeing one another's responses.

Each response includes:

- position;
- arguments;
- assumptions;
- proposed action;
- material risks.

### Round 2: anonymous peer review

The main session replaces identities with stable labels and redistributes the candidates. Each reviewer:

- evaluates correctness and executability;
- ranks or compares candidates;
- identifies at least one blind spot;
- extracts consensus and disagreement.

The audit record retains the real mapping even though reviewers operate on anonymous labels.

### Round 3: one high-impact follow-up

The Moderator identifies the one unresolved question most likely to change the conclusion. It states what conclusion the question could reverse and asks each role to respond.

This is targeted revision pressure, not an invitation to rewrite every answer.

### Round 4: Chair decision package

The Chair receives the prior artifacts and produces:

- consensus;
- unresolved disagreement with reversal signals;
- primary recommendation;
- fallback and switch conditions;
- rejected options and reasons;
- actions, owners, and acceptance criteria;
- risks and stop-loss conditions.

The Chair may create a new synthesis or reframe the problem using existing material. It may not introduce an unverified new fact as if the Council established it.

## 6. Observed run

The source report records:

| Phase | Longest reported duration |
| --- | --- |
| Independent proposals | 21 seconds |
| Anonymous review | 34 seconds |
| High-impact follow-up | 27 seconds |
| Chair synthesis | 61 seconds |
| Whole run | approximately 7 minutes |

The most valuable result was not the numeric allocation recommendation. The Roundtable reframed the question from "which documentation type has more value?" to "does the project have the maintenance mechanisms required to prevent use-case decay?"

That is a grounded second-order synthesis: it emerged from the participants' arguments without inventing an external fact.

## 7. Output contract

```markdown
## Consensus
- ...

## Disagreement
- Position A vs B
  - cause:
  - reversal signal:

## Recommendation
- primary:
- fallback:
- switch condition:
- explicitly rejected:

## Actions
- owner:
  action:
  acceptance criteria:

## Risk and stop-loss
- risk:
  warning signal:
  triggered action:
```

The report treats a missing section as an incomplete decision package.

## 8. Failure and degradation rules

The observed binding defines explicit degradation:

- One of three perspectives fails: continue only if the remaining material is valid; label the missing view and lower confidence.
- Two perspectives fail: degrade to a single-agent pro/con analysis or stop according to risk.
- All fail: stop; do not manufacture a complete-looking synthesis.
- A sub-agent times out: apply the configured timeout and use the degraded profile.
- Responses become homogeneous: strengthen role contracts, add a Challenger, or stop using the Roundtable.

For high-risk decisions, the protocol's quorum and human-escalation rules should be stricter than this general-purpose binding.

## 9. What this use case proves

Observed or directly demonstrated by the source run:

1. Same-runtime sub-agents can execute distinct Council roles.
2. Phase separation creates artifacts more useful than a single "debate with yourself" prompt.
3. Anonymous review can be orchestrated without an external framework.
4. One targeted follow-up can change the decision frame.
5. A Chair can create a grounded second-order synthesis.
6. A decision package can preserve disagreement while remaining actionable.
7. Explicit degraded modes prevent partial failure from masquerading as consensus.

## 10. What it does not prove

- That role prompts eliminate the shared blind spots of one model family.
- That anonymous ranking identifies truth.
- That four rounds are optimal for every task.
- That the Chair is the best checkpoint in every run.
- That decisions improve without later outcome measurement.
- That a fixed Builder/Skeptic/Systems role set fits every domain.

## 11. Mapping to the general protocol

| Council protocol object | Roundtable binding |
| --- | --- |
| GoalContract | Round 0 brief |
| CandidateArtifact | Round 1 role response |
| ReviewArtifact | Round 2 anonymous review |
| ConflictMap | Moderator's consensus/disagreement extraction |
| Revision pressure | Round 3 high-impact follow-up |
| DecisionRecord | Round 4 decision package |
| Run Controller | Main session |
| Chair | Final synthesis sub-agent |
| Outcome evaluation | Not implemented in the recorded run |
| Longitudinal capability | Not implemented |

## 12. Reusable lessons

1. Start with the decision boundary, not the panel.
2. Use isolated initial proposals to reduce anchoring.
3. Give roles different obligations, not different adjectives.
4. Ask only follow-ups that can change the decision.
5. Require reversal signals for unresolved disagreement.
6. Require action and stop-loss fields in the final artifact.
7. Treat homogeneous agreement as a warning, not a success metric.
8. Keep the Controller's termination authority outside the Chair's semantic judgment.
9. Add heterogeneous models only when their expected diversity justifies the extra cost and failure surface.

## 13. Validation checklist for another binding

1. Initial role outputs are generated without peer anchoring.
2. Anonymous labels remain stable during review.
3. The real identity mapping remains auditable.
4. Reviewers identify concrete blind spots, not only preferences.
5. The Moderator selects one decision-changing question.
6. The Chair grounds every material claim in prior artifacts or labels it as unverified.
7. Final output contains disagreement and reversal signals.
8. Final output contains actions and stop-loss conditions.
9. Missing roles are disclosed.
10. The binding works with same-model sub-agents and does not claim false model diversity.
