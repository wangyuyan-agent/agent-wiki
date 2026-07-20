# Kiro Local Council Use Case

- Use case ID: `council.kiro-local`
- Protocol: `council@0.1.0`
- Evidence: `field-tested`
- Conformance: `mapped` — maps to selected `council:L0` mechanisms (isolated role outputs, conflict extraction, and decision synthesis) and the role-diverse profile; complete `council:L0` is not claimed because the run reviewed one shared draft rather than producing independent CandidateArtifacts; anonymized peer review (`council:L1`) and candidate version lineage/best-checkpoint (`council:L2`) were also absent
- Validation scope: one documented role-diverse independent review over a real protocol-level design decision was operated by the Steward; independent CandidateArtifacts, blind review, a deterministic controller, contextual capability estimation, and delayed outcome feedback were not implemented
- Reproducibility: `partial` — topology, role contracts, and lifecycle are documented; exact agent definitions and dispatch prompts are omitted
- Level namespace: `council`
- Last reviewed: 2026-07-20

## 1. Context

This use case records a local Council binding on the Kiro CLI on macOS, invoked by the [Kiro Local Steward](../steward/kiro-local-steward.md) when a **design decision** (not merely execution) needs plural, role-diverse review.

It is distinct from the two existing council bindings:

- Unlike [Multi-Agent Roundtable](multi-agent-roundtable.md) (OpenClaw, four rounds, anonymized peer review, `run-reported`), this binding does **not** anonymize reviewers or run scored peer-review-of-peers.
- Unlike [Local LLM Council](llm-council-local.md) (heterogeneous-model service, three fixed stages), this binding runs **same-runtime, same-model-family** sub-agents inside one Kiro CLI Steward.

Its niche: high-impact, hard-to-reverse **protocol/architecture design** review, where three independent role lenses examine one shared draft artifact and the Steward synthesizes.

## 2. What this binding is for

Use it when the decision is consequential and benefits from controlled disagreement:

- a protocol-level or architecture-level change to a shared design;
- a change that is costly to reverse once adopted;
- a draft where a single lens is likely to miss a structural weakness.

Do **not** use it for ordinary work. Daily "send this research/implementation task to the strategy or execution sub-agent" is plain Steward delegation, not a Council — this matches the protocol's non-goal that "Council is not ordinary parallel task delegation." The deployment reserves the Council for design judgment, precisely because the extra cost only pays off when the frame itself might be wrong.

## 3. Execution topology

```text
Steward (primary agent)
  = Controller + Chair

Isolated sub-agent  = Architecture lens   (system structure, coherence, technical selection)
Isolated sub-agent  = Cognition lens      (framing, hidden assumptions, "is this the right question")
Isolated sub-agent  = Debugging lens      (failure modes, boundary cases, where it breaks in practice)
```

```yaml
diversity_profile:
  role_diversity: high
  model_diversity: low            # same base-model family
  context_isolation: per-sub-agent
  information_diversity: common draft artifact + goal
  method_diversity: role-contract based
independence_group: shared-model-family-a
```

The three lenses are dispatched in parallel over isolated contexts; none sees the others' output before producing its own. The Steward retains full identity mapping (no anonymization) and performs synthesis.

## 4. Lifecycle (selected `council:L0` mechanisms)

```text
0. Steward freezes the goal: the draft artifact + the decision to make
1. Three role lenses review the same artifact independently, in parallel isolated contexts
2. Steward extracts consensus and classified disagreement (conflict map)
3. Steward synthesizes: select / bounded-combine / grounded-reframe, preserving dissent
4. Steward returns one decision to the Principal with provenance and unresolved conflicts
```

This is a useful Council-shaped review profile, but it is not a complete `council:L0` binding. The three role outputs are independent reviews of one shared draft, not independent CandidateArtifacts carrying their own positions, assumptions, risks, reversal signals, and action implications. The mapping below therefore reports mechanisms exercised rather than a conformance level achieved.

Revision rounds are not run by default; when needed, the Steward's delegation primitive can add a bounded review→revision loop, but that path was not exercised as a lineage-tracked `council:L2` cycle. There is no deterministic controller with budgets/terminal states (`council:L3`), no capability estimation (`council:L4`), and no outcome feedback loop (`council:L5`).

## 5. Observed use

The documented run reviewed a proposed change to the local memory-consolidation policy. The high-value signal was **convergence across independent role lenses**: the three lenses, given different obligations and different vocabulary, independently flagged overlapping structural weaknesses in the draft — a duplicated section, and a "rule stated in the policy but not enforced at the capture entry point" defect that two different lenses named in two different ways.

Independent convergence on the same weak point was a stronger correction signal than any single lens, and it changed the draft before adoption. The deployment's rule of thumb: this is worth the cost for protocol-level changes, and overkill for everyday edits.

## 6. Mapping to the general protocol

| Council protocol object | Local binding |
| --- | --- |
| GoalContract | Steward's frozen "draft + decision" brief |
| CandidateArtifact | Gap: one shared draft was reviewed; no independent CandidateArtifacts were produced |
| ReviewArtifact | Each role lens's independent review |
| ConflictMap | Steward's consensus/disagreement extraction |
| Frame challenge | The cognition lens's "is this the right question" check (Inside-Outsider in spirit) |
| DecisionRecord | Steward's synthesized decision with preserved dissent |
| Controller | Steward (process) |
| Chair | Steward (semantic synthesis) |
| Blind review / anonymity | Not implemented (identities visible) |
| Version lineage / best-checkpoint | Not implemented |
| Capability estimation / outcome feedback | Not implemented |

Note: this binding collapses Controller and Chair into the Steward. For a low-round, human-in-the-loop design review this is acceptable, but it does not satisfy the protocol's `council:L3` separation of Controller and Chair authorities.

## 7. What this evidence supports

- Same-runtime, same-model-family sub-agents with genuinely different role obligations can produce useful independent design review.
- Convergence of independent role lenses on the same structural weakness is a high-value correction signal for protocol-level changes.
- A cognition/framing lens can act as an Inside-Outsider frame check that a purely architecture/debugging panel would miss.
- Reserving the Council for design judgment (and using plain delegation for execution) keeps the cost/benefit favorable.

## 8. What it does not establish

- That role prompts remove the shared blind spots of one model family — convergence here reduces *role-specific* blind spots, not *model-family* blind spots (the panel is correlated; `independence_group` is shared).
- Complete `council:L0` conformance: reviewers did not produce independent CandidateArtifacts under the protocol schema.
- Anything at `council:L1`+: no anonymized peer review, no scored aggregation, no version lineage, no deterministic terminal states, no capability history, no delayed outcome measurement.
- That three lenses are the optimal panel for every decision.

## 9. Reusable lessons

1. Give lenses different *obligations*, not different adjectives — architecture/cognition/debugging carve genuinely different failure surfaces.
2. Treat independent convergence as the payoff signal; treat homogeneous agreement within one model family as correlated, not corroborated.
3. Keep a framing/cognition lens on the panel; it is the cheapest guard against solving the wrong problem well.
4. Reserve the Council for design decisions; route execution through plain Steward delegation.
5. Collapsing Controller and Chair into the Steward is fine at low rounds; separate them before adding revision loops or budgets.

## 10. Local binding record

```yaml
binding_id: kiro-local-council
protocol: council
protocol_version: 0.1.0
level_claim: none
mapped_components:
  - council:L0 isolated role outputs
  - council:L0 conflict extraction
  - council:L0 decision synthesis
storage_or_runtime: same-runtime sub-agents inside one Kiro CLI Steward
artifact_locations:
  - Steward-held goal brief and synthesized decision (in-context)
  - version-controlled participant dispatch guide
deviations:
  - reviewers are not anonymized (identities visible to the Steward/Chair)
  - Controller and Chair are the same agent (the Steward)
  - no revision lineage, deterministic controller, capability history, or outcome feedback
validation:
  checklist_completed:
    - initial role outputs generated independently without peer anchoring
    - reviewers identify concrete structural issues, not only preferences
    - conflicts are extracted rather than flattened into consensus
    - final output preserves disagreement
    - same-model sub-agents used; no false model-diversity claim
  evidence: field-tested
  conformance: mapped
  gaps:
    - independent CandidateArtifacts required for complete council:L0
    - anonymized peer review (council:L1)
    - version lineage / best-checkpoint (council:L2)
    - deterministic controller with terminal states (council:L3)
    - contextual capability estimation (council:L4)
    - delayed outcome feedback (council:L5)
last_reviewed: 2026-07-20
```
