# usecases/memory/

Practical memory-system implementations.

These use cases correspond to the general design in [Agent-first Memory Architecture](../../docs/agent-first-memory.md).

Use this directory for concrete memory architectures, deployment stories, automation patterns, and operational pitfalls discovered in real environments.

## Current use cases

- [Kiro Local Memory](kiro-local-memory.md) — evidence `field-tested`, conformance `mapped`; historical retired local lifecycle with a declared migration gap to the current item schema and a supervisor-green/semantic-failure lesson.
- [OpenAB + Codex + k3s Memory](openab-codex-k3s-memory.md) — evidence `field-tested`, conformance `mapped`; containerized lifecycle with declared current-schema gaps.
- [Failed Exploration Withdrawal](failed-exploration-withdrawal.md) — evidence `run-reported`, conformance `mapped`; one private interrupted exploration exposed the need to distinguish task closure, code effects, reversible Memory withdrawal, and authorized erasure without claiming that any durable item or mutation was independently verified.
