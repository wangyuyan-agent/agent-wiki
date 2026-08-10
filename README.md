# agent-wiki

`agent-wiki` is an agent-first docs/wiki knowledge base for LLM and Agent systems.

It records practical documents, design notes, use cases, and operational lessons discovered while working with agents such as Kiro, Codex, Claude Code, Gemini, OpenCode, OpenAB, and future agent runtimes.

The primary reader is an **LLM/Agent**. Humans are maintainers and reviewers, but documents should be structured so agents can reliably retrieve, understand, and reuse them.

## Positioning

This repository is not a pre-filled taxonomy, not a generic note dump, and not a raw chat archive.

Documents are added when real practice or a clearly bounded design discussion produces reusable knowledge, for example:

- A design pattern becomes clear.
- An operational pitfall is discovered.
- A workflow is repeated enough to document.
- An agent memory or steering mechanism is refined.
- A deployment or integration use case becomes reusable.

The structure should grow organically from practice and clearly bounded design work.

Design work MUST declare `design-only` maturity and MUST NOT present proposed behavior as observed behavior. A protocol becomes `practiced` or `field-tested` only when its header names the supporting evidence scope.

## If you are an Agent, start here

1. Read [`protocols.yaml`](protocols.yaml), not every document.
2. Follow the [Agent Adoption Guide](docs/agent-adoption-guide.md) to select one protocol and its minimum binding.
3. Read the selected protocol completely before claiming conformance.
4. Read one matching use case and respect its evidence label.
5. Read [Composable Agent Cognition Protocols](docs/composable-agent-cognition.md) only when two or more protocols need to exchange artifacts.

Protocol maturity:

| Maturity | Meaning |
| --- | --- |
| `design-only` | Coherent proposal; no documented binding evidence yet. |
| `practiced` | At least one concrete binding or run informed the protocol; not every level is validated. |
| `field-tested` | The declared core has repeated real-environment evidence and operational feedback. |

Maturity calibrates evidence. It is not a ranking of importance.

## Structure

```text
agent-wiki/
├── README.md
├── LICENSE
├── protocols.yaml
├── docs/
│   ├── README.md
│   ├── agent-adoption-guide.md
│   ├── agent-first-memory.md
│   ├── agent-first-auto-walk.md
│   ├── agent-first-skill-lifecycle.md
│   ├── agent-first-active-workspace.md
│   ├── agent-first-inner-speech.md
│   ├── agent-first-council.md
│   ├── agent-first-steward.md
│   ├── governed-shared-memory-profile.md
│   ├── governed-artifact-portability-recovery.md
│   ├── governed-artifact-replication-exchange.md
│   └── composable-agent-cognition.md
└── usecases/
    ├── README.md
    ├── memory/
    │   ├── README.md
    │   ├── kiro-local-memory.md
    │   └── openab-codex-k3s-memory.md
    ├── auto-walk/
    │   ├── README.md
    │   ├── kiro-local-walk.md
    │   ├── obsidian-notes-walk.md
    │   ├── reading-queue-walk.md
    │   └── research-corpus-walk.md
    ├── skill/
    │   ├── README.md
    │   └── kiro-taobao-native.md
    ├── council/
    │   ├── README.md
    │   ├── multi-agent-roundtable.md
    │   ├── llm-council-local.md
    │   └── kiro-local-council.md
    └── steward/
        ├── README.md
        └── kiro-local-steward.md
```

## Content model

- `protocols.yaml` — Machine-readable routing index: ids, versions, maturity, level namespaces, artifacts, dependencies, and evidence.
- `LICENSE` — Repository license for original protocol, guide, and use-case text.
- `docs/` — General mechanisms, principles, and design documents.
- `usecases/` — Practical implementations, field reports, and explicitly labeled design examples.
- `usecases/memory/` — Real memory-system implementations that correspond to [Agent-first Memory Architecture](docs/agent-first-memory.md).
- `usecases/auto-walk/` — Real Auto-Walk implementations that correspond to [Agent-first Auto-Walk Architecture](docs/agent-first-auto-walk.md).
- `usecases/skill/` — Real imported or relationship-formed procedures mapped to [Agent-first Skill Lifecycle Architecture](docs/agent-first-skill-lifecycle.md).
- `usecases/council/` — Same-runtime role-diverse and heterogeneous-model bindings that correspond to [Agent-first Council Architecture](docs/agent-first-council.md).
- `usecases/steward/` — Real Steward `1:1:N` bindings that correspond to [Agent-first Steward Architecture](docs/agent-first-steward.md).

`docs/` starts flat on purpose. Add subdirectories only when a topic grows enough to justify structure.

`usecases/` may use small topic folders when multiple practical cases clearly belong together, such as `usecases/memory/`, `usecases/auto-walk/`, `usecases/skill/`, `usecases/council/`, and `usecases/steward/`.

## Current entry points

Start and routing:

- [Protocol manifest](protocols.yaml)
- [Agent Adoption Guide](docs/agent-adoption-guide.md)

Practiced protocols:

- [Agent-first Memory Architecture](docs/agent-first-memory.md) and [Memory use cases](usecases/memory/README.md)
- [Agent-first Auto-Walk Architecture](docs/agent-first-auto-walk.md) and [Auto-Walk use cases](usecases/auto-walk/README.md)
- [Agent-first Skill Lifecycle Architecture](docs/agent-first-skill-lifecycle.md) and [Skill Lifecycle use cases](usecases/skill/README.md)
- [Agent-first Council Architecture](docs/agent-first-council.md) and [Council use cases](usecases/council/README.md)
- [Agent-first Steward Architecture](docs/agent-first-steward.md) and [Steward use cases](usecases/steward/README.md)

Design-only protocols:

- [Agent-first Active Workspace Architecture](docs/agent-first-active-workspace.md)
- [Agent-first Inner Speech Architecture](docs/agent-first-inner-speech.md)

Advanced guides:

- [Composable Agent Cognition Protocols](docs/composable-agent-cognition.md)
- [Governed Shared Memory Composition Profile](docs/governed-shared-memory-profile.md)
- [Governed Artifact Portability and Recovery Guide](docs/governed-artifact-portability-recovery.md)
- [Governed Artifact Replication and Exchange Guide](docs/governed-artifact-replication-exchange.md)

## Writing rules

- Write for agents first.
- Prefer structured documents over prose dumps.
- Give every protocol a stable id, version, maturity, evidence scope, level namespace, and review date.
- Use qualified levels in cross-document references, such as `memory:L5` rather than bare `L5`.
- Give every use case a structured evidence label and explicit validation scope.
- State what the declared evidence supports and what it does not establish.
- Treat closed vocabulary tokens and their normative meanings in `protocols.yaml` as canonical. Reader-facing summaries MAY repeat them for local comprehension, but MUST preserve the same tokens and MUST be updated in the same change as the manifest.
- Include context, source dates, and provenance when useful.
- Do not commit secrets, credentials, or raw chat logs.
- Avoid placeholder files.
- Add documents when practice or clearly bounded design work produces reusable knowledge.
- Keep indexes and README files as navigation, not content dumps.

## Source of authority

- `protocols.yaml` is the canonical routing index for protocol ids, versions, maturity labels, shared vocabularies, and document locations.
- Each protocol document is authoritative for that protocol's semantics, invariants, schemas, and conformance rules.
- Use cases are evidence and binding guidance. They do not redefine the protocol they reference.
- A conflict between the manifest and a document is a repository defect. An Agent MUST surface it rather than guessing which version to implement.

## License

Except where otherwise noted, the original content of this repository is licensed under the [Creative Commons Attribution 4.0 International License](LICENSE) (`CC-BY-4.0`). You may share and adapt it, including commercially, with appropriate attribution and an indication of changes.

A useful attribution is: `agent-wiki contributors, agent-wiki, CC BY 4.0`, plus a link to the material and a note describing modifications.

Inline citations and source links identify third-party material or prior reports used as evidence. Those materials, product names, and trademarks remain subject to their own terms and are not relicensed merely because they are referenced here.
