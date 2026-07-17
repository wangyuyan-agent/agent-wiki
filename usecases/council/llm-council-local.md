# Local LLM Council Use Case

- Use case ID: `council.llm-council-local`
- Protocol: `council@0.1.0`
- Evidence: `source-inspected`
- Conformance: `mapped` — source structure was mapped to the protocol; runtime conformance was not assessed
- Validation scope: source structure only; runtime/API behavior was not validated
- Reproducibility: `private-source` — machine-specific source location and revision are intentionally omitted
- Level namespace: `council`
- Last reviewed: 2026-07-17

## 1. Context

This use case records an early local working copy named `llm-council`.

Source snapshot reviewed on 2026-07-15:

```text
source: local working copy (machine-specific path and revision omitted)
review method: source inspection
runtime/API validation in this review: not performed
```

The repository describes itself as an independent multi-model collaboration and decision infrastructure service. It predates the fuller Council protocol and should be understood as an early executable expression of the idea, not its final architecture.

It is a practical fixed-stage profile of [Agent-first Council Architecture](../../docs/agent-first-council.md).

## 2. Implemented topology

```text
Client
  → HTTP API / Python SDK
  → CouncilEngine
      → model adapters through OpenRouter-compatible API
      → Stage 1 independent opinions
      → Stage 2 anonymous cross-review + Borda aggregation
      → Chair selection
      → Stage 3 synthesis
      → optional Elo update
  → response or SSE event stream
```

The implementation includes:

- FastAPI routes;
- synchronous and asynchronous Python SDK clients;
- SSE progress events;
- OpenRouter-compatible model adapters;
- DSPy structured-output paths with raw-prompt fallback;
- in-memory or Redis Elo storage;
- model-version Elo inheritance policies;
- Docker deployment files and a demo UI.

## 3. Fixed three-stage profile

### Stage 1: independent opinions

Configured models answer the same question in parallel. Each `CouncilOpinion` carries:

- model id;
- anonymous label;
- opinion text;
- key points;
- reasoning-step field when structured output supplies it;
- self-reported confidence;
- latency.

The run requires at least two successful opinions.

### Stage 2: anonymous peer review

Each model reviews other models' opinions and excludes its own. The review returns:

- anonymous-label ranking;
- consensus points;
- disagreement points.

Rankings are combined with Borda count into a model-id order.

The anonymous surface reduces direct model-name bias. The engine still retains the label-to-model mapping for aggregation and audit.

### Stage 3: Chair synthesis

The selected Chair receives:

- opinion summaries;
- aggregated ranking;
- collected consensus points;
- collected disagreement points.

It returns:

- final decision;
- incorporated opinions;
- rejected opinions;
- optional reasoning field and latency.

The raw fallback prompt asks the Chair to explain rejected views, but the fallback cannot always populate the structured incorporated/rejected lists.

## 4. Current artifact model

The implementation's main data classes map as follows:

| Local object | General protocol analogue |
| --- | --- |
| `CouncilOpinion` | CandidateArtifact v1 |
| `CouncilReview` | ReviewArtifact, with ranking/consensus/disagreement |
| `CouncilResult` | Partial DecisionRecord + RunRecord summary |
| aggregated ranking | Run aggregation output |
| Chair model id | ChairSelectionPolicy result |
| Elo update | Longitudinal capability/reputation signal |

The local objects are intentionally simpler than the general schemas. They do not yet carry GoalContract revisions, candidate lineage, issue-level review responses, conflict types, terminal-state reasons, or delayed outcomes.

## 5. Diversity profile

This binding is designed for heterogeneous configured models:

```yaml
diversity_profile:
  role_diversity:
    stage1: proposer
    stage2: reviewer
    stage3: chair
  model_diversity: configurable list
  context_isolation: per API call/stage
  information_diversity: common user question/context
  method_diversity: mostly model-family differences
```

The same model participates in different roles across stages, but the implementation does not create several simultaneous role-specialized sub-agents from one model. A future binding could add that topology without changing the general protocol.

## 6. Elo and model inheritance

The implementation maintains Elo by `task_type` and updates it from the current Borda-derived ranking. New models have an observation period and larger K factor.

It also contains explicit version-inheritance policies:

- minor update: full inheritance with a shorter observation period;
- major update: partial regression toward the initial rating;
- new series: smaller inheritance;
- unrelated model: fresh initial rating.

This is a useful experiment in longitudinal capability tracking, but it exposes why Elo must remain an optional adapter:

1. The update signal is peer ranking, not external outcome.
2. Proposer, reviewer, and synthesizer capability are not independently estimated by the main run path.
3. A task-type label is broader than a complete domain/role/tool context.
4. Repeated peer preference may create a self-reinforcing reputation loop.
5. Model behavior may change without a clean version-lineage relation.

The protocol therefore retains the experiment while separating:

```text
current artifact evaluation
current run aggregation
historical capability estimation
delayed outcome evaluation
```

## 7. Chair selection boundary

The source contains a three-level intended policy:

1. current-run rank;
2. historical Elo as a tie-breaker;
3. rotation if Elo also ties.

At the reviewed snapshot, the main `select_chairman` path selects the first aggregated model and contains a TODO for precise Borda tie detection. A separate tie-break helper exists but is not wired into that simplified main selection path.

This is implementation evidence for a protocol lesson:

> Chair selection must be an explicit replaceable policy, and documentation should distinguish intended policy from the behavior of the current binding.

The general protocol also allows a dedicated synthesizer that did not author the top candidate.

## 8. Service surfaces

The binding exposes Council as infrastructure:

- `POST /api/v1/council/vote`
- streaming vote endpoint/events;
- model listing;
- Elo leaderboard and per-model rating endpoints;
- sync/async SDK methods;
- health endpoint.

These are binding concerns. The Council protocol does not require HTTP, SSE, Redis, DSPy, Docker, or OpenRouter.

## 9. What the inspected source structure demonstrates

From source inspection:

1. The code contains a provider-neutral registry and paths intended to invoke several configured models.
2. Independent proposal and anonymous cross-review are represented with small structured objects.
3. API, SDK, and stream adapters target the same fixed three-stage engine.
4. Explicit error/degraded paths exist for individual model failure and minimum-quorum loss.
5. Aggregation, storage, provider, and synthesis concerns are separated into modules.
6. Historical model-version rating experiments are represented alongside current-run deliberation.

These are structural observations, not runtime guarantees. The validation needs in §13 remain open.

## 10. What remains outside this snapshot

The reviewed implementation does not yet implement the fuller ideas developed after it:

- GoalContract and explicit success criteria;
- multi-round targeted revision;
- candidate version lineage and best-checkpoint rollback;
- marginal-gain, plateau, regression, or oscillation control;
- structured conflict taxonomy;
- Inside-Outsider frame challenge;
- deterministic run terminal states beyond success/error;
- role/domain-specific capability uncertainty;
- delayed external outcome feedback;
- Pareto or non-ranking decision modes;
- same-model parallel role-specialized sub-agents.

These are not defects relative to the original experiment. They mark the distance between an early binding and the now broader protocol.

## 11. Failure behavior

Observed from the source structure:

- Fewer than two model adapters/opinions returns an error state.
- Individual Stage 1 or Stage 2 failures are logged and omitted.
- DSPy Stage 3 failure degrades to a raw provider call.
- Final Stage 3 provider failure returns a synthesized error string/result.
- Streaming mode emits explicit error events.

Future high-risk bindings should add:

- per-role quorum, not only total opinion count;
- missing-perspective disclosure;
- controller-owned stage timeouts actually enforced end to end;
- abstention when remaining artifacts are materially incomplete;
- best-checkpoint return on late-stage failure.

## 12. Evolution path

A protocol-aligned evolution could proceed without a rewrite:

```text
Current CouncilOpinion
  → add CandidateArtifact ids and lineage

Current CouncilReview
  → add issue-level evidence, severity, and revision request

Current CouncilResult
  → split DecisionRecord from RunRecord

Fixed engine flow
  → Controller state machine with profiles

Borda/Elo hard wiring
  → AggregationPolicy + CapabilityEstimator + OutcomeEvaluator interfaces

Model list
  → CouncilMember descriptors and independence groups
```

The existing three-stage behavior can remain a `quick-three-stage` profile while richer runs opt into revision and outcome feedback.

## 13. Validation needs before claiming runtime conformance

This document was produced by source inspection, so a future runtime validation should verify:

1. At least two real configured models complete all three stages.
2. Reviewers never receive their own opinion.
3. Anonymous labels remain stable and unique.
4. Borda aggregation includes every valid reviewed candidate.
5. Actual Chair selection matches the documented policy, including ties.
6. SSE and non-streaming runs return equivalent final artifacts.
7. Redis and memory storage preserve rating semantics.
8. Provider failure produces the intended degraded state.
9. Re-running a task does not corrupt rating history.
10. Model-version inheritance is exercised with real predecessor mappings.

## 14. Reusable lessons

1. An early service implementation is valuable evidence but should not define the protocol ontology.
2. Fixed stages are a useful profile, not a universal lifecycle.
3. Anonymity and provenance must coexist.
4. Peer ranking and real-world success are different signals.
5. Historical reputation must remain contextual and uncertain.
6. Chair selection is a separate capability/policy from answer ranking.
7. Provider, storage, aggregation, and transport adapters belong to bindings.
8. Protocol evolution can preserve the simple API while enriching internal artifacts and control.
