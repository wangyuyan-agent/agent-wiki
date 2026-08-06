# docs/

General design documents and reusable principles for LLM/Agent systems.

Use this directory for documents that answer:

- What is the mechanism?
- What are the design principles?
- How should agents reason about this pattern across tools and runtimes?
- What protocol should an agent follow when implementing this pattern elsewhere?

`docs/` is intentionally flat at the beginning. Create subdirectories only when several real documents accumulate around the same topic.

## Current documents

Start here:

- [Agent Adoption Guide](agent-adoption-guide.md) — Low-context protocol selection, reading order, minimal bindings, and bootstrap record.
- [Protocol manifest](../protocols.yaml) — Machine-readable versions, maturity, level namespaces, dependencies, artifacts, and evidence.

Practiced protocols:

- [Agent-first Memory Architecture](agent-first-memory.md) — `practiced`; portable memory mechanism and implementation protocol for LLM agents.
- [Agent-first Auto-Walk Architecture](agent-first-auto-walk.md) — `practiced`; exploratory association over consolidated memory or any structured corpus.
- [Agent-first Skill Lifecycle Architecture](agent-first-skill-lifecycle.md) — `practiced`; imported and relationship-formed procedural artifacts share evidence-, authority-, version-, and rollback-aware lifecycle rules.
- [Agent-first Council Architecture](agent-first-council.md) — `practiced`; single-agent and multi-agent deliberation, revision, evaluation, and termination.
- [Agent-first Steward Architecture](agent-first-steward.md) — `practiced`; the `1:1:N` relationship and coordination protocol.

Design-only protocols:

- [Agent-first Active Workspace Architecture](agent-first-active-workspace.md) — `design-only`; short-lived, source-aware task state for calibrating current attention.
- [Agent-first Inner Speech Architecture](agent-first-inner-speech.md) — `design-only`; bounded runtime self-guidance, including the Inside-Outsider stance.

Advanced:

- [Composable Agent Cognition Protocols](composable-agent-cognition.md) — `design-only`; composition rules for explicit artifact exchange. Read after selecting two or more protocols.
- [Governed Shared Memory Composition Profile](governed-shared-memory-profile.md) — `design-only`; perspective-preserving shared standing over existing artifacts with declared audience and admission authority.

## Related use cases

- [Memory use cases](../usecases/memory/README.md) — Practical implementations of the memory architecture.
- [Auto-Walk use cases](../usecases/auto-walk/README.md) — Practical implementations of Auto-Walk.
- [Skill Lifecycle use cases](../usecases/skill/README.md) — Imported and relationship-formed procedures with explicit lifecycle evidence and gaps.
- [Council use cases](../usecases/council/README.md) — Same-runtime sub-agent and heterogeneous-model Council bindings.
- [Steward use cases](../usecases/steward/README.md) — Real `1:1:N` Steward bindings coordinating participants and managed resources.
