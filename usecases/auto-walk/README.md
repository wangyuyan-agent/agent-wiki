# usecases/auto-walk/

Practical Auto-Walk implementations.

These use cases correspond to the general design in [Agent-first Auto-Walk Architecture](../../docs/agent-first-auto-walk.md).

Use this directory for concrete walk runners, hypothesis pools, surfacing wiring, and operational pitfalls discovered in real environments.

## Current use cases

- [Kiro Local Walk](kiro-local-walk.md) — evidence `field-tested`, conformance `partially-verified`; historical retired Auto-Walk binding with one calendar-aligned scheduled firing observed and `auto-walk:L4` still unverified.
- [Obsidian Notes Walk](obsidian-notes-walk.md) — evidence `design-example`, conformance `proposed`; standalone Auto-Walk over a Markdown notes vault.
- [Reading Queue Walk](reading-queue-walk.md) — evidence `design-example`, conformance `proposed`; standalone Auto-Walk over a daily digest of articles.
- [Research Corpus Walk](research-corpus-walk.md) — evidence `design-example`, conformance `proposed`; standalone Auto-Walk over a mixed research corpus.

Each use case is independent. Pick whichever binding matches the corpora you already have.
