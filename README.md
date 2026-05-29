# agent-wiki

`agent-wiki` is an agent-first docs/wiki knowledge base for LLM and Agent systems.

It records practical documents, design notes, use cases, and operational lessons discovered while working with agents such as Kiro, Codex, Claude Code, Gemini, OpenCode, OpenAB, and future agent runtimes.

The primary reader is an **LLM/Agent**. Humans are maintainers and reviewers, but documents should be structured so agents can reliably retrieve, understand, and reuse them.

## Positioning

This repository is not a pre-filled taxonomy, not a generic note dump, and not a raw chat archive.

Documents are added when real practice produces reusable knowledge, for example:

- A design pattern becomes clear.
- An operational pitfall is discovered.
- A workflow is repeated enough to document.
- An agent memory or steering mechanism is refined.
- A deployment or integration use case becomes reusable.

The structure should grow organically from practice.

## Structure

```text
agent-wiki/
├── README.md
├── docs/
│   ├── README.md
│   ├── agent-first-memory.md
│   └── agent-first-auto-walk.md
└── usecases/
    ├── README.md
    ├── memory/
    │   ├── README.md
    │   ├── kiro-local-memory.md
    │   └── openab-codex-k3s-memory.md
    └── auto-walk/
        ├── README.md
        ├── kiro-local-walk.md
        ├── obsidian-notes-walk.md
        ├── reading-queue-walk.md
        └── research-corpus-walk.md
```

## Content model

- `docs/` — General mechanisms, principles, and design documents.
- `usecases/` — Practical implementations, deployment stories, integration notes, and lessons learned from real environments.
- `usecases/memory/` — Real memory-system implementations that correspond to [Agent-first Memory Architecture](docs/agent-first-memory.md).
- `usecases/auto-walk/` — Real Auto-Walk implementations that correspond to [Agent-first Auto-Walk Architecture](docs/agent-first-auto-walk.md).

`docs/` starts flat on purpose. Add subdirectories only when a topic grows enough to justify structure.

`usecases/` may use small topic folders when multiple practical cases clearly belong together, such as `usecases/memory/` and `usecases/auto-walk/`.

## Current entry points

- [Agent-first Memory Architecture](docs/agent-first-memory.md)
- [Memory use cases](usecases/memory/README.md)
- [Agent-first Auto-Walk Architecture](docs/agent-first-auto-walk.md)
- [Auto-Walk use cases](usecases/auto-walk/README.md)

## Writing rules

- Write for agents first.
- Prefer structured documents over prose dumps.
- Include context, source dates, and provenance when useful.
- Do not commit secrets, credentials, or raw chat logs.
- Avoid placeholder files.
- Add documents when practice produces reusable knowledge.
- Keep indexes and README files as navigation, not content dumps.
