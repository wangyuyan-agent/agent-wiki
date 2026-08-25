# usecases/council/

Concrete bindings of [Agent-first Council Architecture](../../docs/agent-first-council.md) at different evidence levels.

Council use cases differ in execution topology, model diversity, number of rounds, aggregation policy, and runtime surface. Each case must state what was observed and what remains a protocol-level proposal.

## Current use cases

- [Multi-Agent Roundtable](multi-agent-roundtable.md) — evidence `run-reported`, conformance `mapped`; same-runtime sub-agents execute role-diverse proposal, blind review, targeted follow-up, and synthesis rounds.
- [Local LLM Council](llm-council-local.md) — evidence `source-inspected`, conformance `mapped`; early heterogeneous-model service implementation with three fixed stages, API/SSE/SDK surfaces, and optional Elo history.
- [Kiro Local Council](kiro-local-council.md) — evidence `field-tested`, conformance `mapped`; historical retired same-runtime, same-model-family role-diverse design review covering selected `council:L0` mechanisms, without independent CandidateArtifacts or anonymized peer review.

These are independent bindings. None defines the Council protocol by itself.
