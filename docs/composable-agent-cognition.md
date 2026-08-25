# Composable Agent Cognition Protocols

- Document ID: `composition`
- Version: `0.2.0`
- Maturity: `design-only`
- Evidence scope: component protocols have independent evidence; the full composition has no documented conformance run
- Level namespace: `composition:C0`–`composition:C5`
- Last updated: 2026-08-26

## 1. Purpose

This document defines how the agent-first mechanisms in this repository compose without becoming one mandatory cognitive runtime.

The core idea is:

> Each mechanism is a portable protocol. One agent may execute it alone, several agents may share its roles, and multiple protocols may be composed through explicit artifacts rather than hidden coupling.

The protocols currently covered are:

- [Agent-first Memory](agent-first-memory.md) — calibrates trust in retained experience.
- [Agent-first Auto-Walk](agent-first-auto-walk.md) — explores weak, lateral hypotheses without mutating memory.
- [Agent-first Skill Lifecycle](agent-first-skill-lifecycle.md) — calibrates trust in adopted procedure through provenance, authority, scoped evidence, and rollback.
- [Agent-first Active Workspace](agent-first-active-workspace.md) — calibrates what receives attention in the current task.
- [Agent-first Inner Speech](agent-first-inner-speech.md) — converts active state into bounded self-guidance.
- [Agent-first Council](agent-first-council.md) — creates, critiques, revises, and adjudicates multiple candidate views.
- [Agent-first Steward](agent-first-steward.md) — preserves one Principal relationship while coordinating many participants and managed resources.

This is a composition guide, not a claim that an agent has human consciousness.

## 2. Design goals

1. Let a single agent use any protocol without installing a separate service.
2. Let several agents or sub-agents divide the same protocol's roles.
3. Let heterogeneous models participate without making provider identity part of the protocol.
4. Keep long-term memory, current attention, self-guidance, exploration, deliberation, and delegated coordination separate.
5. Make every cross-protocol transition explicit, source-aware, and auditable.
6. Allow implementations to start manually and add automation later.

## 3. Non-goals

This document does not define:

- A single cognitive operating system that every agent must run.
- A mandatory supervisor, Steward, or daemon.
- Direct access to a model's latent representation or biological cognition.
- A requirement to persist private reasoning or chain-of-thought.
- A universal ontology for beliefs, emotions, identity, or consciousness.
- A rule that every task must invoke every protocol.

Anthropic's Global Workspace / J-space research is an engineering inspiration for making current task state explicit. The Active Workspace protocol is an external control surface; it does not claim to read or write a model's internal J-space.

## 4. Protocol map

Each protocol calibrates a different resource:

| Protocol | Calibrates | Primary artifact | Default lifetime |
| --- | --- | --- | --- |
| Memory | Trust in the past | Memory item | Cross-session |
| Auto-Walk | Possibility at the edge | Weak hypothesis | Multi-session until discharge/expiry |
| Skill Lifecycle | Trust in adopted procedure | Candidate/evidence/adoption/lifecycle records | Cross-session version lifecycle plus bounded activation episodes |
| Active Workspace | Current attention | Workspace snapshot/item | One task or bounded run |
| Inner Speech | Explicit self-guidance | Control cue | One step or short phase |
| Council | Plural deliberation | Candidate/review/decision record | One decision run plus outcome record |
| Steward | Relationship continuity and delegated coordination | Relationship/work order/result envelope | Cross-task relationship plus bounded work runs |

Autodream and archive are subprotocols of Memory. Inside-Outsider is a stance within Inner Speech and an optional frame-check in Council. They do not require separate services.

### 4.1 Level namespaces

Implementation levels are local cumulative capability ladders, not a shared maturity scale. A bare `L4` is meaningful only inside its declaring document and MUST NOT be compared with another protocol's `L4`. A binding may disclose isolated capability tests above its current contiguous level, but it MUST NOT claim the higher level until all lower requirements pass.

| Document | Qualified range | Meaning of the prefix |
| --- | --- | --- |
| Memory | `memory:L0`–`memory:L5` | Memory implementation capability |
| Auto-Walk | `auto-walk:L0`–`auto-walk:L4` | Walk generation, surfacing, and feedback capability |
| Skill Lifecycle | `skill:L0`–`skill:L4` | Procedure adoption, evidence, automation, and formation capability |
| Active Workspace | `active-workspace:L0`–`active-workspace:L4` | Workspace structure and sharing capability |
| Inner Speech | `inner-speech:L0`–`inner-speech:L4` | Cue generation and feedback capability |
| Council | `council:L0`–`council:L5` | Deliberation and outcome-evaluation capability |
| Steward | `steward:S0`–`steward:S5` | Relationship and delegation capability |
| Composition guide | `composition:C0`–`composition:C5` | Cross-protocol integration capability |

Within one document, the short form MAY be used after the namespace is declared. Every cross-document reference and machine-readable binding record MUST use the qualified form.

## 5. The composition invariant

Protocols communicate by emitting artifacts into another protocol's public interface. They do not silently mutate one another's internal state.

```text
Allowed:
  Workspace requests Memory retrieval by item id or trigger.
  Inner Speech emits a bounded control cue into Workspace.
  Council emits a DecisionRecord for the acting agent.
  Steward issues a bounded WorkOrder to a participant.
  Steward invokes Council with a GoalContract and evidence snapshot.
  A confirmed Council outcome enters Memory through Memory capture.
  A discharged Walk hypothesis spawns a new Memory item through capture.
  A Skill activation observation enters Memory only through Memory capture.
  A Skill privilege delta requests a decision from its binding's authority/security path.

Forbidden:
  Auto-Walk edits a Memory topic directly.
  A staged Skill activates itself or widens the standing grant used to adopt it.
  Skill evaluation rewrites historical evidence when execution context changes.
  Inner Speech silently rewrites long-term Memory.
  Council changes Steering because several members agreed.
  An agent promotes its own repeated observation into Conventions or Steering without an attributable authorizing decision.
  Steward expands authority because a participant requests it.
  Steward rewrites participant dissent while synthesizing a result.
  Workspace persists every transient thought as durable knowledge.
  Memory forces a stale item into the current task without activation gating.
```

The general rule is:

> Read peers through their retrieval interfaces; write peers through their capture or event interfaces.

## 6. Shared artifact envelope

A binding MAY use files, JSON, database rows, events, or in-memory objects. Any artifact crossing protocol boundaries SHOULD carry this minimum envelope:

```yaml
artifact_id: <stable id within the run or store>
artifact_type: <producer-defined type such as memory_item, hypothesis, control_cue, candidate_artifact, candidate_record, metamemory_feedback, or policy_proposal>
producer_protocol: <protocol id>
protocol_version: <producer protocol version>
created_at: <timestamp>
producer: <agent/model/runtime or role id>
task_id: <task/run id when applicable>
source_refs:
  - <smallest stable source reference>
derived_from:
  - <optional; smallest source reference that uniquely resolves in the receiving scope to the consumed artifact and its exact version, revision, or content identity; include source producer protocol/version and run or store scope when needed; required when a materialized rendering or transformation has its own artifact identity>
confidence_scheme: <optional; epistemic-status-v1 | ordinal-confidence-v1 | documented protocol-defined scheme>
confidence: <optional; closed token from confidence_scheme>
status: <optional; protocol-specific closed token when the artifact has a lifecycle>
visibility: <private-ephemeral | shared-run | durable | public-rationale>
```

Protocol-specific schemas add fields, but the envelope preserves provenance, scope, and lifetime across composition boundaries.

`artifact_type` is not one global closed ontology. It is a stable type declared by the producing protocol/version and SHOULD match that protocol's manifest entry or schema. Receivers route by `producer_protocol + protocol_version + artifact_type`; they MUST NOT guess a schema from a generic name alone.

`private-ephemeral` does not imply that hidden chain-of-thought is available. It means a concise machine-operational artifact is not intended for the user or durable storage.

### 6.1 Confidence schemes

`confidence` is not globally meaningful without its scheme. Whenever a cross-protocol artifact carries `confidence`, it MUST also carry `confidence_scheme`. Artifacts such as authority grants that do not make an epistemic or predictive claim SHOULD omit both fields rather than inventing confidence.

| Scheme | Closed values | Use |
| --- | --- | --- |
| `epistemic-status-v1` | `confirmed`, `observed-once`, `inferred`, `unknown` | Source/evidence status for factual or state-like claims: authoritative/repeated/corroborated; one direct observation; derived; or unclassified. |
| `ordinal-confidence-v1` | `low`, `medium`, `high` | Bounded confidence in hypotheses, cues, predictions, or recommendations. |
| Documented protocol-defined scheme | Vocabulary declared by the producing protocol and version | Only when neither shared scheme preserves the intended semantics. |

`confirmed` is scoped: it means an authoritative source, repeated observation, or independent corroboration supports the claim for its stated scope. It does not mean permanent or universally true. `observed-once` is the correct token for one direct bounded check even when that observation is clear.

Receivers MUST NOT compare values across different schemes or silently convert one scheme into another. `unknown` is a real epistemic state; it is not equivalent to `low`. A protocol MAY omit `confidence_scheme` inside a private schema only when the schema declares one fixed scheme, but it MUST restore the field when the artifact crosses a protocol boundary.

When producer and receiver define different status vocabularies, the receiver MUST preserve the producer token as `origin_status` and assign its own local `status`. Reusing one token field with a new meaning is forbidden.

### 6.2 Outcome verdict scheme

Memory activation, Inner Speech intervention feedback, and Skill activation observation share `intervention-outcome-v1`:

| Value | Meaning |
| --- | --- |
| `helpful` | Materially supported a successful or better-calibrated action. |
| `misleading` | Materially pushed the action in a wrong direction. |
| `neutral` | Was used but did not materially affect the outcome. |
| `unknown` | Outcome or causal contribution cannot yet be judged. |

Cross-protocol feedback artifacts MUST carry `verdict_scheme: intervention-outcome-v1`. Protocol-local outcomes such as Auto-Walk's `engaged | ignored | rejected` are different events and MUST NOT be mapped into this scheme without an explicit attribution step.

### 6.3 Derived representations

`source_refs` identifies source, evidence, or authority context that supports or constrains an artifact's content or effect. `derived_from` states a different relation: transformation lineage from materialized content to its immediate source artifacts. The two are not interchangeable.

The envelope member `derived_from` is reserved for that transformation-lineage meaning. A homonymous field inside a producer schema retains its protocol-local meaning — for example, Steward's `AuthorityGrant.derived_from` names an authority source, not content lineage. Before such an artifact crosses a protocol boundary, the binding MUST namespace or rename the protocol-local homonym so a receiver cannot confuse the two relations. This disambiguation changes only the boundary transport encoding: the owning protocol evaluates artifact and content identity over its protocol-local schema, and a faithful transport re-encoding that preserves semantics, producer, lineage, and disclosure scope is identity-preserving propagation rather than a new derived artifact.

For a materialized rendering or transformation that receives its own artifact identity, `derived_from` MUST resolve uniquely in the receiving scope to the exact source artifact version, revision, or content identity consumed. When the source `artifact_id` is not globally unique, the reference also carries the source producer protocol/version and run or store scope needed to disambiguate it. Every material immediate source MUST have an entry, unless one referenced aggregate snapshot closes the exact source set consumed. For artifacts known to have been produced under `composition@0.2.0` or later, omitting `derived_from` from a new-identity derived artifact is nonconformance; absence on a legacy or contract-unknown artifact proves neither original production nor identity-preserving propagation.

A transformation that changes semantics or disclosure scope MUST mint a new artifact identity and therefore MUST carry `derived_from`. A verified identity-preserving propagation MAY preserve the owning protocol's artifact or content identity only when wording, semantics, producer, source lineage, and disclosure scope are unchanged; otherwise it is a new derived artifact, consistent with [Governed Shared Memory §4.3](governed-shared-memory-profile.md#43-rendering-and-lineage). Only that verified identity-preserving propagation MAY satisfy an exact-source resolution through the representation; a new-identity, lossy, or unverified derivation cannot.

A derived artifact MUST NOT silently inherit or upgrade its source's authority, standing, evidence state, confidence, or status. The receiver makes any local admission or classification explicitly; when producer and receiver status vocabularies differ, the `origin_status` rule in §6.1 applies.

A transformation MUST be treated as lossy for an intended use unless the owning protocol or binding cites applicable, re-checkable evidence or validation that establishes fidelity for that use. Fidelity does not itself create authority, standing, evidence, confidence, or independent corroboration. Currentness is evaluated against the complete set of material sources required for the intended use: each must resolve to the identity and version required by that use. Age alone neither preserves nor invalidates a derivation.

When later resolution fails, the `access-restricted`, `source-unavailable`, and `source-erased` distinctions in [Governed Shared Memory §5–§6](governed-shared-memory-profile.md#5-lifecycle-and-read-discipline) apply. The recorded source identity remains the lineage object only while retaining it is authorized. If erasure covers that identity or reference, a permitted content-free tombstone or sanitized replacement carries only the lineage that may remain and cannot satisfy exact-source resolution. Live resolvability and permitted use are evaluated separately. A decision whose correctness depends on the exact wording or structure of any source — such as authority text, closed-vocabulary tokens, triggers, or validation criteria — MUST resolve every source version required by that decision and MUST NOT rely on an unresolved or new-identity derived representation alone. Derived representations MAY guide attention or selection.

Regenerable internal state that materially affects retrieval, routing, or action remains binding-owned, but the binding MUST make its source boundary, currentness basis, and material limitations recoverable. If those are insufficient for the intended effect, the binding MUST rehydrate the state, resolve the source through an authorized path, narrow the effect, or fail closed. Internal state that neither crosses a protocol boundary nor materially affects retrieval, routing, or action remains binding-defined under the [Portability and Recovery four-plane classification](governed-artifact-portability-recovery.md#4-four-plane-classification).

## 7. One agent or many

A protocol role is not the same thing as a model identity.

```text
role execution = model/runtime + role contract + context slice + tools + memory scope
```

The same protocol can therefore run in several shapes:

### 7.1 Single-agent sequential

One agent executes the phases in order. This is the minimum portable form and MUST remain valid unless a protocol explicitly requires external independence.

Examples:

- One agent creates and updates its own Active Workspace.
- One agent uses an Inside-Outsider cue before an irreversible action.
- One agent simulates proposer, critic, and synthesizer phases with separated artifacts.

### 7.2 Same-model isolated roles

Sub-agents or fresh contexts use the same model family with different role contracts. This adds functional diversity and reduces context contamination, but shared model priors remain a correlated-risk source.

### 7.3 Heterogeneous agents

Different models, providers, tools, or evidence scopes execute roles. This may add inductive diversity, but provider labels do not prove independence. Bindings should measure actual redundancy, disagreement, and contribution.

### 7.4 Hybrid escalation

A cheap single-agent or same-model run executes first. A heterogeneous Council or independent verifier is invoked only when risk, uncertainty, conflict, or irreversibility crosses a configured threshold.

The protocol defines artifacts and invariants. The binding chooses the execution topology.

## 8. Common composition profiles

### 8.1 Focused single-agent task

```text
Task
  → Active Workspace initializes goal, constraints, evidence, and conflicts
  → Memory supplies gated context
  → Inner Speech emits short orientation or verification cues
  → Agent acts
  → Durable outcome enters Memory only through capture
```

Auto-Walk and Council remain unused unless triggered. Composition does not mean mandatory invocation.

### 8.2 Difficult decision

```text
Active Workspace detects unresolved high-impact conflict
  → Council receives a GoalContract and evidence snapshot
  → Council returns candidates, conflict map, dissent, and DecisionRecord
  → Inner Speech turns the decision into the next bounded action
  → Outcome is observed
  → Memory records the reusable result and provenance
```

### 8.3 Frame challenge

```text
Workspace shows repeated failure, premature consensus, or evidence-confidence mismatch
  → Inside-Outsider reads a bounded workspace snapshot
  → emits frame-holds or frame-challenge plus re-entry action
  → acting agent accepts, rejects, or defers explicitly
```

### 8.4 Offline learning

```text
Memory archive
  → Autodream consolidates state and knowledge
  → Auto-Walk explores weak cross-topic hypotheses
  → confirmed outcomes return through Memory capture
  → metamemory feedback adjusts review priority and proposes policy changes
```

Auto-Walk never becomes the maintenance stage, and metamemory never changes the memory constitution autonomously.

### 8.5 Stewarded `1:1:N` task

```text
Principal maintains one conversation with Steward
  → Steward preserves original intent and initializes Active Workspace
  → Memory supplies relevant relationship/project continuity
  → Steward acts directly or issues bounded WorkOrders
  → participants and managed resources return ProgressEvents/ResultEnvelopes
  → optional Council resolves a selected high-impact disagreement
  → Steward verifies, integrates, and returns one inspectable result
  → reusable outcomes enter Memory only through capture
```

The Steward compresses coordination, not accountability. The Principal can inspect, interrupt, revoke, bypass, export, or replace the Steward.

### 8.6 Governed shared standing

When several participants need durable shared standing over existing artifacts, read the [Governed Shared Memory Composition Profile](governed-shared-memory-profile.md).

The profile preserves each artifact's producer, source, status, confidence, and authority while a declared space grants bounded standing. It is not a shared-truth store, does not authorize direct writes to participants' Memory stores, and defines no separate conformance level. An Agent may discover that the profile appears applicable, but space creation, audience, authority, and admission require a declared binding.

## 9. Beliefs and expectations

Belief-like records may be useful as cross-cutting artifacts, especially in Council and outcome feedback:

```yaml
claim: <what is believed>
subject: <whose or what system's belief>
source_refs: []
time_scope: <when it applies>
confidence_scheme: ordinal-confidence-v1
confidence: <low | medium | high>
expected_outcome: <what should happen if the claim holds>
falsifier: <what would count against it>
observed_outcome: <filled later>
```

This is an optional artifact shape, not a universal Belief OS. A generated belief model is a hypothesis consistent with available text, not direct access to a human's or agent's true internal state.

## 10. Attention and trust boundaries

Composition creates new failure surfaces. Every binding MUST preserve these boundaries:

1. **Memory is testimony, not truth.** Workspace activation does not upgrade confidence.
2. **A hypothesis is not memory.** Walk discharge creates a new sourced memory item; it does not promote the hypothesis object.
3. **Consensus is not evidence.** Council agreement cannot replace external verification.
4. **A control cue is not a durable lesson.** Inner Speech expires unless an independently reusable outcome is captured.
5. **Workspace salience is not importance forever.** Current activation must not become long-term priority by default.
6. **Distance is not objectivity.** Inside-Outsider observations are counterweights, not privileged truth.
7. **Delegation is not new authority.** A Steward may narrow and route granted authority; it cannot create or silently expand it.

## 11. Ownership and mutation

Every composed run MUST name an owner for each mutable surface:

| Surface | Default writer |
| --- | --- |
| Memory inbox | Memory capture path |
| Memory distilled store | Autodream/review binding |
| Walk pool | Walk runner |
| Skill candidates and lifecycle records | Skill Lifecycle binding; Principal or granted authority owns adoption |
| Active Workspace | Task controller or elected workspace owner |
| Inner Speech cue | Acting agent or bounded observer role |
| Council artifacts | Role owner; RunRecord owned by controller |
| Steward relationship/work graph | Logical Steward; Principal owns intent and authority |
| Steering/conventions | Human-reviewed promotion path |

Multi-agent bindings MUST either elect a single writer or define optimistic concurrency with revision checks. Last-writer-wins is not a valid default for a shared cognitive surface.

## 12. Observability without thought dumping

Agents need replayable state, but replayability does not require full private reasoning.

Persist:

- goals and success criteria;
- evidence and source references;
- assumptions that materially affect action;
- conflicts and decisions;
- accepted/rejected interventions;
- outcome and feedback events.

Do not require:

- hidden chain-of-thought;
- unrestricted internal monologue;
- token-by-token reasoning traces;
- transient associations that did not affect an action.

A binding SHOULD expose concise public rationale separately from private-ephemeral control artifacts.

## 13. Degraded operation

Each protocol must fail independently:

- If Memory is unavailable, the task may continue with explicit loss of historical context.
- If Inner Speech is unavailable, the agent can act directly from Workspace.
- If Council members fail, the run degrades according to its minimum quorum and records missing perspectives.
- If Auto-Walk is unavailable, stable task execution is unaffected.
- If Skill Lifecycle automation is unavailable, explicit manual adoption and rollback may continue at `skill:L0`.
- If Workspace persistence is unavailable, a single-session in-memory snapshot is valid.
- If Steward is unavailable, the Principal can inspect/export canonical state and continue directly or appoint a replacement.

Failure of an optional protocol MUST NOT make an unrelated basic task impossible.

## 14. Adoption levels

| Level | Name | Capability |
| --- | --- | --- |
| `composition:C0` | Standalone | One protocol, one agent, manual artifacts. |
| `composition:C1` | Explicit interfaces | Artifacts carry provenance, lifetime, and status. |
| `composition:C2` | Local composition | Two or more protocols exchange artifacts in one runtime. |
| `composition:C3` | Multi-agent composition | Roles are distributed with ownership and concurrency rules. |
| `composition:C4` | Outcome feedback | Decisions and memory activations receive delayed result signals. |
| `composition:C5` | Conformance | Bindings pass protocol-specific and cross-protocol validation suites. |

Start at `composition:C0`. Do not add orchestration merely to claim a higher level.

Component evidence does not compose by itself. A protocol-local or single-edge result establishes only that named scope, even when every component passes separately. A `composition:C5` claim additionally MUST declare its composed scope and observable acceptance criteria. For every path included in that scope, a cited end-to-end check MUST execute the composed path, observe every material cross-protocol boundary invariant and the final decision, artifact, or authority effect the composition exists to produce, and meet all declared criteria. The check MAY be manual or automated. Failed, undetermined, or uncovered criteria prevent a C5 claim for that scope. Untested paths and unobserved invariants on tested paths remain explicit gaps: they do not erase narrower evidence, but narrower evidence MUST NOT be reported as composed conformance.

## 15. Composition checklist

Before claiming that protocols compose safely, verify:

1. Each protocol still runs alone.
2. Every cross-protocol write uses a public capture/event interface.
3. Artifact provenance survives the transition.
4. Transient Workspace and Inner Speech artifacts expire.
5. Council consensus cannot silently enter Memory or Steering.
6. Auto-Walk cannot mutate Memory.
7. A single agent can execute the minimum profile.
8. A multi-agent binding names one owner per mutable surface.
9. Degraded operation is explicit and testable.
10. No component requires full chain-of-thought persistence.
11. Steward delegation preserves Principal intent, bounded authority, participant provenance, and takeover paths.
12. Skill candidates cannot activate themselves, rewrite their evidence, or widen their own adoption authority.
13. Cross-protocol derived representations carry an unambiguous `derived_from` for every material immediate source when required; source resolution and currentness cover the complete load-bearing set, and derivation does not silently inherit authority, evidence state, confidence, or status.
14. A composed-conformance claim cites component-local checks and scoped end-to-end checks that observe every material boundary invariant and final effect on each claimed path; failed, undetermined, uncovered, or merely component-local evidence is reported only for its actual scope.

## 16. Final rule

The protocols form a federation, not a hierarchy:

```text
Memory calibrates the past.
Workspace calibrates present attention.
Inner Speech calibrates explicit self-guidance.
Council calibrates plural deliberation.
Auto-Walk expands possibility without claiming truth.
Skill Lifecycle calibrates procedure at adoption and automation boundaries.
Steward compresses coordination while preserving one accountable relationship.

Artifacts cross boundaries.
Authority does not.
Each protocol stands alone.
Composition remains optional and explicit.
```
