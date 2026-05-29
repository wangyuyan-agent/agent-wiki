# usecases/auto-walk/

Practical Auto-Walk implementations.

These use cases correspond to the general design in [Agent-first Auto-Walk Architecture](../../docs/agent-first-auto-walk.md).

Use this directory for concrete walk runners, hypothesis pools, surfacing wiring, and operational pitfalls discovered in real environments.

## Current use cases

- [Kiro Local Walk](kiro-local-walk.md) — Auto-Walk layered on a local `.kiro/memories` setup. The canonical memory-coupled binding.
- [Obsidian Notes Walk](obsidian-notes-walk.md) — Standalone Auto-Walk over a Markdown notes vault. Outputs walk reports for human reading.
- [Reading Queue Walk](reading-queue-walk.md) — Standalone Auto-Walk over a daily digest of articles (HN, papers, blogs).
- [Research Corpus Walk](research-corpus-walk.md) — Standalone Auto-Walk over a mixed research corpus (papers + CVEs + notes).

Each use case is independent. Pick whichever binding matches the corpora you already have.
