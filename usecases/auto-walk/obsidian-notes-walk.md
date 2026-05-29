# Obsidian Notes Walk Use Case

## 1. Context

This use case describes a standalone Auto-Walk binding for a Markdown notes vault (Obsidian, Logseq, Foam, or plain Markdown). The walk runs over the user's own notes, produces candidate associations between distant notes, and writes Walk reports back into the vault as ordinary Markdown files for human reading.

The design is a practical implementation of [Agent-first Auto-Walk Architecture](../../docs/agent-first-auto-walk.md), specifically the standalone mode described in §14. No agent-wiki memory is required.

This binding differs from [Kiro Local Walk](kiro-local-walk.md) in three structural ways:

- The corpus is the user's notes, not distilled agent memory.
- There is no agent-side surfacing protocol (no SKILL.md, no `/walk` slash command). Output is a Markdown report the user reads in their notes app.
- There is no memory inbox to discharge into. Discharge becomes "write a follow-up note in the vault yourself."

## 2. Design philosophy

This binding borrows from:

1. **Agent-first Auto-Walk Architecture** — the walking principle (§5), the portable corpus interface (§8), the standalone surfacing fallback (§14.2).
2. **Obsidian / Roam / Logseq PKM patterns** — atomic notes, wikilinks as explicit neighbor edges, daily notes, tag taxonomies.
3. **The "second brain" practice** — write things down rather than memorize, revisit periodically, use connections as the unit of knowledge.

Core claim:

> Give your notes vault a weekly process that reads what you've written, finds non-obvious connections between distant notes, and writes those candidates back into the vault as readable reports — without ever auto-editing your existing notes.

## 3. Corpus layout

The vault hosts both the source notes and the walks:

```text
<vault>/
├── <regular notes>.md             # your existing notes (untouched by Auto-Walk)
├── daily/                         # daily notes, if you use them
│   └── YYYY-MM-DD.md
└── walks/                         # NEW — Auto-Walk's home
    ├── reports/                   # human-readable Walk reports (this is the surface)
    │   └── YYYY-MM-DD.md
    ├── active/                    # candidate hypotheses (YAML)
    │   └── hyp-YYYY-MM-DD-NNN.yaml
    ├── discharged/
    ├── rejected/
    ├── archived/
    ├── noteworthy/
    ├── log.md
    └── scripts/
        └── walk-run.sh
```

`walks/` lives **inside the vault** on purpose:

- Reports are first-class notes the user reads in their PKM tool.
- Wikilinks (`[[hyp-2026-05-28-001]]`) resolve correctly in Obsidian/Logseq.
- Vault sync (iCloud, Syncthing, Git) carries `walks/` with everything else.

## 4. Item model

An "item" in this corpus is one of:

| Granularity | Definition | Trade-off |
| --- | --- | --- |
| Whole note | One `.md` file = one item | Simpler enumeration; loses sub-note structure |
| Note section | One `## heading` block = one item | Sharper bridges; complex enumeration |
| Atomic block | Obsidian block-id'd paragraph | Most precise; requires explicit `^id` markers |

**Recommended starting point**: whole note. Graduate to section-level only when the vault has many long notes that mix topics.

Metadata sources:

- **Frontmatter** (YAML at file top): explicit tags, status, date, type
- **File mtime + ctime**: implicit timeline
- **Wikilinks** (`[[Target Note]]`): explicit neighbor edges
- **Tags** (`#topic/subtopic`): taxonomic neighbors
- **Backlinks** (computed from wikilinks): reverse neighbors

Neighbor retrieval (§11.3 of protocol):

- **Near**: wikilink + backlink graph within 1–2 hops of seed
- **Middle**: shares a tag with seed but not directly linked
- **Far**: random sample weighted **away** from the seed's most frequent tags

## 5. Walk runner

A weekly script (Friday, mirroring `kiro-local-walk.md` §6.1) that:

1. Skips if vault has fewer than ~20 substantive notes (smaller vaults rarely produce useful bridges).
2. Picks one **propositional** seed (per §11.2 of protocol):
   - Default: a tag or wikilink cluster that appeared frequently in the last 7 days.
   - Alternative: a "stalled" topic — many notes but no recent updates.
   - Force a random "forgotten note" seed at least one walk per month.
3. Retrieves near/middle/far items per §11.3.
4. Calls an LLM (any API; this binding is agent-agnostic) with three sub-prompts per §11.4: INVENTORY → ROAM → CRITIQUE.
5. Parses surviving hypotheses into `walks/active/hyp-YYYY-MM-DD-NNN.yaml`. Routes critic-rejected-but-noteworthy candidates to `walks/noteworthy/`.
6. Writes a human-readable report to `walks/reports/YYYY-MM-DD.md`.
7. Appends to `walks/log.md`.

The runner is generic. Implementation tooling is open: `llm` CLI, Anthropic / OpenAI SDK, `aichat`, `mods`, or a local model via Ollama. The protocol does not prescribe the runtime.

Skeleton:

```bash
#!/bin/bash
set -euo pipefail
VAULT="$HOME/Documents/MyVault"
TODAY=$(date +%Y-%m-%d)

# 1. Enumerate vault notes, build tag/link index
# 2. Pick seed from recent activity
# 3. Sample near/middle/far items
# 4. Run INVENTORY -> ROAM -> CRITIQUE via LLM API
# 5. Parse YAML hypotheses; route to active/ or noteworthy/
# 6. Render reports/$TODAY.md from active hypotheses
# 7. Append log
```

## 6. Walk procedure

Identical to protocol §11.4. Three sub-prompts: INVENTORY → ROAM → CRITIQUE. Critic gate per §11.5.

The noteworthy escape valve (§11.6) is especially relevant here: cross-note analogies across very different topics are frequently single-source per topic, and the `noteworthy/` bucket preserves these for human review without polluting `active/`.

## 7. Output mode — the Walk Report

Each walk produces one `walks/reports/YYYY-MM-DD.md`. This **is** the primary surface.

Recommended report format:

```md
---
title: Walk Report 2026-05-28
seed: ...
hypotheses:
  - hyp-2026-05-28-001
  - hyp-2026-05-28-002
---

# Walk Report — 2026-05-28

## Seed

<one or two sentences stating the propositional seed>

## Inventory

What the seed touches, in plain bullets. From the INVENTORY phase, lightly edited.

## Candidate associations

### [[hyp-2026-05-28-001]] — <one-line claim>

- **Refs**: [[Note A]], [[Note B]], [[Note C]]
- **Applies when**: ...
- **Confidence**: medium
- **Why it may matter**: ...

### [[hyp-2026-05-28-002]] — ...

## Critic rejections

For transparency, list rejected candidates with reasons:

- R3 — <claim> → rejected: single-source generalization
- R5 — <claim> → rejected: applies_when 含糊

## Noteworthy (if any)

- [[hyp-2026-05-28-006]] — <claim> → flagged for human review

## Notes for review

<one paragraph the runner produces: which hypotheses might be worth confirming, which feel weak, what to look at next>
```

The `[[wikilinks]]` make hypothesis IDs clickable. Each YAML file in `active/` renders as its own note when the vault is opened in Obsidian/Logseq, with the report linking to it.

Reports accumulate in `walks/reports/` and form an audit trail.

## 8. Lifecycle adaptations for standalone

Most of protocol §13 applies as-is. Two differences:

### 8.1 Discharge: no memory inbox

In `kiro-local-walk.md`, discharge writes a new atomic memory item into `memory/memory.md`. Here, there is no inbox. Instead:

- When the user confirms a hypothesis, they write a new note (or extend an existing one) in the vault — by hand.
- The walk runner **does not** auto-write to user notes. Ever.
- The user manually moves the hypothesis YAML from `active/` to `discharged/` after writing the corresponding note.
- The discharged YAML can carry an optional `note_link` field pointing to the user's new note.

### 8.2 No A mode

There is no conversational agent reading `walks/active/` on each turn. **A mode does not exist in this binding.**

C mode degrades to "user reads the latest Walk Report." The report itself is the surface.

If the user happens to use Obsidian + an AI plugin (e.g., Smart Connections), they can wire that plugin to pull from `walks/active/`, but that integration is out of scope for this binding.

## 9. Key design decisions

### 9.1 Why `walks/` inside the vault

Putting `walks/` inside the vault (rather than a sibling folder) means reports render as ordinary notes, wikilinks resolve, and vault sync carries `walks/` across machines. The cost is one extra folder in the vault root. Most vaults already have system folders (`templates/`, `attachments/`).

### 9.2 Why item = whole note initially

Sub-note granularity requires more wiring (block IDs, parsing) and yields marginal bridge quality on small vaults. Graduate to sections only when the vault has many large mixed-topic notes.

### 9.3 Why no auto-edit of user notes

The walk runner can read everything in the vault. It writes only to `walks/`. This protects the user from silent changes to canonical notes.

This is the same invariant as protocol §6.3 "Auto-Walk reads memory but never writes to it" — applied to a different corpus.

### 9.4 Why Friday weekly

Same reasoning as `kiro-local-walk.md` §10.1: end-of-work-week consolidation rhythm, weekend reading availability.

## 10. Testable rollout

### 10.1 L1 — Manual walk, one report

1. Create `walks/` inside the vault with the structure in §3.
2. Pick a propositional seed by hand. Pick 5–8 notes by hand for near/middle/far.
3. Run the multi-pass prompt (adapt `kiro/skills/auto-walk/walk-emit-prompt.md` from the kiro binding — change corpus paths and tooling references).
4. Save the YAML hypotheses to `walks/active/`. Write a report to `walks/reports/<today>.md`.
5. Open the report in your PKM tool. Click a hypothesis wikilink. Confirm rendering.

Pass criterion: at least one hypothesis with valid fields; report renders correctly in your tool of choice.

### 10.2 L2 — Scheduled walk

1. Write `scripts/walk-run.sh` that does §5 unattended.
2. Schedule it (cron, launchd, systemd timer, or GitHub Action) for Friday.
3. Verify a report appears in `walks/reports/` after one Friday.

Pass criterion: unattended run produces a report; critic rejections logged.

### 10.3 L3 — Not applicable

There is no A-mode surfacing in this binding. Skip.

### 10.4 L4 — Feedback loop (optional)

If the user maintains a habit of moving confirmed hypotheses to `discharged/`, the runner can learn:

- Topics whose hypotheses are never confirmed → lower seed weight.
- Phrasing patterns from rejected hypotheses → soft blocklist in ROAM.

Optional; deferred until enough data accumulates.

## 11. Pitfalls (provisional)

| Pitfall | Cause | Mitigation |
| --- | --- | --- |
| Walks generate generic associations | Vault has many shallow notes, few deep ones | Curate first; raise minimum note size threshold |
| Reports pile up unread | No reading habit established | Schedule a "walk review" calendar block alongside the Friday run |
| Hypotheses reference dead links | Notes renamed/moved after walk | Re-run periodically; treat dead-link `active/` items as expired |
| Bridge fatigue (same topics) | Seed selection too narrow | Force one monthly walk with a random forgotten-note seed |
| Vault sync conflicts on `walks/` | Multi-device walks run simultaneously | Pin the walk runner to one device; sync results outward |
| Tag-heavy bridges feel forced | Near retrieval relies only on tags | Mix in wikilink and backlink graph for "Near" |

## 12. Essence

```text
The vault holds what you've written.
The walk reads it weekly.
The walk produces hypotheses but never edits your notes.
The report is a regular vault note you read in your usual tool.
Confirmed hypotheses become new notes you write yourself.
```

Auto-Walk for an Obsidian-style vault is not a replacement for note-taking. It is a sibling layer that proposes connections you may not have consciously noticed.
