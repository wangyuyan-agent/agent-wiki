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

### The deeper purpose: trust calibration

Storing text is the easy part. An LLM agent's storage is already near-perfect and permanent; what it lacks is doubt. The agent has no built-in epistemic gradient telling it which of its own records still deserve belief.

So the real adversary of an agent memory system is not forgetting, and not even staleness — it is the agent's **uncritical trust in its own past records**. A stale fact is dangerous only because the agent believes it without question.

This reframes the whole design. The product of a memory system is not the stored text; it is the **trust-calibration metadata** around each item — its source, its date, its epistemic kind, its status. Those fields are load-bearing structure, not decoration. Every rule below ultimately serves one goal: keep each memory item's believability honestly calibrated. `additive-only` (§4, §14) earns its place only as a carrier of that calibration signal — never as "more is better."

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
- A system where AI can freely delete or rewrite long-term `knowledge` without review. (`state` facts are non-destructively superseded — see §4 and §14 — which is *not* deletion: the prior value is retained as history and recoverable from archive.)
- A single fixed directory layout that every platform must copy exactly.

The protocol matters more than the exact filenames.

## 4. Core model

Agent memory has three layers, one lifecycle, and two epistemic kinds.

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

### Epistemic kinds

Every memory item is one of two epistemic kinds. The kind governs how the item may be updated, and it is the single most load-bearing field in the system.

```text
state     = a current-value fact about the world that can change.
            (an IP address, a port, a schedule time, a service status, a version)
            There is one correct current value; old values are superseded, not piled up.

knowledge = a durable lesson, root cause, decision, rationale, or pattern.
            (why a deployment failed, a debugging heuristic, why a preference was chosen)
            There is no single "current" value; understanding accumulates.
```

This is the same line data engineering draws between a current-state table (SCD type-1: overwrite in place) and an event log (SCD type-2: append forever). OpenAI's late-2026 ChatGPT memory rewrite ("going to Singapore" → "went to Singapore" once the date passes) is exactly a `state` supersede done right.

It follows that **`additive-only` is not a universal creed — it is the correct policy for `knowledge`.** For `state`, blind accumulation is the disease, not the cure: ten stale IP addresses buried under `[待清理]` markers are worse than one superseded value with a clean history. Treating every item as append-only over-protects `state` and lets staleness quietly rot the index.

So the two kinds diverge through the rest of the lifecycle:

- `knowledge` → additive; may **cool / demote** over time (lose retrieval weight, get merged) but is never silently deleted (§14, §16).
- `state` → **non-destructively superseded** when a newer value arrives, under the four constraints in §14.

One hard caution governs the boundary: **when in doubt, treat an item as `knowledge`.** Misclassifying `knowledge` as `state` is an irreversible loss — a hard-won lesson gets overwritten. Misclassifying `state` as `knowledge` only costs some index bloat — a recoverable nuisance. The classifier must be high-precision on `state` and tolerate false negatives. This asymmetry is the same shape as the Auto-Walk surfacing gate (§12.2 there): when unsure, fail safe.

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

## 7. Storage interface

The lifecycle (§4) and the memory-item schema (§9) are the protocol's invariants. The exact directory shape is *not*. Different agent runtimes — local filesystems, PVC-mounted containers, KV stores, embedded databases, hybrid setups — should be able to host this protocol without rewriting it.

To keep the protocol portable, every binding MUST expose a small abstract interface. This mirrors the Auto-Walk corpus interface (§8 of the walk protocol), which is what made walks runnable over notes vaults, reading queues, and research corpora without rewriting the walk lifecycle.

### 7.1 Required capabilities of a storage binding

Any binding that claims to implement this protocol MUST provide the five operations below. The names are notional; what matters is that each operation exists and behaves as described.

1. **Inbox append.** Append a captured item to the hot inbox, in the §9 schema. (Backed by a `memory.md` file, a row in a SQLite table, an append-only log, etc.)
2. **Archive (durable, append-only).** Move or copy the inbox's accumulated content into a durable, append-only layer keyed by a date or other monotonically advancing identifier. The archive layer MUST NOT be mutated after writing, because §13, §14.2 (state supersede recovery floor), and §9 (preferred `Source` anchor) all depend on its immutability.
3. **Item store with metadata.** Read and write distilled items keyed by a stable id, carrying the §9 fields (`kind`, `subject`, `Status`, `superseded_by`, `Source`, `Confidence`, source date). Updates to `Status` and `superseded_by` MUST be atomic with respect to autodream's supersede operation (§14.2).
4. **Index / navigation surface.** Expose a navigable summary (the §10 index role) that returns ordered candidates for a given trigger or topic. May be a Markdown file, a tag table, an embedding-backed nearest-neighbour query — anything that satisfies the trigger semantics in §10.
5. **Operation log.** Record lifecycle events (`archive`, `autodream`, `supersede`, `cool`, `merge`, `pending-cleanup`, `review`) with timestamps, sufficient for post-hoc audit. The log itself need not be Markdown; it must be replayable.

A binding MAY add capabilities (search, embeddings, encryption, sync), but MUST NOT remove any of the five.

### 7.2 Required guarantees

- **Append-only archive.** Without this, recovery from autodream misjudgments (§14.2) is not possible, and `Source` anchors corrode.
- **Atomic supersede.** A `state` supersede that updates the prior row's `Status` and adds a new row MUST not leave the store in a state where both rows are simultaneously `active`. (For a filesystem binding, this is achieved by running the operation within a single autodream pass and committing the file atomically.)
- **Stable item identity.** An item id, once assigned, MUST persist across autodream passes. `superseded_by` and walk discharge back-pointers (§13.1 of the walk protocol) rely on this.
- **Single writer per binding.** This protocol does not specify a multi-writer model. A binding that crosses runtimes (e.g., a PVC shared between two pods) MUST elect a single writer per autodream pass, or define its own concurrency contract on top.

### 7.3 Reference filesystem layout

A common, fully-conforming filesystem binding looks like this:

```text
<agent-home>/
├── AGENTS.md / CLAUDE.md / GEMINI.md / steering/*
└── memory/
    ├── README.md
    ├── conventions.md
    ├── memory.md          # capability 1 (inbox append)
    ├── log.md             # capability 5 (operation log)
    ├── index.md           # capability 4 (index/navigation)
    ├── archive/           # capability 2 (durable, append-only)
    │   └── YYYY-MM-DD.md
    ├── topics/            # capability 3 (item store with metadata)
    │   ├── user-preferences.md
    │   ├── environment.md
    │   ├── workflows.md
    │   ├── decisions.md
    │   ├── operational-pitfalls.md
    │   └── memory-system-design.md
    └── scripts/
        └── archive-memory.sh
```

Minimal filesystem layout:

```text
<agent-home>/
├── AGENTS.md / CLAUDE.md / GEMINI.md
└── memory/
    ├── conventions.md
    ├── memory.md
    ├── index.md
    └── topics/
```

Other valid bindings: a PVC-backed setup that swaps `topics/` for a SQLite items table; a hosted runtime that backs the inbox by an event queue and the archive by an object-store bucket. The §4 lifecycle and the §9 schema do not change.

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

A memory item must be concise, source-aware, and reusable. Two fields are mandatory on every item — `kind` and `Source` — because they carry the trust-calibration signal (§1).

Required minimum format:

```md
- [YYYY-MM-DD] (kind) <distilled reusable fact or preference>. Source: <archive/topic/anchor>.
```

`kind` is `state` or `knowledge` (§4). `Source` is required, not optional — an item whose provenance cannot be named cannot be audited later, and uncalibrated provenance is exactly the blind-trust failure §1 warns against. This also corrects an inversion: the Auto-Walk protocol already *requires* `supporting_refs` on every hypothesis, yet memory items historically left `Source` optional — the lower-trust artifact was held to a stricter standard than the durable one.

Extended format for higher-risk items:

```md
- [YYYY-MM-DD] <fact>
  - id: <stable identifier>                    # required; see field notes
  - kind: <state | knowledge>                  # required
  - subject: <stable key>                      # required for state; the thing whose value this is
  - Scope: <global | project | environment | workflow | user preference>
  - Status: <active | superseded | stale | pending-cleanup>
  - superseded_by: <item id>                   # set when Status = superseded; references another item's id
  - inspired_by: <hypothesis id>               # optional; set when this item was discharged from a walk hypothesis (auto-walk §6.2.1)
  - corroborating_refs:                        # optional; secondary corpus refs that corroborate but do not constitute the Source
    - <archive/YYYY-MM-DD.md#anchor>
  - Source: <archive/YYYY-MM-DD.md#anchor or conversation context>   # required
  - Confidence: <confirmed | observed-once | inferred>
```

Field notes:

- `id` (required): a stable identifier that persists across autodream passes. Convention: `mem-YYYY-MM-DD-NNN` where NNN is a per-day ordinal assigned by scanning existing items for `max(NNN) + 1` (parallel to the walk hypothesis id convention). The id is what `superseded_by` points at, what walk discharge back-pointers reference (auto-walk §13.1), and what §7's "stable item identity" guarantee promises. A binding that uses a database-backed item store MAY use the database's primary key in lieu of the date-ordinal scheme, provided the id is stable across autodream passes.
- `kind` (required): drives the update policy. `state` may be superseded; `knowledge` is additive (§14).
- `subject` (required for `state`): a stable key naming *what* this is the current value of (e.g. `host:public-ip`, `nightly-job:schedule`). Supersede matches on `subject`, deterministically — never on fuzzy text similarity, which would be unsafe.
- `Status`: a closed token enum, not free prose. A `[待清理]`-style marker written as prose cannot be processed reliably by a machine; a `pending-cleanup` token can. Token semantics:
  - `active` — current; default for any newly captured item.
  - `superseded` — a newer `state` row exists for this `subject`; this row is retained as history. Set by autodream supersede (§14.2). Always paired with `superseded_by`.
  - `pending-cleanup` — autodream marked this item as needing human attention (typically a `knowledge` item that a later observation appears to refute, §14.3). Cleared by review (§16).
  - `stale` — a *human reviewer* has judged the item no longer applicable but has not yet decided whether to merge, demote, or replace it. Autodream MUST NOT assign `stale` on its own (autodream uses `superseded` for `state` and `pending-cleanup` for `knowledge`); `stale` is the human-only intermediate state that arises during review (§16) when judgment is needed but the resolution is not yet known.
- `inspired_by` (optional): when this item was created by a walk discharge (auto-walk §6.2.1), it carries the discharged hypothesis id here, and *only* here. Putting the hypothesis id into `Source` is forbidden — that would let a lateral artifact impersonate evidence (auto-walk §6.2 invariant).
- `corroborating_refs` (optional): when `Source` names a non-corpus event (typically a user statement, see auto-walk §6.2.2), `corroborating_refs` MAY enumerate corpus items that corroborate the fact but did not by themselves justify it. This keeps the primary `Source` honest about what actually made the fact true.
- `Source` (required): prefer the **smallest stable addressable unit**, and **prefer anchoring into an append-only layer** (e.g. `archive/YYYY-MM-DD.md`) over a mutable one (`topics/X.md#heading`). Mutable files get rewritten by later distillation, so any anchor into them — heading *or* line range — corrodes over time. The archive does not move. (This is why a rigid `#L<start>-<end>` requirement is *not* mandated: line numbers drift at least as often as headings; the durable fix is anchoring the immutable layer, not picking an addressing scheme.)

Examples:

```md
- [2026-05-11] (knowledge) In OpenAB + Codex on k3s, mutable `AGENTS.md` should live on PVC rather than a read-only ConfigMap. Source: archive/2026-05-11.md.
```

```md
- [2026-05-21] (state) Local default model is `<model-id-A>`.
  - kind: state
  - subject: local:default-model
  - Scope: environment
  - Status: superseded
  - superseded_by: [2026-06-01]
  - Source: archive/2026-05-21.md
```

```md
- [2026-05-11] (knowledge) User prefers English responses, but may discuss architecture in Chinese.
  - kind: knowledge
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

- [YYYY-MM-DD] (kind) Short summary → topics/example.md

## Topic Map

- user-preferences.md — Read when handling user style, language, personal preferences.
- environment.md — Read when working with local/project/deployment environment facts.
- workflows.md — Read when executing known SOPs.
- decisions.md — Read when checking previous architecture or product decisions.
- operational-pitfalls.md — Read when debugging recurring tool/deployment failures.
- memory-system-design.md — Read when modifying the memory system itself.

## Pending Cleanup

Items whose `Status` is `pending-cleanup` (a closed token, not free-form prose). Each entry carries the same metadata as a §9 item, including `kind` and `Source`. A `pending-cleanup` `state` item with a known successor SHOULD additionally carry `superseded_by` so that automated maintenance can resolve it without human review (§14).

```

Index rules:

- Keep it concise, ideally around 200 lines or less.
- Include topic paths and trigger descriptions.
- Keep recent activity short, for example the latest 10 items.
- Do not paste archive content back into the index.
- Use the closed `Status` enum from §9 (`active | superseded | stale | pending-cleanup`) — never invent free-form markers like `[待清理]` in prose form, which a machine cannot reliably parse and which is the empirical root cause of cleanup-marker bloat.
- Stale `state` items are non-destructively superseded (§14), not piled into Pending Cleanup. Pending Cleanup is reserved for `knowledge` items awaiting human review (§16) and for `state` items whose successor is not yet known.

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

- [YYYY-MM-DD] (kind) Distilled reusable fact. Source: archive/YYYY-MM-DD.md.

## Pending cleanup

Entries whose `Status` is `pending-cleanup` per §9 (no free-form `[待清理]` prose). Use `superseded_by` to chain a `state` row to its successor.
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
3. Tag every captured item with its `kind` (`state` or `knowledge`, §4). When in doubt, tag it as `knowledge` — misclassification of knowledge as state is irreversible (§4); the reverse is only nuisance.
4. **For every `state` item, supply a `subject` key at capture time.** Without a `subject`, autodream cannot supersede the item (§14.2 constraint 4), and the item becomes a permanently-accumulating "current value" — exactly the staleness rot §4 warns against. If a `subject` cannot honestly be named, the item is not actually a `state` fact and MUST be re-tagged as `knowledge`. This is the single highest-frequency inlet for the schema; failing the requirement here silently breaks `state`'s entire lifecycle.
5. Include date and `Source` (required, §9). Assign an `id` per the §9 convention.
6. Do not copy full chat logs.
7. Do not treat one-time emotion as long-term knowledge.
8. Do not overwrite `knowledge` directly. `state` is updated by the autodream supersede protocol (§14), not by raw inbox overwrites.
9. Prefer add-first; cleanup of `state` is owned by autodream (§14); cleanup of `knowledge` is reviewed by humans (§16).

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

The reason to archive before AI distillation is twofold:

1. Raw memory must be preserved even if the agent fails, hallucinates, or produces a bad summary.
2. The archive layer is **append-only**, which makes it the durable substrate for two later guarantees: it is the recovery floor for autodream's `state` supersede operations (§14), and it is the preferred anchor target for `Source` references (§9). Mutating the archive after the fact breaks both.

## 14. Autodream protocol

Autodream is the AI distillation stage. It operates on the two epistemic kinds (§4) under different rules — and that asymmetry is the heart of this protocol. Treating both kinds with one universal `additive-only` rule is what causes `Pending Cleanup` to grow without bound; treating both with one universal `synthesize-and-rewrite` rule is what causes hard-won lessons to disappear silently. Autodream takes the middle path: **selective supersede** for `state`, **additive plus cooling** for `knowledge`.

Inputs:

- Today's archive
- Current `index.md`
- Relevant topic pages
- Memory protocol

Outputs:

- Updated `index.md`
- Updated `topics/*.md`
- `log.md` entry, with explicit records of any `supersede` and `cool` operations

### 14.1 General rules

- Preserve `Source` and source dates on every item touched.
- Do not invent facts not present in the archive.
- Do not promote a one-off incident into a universal rule unless explicitly confirmed.
- Keep `index.md` concise.
- Split or merge topics when useful.
- Never write to `conventions.md` or to `memory/memory.md`. Autodream reads `memory.md`'s already-archived form, never the live inbox.

### 14.2 `state` items: non-destructive supersede

When today's archive contains a new value for an existing `state` `subject` (§9), autodream MAY supersede the prior value — under all four of the following constraints. Missing any one collapses this back to "blind rewrite," which is exactly what §4 warns against.

1. **Non-destructive.** The prior row is not deleted. Its `Status` is updated to `superseded`, and a `superseded_by` pointer is added. The newer row appears as a fresh entry with its own date and `Source`. Recovery from a misjudgment is always possible — the archive (an immutable layer, §13) holds the original, and the prior row is still in `index.md`/`topics/*.md` as history. This is the SCD type-2 shape, not type-1.
2. **When in doubt, do not supersede (疑則從加).** Misclassifying a `knowledge` lesson as a `state` value is irreversible in *interpretation*; the text survives, but the lesson loses its weight. Therefore the supersede classifier must be high-precision and tolerate false negatives — when ambiguous, leave both rows as additive entries. This is the same asymmetric-threshold pattern as Auto-Walk §12.2: a missed cleanup is recoverable; a wrong supersede is not.
3. **Match on the formal `kind` field, not on text similarity.** Both rows must carry `kind: state`; supersede is forbidden between rows of unmatched kinds, and forbidden when `kind` is absent. Inferring `state`-ness from prose is the failure mode that turns this into "AI silently rewriting knowledge."
4. **Match on `subject` deterministically.** Two `state` rows are subject to supersede iff their `subject` keys are equal as strings. No fuzzy matching, no embedding similarity, no LLM judgment. If the runner cannot find a `subject` key, it cannot supersede.

Each supersede MUST be logged in `log.md` with the prior `subject`, the prior date/value, and the new date/value, so the operation is auditable post-hoc.

### 14.3 `knowledge` items: additive, with cooling

`knowledge` items are not superseded. Understanding accumulates; new lessons add to old ones, sometimes contradicting them, and that contradiction is itself information (Reconcile, §15.2).

Two non-deletion mechanisms govern `knowledge` over time:

- **Cooling (demotion):** an item that has not been engaged for a long span MAY have its retrieval weight reduced — for example, demoted from `index.md` summary to a deeper position in a topic page, or from a topic's "Facts and lessons" section to a "Historical lessons" appendix. The item is not removed; it is moved further from the hot path.
- **Merging:** several near-duplicate lessons MAY be folded into one consolidated entry whose `Source` enumerates all original archive references. The consolidated entry's date is the most recent member's date.

Neither cooling nor merging is deletion. Both are reversible by reading the archive. Both must log a `cool` or `merge` entry to `log.md`.

`knowledge` items whose veracity is itself in doubt — not stale, but possibly wrong — get `Status: pending-cleanup` and wait for human review (§16). Autodream does not attempt to refute `knowledge` on its own.

### 14.4 Prompt template

```md
You are maintaining an agent memory system whose central rule is asymmetric:
- `state` items may be superseded under the four constraints in §14.2.
- `knowledge` items are additive; you MAY cool or merge them but never delete.
- When in doubt about the kind, treat the item as `knowledge`.

Read:
- `memory/archive/{{date}}.md`   (today's raw input — your only source of new facts)
- `memory/index.md`
- relevant `memory/topics/*.md`

Tasks:
1. Extract long-term reusable items from the archive. Tag every new item's `kind` and `Source` (required, §9). Use `subject` for `state` items.
2. For each new `state` item:
   a. Look for an existing item with the same `subject` AND `kind: state`.
   b. If found, mark the existing row `Status: superseded`, set `superseded_by` to the new row, and add the new row dated today.
   c. Log the supersede (subject, prior date/value, new date/value) in `memory/log.md`.
   d. Never delete the prior row. Never supersede across kinds. Never supersede on text similarity.
3. For each new `knowledge` item: append it. Do not overwrite. If it appears to refute an existing `knowledge` item, set the existing item's `Status: pending-cleanup` and append the new one — do not delete.
4. Cooling pass (optional, low-risk): identify `knowledge` items unused for a long span and demote their position. Do not delete; log each demotion.
5. Resolve any `pending-cleanup` `state` items whose `superseded_by` is now known.
6. Update `index.md` as a navigation index, not a content dump. Keep it concise.
7. Append an autodream entry to `memory/log.md` summarizing supersedes, cools, merges, and additions.
```

## 15. Retrieval protocol

Retrieval has two halves: *when* to read (§15.1, traditional retrieval-trigger logic), and *how skeptically* to read once a memory item is in context (§15.2, the trust-calibration discipline). The second half is where most retrieval protocols silently fail. An agent's blind trust in its own past records (§1) lives precisely in the gap between "I retrieved this row" and "I am about to act on what it says."

### 15.1 When to retrieve

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
- The user says "as before" or asks about prior decisions.
- The task touches known environment or workflow areas.
- The agent needs user preferences.
- The task is a memory review, migration, or debugging task.

Do not read memory when:

- The task is self-contained.
- Memory is unlikely to change the answer.
- The only available memory is raw archive and there is no audit need.

### 15.2 How skeptically to read (Hot rule, mandatory)

Read every retrieved item *as testimony, not fact*. The text is what was once captured; it is not automatically what is true now. The agent MUST apply the following discipline whenever it retrieves a memory item:

1. **Read the metadata first.** `kind`, `Source`, `Status`, source date, and `Confidence` (§9) are what calibrate the item. An item without these — or with very old date and no recent corroboration — is not "false," but it is not load-bearing either. Down-weight it.
2. **Down-weight stale and superseded.** A row whose `Status` is `superseded`, `stale`, or `pending-cleanup` MUST not be used as a current factual basis. It MAY be cited as historical context if explicitly framed as such. For a `superseded` `state` row, follow the `superseded_by` pointer to the live row.
3. **Prefer the most recent `state` row by `subject`.** When two `state` rows share a `subject` and have not been reconciled by autodream, treat the older one as `superseded` and surface the discrepancy to the user (Reconcile, §15.2.1).
4. **Reconcile before acting.** If two retrieved items appear to contradict each other on the same subject — whether by `subject` collision in `state`, or by direct contradiction in `knowledge` — the agent MUST surface the conflict in its response, not silently pick one. Suppressing a conflict is the dominant blind-trust failure mode. Conflict resolution is a first-class step, not a fallback.
5. **Honour the asymmetry between memory and walk.** Auto-Walk hypotheses are already read with explicit suspicion (zero-trust gating, §12 of the walk protocol). This protocol now applies the *same* suspicion to memory itself. The previous gap — walks doubt themselves, memory does not — is the exact unguarded seam in which blind-trust failures live.

This is a Hot rule. It belongs in steering or conventions and SHOULD be loaded on every session, not derived per task.

#### 15.2.1 Reconcile output shape

When the agent surfaces a conflict, it does so explicitly, with all rows visible and dated:

```md
Conflict on `subject: <key>`:
  - [date-A] (kind) value-A. Source: ...   ← `Status: superseded`
  - [date-B] (kind) value-B. Source: ...   ← currently `active`

Acting on [date-B]'s value. The earlier row is retained as history.
If the earlier row should be the current truth, ask me to reconcile.
```

For `knowledge` contradictions, both items remain `active` until human review (§16), and the agent's response cites both rather than picking. The user's choice to act on one is what discharges the conflict, not the agent's silent inference.

## 16. Review protocol

Manual review is a **safety net**, not the primary garbage collector. Routine staleness — `state` superseding, `knowledge` cooling, `pending-cleanup` resolution for `state` — is owned by autodream (§14). Review exists for the cases autodream cannot or must not handle on its own:

- `knowledge` items in `pending-cleanup` (autodream marks; only humans clear).
- Items that autodream's classifier was unsure about and left as additive.
- Cross-topic conflicts and duplicates that need editorial judgment.
- Steering/conventions/memory boundary violations.
- Schema drift (items missing `kind` or `Source`; legacy `[待清理]` prose markers that predate §9).

A manual `review memory` workflow should:

1. Check whether `index.md` is too long.
2. Inspect items whose `Status` is `pending-cleanup` (per §9 token enum), and any legacy free-form `[待清理]`/`[待确认]` markers awaiting migration.
3. Find duplicate or conflicting topic entries; treat conflicts per §15.2 (Reconcile).
4. Check steering/memory boundary violations.
5. Check whether archive files were not distilled.
6. Verify `Source` and source dates are present (both required by §9).
7. Verify each item carries a `kind`; classify any legacy items missing it.
8. Identify missing triggers for important topics.
9. Propose cleanup before any destructive change.

Review should produce a plan before destructive changes. The default action on any ambiguous item is to retain it and lower its retrieval weight (cooling, §14.3), not to delete it.

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
| AI deletes useful knowledge | Lost memory | Non-destructive supersede for `state` (§14.2); additive + cooling for `knowledge` (§14.3); archive as recovery floor |
| **Blind trust in self-records** | Agent acts on stale or contradictory memory as if current | §15.2 retrieval discipline: read metadata first, down-weight `superseded`/`stale`, surface conflicts via Reconcile |
| **Cleanup-marker bloat** (`[待清理]` accumulating without ever being cleared) | Index fills with unresolved markers; signal-to-noise drops | Closed `Status` token enum (§9); `state` cleared by autodream supersede (§14.2); `knowledge pending-cleanup` resolved by review (§16) |
| **`knowledge` misclassified as `state`** | Hard-won lesson silently overwritten by a later "value" | High-precision classifier with false-negative tolerance (§4); supersede gated on formal `kind` field and exact `subject` match, never text similarity (§14.2) |
| One incident becomes permanent rule | Overgeneralized behavior | Promote to steering only after review |
| Archive not distilled | Knowledge stays hidden | Log archive/autodream status |
| Duplicate rules | Contradictions | Single source of truth; surface via Reconcile (§15.2) |
| Secrets in memory | Security leak | Never store credentials or tokens |
| Mutable-anchor `Source` corrosion | `Source` references break as mutable files get rewritten by later distillation | Prefer anchoring `Source` into the append-only archive layer (§9, §13) |

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

Agent-first memory is not a file. It is a pipeline whose product is calibrated trust:

```text
Hot controls behavior.
Conventions stabilize rules.
Inbox captures, with kind.
Archive preserves, append-only.
Autodream distills — supersedes `state`, accumulates `knowledge`.
Index navigates with trust signals visible.
Topics retain knowledge.
Retrieval reads skeptically, surfaces conflicts.
Review corrects drift; humans hold the deletion key.
```

The adversary is not forgetting. It is the agent's blind trust in its own past records. Every field on every item — `kind`, `Source`, `Status`, source date — exists to keep that trust honestly calibrated. Lose the calibration and `additive-only` is no longer a memory system; it is a hoard.
