# usecases/memory/

Practical memory-system implementations.

These use cases correspond to the general design in [Agent-first Memory Architecture](../../docs/agent-first-memory.md).

Use this directory for concrete memory architectures, deployment stories, automation patterns, and operational pitfalls discovered in real environments.

## Current use cases

- [Kiro Local Memory](kiro-local-memory.md) — evidence `field-tested`, conformance `mapped`; local `.kiro/memories` lifecycle with a declared migration gap to the current item schema.
- [OpenAB + Codex + k3s Memory](openab-codex-k3s-memory.md) — evidence `field-tested`, conformance `mapped`; containerized lifecycle with declared current-schema gaps.
