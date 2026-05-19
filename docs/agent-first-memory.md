# Agent-first LLM Memory Architecture

## 1. Purpose

This document defines a portable memory mechanism for LLM agents.

It is intended for agents such as Kiro, Codex, Claude Code, Gemini, OpenCode, OpenAB-hosted agents, Copilot-like agents, and future agent runtimes. The design assumes only that the agent can read persistent instructions and, ideally, read/write files.

The goal is not to store more text. The goal is to give agents a safe lifecycle for memory:

```text
Capture → Archive → Distill → Index → Retrieve → Review
```

In operational terms:

```text
Collect during work → preserve raw snapshots → distill with AI → maintain a wiki index → retrieve on demand → audit explicitly
```

## 2. Design goals

A good agent memory system should:

1. Preserve useful context across sessions, restarts, rollouts, and machines.
2. Keep always-loaded instructions small and behavior-oriented.
3. Separate short-term notes, long-term knowledge, and raw evidence.
4. Let agents retrieve only the memory that is relevant to the task.
5. Support automatic maintenance without trusting automation to delete knowledge silently.
6. Preserve enough source context to audit how a memory was created.
7. Work across different agent products by mapping the same protocol onto each product's native instruction and workflow mechanisms.

## 3. Non-goals

This architecture is not:

- A raw chat archive.
- A replacement for source control, logs, issue trackers, or project docs.
- A place to store secrets or credentials.
- A guarantee that all memories are true forever.
- A system where AI can freely delete or rewrite long-term knowledge without review.
- A single fixed directory layout that every platform must copy exactly.

The protocol matters more than the exact filenames.

## 4. Core model

Agent memory has three layers and one lifecycle.

### Layers

```text
Hot    = always loaded; controls behavior (steering + conventions)
Warm   = triggered on demand; provides task context
Cold   = searched or audited; preserves evidence
```

### Lifecycle

```text
Inbox captures.
Archive preserves.
Autodream distills.
Index navigates.
Topics retain knowledge.
Conventions stabilize rules.
Review corrects drift.
```

## 5. Steering vs conventions vs memory

Separate instructions, rules, and memories.

```text
Steering / Instructions = WHAT / HOW (system-level directives, identity, capabilities)
Conventions / Rules     = WHAT IS ALWAYS TRUE (stable behavioral rules, workflow mandates)
Memory / Knowledge      = WHAT HAPPENED / WHAT WE LEARNED (dynamic experience)
```

The three layers have different change frequencies:

| Layer | Changes when | Examples |
| --- | --- | --- |
| Steering | Agent identity or capabilities change | Persona definition, tool permissions, response style |
| Conventions | A new stable rule is established | "NIT is mandatory", "always use wangyuyan-agent for commits", security policies |
| Memory | Every session with new learnings | "k3s ConfigMap was read-only", "kiro-pool needs symlink fix" |

Examples:

| Belongs in steering | Belongs in conventions | Belongs in memory |
| --- | --- | --- |
| When the user says "remember", append a note to `memory.md`. | Git identity defaults to `wangyuyan-agent`. | On 2026-05-11, ConfigMap-mounted `AGENTS.md` was found to be read-only in k3s. |
| Read `memory/index.md` before touching prior decisions. | All agent-wiki commits must pass sensitive info scan. | The OpenAB + Codex deployment stores mutable memory on PVC. |
| Do not store raw chat logs. | NIT findings require fixes before approve. | A previous rollout failed because `KUBECONFIG` was only set in a shell profile. |

Promotion path:

```text
Memory (observed once) → Conventions (confirmed stable rule) → Steering (changes agent behavior)
```

Do not promote one incident into a convention. Put experience into memory first; promote to conventions only after repeated confirmation or explicit user decision. Promote to steering only if it changes the agent's fundamental behavior.

## 6. Hot / Warm / Cold decision tree

Use this decision tree for any candidate instruction or memory item:

```text
If this is not loaded, will the agent's next response or action likely be wrong?
│
├─ Yes, for almost every task
│  → Hot steering / hot entry
│
├─ Yes, but only for a specific task, path, domain, or workflow
│  → Warm context with a clear trigger
│
└─ No, it is historical, evidential, or reference material
   → Cold storage
```

Rules of thumb:

- If it changes what the agent must do on every relevant task, keep it Hot.
- If it has a clear trigger and is longer than roughly 1KB, keep only the trigger in Hot and the body in Warm.
- If it is mostly history, raw evidence, or rationale, keep it Cold.
- If no trigger points to it, a Warm topic effectively becomes Cold.

## 7. Portable directory structure

A full implementation can use this shape:

```text
<agent-home>/
├── AGENTS.md / CLAUDE.md / GEMINI.md / steering/*
└── memory/
    ├── README.md
    ├── conventions.md
    ├── memory.md
    ├── log.md
    ├── index.md
    ├── archive/
    │   └── YYYY-MM-DD.md
    ├── topics/
    │   ├── user-preferences.md
    │   ├── environment.md
    │   ├── workflows.md
    │   ├── decisions.md
    │   ├── operational-pitfalls.md
    │   └── memory-system-design.md
    └── scripts/
        └── archive-memory.sh
```

Minimal implementation:

```text
<agent-home>/
├── AGENTS.md / CLAUDE.md / GEMINI.md
└── memory/
    ├── conventions.md
    ├── memory.md
    ├── index.md
    └── topics/
```

## 8. File responsibilities

### Hot entry: `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` / steering files

The hot entry should only do four things:

1. Define identity and hard rules.
2. Point to the memory root.
3. Define when to read memory.
4. Define when to write memory.

It should not store short-term memory bodies or long historical explanations.

Example:

```md
## Memory Protocol

Memory root: `./memory`

Read memory when:
- The user asks about prior preferences, decisions, environment, or history.
- The task depends on previous setup or operational context.
- The user says "as before", "remember", "don't forget", or references past work.

Write memory when:
- The user explicitly says "remember", "don't forget", "from now on", or "this is my preference".
- A reusable operational pitfall, decision, workflow lesson, or stable environment fact is confirmed.

Retrieval order:
1. Read `memory/index.md`.
2. Read relevant `memory/topics/*.md`.
3. Read `memory/archive/*.md` only for audit or source tracing.
```

### Conventions: `memory/conventions.md`

`conventions.md` stores stable behavioral rules that rarely change.

It should be loaded as a Hot resource (via agent config/resources), not merely referenced from `index.md`. This ensures rules are always enforced regardless of context pressure.

Use it for:

- Identity and authentication rules (default git identity, credential sources).
- Security policies (sensitive info scanning before public commits).
- Workflow mandates (post-action checklists, PR review rules).
- Environment constraints (sandbox HOME behavior, SSH port conventions).
- Memory system rules (structure definitions, autodream constraints).

Do not use it for:

- One-time incidents or debugging experiences (those belong in memory/index).
- System-level identity or capability definitions (those belong in steering).
- Temporary preferences that may change.

Change frequency: low. Only updated when a new stable rule is established or an existing rule is revised. Autodream should never modify this file.

### Inbox: `memory/memory.md`

`memory.md` is a hot inbox, not the final knowledge base.

Use it for:

- User-stated preferences waiting for distillation.
- Stable environment facts that were just confirmed.
- Operational pitfalls discovered during work.
- Reusable conclusions that need later review.

Do not use it for:

- Full chat transcripts.
- Temporary feelings or speculation.
- Large logs.
- Final polished knowledge.

### Timeline: `memory/log.md`

`log.md` is an operations trace, not knowledge content.

It records events such as:

- bootstrap
- archive
- archive-skip
- autodream
- autodream-skip
- review
- cleanup
- manual-correction

### Index: `memory/index.md`

`index.md` is a wiki-style navigation and trigger index.

It should answer:

- Which topic should the agent read first?
- What recent activity matters?
- Which topics are active, stale, or pending cleanup?
- Where is the canonical source for a class of memory?

It should not become a second content dump.

### Topics: `memory/topics/*.md`

Topic pages are long-term distilled knowledge.

A topic is Warm if it has a reliable trigger from `index.md`. Otherwise it is Cold.

### Archive: `memory/archive/YYYY-MM-DD.md`

Archive files are Cold raw evidence.

They are used for:

- audit
- source tracing
- re-distillation
- recovery after bad summarization

They should not be loaded by default.

## 9. Memory item format

A memory item should be concise, source-aware, and reusable.

Recommended minimum format:

```md
- [YYYY-MM-DD] <distilled reusable fact or preference>. Source: <session/archive/topic if useful>.
```

Extended format for higher-risk items:

```md
- [YYYY-MM-DD] <fact>
  - Scope: <global | project | environment | workflow | user preference>
  - Status: <active | pending-confirmation | stale | 待清理>
  - Source: <archive/YYYY-MM-DD.md or conversation context>
  - Confidence: <confirmed | observed-once | inferred>
```

Examples:

```md
- [2026-05-11] In OpenAB + Codex on k3s, mutable `AGENTS.md` should live on PVC rather than a read-only ConfigMap. Source: archive/2026-05-11.md.
```

```md
- [2026-05-11] User prefers English responses, but may discuss architecture in Chinese.
  - Scope: user preference
  - Status: active
  - Source: explicit user preference
  - Confidence: confirmed
```

## 10. Index format

Recommended `memory/index.md` structure:

```md
# Memory Index

## Recent Activity

- [YYYY-MM-DD] Short summary → topics/example.md

## Topic Map

- user-preferences.md — Read when handling user style, language, personal preferences.
- environment.md — Read when working with local/project/deployment environment facts.
- workflows.md — Read when executing known SOPs.
- decisions.md — Read when checking previous architecture or product decisions.
- operational-pitfalls.md — Read when debugging recurring tool/deployment failures.
- memory-system-design.md — Read when modifying the memory system itself.

## Pending Cleanup

- [待清理] ...
```

Index rules:

- Keep it concise, ideally around 200 lines or less.
- Include topic paths and trigger descriptions.
- Keep recent activity short, for example the latest 10 items.
- Do not paste archive content back into the index.
- Mark stale items as `[待清理]` instead of deleting automatically.

## 11. Topic page format

Recommended topic page frontmatter:

```md
---
title: Operational Pitfalls
layer: warm
triggers:
  - k3s troubleshooting
  - OpenAB deployment
  - kubectl cannot connect
  - CronJob failed
last_updated: YYYY-MM-DD
source_dates:
  - YYYY-MM-DD
---
```

Recommended body:

```md
# Operational Pitfalls

## Summary

One or two paragraphs that tell the agent when this topic matters.

## Facts and lessons

- [YYYY-MM-DD] Distilled reusable fact with source date.

## Pending cleanup

- [待清理] Item that may be stale.
```

## 12. Capture protocol

Write memory when the user explicitly says:

- remember
- don't forget
- from now on
- this is my preference
- 记住
- 不要忘了
- 以后都这样
- 这是我的偏好

Also write memory when a reusable operational pitfall, decision, workflow lesson, tool constraint, or stable environment fact is confirmed.

Capture rules:

1. Compress the content into a reusable conclusion.
2. Append it to `memory/memory.md` first.
3. Include date and source when useful.
4. Do not copy full chat logs.
5. Do not treat one-time emotion as long-term knowledge.
6. Do not overwrite old knowledge directly.
7. Prefer add-first, cleanup-later.

## 13. Archive protocol

Archive should be deterministic and should not require AI.

Steps:

1. Check whether `memory.md` has substantive content.
2. Move or append it to `archive/YYYY-MM-DD.md`.
3. Recreate a blank `memory.md` with a date header.
4. Append an archive entry to `log.md`.
5. Rotate long logs if needed.

Possible schedulers:

| Environment | Scheduler |
| --- | --- |
| macOS | launchd |
| Linux | systemd timer or cron |
| Kubernetes | CronJob |
| OpenAB | usercron shell pre-step |
| GitHub | scheduled workflow |
| Manual | agent command or skill |

The reason to archive before AI distillation is simple: raw memory should be preserved even if the agent fails, hallucinates, or produces a bad summary.

## 14. Autodream protocol

Autodream is the AI distillation stage.

Inputs:

- Today's archive
- Current `index.md`
- Relevant topic pages
- Memory protocol

Outputs:

- Updated `index.md`
- Updated `topics/*.md`
- `log.md` entry

Rules:

- Incremental only.
- Do not delete automatically.
- Mark obsolete items as `[待清理]`.
- Preserve source dates.
- Do not invent unsupported facts.
- Do not promote one-off incidents into universal rules.
- Keep the index concise.
- Split or update topics when useful.

Prompt template:

```md
You are maintaining an agent memory system.

Read:
- `memory/archive/{{date}}.md`
- `memory/index.md`
- relevant `memory/topics/*.md`

Tasks:
1. Extract only long-term reusable knowledge.
2. Update `memory/index.md` as a navigation index, not a full summary.
3. Update or create topic pages when needed.
4. Preserve source dates.
5. Do not delete existing knowledge. Mark stale items as `[待清理]`.
6. Do not invent facts not supported by archive.
7. Do not turn one-time incidents into permanent rules unless explicitly confirmed.
8. Keep `index.md` concise.
9. Append an autodream entry to `memory/log.md`.
```

## 15. Retrieval protocol

Retrieval order:

```text
1. Hot instruction file
2. memory/index.md
3. Relevant memory/topics/*.md
4. memory/archive/*.md only for audit or source tracing
```

Agents should not read all memory by default.

Read memory when:

- The task references previous work.
- The user says “as before” or asks about prior decisions.
- The task touches known environment or workflow areas.
- The agent needs user preferences.
- The task is a memory review, migration, or debugging task.

Do not read memory when:

- The task is self-contained.
- Memory is unlikely to change the answer.
- The only available memory is raw archive and there is no audit need.

## 16. Review protocol

A manual `review memory` workflow should:

1. Check whether `index.md` is too long.
2. Inspect `[待清理]` and `[待确认]` items.
3. Find duplicate or conflicting topic entries.
4. Check steering/memory boundary violations.
5. Check whether archive files were not distilled.
6. Verify source dates.
7. Identify missing triggers for important topics.
8. Propose cleanup before deleting anything.

Review should produce a plan before destructive changes.

## 17. Promotion path

Memory items can be promoted through layers as they prove stable:

```text
Memory → Conventions → Steering
```

### Memory → Conventions

Promote when a memory item becomes a stable behavioral rule.

Criteria:

- The rule applies across future sessions.
- It has been confirmed by repeated experience or explicit user decision.
- It is not merely historical context.
- It is a "what is always true" statement, not a "what happened once" statement.

### Conventions → Steering

Promote when a convention changes the agent's fundamental identity or capabilities.

Criteria:

- The rule changes what the agent must do on every task.
- It defines identity, persona, or capability boundaries.
- It belongs in the always-loaded hot entry.

### Do not promote

- One-off incidents.
- Unverified guesses.
- Temporary preferences.
- Environment-specific facts that only matter in one project.

### Process

1. Identify the memory item and source date.
2. Rewrite it as a stable rule (for conventions) or WHAT/HOW behavior (for steering).
3. Add it to the appropriate file.
4. Leave a pointer or note in memory if useful.
5. Remove or mark duplicate wording to avoid contradiction.

## 18. Failure modes

| Failure mode | Symptom | Prevention |
| --- | --- | --- |
| Hot memory bloat | Agent ignores critical rules | Keep Hot short; move bodies to Warm |
| Raw chat archive | Memory becomes unreadable | Capture distilled conclusions only |
| Index becomes content dump | Agent cannot find triggers | Keep index as navigation |
| Topic without trigger | Topic is never read | Add trigger in index |
| AI deletes useful knowledge | Lost memory | Additive autodream; mark stale before deletion |
| One incident becomes permanent rule | Overgeneralized behavior | Promote to steering only after review |
| Archive not distilled | Knowledge stays hidden | Log archive/autodream status |
| Duplicate rules | Contradictions | Single source of truth |
| Secrets in memory | Security leak | Never store credentials or tokens |

## 19. Agent-specific mapping

| Agent | Hot entry | Warm workflow | Memory root / notes |
| --- | --- | --- | --- |
| Kiro | `.kiro/steering/*` | scripts / launchd / wrappers | `~/.kiro/memories/` |
| Codex | `AGENTS.md` | `.codex/skills/*` | `memory/` |
| Claude Code | `CLAUDE.md` / `MEMORY.md` index | commands/hooks | `memory/` or topic files |
| Gemini | `GEMINI.md` / `MEMORY.md` index | scripts | `memory/` |
| Copilot | `.github/copilot-instructions.md` | path-specific instructions | repo docs/memory |
| OpenCode | `AGENTS.md` | custom commands/hooks | `memory/` |
| OpenAB-hosted agent | `AGENTS.md` or agent-specific entry | usercron / skills / CLI | persistent volume or mounted workspace |

The mapping can vary. The invariant is the protocol: Hot entry, inbox capture, raw archive, distilled topics, navigable index, explicit review.

## 20. Implementation levels

| Level | Name | Capability |
| --- | --- | --- |
| L0 | Manual memory | Agent writes `memory.md` when asked. |
| L1 | Structured memory | Adds `index.md`, `topics/`, `archive/`. |
| L2 | Scheduled archive | Raw inbox is archived automatically. |
| L3 | Autodream | AI distills archive into index/topics. |
| L4 | Review + validation | Explicit audit, cleanup, and fresh-session tests. |

A system can start at L0 and evolve. Do not block adoption on full automation.

## 21. Validation checklist

After implementing memory for an agent, verify:

1. A fresh session can locate the memory root.
2. The agent knows when to read `index.md`.
3. The agent can write a distilled note to `memory.md`.
4. Archive preserves `memory.md` before distillation.
5. Autodream does not delete existing knowledge.
6. `index.md` links to relevant topics with clear triggers.
7. A topic page has source dates.
8. Raw archive is not loaded by default.
9. `review memory` produces a cleanup plan before deletion.
10. A known high-risk rule still works in a fresh session.

## 22. Practical use cases

Concrete implementations of this architecture:

- [Kiro Local Memory](../usecases/memory/kiro-local-memory.md)
- [OpenAB + Codex + k3s Memory](../usecases/memory/openab-codex-k3s-memory.md)

## 23. Final rule

Agent-first memory is not a file. It is a pipeline:

```text
Hot controls behavior.
Conventions stabilize rules.
Inbox captures.
Archive preserves.
Autodream distills.
Index navigates.
Topics retain knowledge.
Review corrects drift.
```
