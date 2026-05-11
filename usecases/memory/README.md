# usecases/memory/

Practical memory-system implementations.

These use cases correspond to the general design in [Agent-first Memory Architecture](../../docs/agent-first-memory.md).

Use this directory for concrete memory architectures, deployment stories, automation patterns, and operational pitfalls discovered in real environments.

## Current use cases

- [Kiro Local Memory](kiro-local-memory.md) — Local `.kiro/memories` architecture with archive, autodream, index, symlinked dotfiles storage, and launchd automation.
- [OpenAB + Codex + k3s Memory](openab-codex-k3s-memory.md) — Containerized memory architecture for long-running OpenAB/Codex agents on k3s.
