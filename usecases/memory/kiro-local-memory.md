# Kiro Local Memory Use Case

## 1. Context

This use case describes a local `.kiro/memories` memory system for cross-session persistent agent memory on macOS.

The goal is to let an AI agent keep useful memory across sessions while automatically maintaining that memory without requiring the human to manually curate files every day.

The design is a practical implementation of [Agent-first Memory Architecture](../../docs/agent-first-memory.md).

## 2. Design philosophy

This system borrows from three sources:

1. **Karpathy-style `llm-wiki`** — the idea of a wiki-like index as the entry point for agent knowledge.
2. **OpenClaw PR #372 autodream pattern** — a staged memory pipeline where raw memory is preserved first and distilled later.
3. **Claude Code-style `MEMORY.md` + topics separation** — a small hot index plus deeper topic pages, separating frequently loaded memory from cold or warm knowledge.

The core idea:

> Give the AI agent persistent cross-session memory that can maintain itself automatically, without requiring the human to manually organize notes.

## 3. Directory structure

```text
~/.kiro/memories/
├── conventions.md     -> symlink -> dotfiles-ai stable rules (rarely changed)
├── memory.md          # daily inbox / hot working memory, written during sessions
├── log.md             # operation timeline for archive/dream/review events
├── index.md           -> symlink -> dotfiles-ai wiki index
├── archive/           -> symlink -> dotfiles-ai daily archives
│   ├── 2026-05-02.md
│   ├── 2026-05-03.md
│   └── ...
└── topics/            -> symlink -> dotfiles-ai topic pages
    ├── memory-system-design.md
    ├── steering-design-guide.md
    └── openab-deployment.md
```

## 4. Layering model

| Layer | File | Nature | Loading | Versioning |
| --- | --- | --- | --- | --- |
| Conventions | `conventions.md` | Stable rules (the "law"), rarely changed | **Hot**: agent resource, auto-loaded every session | Managed by `dotfiles-ai` |
| Hot inbox | `memory.md` | Daily real-time notes written during sessions | **Hot**: agent resource, auto-loaded | Not versioned |
| Cold index | `index.md` | Wiki-style knowledge index updated by AI distillation | **Hot**: agent resource, auto-loaded | Managed by `dotfiles-ai` |
| Timeline | `log.md` | Operation log; keeps recent archive/dream/review entries | Cold | Not versioned |
| Cold archive | `archive/` | Daily raw memory snapshots | Cold | Managed by `dotfiles-ai` |
| Cold topics | `topics/` | Deep topic pages split out after enough accumulated material | **Warm**: loaded on demand | Managed by `dotfiles-ai` |

### Why conventions is Hot (not Warm)

The decision tree from the architecture doc asks: "If this is not loaded, will the agent's next response or action likely be wrong?"

For conventions, the answer is yes. Without loading conventions, the agent may:
- Use the wrong git identity
- Push with wrong HOME (sandbox vs real)
- Skip mandatory security scans
- Violate workflow mandates

Therefore conventions must be loaded via agent resource (same mechanism as steering), not via index.md reference. This ensures it is always present regardless of context pressure.

## 5. Version-control strategy

Structural memory files are symlinked into a `dotfiles-ai` repository:

- `conventions.md`
- `index.md`
- `archive/`
- `topics/`

These files are useful across machines and should be synchronized.

High-frequency local files stay local:

- `memory.md`
- `log.md`

They are temporary, noisy, and change often. Keeping them out of version control avoids churn and prevents the repo from becoming a raw session dump.

## 6. AutoDream mechanism

Two scheduled jobs run through macOS `launchd`.

`launchd` is preferred over `cron` because `cron` does not wake a sleeping Mac, while `launchd` with `StartCalendarInterval` can run after wake.

### Stage 1: auto-archive, daily 07:30

This stage is pure shell and does not use AI.

Steps:

1. Check whether `memory.md` has substantive content, ignoring blank lines, headings, and comments.
2. If content exists, move or append it to `archive/YYYY-MM-DD.md`.
3. Recreate a blank `memory.md` with the current day's header.
4. Append an archive record to `log.md`.
5. Rotate `log.md` when it exceeds the retention window, for example keeping the latest 100 entries.

Rationale:

> Archiving is mechanical. It should not depend on model judgment. Raw memory must be preserved before AI transforms it.

### Stage 2: auto-dream, daily 07:40

This stage invokes AI to distill memory.

Execution mode:

```text
kiro-wrap chat --no-interactive --trust-all-tools
```

Steps:

1. Check whether today's archive exists; skip if there is nothing to process.
2. Build a prompt instructing the AI to read the archive and existing `index.md`.
3. Ask the AI to:
   - Extract long-term valuable knowledge from the archive.
   - Update `index.md`.
   - Prefer additive updates: add or revise, but do not delete.
   - Mark stale entries as `[待清理]`.
   - Preserve source-date markers on each item.
   - Keep `index.md` under roughly 200 lines.
   - Split a topic into `topics/` when it accumulates more than about 5 useful entries.
   - Update a “recent activity” section, keeping about the latest 10 items.
4. Append a dream record to `log.md`.

## 7. Flow

```text
Daytime usage                    07:10                07:20
────────────────────────────────────────────────────────────
sessions write memory.md   →   archive moves it   →   AI distills index/topics
                              (shell)                 (kiro-wrap)
```

Output:

- `archive/YYYY-MM-DD.md`
- recreated empty `memory.md`
- updated `index.md`
- updated `topics/*.md` when needed
- `log.md` operation trace

## 8. Key design decisions

### 8.1 Steering, conventions, and memories are separate

Steering stores static specifications:

```text
WHAT / HOW (system-level directives)
```

Conventions store stable behavioral rules:

```text
WHAT IS ALWAYS TRUE (identity, security, workflow mandates)
```

Memories store dynamic experience:

```text
WHAT HAPPENED / WHAT WAS LEARNED
```

They should not be mixed. Autodream maintains memories but never touches steering or conventions.

### 8.2 Sub-agents mount memory selectively

Not every sub-agent should see all memory.

Memory visibility should be configured through resources or equivalent capability boundaries. Agents should receive only the memory layer relevant to their role.

### 8.3 `launchd` scripts must set `PATH`

`launchd` does not load shell profiles. Scripts should explicitly export paths such as:

```text
~/.local/bin
~/.cargo/bin
/opt/homebrew/bin
```

### 8.4 Auto-dream must fix `HOME` when needed

If Kiro's sandbox profile changes `HOME`, auto-dream should explicitly set:

```sh
HOME="$REAL_HOME"
```

before invoking `kiro-wrap`.

## 9. Review entry point

The system preserves an explicit manual audit path:

```text
review memory
```

A review should inspect:

- stale items
- duplicate entries
- index bloat
- missing source dates
- topic pages that should be split or merged
- memories that should or should not be promoted to conventions or steering

## 10. Essence

The system can be summarized as:

```text
Daytime human-agent collaboration creates memory.
Nightly archive preserves it.
Morning AI distillation extracts long-term knowledge.
The result becomes a wiki-like memory system.
```

Humans do not need to manually organize daily notes, but they keep an explicit audit entry point.
