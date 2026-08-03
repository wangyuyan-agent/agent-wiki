# Agent-first Inner Speech Architecture

- Protocol ID: `inner-speech`
- Version: `0.1.0`
- Maturity: `design-only`
- Evidence scope: No documented binding yet.
- Level namespace: `inner-speech:L0`–`inner-speech:L4`
- Last updated: 2026-08-03

## 1. Purpose

Agents often have enough information but still need an explicit cue to use it well. They lose the immediate goal, repeat a failed approach, over-trust a remembered conclusion, continue after marginal value has vanished, or recognize a conflict without turning it into the next action.

Inner Speech is a bounded runtime self-guidance protocol. It converts selected [Active Workspace](agent-first-active-workspace.md) state into concise control language for:

- orientation;
- goal maintenance;
- self-explanation;
- micro-planning;
- uncertainty and conflict checks;
- self-regulation;
- continuity across a bounded run;
- temporary self-distancing through the Inside-Outsider stance.

Its product is **explicit control**, not narration for its own sake.

> Workspace says what is active. Inner Speech says what the acting agent should notice or do next.

## 2. Human inspiration and engineering boundary

Human inner speech can be experienced as full internal sentences, dialogue, self-address, or highly condensed verbal thought. Developmental research often describes a movement from social speech to overt private speech and then to more internal and condensed self-guidance. Inner speech is also associated with maintaining task rules, sequencing, planning, and executive control.

Useful background:

- [Inner Speech: Development, Cognitive Functions, Phenomenology, and Neurobiology](https://pmc.ncbi.nlm.nih.gov/articles/PMC4538954/)
- [Inner Speech and Executive Function in Children](https://pmc.ncbi.nlm.nih.gov/articles/PMC11218747/)

The protocol borrows the control function, not the phenomenological claim. An LLM executing this protocol is not thereby proven to hear a voice, possess consciousness, or expose its internal latent computation.

Agent-first Inner Speech is operational:

```text
input:  bounded task state
output: concise control cue
effect: attention or action may change
```

## 3. Design goals

1. Turn active task state into the smallest useful self-guidance.
2. Make silence the default when no intervention is needed.
3. Support expanded guidance for difficult tasks and condensed cues for familiar ones.
4. Separate private-ephemeral control from durable rationale and public explanation.
5. Let one agent execute the protocol or delegate a stance to a sub-agent.
6. Prevent recursive self-commentary and performative reflection.
7. Require source references for factual or frame-changing cues.
8. Route durable learning through Memory rather than storing raw inner narration.

## 4. Non-goals

Inner Speech is not:

- A requirement to reveal chain-of-thought.
- A transcript of every internal token or considered alternative.
- A second final answer written to the agent itself.
- A permanent persona or supervisor.
- A substitute for tool evidence, Memory, or Council.
- A guarantee of correctness or objectivity.
- An excuse to delay obvious low-risk actions.
- A mechanism that directly edits long-term Memory, Steering, or user goals.

## 5. Core model

An Inner Speech event is a bounded intervention in an action loop:

```text
trigger
  → read a bounded Workspace snapshot
  → select one mode
  → emit one concise cue
  → acting agent accepts/rejects/defers or acts
  → observe outcome when available
  → expire; optionally emit feedback
```

It does not run continuously. Familiar action may proceed with no explicit cue.

## 6. Modes

### 6.1 Orientation

Restate the immediate objective and the boundary most likely to be forgotten.

```text
The task is diagnosis, not repair. Establish the runtime cause before proposing changes.
```

### 6.2 Goal maintenance

Detect drift from observable success criteria.

```text
The current work improves the report format but does not answer whether the service is healthy.
Return to the health evidence.
```

### 6.3 Self-explanation

Name a decision-relevant reason without dumping full reasoning.

```text
Prefer the live configuration because the repository file may not match the deployed revision.
```

### 6.4 Micro-planning

Choose the next one to three bounded actions.

```text
First read the active cron entry; then inspect its log target; only then interpret missing logs.
```

### 6.5 Uncertainty/conflict check

Surface a confidence-evidence mismatch or unresolved contradiction.

```text
The proxy explanation is still inferred. A direct request without the proxy would discriminate it.
```

### 6.6 Self-regulation

Apply a task boundary or safety invariant.

```text
Do not let the surfaced Walk hypothesis change the main recommendation without verification.
```

### 6.7 Continuity

Maintain a concise task thread across phases or context hand-offs.

```text
Evidence collection is complete; the unresolved issue is ownership of the shared state, not storage choice.
```

### 6.8 Inside-Outsider

Temporarily treat the acting agent, its current plan, and its framing assumptions as objects of observation while retaining the local context needed to re-enter the task.

This mode is defined fully in §11.

## 7. Expanded and condensed forms

Inner Speech SHOULD adapt its form to task need.

| Form | Use | Example |
| --- | --- | --- |
| Silent | No cue adds value | Routine deterministic step |
| Condensed | Familiar control signal | `verify source → then act` |
| Expanded | Novel, conflicting, or high-risk situation | Goal + conflict + next discriminating action |
| Dialogic | Two legitimate internal positions need articulation | `Actor says continue; observer says verify the premise first` |

Expanded does not mean unrestricted. The cue remains task-scoped and action-oriented.

A binding MAY begin with explicit expanded templates and become more condensed as reliable routines are established. This resembles developmental internalization without pretending that the agent is a child learning language.

## 8. Event schema

```yaml
cue_id: iv-2026-07-15-001
task_id: task-001
workspace_revision: 8
mode: uncertainty-check
trigger: "high-confidence action depends on one inferred assumption"
cue: "Verify database reachability from the application container before changing credentials."
source_refs:
  - assumption:a-001
  - evidence:e-004
confidence_scheme: ordinal-confidence-v1
confidence: medium
recommended_action: verify
urgency: high
status: proposed
created_at: 2026-07-15T10:20:00+08:00
expires_after: "next discriminating observation"
```

Required fields for a structured cue record (`inner-speech:L1+`; an `inner-speech:L0` manual cue may remain an unstructured checklist entry):

- `cue_id`
- `task_id`
- `mode`
- `trigger`
- `cue`
- `recommended_action`
- `status`
- an expiry condition

`source_refs` is required when the cue makes a factual, causal, or frame-changing claim. A pure reminder of an existing anchor may reference that anchor.

`confidence_scheme` and `confidence` are optional for pure reminders. They are required when a cue makes a predictive or frame-changing claim and use `ordinal-confidence-v1` (`low | medium | high`). Confidence measures the cue's claim, not its authority.

## 9. Cue status and authority

The acting agent or Workspace owner sets one closed status:

- `proposed`
- `accepted`
- `rejected`
- `deferred`
- `satisfied`
- `expired`

Inner Speech has advisory authority by default.

It MAY block action only when an external safety policy already grants that block. The cue itself cannot invent new permissions, redefine the user's goal, or promote itself into Steering.

## 10. Trigger policy

### 10.1 Useful triggers

Generate a cue when:

- the immediate goal or boundary is likely to be lost;
- evidence and confidence are mismatched;
- two active artifacts conflict;
- the same approach has failed repeatedly;
- an action is costly or difficult to reverse;
- the plan has grown without measurable progress;
- Memory strongly anchors the action but may be stale;
- Council members agree for materially identical reasons;
- a user explicitly asks for another perspective;
- the task changes phase and needs a continuity marker.

### 10.2 Silence conditions

Stay silent when:

- the next action is deterministic, low-risk, and reversible;
- the cue merely repeats visible instructions;
- no material change to attention or action would result;
- the same cue was recently rejected and no new evidence exists;
- the task is already waiting for an external event;
- generating a cue costs more than the likely mistake.

Silence is a successful protocol outcome.

### 10.3 Cooldown

A rejected or satisfied cue SHOULD not recur until:

- new evidence appears;
- a named review condition is met;
- the task changes phase;
- a material failure occurs.

## 11. Inside-Outsider stance

### 11.1 Definition

Inside-Outsider is embedded distance:

```text
Inside:
  retains the goal, evidence, history, constraints, responsibility, and practical costs.

Outsider:
  temporarily stops treating the current plan, narrative, confidence, and identity commitments as premises.
```

Its purpose is not to oppose the actor. Its purpose is to expose the frame that both support and opposition may be assuming.

Self-distancing research provides a useful human analogy: people may reason more wisely about another person's conflict than their own, and a distanced perspective can reduce that asymmetry. But distance is context-sensitive and does not guarantee impartial or moral conclusions.

References:

- [Exploring Solomon's Paradox](https://pubmed.ncbi.nlm.nih.gov/24916084/)
- [Decentering and Related Constructs](https://pmc.ncbi.nlm.nih.gov/articles/PMC5103165/)
- [Distanced self-talk increases rational self-interest](https://pmc.ncbi.nlm.nih.gov/articles/PMC8752811/)

Therefore Inside-Outsider is a counterweight, never a truth oracle.

### 11.2 The four-phase loop

```text
Immersion
  understand and participate in the task
    ↓
Distancing
  make the current frame and commitments observable
    ↓
Reframing
  inspect excluded boundaries, stakeholders, timescales, and counterfactuals
    ↓
Re-entry
  return one smallest useful action: continue, verify, redirect, pause, or escalate
```

Re-entry is mandatory. An observation without a re-entry action is commentary, not a control intervention.

### 11.3 Questions

The stance asks, in order:

1. **Name the frame.** What is the actor treating as given?
2. **De-identify.** If another competent agent were doing this, what would be immediately visible?
3. **Shift the boundary.** Which stakeholder, system, timescale, incentive, or alternative goal is outside the current view?
4. **Find reversal evidence.** What observation would change the frame or stop the plan?
5. **Re-enter.** What is the smallest justified change to current action?

### 11.4 Output

```yaml
mode: inside-outsider
current_frame: "The problem is assumed to be how to migrate the database."
blind_spot_candidate: "The service boundary itself may no longer be needed."
outside_observation: "All options preserve an architecture that the current product no longer requires."
source_refs:
  - goal:current
  - decision:architecture-2024
reversal_signal: "A current consumer still requires independent database ownership."
reentry_action: verify
confidence_scheme: ordinal-confidence-v1
confidence: medium
```

It may also emit:

```yaml
result: frame-holds
reason: "The boundary was explicitly revalidated by current evidence."
reentry_action: continue
```

The stance is not required to manufacture a challenge.

### 11.5 Permissions

Inside-Outsider SHOULD:

- read a bounded Workspace snapshot;
- remain read-only;
- submit one interrupt;
- cite evidence or explicitly label inference;
- accept silence or `frame-holds` as valid;
- expire after the re-entry decision.

It MUST NOT:

- directly rewrite the goal or plan;
- claim privileged access to true motives or latent thoughts;
- use distance to escape task responsibility;
- persist a psychological narrative about the user without evidence;
- recurse into an Inside-Outsider-of-Inside-Outsider loop.

### 11.6 Trigger conditions

Inside-Outsider is especially useful when:

- three or more attempts repeat the same causal frame;
- Council reaches fast consensus with low rationale diversity;
- implementation work keeps expanding while the goal stays unmet;
- sunk cost or identity commitment is visible;
- the task is high-impact or difficult to reverse;
- the user asks, "What am I missing?" or "Could the framing be wrong?"

It is normally unnecessary for routine execution.

## 12. Single-agent binding

One agent can execute Inner Speech without a sub-agent:

```text
1. Read only the active goal, constraints, current conflict, and next action.
2. Check whether a trigger exists.
3. Select at most one mode.
4. Produce one cue or stay silent.
5. Apply or record the cue.
6. Expire it after the named condition.
```

For Inside-Outsider, the same agent can use a third-person or observer prompt, but grammatical third person is optional. The functional requirement is disidentification from the current frame, not a particular pronoun.

## 13. Multi-agent binding

A sub-agent MAY execute a mode from a frozen Workspace snapshot. Isolation can reduce commitment to the actor's unfolding narration.

Possible topologies:

- same model, isolated observer context;
- different model as frame observer;
- Council moderator invoking Inside-Outsider before synthesis;
- specialist producing a safety or domain control cue.

The producer must receive:

- the exact GoalContract;
- relevant evidence and constraints;
- current assumptions and action;
- its authority and output schema.

It should not receive unrelated private history merely to feel more "inside."

## 14. Connections to other protocols

### Active Workspace

Workspace is the default input and the place where material cues are accepted, rejected, or deferred.

### Memory

Inner Speech may request a Memory verification or flag a possibly misleading activation. It does not modify Memory. After an outcome, a separate metamemory feedback event may record whether a cited memory helped or misled.

### Council

Council roles may use ordinary cues privately. A shared Inside-Outsider frame challenge is a separate artifact and does not participate in candidate ranking.

### Auto-Walk

Inner Speech may remind the actor that a surfaced hypothesis is weak. It cannot convert speculation into evidence.

## 15. Persistence policy

Most cues expire and are never stored durably.

Persist only when at least one is true:

- the cue materially changed a decision;
- it prevented or exposed a failure;
- its outcome will be evaluated later;
- it expresses a reusable lesson independently supported by evidence;
- an audit requires the accepted/rejected intervention.

Even then, persist the decision-relevant artifact, not an unrestricted internal monologue.

```text
Bad durable record:
  every self-directed sentence generated during the task

Good durable record:
  "Inside-Outsider challenge accepted: verified service ownership before migration; evidence showed migration was unnecessary."
```

Reusable lessons enter Memory through its capture protocol.

## 16. Outcome feedback

When a cue influenced action, a binding MAY emit:

```yaml
cue_id: iv-2026-07-15-001
task_id: task-001
action_taken: verify
outcome: "Assumption was disproven"
verdict_scheme: intervention-outcome-v1
verdict: helpful
evidence_refs: ["runtime:query-004"]
observed_at: <timestamp>
```

Allowed verdicts:

- `helpful`
- `misleading`
- `neutral`
- `unknown`

One outcome must not automatically rewrite the trigger policy. Repeated evidence may produce a policy-change proposal for human or governed review.

A policy-change proposal is the protocol's `policy_proposal` artifact, mirroring the governed-proposal pattern of [Memory §23.5](agent-first-memory.md#235-policy-proposal):

```yaml
proposal_id: ispolicy-2026-07-15-001
target: trigger-policy:repeated-failure-threshold
supporting_cue_feedback:
  - iv-2026-07-15-001
expected_benefit: "Earlier frame checks after repeated failures"
risk: "More interruptions during recoverable work"
status: pending-review
```

A `policy_proposal` MUST NOT auto-apply. It waits for human or governed review; an accepted change is applied by the reviewer's decision, not by the proposing path.

## 17. Failure modes

| Failure mode | Symptom | Prevention |
| --- | --- | --- |
| Constant narration | Agent comments on every action | Trigger gate and silence default |
| Recursive reflection | Meta-analysis never returns to work | One mode, one cue, mandatory re-entry |
| Performative dissent | Inside-Outsider always challenges | Allow `frame-holds`; require material delta |
| Hallucinated objectivity | Observer stance is treated as truth | Evidence, confidence, advisory authority |
| Goal hijack | Cue silently redefines user intent | Goal remains a Workspace anchor |
| Memory mythmaking | Transient narration becomes identity | Expire cues; capture only evidenced lessons |
| Thought leakage | Private control text appears as public reasoning | Separate visibility layers and public rationale |
| Observer lacks context | Advice ignores real constraints | Bounded but sufficient Workspace snapshot |
| Observer overfits context | It reproduces the actor's frame verbatim | Isolation, de-identification questions, optional heterogeneous model |
| Responsibility escape | Distance becomes an excuse not to act | Mandatory re-entry action and owner decision |

## 18. Implementation levels

| Level | Name | Capability |
| --- | --- | --- |
| `inner-speech:L0` | Manual cue | Agent uses an explicit orientation or verification checklist on demand. |
| `inner-speech:L1` | Mode-gated | Trigger, mode, cue schema, status, and expiry are structured. |
| `inner-speech:L2` | Workspace-connected | Cues read bounded Workspace state and produce interrupts. |
| `inner-speech:L3` | Isolated stance | Sub-agent or fresh context can execute selected modes. |
| `inner-speech:L4` | Feedback-aware | Material cues receive delayed outcome verdicts and policy proposals. |

## 19. Validation checklist

Verify the items applicable at the claimed level and under the conditions the binding has enabled; untagged items apply from `inner-speech:L0`.

1. A trivial task can complete with no Inner Speech cue.
2. A cue names a trigger and recommended action.
3. Factual or frame-changing cues carry source references.
4. The acting agent can reject or defer a cue.
5. A cue expires after its named condition.
6. The protocol does not require chain-of-thought persistence.
7. (when the Inside-Outsider mode is implemented) Inside-Outsider can return `frame-holds`.
8. (when the Inside-Outsider mode is implemented) Every Inside-Outsider challenge includes a re-entry action.
9. A cue cannot directly edit Memory, Steering, or the user goal.
10. A single agent can execute the protocol without a service.
11. (`inner-speech:L3+`) A sub-agent binding discloses its model, role, context scope, and authority.
12. (when cues are persisted) Only decision-relevant outcomes become durable artifacts.

## 20. Final rule

Inner Speech should be less like a commentator and more like a well-timed self-cue:

```text
Speak only when attention or action may materially improve.
Use the smallest form that works.
Name evidence, uncertainty, and boundaries.
Let the actor decide.
Expire the cue.

When distance is needed:
  immerse,
  step outside the frame,
  reframe,
  and re-enter with one useful action.
```
