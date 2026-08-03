# Agent-first Steward Architecture

- Protocol ID: `steward`
- Version: `0.1.0`
- Maturity: `practiced`
- Evidence scope: one field-tested single-agent binding operates the `1:1:N` topology at `steward:S1` with substantial `steward:S2` coverage and partial `steward:S3`/`steward:S4` elements; the `steward@0.1.0` artifact schema, a field-tested durable canonical task record in ordinary Steward work, per-order revocable grants, heterogeneous-participant operation within the binding, and formal takeover remain unvalidated (see [Kiro Local Steward](../usecases/steward/kiro-local-steward.md))
- Level namespace: `steward:S0`–`steward:S5`
- Last updated: 2026-08-03
- Origin: maintainer design discussion captured on 2026-07-15; raw private conversations are intentionally omitted

## 1. Purpose

Agent interaction has evolved through three useful topologies:

```text
1:1
  one human ↔ one agent

1:N
  one human ↔ many agent sessions

1:1:N
  one human ↔ one trusted Steward ↔ many agents, runtimes, and managed resources
```

The first transition increases available capability, but it also transfers coordination work to the human. The human must decide which agent to ask, repeat context, track parallel sessions, compare answers, supervise execution, recover failures, and integrate results.

The `1:1:N` topology restores a single relationship surface without giving up the capabilities of many participants:

> The Principal communicates with one sufficiently capable Steward. The Steward understands the ongoing relationship, manages the work graph, and coordinates the N participants and resources needed to produce an accountable result.

This protocol defines that relationship and coordination mechanism. It can be followed by an agent directly from this document; it does not require a permanent Steward service.

Its product is **delegated coordination with one accountable interface**.

## 2. Origin: from conversation scaling to coordination scaling

### 2.1 `1:1` — direct relationship

In the original interaction model, one human talks to one agent.

```text
Human
  ↕ shared conversation
Agent
```

This has strong continuity and a clear responsibility boundary. The human knows where context lives and who is responding. Its limitation is capability concentration: one agent, context, runtime, and tool set must handle the whole task.

### 2.2 `1:N` — the human becomes the orchestrator

Multi-agent tools make it possible for one human to open and manage many agent sessions:

```text
             ┌─ Agent A
Human ───────┼─ Agent B
             ├─ Agent C
             └─ Agent N
```

This increases parallelism and specialization, but the topology quietly assigns a new job to the human: orchestration.

The human now has to:

- choose the right participant for each subtask;
- restate goals, constraints, and corrections across sessions;
- decide what context each participant needs;
- watch progress and detect stalled or duplicated work;
- reconcile disagreements and incompatible outputs;
- authorize risky actions in several places;
- remember which result is current and who produced it;
- synthesize many partial conversations into one decision.

The number of conversations has scaled, but the human's coordination bandwidth has not.

### 2.3 `1:1:N` — one relationship, many executors

`1:1:N` separates the **relationship topology** from the **execution topology**:

```text
Relationship topology:  Principal 1 ↔ 1 Steward
Execution topology:                     Steward 1 ↔ N participants/resources
```

In the originating design, the second `1` is one sufficiently capable model or Agent with which the human communicates directly. Other Agents, VPS runtimes, and execution environments are managed behind that relationship surface. The protocol generalizes how the second `1` may be implemented without changing this human experience.

The Principal maintains one coherent conversation. The Steward absorbs most session management and translates the Principal's intent into a supervised work graph.

The second `1` is a logical identity and accountability boundary. It does not require one physical process, one model call, or one machine. A binding may replicate the Steward runtime or use internal sub-agents, but it MUST present one consistent relationship, authority contract, and responsibility chain to the Principal.

The `N` side may include:

- local agents and sub-agents;
- agents using different models or providers;
- Council members;
- tools and deterministic workflows;
- remote runtimes and VPS hosts;
- human specialists;
- future services that expose compatible task interfaces.

The Steward is therefore not merely another participant in a group chat. It is the trusted coordination boundary between the Principal and an expandable execution environment.

### 2.4 From `1:1:N` to a butler-style Agent

Once the second `1` also maintains long-term relationship continuity, supervises ongoing tasks, manages remote resources, and can act across time and interfaces, the topology naturally extends toward a butler-style Agent.

That later system form may add persistence, scheduling, notifications, multi-device access, hosted execution, and operational infrastructure. Those features are not the origin of Steward; they are downstream realizations of the same relationship:

```text
one human relationship
  + delegated management of N capabilities
  + continuity across tasks and time
  = possible butler-style Agent system
```

This wiki records the portable relationship and coordination protocol now. A future butler service should be specified separately as one implementation of it.

## 3. Terminology

| Term | Meaning |
| --- | --- |
| Principal | The human or authorized owner whose goals, values, permissions, and risk choices govern the relationship. |
| Steward | The single logical interface responsible for interpreting intent, coordinating work, preserving continuity, and returning accountable results. |
| Participant | An agent, sub-agent, model role, human, tool, or workflow that performs bounded work. |
| Managed resource | An execution environment or asset such as a VPS, repository, database, browser session, device, or external service. |
| Relationship state | Stable, reviewable context needed to serve the Principal across tasks. |
| Work graph | The set of dependent or parallel work orders managed for one goal. |
| Binding | A concrete realization of this protocol in one agent, several agents, a CLI, an API, or a future service. |

`Steward` names a role and protocol contract. It does not require anthropomorphic behavior, emotional dependency, or a claim that the agent possesses human understanding.

## 4. Design goals

1. Let the Principal maintain one coherent relationship while using many capabilities.
2. Move routine routing, context distribution, session tracking, supervision, and result integration away from the Principal.
3. Preserve the Principal as the source of goals, values, permissions, and final escalation decisions.
4. Make every delegation bounded, attributable, observable, and revocable.
5. Keep participant identity and evidence provenance visible through synthesis.
6. Support local and remote agents, tools, and managed resources through one protocol.
7. Allow the Steward role to run inside one capable agent without a separate system service.
8. Preserve direct inspection, intervention, export, and bypass by the Principal.
9. Compose with Memory, Active Workspace, Inner Speech, Council, and Auto-Walk without owning their internal state.
10. Degrade safely when the Steward or a participant is unavailable.

## 5. Non-goals

This protocol does not define:

- A universal super-agent with unrestricted authority.
- A requirement that every task be delegated.
- A hidden router that conceals participants, evidence, cost, or failure.
- A system that makes human value choices by inference when escalation is possible.
- A requirement to expose or persist participant chain-of-thought.
- A replacement for Council deliberation, Memory consolidation, or task-specific agents.
- A permanent daemon, hosted assistant, account system, notification platform, or user interface.
- Multi-tenancy, account management, deployment, or service-level operations.
- A claim that the Steward must be the best available model at every specialist task.

The later **butler-style Agent service** is a possible binding built on this protocol. Its product and infrastructure concerns remain a separate design.

## 6. The core invariant

The Steward may coordinate authority, but it does not create authority.

```text
Principal
  supplies goals, values, permissions, and corrections
      ↓
Steward
  interprets, decomposes, delegates, supervises, integrates, and escalates
      ↓
Participants and resources
  execute only within an explicit work and authority envelope
```

Every action on the `N` side MUST be traceable to:

1. a current Principal intent or previously approved standing policy;
2. a Steward-owned goal or work order;
3. a bounded authority grant;
4. an identifiable participant or deterministic tool;
5. an observable result, failure, or unresolved state.

The Steward MUST NOT enlarge its own authority merely because delegation would be convenient.

## 7. What makes a Steward sufficiently capable

“Sufficiently capable” does not mean omniscient or universally superior. It means the Steward can reliably perform the coordination role for the current scope.

A conforming Steward SHOULD be able to:

- maintain the Principal's active goal and interaction continuity;
- distinguish user intent from its own inference;
- know when it can act directly and when to delegate;
- discover and compare participant capabilities;
- distribute only the context required for a subtask;
- define observable completion and verification criteria;
- monitor progress without micromanaging private reasoning;
- detect disagreement, duplication, drift, and false completion;
- synthesize outputs without erasing provenance or dissent;
- recognize authority boundaries and request approval;
- admit uncertainty, expose failures, and support intervention;
- preserve an inspectable state that another Steward can resume.

If those capabilities are missing for a material task, the correct behavior is escalation, a narrower commitment, or transfer—not confident orchestration theater.

## 8. Relationship contract

The long-lived `1:1` side SHOULD be represented by a reviewable `StewardRelationship` rather than inferred from an entire raw chat history.

```yaml
relationship_id: rel-001
principal_id: principal-owner
steward_identity: steward-primary
status: active

purpose:
  - "Help the Principal turn intent into accountable outcomes"

interaction_preferences:
  default_summary_depth: concise
  surface_parallel_sessions: on_request
  interrupt_policy: material_only

standing_authority:
  allowed_without_confirmation:
    - read_scoped_project_files
    - run_reversible_diagnostics
  always_confirm:
    - publish_external_content
    - spend_money
    - destructive_or_irreversible_action

memory_policy:
  allowed_scopes: [relationship, project]
  human_review_for_identity_or_value_changes: true

inspection:
  participant_provenance_visible: true
  delegation_log_available: true
  export_supported: true
  bypass_supported: true
```

This is a conceptual schema. A binding may use files, database records, prompt state, or explicit user instructions.

Relationship state MUST distinguish:

- explicit Principal statements;
- repeated but unconfirmed preferences;
- Steward inferences;
- project-scoped conventions;
- temporary task constraints.

Repeated behavior does not silently become permanent identity or authority.

## 9. Managed capability and resource registry

The Steward cannot route responsibly without knowing what it manages.

### 9.1 Participant capability card

```yaml
participant_id: agent-research-01
kind: agent
capabilities: [source_research, evidence_synthesis]
limitations: [no_external_write]
context_modes: [isolated, project]
tools: [browser]
cost_class: medium
latency_class: interactive
independence_group: model-family-a
health: available
last_verified_at: <timestamp>
```

### 9.2 Managed resource card

```yaml
resource_id: runtime-build-01
kind: remote_runtime
capabilities: [build, test]
owner: principal-owner
access_scope: project-alpha
mutation_risk: medium
credential_ref: secret-store-reference-only
health: available
last_verified_at: <timestamp>
```

Secrets MUST NOT be embedded in capability cards, work orders, prompts, logs, or wiki documents. Bindings should pass opaque credential references through a separate secret boundary.

A VPS is a managed resource, not an agent. An agent acting through it remains responsible for the action; the machine does not become the decision owner. One host MAY simultaneously be a managed resource and host one or more agent processes that participate under their own bindings; operating the host and commanding a hosted agent are distinct authorities with distinct scopes.

## 10. Core protocol artifacts

### 10.1 IntentRecord

Captures what the Principal actually requested before decomposition.

```yaml
intent_id: intent-001
principal_statement: <minimal faithful statement>
interpreted_goal: <Steward interpretation>
assumptions: []
clarifications: []
status: understood
```

### 10.2 GoalContract

Defines the outcome, success criteria, constraints, non-goals, risk, and decision owner. The Council protocol's `GoalContract` MAY be reused.

### 10.3 WorkOrder

```yaml
work_order_id: work-003
goal_contract_id: goal-001
assigned_to: agent-research-01
task: <bounded deliverable>
context_refs: []
success_criteria: []
non_goals: []
dependencies: []
authority_grant_id: auth-003
budget:
  time: 10m
  cost: <binding-defined>
status: assigned
report_to: steward-primary
```

### 10.4 AuthorityGrant

```yaml
authority_grant_id: auth-003
granted_by: steward-primary
derived_from: relationship-policy-or-principal-approval
allowed_actions: [read, analyze]
forbidden_actions: [write, publish, purchase]
resource_scope: [project-alpha]
expires_at: <timestamp>
revocable: true
```

An `AuthorityGrant` can narrow inherited authority but cannot broaden it.

A binding MAY satisfy authority-awareness primarily through a standing authority policy (§8) instead of per-order grants, provided the policy is attributable to an explicit Principal decision, reviewable, revocable, and bounded with explicit always-confirm classes, and actions taken under it leave an audit trail. Per-order `AuthorityGrant`s remain REQUIRED for any action that exceeds the standing policy. This choice does not waive `steward:S3`'s audit requirement.

### 10.5 ProgressEvent

```yaml
event_id: progress-014
work_order_id: work-003
participant_id: agent-research-01
status: blocked
summary: <concise observable state>
evidence_refs: []
needs: [additional_source_access]
```

### 10.6 ResultEnvelope

```yaml
result_id: result-003
work_order_id: work-003
producer: agent-research-01
status: completed
claims: []
evidence_refs: []
artifacts: []
uncertainties: []
unresolved_dissent: []
verification: []
```

### 10.7 EscalationRequest

```yaml
escalation_id: esc-002
goal_contract_id: goal-001
reason: value_choice_required
options: []
tradeoffs: []
recommended_default: <optional reversible default>
deadline: <optional>
```

### 10.8 StewardDigest

The default Principal-facing update compresses coordination state without hiding it:

```yaml
goal_status: in_progress
completed: []
in_progress: []
blocked: []
decisions_needed: []
material_risks: []
participant_details: available_on_request
next_checkpoint: <condition or time>
```

The digest replaces routine session management for the Principal. It must not replace traceability.

## 11. Steward lifecycle

```text
receive Principal intent
  → preserve the original statement
  → interpret goal, constraints, and authority
  → decide: act directly, delegate, invoke Council, or ask
  → create/update canonical task state (Active Workspace when adopted)
  → discover participants and resources
  → issue bounded WorkOrders and AuthorityGrants
  → monitor ProgressEvents and dependencies
  → intervene on drift, conflict, risk, or failure
  → verify and integrate ResultEnvelopes
  → escalate value choices, missing authority, or material uncertainty
  → return one coherent answer plus inspectable provenance
  → capture only reusable outcomes through Memory
  → close or retain explicit follow-up state
```

The Steward SHOULD perform work directly when delegation would add more coordination cost than value.

## 12. Routing and delegation policy

Before delegation, the Steward SHOULD evaluate:

1. Does the task benefit from specialization, isolation, parallelism, or independence?
2. Is the selected participant's capability current and relevant?
3. What is the smallest sufficient context slice?
4. What authority and resources are actually required?
5. How will completion be observed and verified?
6. What dependencies or conflicting writers exist?
7. What should happen if the participant fails or times out?

Valid execution shapes include:

### 12.1 Direct execution

The Steward performs the task itself. This preserves the `1:1:N` model even when `N = 0` for a particular task.

### 12.2 Same-model sub-agents

The Steward creates isolated roles or contexts using the same model family. It MUST disclose correlated model risk when independence matters.

### 12.3 Heterogeneous agents

The Steward routes to different providers or runtimes based on capability, independence, cost, latency, or tool access.

### 12.4 Council invocation

The Steward asks a Council to deliberate on a bounded decision. The Council returns candidates, dissent, and a `DecisionRecord`; it does not inherit the whole Steward relationship.

### 12.5 Remote execution

The Steward assigns bounded operations to an agent or workflow acting on a managed runtime such as a VPS. Remote location never implies broader permission.

### 12.6 Human participation

The Steward may route a value judgment, approval, or specialist question to a human. Human participation is not a failure of agent autonomy; it is correct authority routing.

## 13. Principal experience

The defining user experience is not “many chats displayed in one interface.” It is one continuous, inspectable relationship.

By default, the Principal should receive:

- one coherent understanding of the goal;
- concise updates at meaningful checkpoints;
- explicit questions only when input or authority is material;
- one integrated result;
- visible uncertainty, dissent, source provenance, and action status;
- the ability to inspect any delegation or participant output;
- the ability to interrupt, redirect, revoke, or take over.

The Principal SHOULD NOT have to:

- repeatedly copy context between agents;
- poll every participant for status;
- reconcile routine formatting differences;
- remember which session owns the current task state;
- diagnose ordinary participant failure;
- manually assemble partial results unless they choose to.

Coordination compression is successful only if it reduces human operational load without reducing human control.

## 14. Composition with other protocols

Steward is a coordination protocol, not a cognitive container.

| Protocol | Relationship to Steward |
| --- | --- |
| Memory | Supplies gated relationship and project continuity; receives only selected reusable outcomes through capture. |
| Active Workspace | Optional structured binding for the canonical goal, work graph, dependencies, evidence, conflicts, and current actions. Without it, Steward keeps an equivalent bounded task record. |
| Inner Speech | Remains local to the acting agent; only bounded decision-relevant cues cross into shared coordination state. |
| Council | Provides plural deliberation for selected decisions; the Steward routes and integrates but cannot manufacture consensus. |
| Auto-Walk | May surface optional weak hypotheses; it never silently changes the work graph or Principal intent. |
| Autodream | Consolidates Memory; it does not redefine the Steward relationship or authority policy autonomously. |

A common composition is:

```text
Principal intent
  → StewardRelationship + canonical task state
  → Memory retrieval for relevant continuity
  → WorkOrders to selected participants/resources
  → optional Council for high-impact disagreement
  → ResultEnvelopes and runtime evidence
  → Steward synthesis and Principal-facing answer
  → selective Memory capture
```

The Steward coordinates these protocols through their public artifacts. It does not gain permission to mutate their internal state.

## 15. Trust, inspection, and reversibility

The `1:1` relationship can create strong convenience and strong concentration risk. A conforming binding MUST preserve:

### 15.1 Provenance

The Steward may compress presentation but must retain who produced each claim, artifact, action, and verification result.

### 15.2 Inspectability

The Principal can request the work graph, participant list, authority grants, status, evidence, dissent, and raw public artifacts.

### 15.3 Revocability

The Principal can revoke a work order, authority grant, resource, standing policy, or the Steward relationship itself.

### 15.4 Exportability

Relationship state, active work, and durable artifacts should use portable formats so another authorized Steward can resume them.

### 15.5 Bypass

The Principal can communicate with or operate a participant/resource directly when needed. The Steward is the default interface, not an inescapable gatekeeper.

### 15.6 Separation of duties

For high-risk actions, the participant proposing an action SHOULD differ from the verifier or approver. A Steward must not use synthesis to hide a failed independent check.

## 16. Failure modes

### 16.1 Human bottleneck becomes Steward bottleneck

One interface may become a latency or context bottleneck. Use bounded parallelism, checkpoints, context partitioning, and explicit degraded modes.

### 16.2 Context compression loss

The Steward may omit a constraint or dissent while briefing participants or summarizing results. Preserve the original intent, source references, and inspectable work artifacts.

### 16.3 Authority creep

Convenience may encourage the Steward to infer broader standing permission. Use explicit, expiring, revocable grants and escalate ambiguity.

### 16.4 Information monopoly

The Steward may become the only entity that can interpret relationship state. Require portable artifacts, export, direct inspection, and takeover procedures.

### 16.5 False completion

Participants may report completion without runtime evidence, and the Steward may pass it through. Completion criteria and verification must be defined before delegation.

### 16.6 Synthesis laundering

An integrated answer may erase minority warnings, provenance, or contradictory evidence. Preserve unresolved dissent and distinguish evidence from the Steward's judgment.

### 16.7 Relationship overreach

Long-term familiarity may be mistaken for permission, values, or identity. Separate explicit statements, inferences, task context, and standing policy.

### 16.8 Hidden cost and resource use

The `N` side can consume models, machines, time, or money invisibly. Expose material budgets and require approval for spending or resource expansion beyond policy.

### 16.9 Single point of failure

If the Steward disappears, ongoing work may become inaccessible. Persist resumable public state and define a transfer or direct-operation path.

### 16.10 Capability theater

The Steward may delegate for appearance or claim supervision it did not perform. Prefer direct execution for simple work and record actual verification events.

### 16.11 Stale view

The Steward's picture of its environment drifts in two ways: registry entries diverge from reality (addresses, services, health), and the Principal or another agent legitimately mutates a managed resource in parallel. Routing or acting on a stale view causes wrong action. The Steward MUST NOT assume exclusive control of a managed resource or that its cached view is current. Keep `last_verified_at` honest on capability and resource cards, and re-verify a stale card before high-risk operations on that participant or resource.

## 17. Degraded operation and recovery

- If a participant fails, reassign, narrow, retry under policy, or return a partial result with the failure visible.
- If a managed resource fails, stop dependent work and avoid silently switching to an unauthorized resource.
- If Council quorum fails, preserve available views and unresolved status.
- If Memory is unavailable, continue with explicit loss of relationship/project history.
- If the Steward loses context, reload the relationship contract and canonical task state rather than inventing continuity.
- If the Steward is unavailable, the Principal can inspect/export state and continue directly or appoint another Steward.
- If authority is unclear, pause only the affected action; unrelated safe work may continue.

Recovery MUST NOT broaden authority or conceal that the execution path changed.

## 18. Minimal binding

A single capable agent can implement the protocol without external infrastructure:

1. Treat the current user as Principal.
2. Preserve their original request and identify goal, constraints, and authority.
3. Maintain one explicit canonical task record; use Active Workspace if that optional protocol is adopted. (An in-context record satisfies `steward:S1`; `steward:S2` requires it to be durable and inspectable independently of the live context.)
4. Decide whether to act directly or delegate to available sub-agents/tools.
5. Give every delegated task bounded context and success criteria.
6. Track status and evidence in the canonical task record.
7. Ask the user only for material choices, permission, or missing context.
8. Integrate results with provenance and unresolved uncertainty.
9. Let the user inspect or redirect delegated work.
10. Capture durable lessons only through the Memory protocol.

This is already a valid `1:1:N` Steward binding. A hosted butler system is an optional future implementation, not a prerequisite.

## 19. Conformance levels

| Level | Name | Capability |
| --- | --- | --- |
| `steward:S0` | Direct relationship | One Principal and one agent; no delegated participants. |
| `steward:S1` | Explicit delegation | The Steward creates bounded work orders for one or more participants. |
| `steward:S2` | Canonical coordination | A durable canonical task record inspectable independently of the Steward's live context, capability registry, status, provenance, and result integration. |
| `steward:S3` | Authority-aware | Revocable authority (standing policy and/or per-order grants, §10.4), approval gates, resource scopes, and audit records. |
| `steward:S4` | Resilient `1:1:N` | Failure recovery, takeover/export, heterogeneous participants, and independent verification. |
| `steward:S5` | Service binding | A separately specified persistent or hosted butler-style system implements the protocol. |

`steward:S5` is not inherently more intelligent or trustworthy than `steward:S2`–`steward:S4`. It describes operational realization, not protocol quality.

## 20. Conformance checklist

Before calling a binding a Steward architecture, verify the items applicable at the claimed level and under the conditions the binding has enabled; untagged items apply from `steward:S1`.

1. The Principal has one logical relationship and accountability interface.
2. The original Principal intent survives decomposition.
3. The Principal no longer has to manually manage routine N-way session state.
4. (`steward:S2+`) Every participant and resource has a known scope and capability.
5. Every delegated action has a bounded work order and authority source.
6. The Steward cannot expand its own authority.
7. Progress, failure, provenance, dissent, cost, and material risk remain inspectable.
8. Result synthesis does not convert consensus into evidence.
9. The Principal can interrupt and bypass the Steward at any level; revoke a grant or the standing policy (`steward:S3+`); and export state or replace the Steward (`steward:S4+`).
10. Relationship memory distinguishes explicit statements from inference.
11. Participant private reasoning is not required for observability.
12. (`steward:S4+`) Steward failure has a resumable recovery path.
13. Simple tasks may still be executed directly.
14. The design works as a protocol before it becomes a service.

## 21. Practical use cases

- [Kiro Local Steward](../usecases/steward/kiro-local-steward.md) — `Evidence: field-tested`; `Conformance: partially-verified`. A local `steward:S1` binding with substantial `steward:S2` coverage and explicit higher-level gaps.

## 22. Final rule

```text
1:1 gives the human one relationship.
1:N gives the human many capabilities and many coordination burdens.
1:1:N keeps one relationship while delegating the coordination burden.

The Principal owns intent, values, and authority.
The Steward owns coordination and accountability.
Participants own bounded execution.

One relationship does not mean hidden work.
Many executors do not mean fragmented responsibility.
The Steward is the bridge, not the sovereign.
```
