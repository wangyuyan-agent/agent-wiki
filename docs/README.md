# docs/

General design documents and reusable principles for LLM/Agent systems.

Use this directory for documents that answer:

- What is the mechanism?
- What are the design principles?
- How should agents reason about this pattern across tools and runtimes?
- What protocol should an agent follow when implementing this pattern elsewhere?

`docs/` is intentionally flat at the beginning. Create subdirectories only when several real documents accumulate around the same topic.

## Current documents

- [Agent-first Memory Architecture](agent-first-memory.md) — Portable memory mechanism and implementation protocol for LLM agents.
- [Agent-first Auto-Walk Architecture](agent-first-auto-walk.md) — Portable exploratory association mechanism that runs over consolidated memory or any structured corpus, generating weak hypotheses without mutating stable memory.

## Related use cases

- [Memory use cases](../usecases/memory/README.md) — Practical implementations of the memory architecture.
- [Auto-Walk use cases](../usecases/auto-walk/README.md) — Practical implementations of Auto-Walk.
