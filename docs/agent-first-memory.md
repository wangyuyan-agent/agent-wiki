# Agent-first LLM Memory Architecture

- Protocol ID: `memory`
- Version: `0.2.0`
- Maturity: `practiced`
- Evidence scope: Real-environment evidence informs the lifecycle through `memory:L4`. One private run report exposed a failed-exploration withdrawal boundary and informed `memory@0.2.0`, but no `WithdrawalRecord`, erasure path, current item schema, or `memory:L5` path has been end-to-end validated
- Level namespace: `memory:L0`–`memory:L5`
- Last updated: 2026-08-13

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

Storing exact text is the easy part once a binding has durable storage. The harder problems are continuity, retrieval, decay, contradiction, and doubt. An agent has no reliable built-in epistemic gradient telling it which of its own records still deserve belief.

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
8. Let an attributable owner withdraw a bounded memory scope without pretending to erase model context, undo project mutations, or physically delete retained content.

## 3. Non-goals

This architecture is not:

- A raw chat archive.
- A replacement for source control, logs, issue trackers, or project docs.
- A place to store secrets or credentials.
- A guarantee that all memories are true forever.
- A system where AI can freely delete or rewrite long-term `knowledge` without review. (`state` facts are non-destructively superseded — see §4 and §14 — which is *not* deletion: the prior value is retained as history and recoverable from archive.)
- A project rollback, temporary-workspace cleanup, or selective deletion mechanism for the current model context. Memory withdrawal changes future influence; external effects and retained bytes remain under their owning surfaces.
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

This resembles the data-engineering distinction between a current-state view and a history-preserving change log. The protocol's actual update shape is closest to a type-2 slowly changing dimension: a new `state` row becomes current while the prior row remains addressable as superseded history. It is not a type-1 overwrite, because the old value is not destroyed.

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
| Conventions | A new stable rule is established | "NIT is mandatory", "always use the approved maintainer identity for commits", security policies |
| Memory | Every session with new learnings | "k3s ConfigMap was read-only", "kiro-pool needs symlink fix" |

Examples:

| Belongs in steering | Belongs in conventions | Belongs in memory |
| --- | --- | --- |
| When the user says "remember", append a note to `memory.md`. | Git identity defaults to the approved maintainer identity. | On 2026-05-11, a configuration-mounted `AGENTS.md` was found to be read-only in a container deployment. |
| Read `memory/index.md` before touching prior decisions. | All agent-wiki commits must pass sensitive info scan. | The OpenAB + Codex deployment stores mutable memory on PVC. |
| Do not store raw chat logs. | NIT findings require fixes before approve. | A previous rollout failed because `KUBECONFIG` was only set in a shell profile. |

Promotion path:

```text
Memory (observed once) → Conventions (confirmed stable rule) → Steering (changes agent behavior)
```

Do not promote one incident into a convention. Put experience into memory first; promote to conventions only after repeated confirmation or explicit user decision. Promote to steering only if it changes the agent's fundamental behavior. Repeated confirmation establishes promotion *eligibility*; the write into conventions or steering additionally requires promotion *authority* (§17).

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

To keep the protocol portable, structured bindings expose a small abstract interface. `memory:L0` is the deliberate exception: it requires only manual capture using the minimum §9 record. A `memory:L1` or higher binding MUST expose all five capabilities below. Scheduling begins at `memory:L2`; AI distillation begins at `memory:L3`.

### 7.1 Required capabilities of a storage binding

Any binding that claims `memory:L1` or higher MUST provide the five operations below. The names are notional; what matters is that each operation exists and behaves as described.

1. **Inbox append.** Append a captured item to the hot inbox, in the §9 schema. (Backed by a `memory.md` file, a row in a SQLite table, an append-only log, etc.)
2. **Archive (durable, append-only in ordinary operation).** Move or copy the inbox's accumulated content into a durable, append-only layer keyed by a date or other monotonically advancing identifier. Except for an authorized §12.3 erasure, the archive layer MUST NOT be mutated after writing, because §13, §14.2 (state supersede recovery floor), and §9 (preferred `Source` anchor) all depend on its immutability. A binding subject to erasure obligations must use storage that can execute the exception without retaining covered content.
3. **Item store with metadata.** Read and write distilled items keyed by a stable id, carrying the §9 fields (date, `kind`, `Status`, `Source`, `subject` for `state`, and `superseded_by` when superseded). `Confidence` is optional, but its scheme is mandatory when present. Updates to `Status` and `superseded_by` MUST be atomic with respect to autodream's supersede operation (§14.2).
4. **Index / navigation surface.** Expose a navigable summary (the §10 index role) that returns ordered candidates for a given trigger or topic. May be a Markdown file, a tag table, an embedding-backed nearest-neighbour query — anything that satisfies the trigger semantics in §10.
5. **Operation log.** Record lifecycle events (`archive`, `autodream`, `supersede`, `cool`, `merge`, `pending-cleanup`, `withdraw`, `reinstate`, `erase`, `review`) with timestamps, sufficient for post-hoc audit. The log itself need not be Markdown; it must be replayable. `withdraw` and `reinstate` carry the §12.2 control record; `erase` carries only the allowed content-free tombstone and scope receipt from §12.3.

A binding MAY add capabilities (search, embeddings, encryption, sync), but MUST NOT remove any of the five.

### 7.2 Required guarantees for `memory:L1+`

- **Append-only archive in ordinary operation.** Without this, recovery from autodream misjudgments (§14.2) is not possible, and `Source` anchors corrode. Authorized erasure follows §12.3 and preserves only allowed content-free lineage.
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
    ├── archive/           # capability 2 (durable, ordinary append-only)
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

Valid `memory:L0` starter layout:

```text
<agent-home>/
├── AGENTS.md / CLAUDE.md / GEMINI.md
└── memory/
    └── memory.md
```

This starter does not yet claim the structured archive, item-store, index, or operation-log guarantees of `memory:L1`.

Other valid bindings: a PVC-backed setup that swaps `topics/` for a SQLite items table; a hosted runtime that backs the inbox by an event queue and the archive by an object-store bucket. The §4 lifecycle and the §9 schema do not change.

## 8. File responsibilities

### Hot entry: `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` / steering files

The hot entry should only do five things:

1. Define identity and hard rules.
2. Point to the memory root.
3. Define when to read memory.
4. Define when to write memory.
5. Define how bounded withdrawal requests are routed before retrieval.

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

Withdraw memory influence when:
- The user says "forget that exploration", "do not use that conclusion", or otherwise withdraws a bounded prior run, item, or source scope.
- Treat this as the §12.2 reversible withdrawal path unless the user explicitly requests the §12.3 authorized erasure path.

Retrieval order:
1. Resolve applicable withdrawal/reinstatement controls from the operation log or binding control store.
2. Read the eligible scope in `memory/index.md`.
3. Read relevant eligible scope in `memory/topics/*.md`.
4. Read eligible `memory/archive/*.md` scope only for audit or source tracing.
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
- withdraw
- reinstate
- erase (content-free receipt only)

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

A memory item must be concise, source-aware, and reusable. Date, stable `id`, `kind`, and `Source` are mandatory on every captured item. A `state` item also requires `subject`. These fields carry the minimum trust-calibration and lifecycle signal (§1).

Required minimum inbox format:

```md
- [YYYY-MM-DD] [mem-YYYY-MM-DD-NNN] (kind) <distilled reusable fact or preference>. Source: <archive/topic/anchor or current source event>.
```

For `state`, add `Subject: <stable-key>` to the same record or use the structured form below. `Status` defaults to `active` while the item is in the inbox and MUST be materialized when it enters a `memory:L1+` item store.

`kind` is `state` or `knowledge` (§4). `Source` is required, not optional — an item whose provenance cannot be named cannot be audited later, and uncalibrated provenance is exactly the blind-trust failure §1 warns against. This also corrects an inversion: the Auto-Walk protocol already *requires* `supporting_refs` on every hypothesis, yet memory items historically left `Source` optional — the lower-trust artifact was held to a stricter standard than the durable one.

Canonical structured format for distilled items (`memory:L1+`):

```md
- [YYYY-MM-DD] <fact>
  - id: <stable identifier>                    # required; see field notes
  - kind: <state | knowledge>                  # required
  - subject: <stable key>                      # required for state; the thing whose value this is
  - Scope: <global | project | environment | workflow | user preference>  # optional
  - Status: <active | superseded | stale | pending-cleanup>                # required in item store
  - superseded_by: <item id>                   # set when Status = superseded; references another item's id
  - inspired_by: <hypothesis id>               # optional; set when this item was discharged from a walk hypothesis (auto-walk §6.2.1)
  - corroborating_refs:                        # optional; secondary corpus refs that corroborate but do not constitute the Source
    - <archive/YYYY-MM-DD.md#anchor>
  - Source: <archive/YYYY-MM-DD.md#anchor or conversation context>   # required
  - Confidence-Scheme: epistemic-status-v1                                # required when Confidence is present
  - Confidence: <confirmed | observed-once | inferred | unknown>          # optional
```

Field notes:

- `id` (required): a stable identifier that persists across autodream passes. Convention: `mem-YYYY-MM-DD-NNN` where NNN is a per-day ordinal assigned by scanning existing items for `max(NNN) + 1` (parallel to the walk hypothesis id convention). The id is what `superseded_by` points at, what walk discharge back-pointers reference (auto-walk §13.1), and what §7's "stable item identity" guarantee promises. A binding that uses a database-backed item store MAY use the database's primary key in lieu of the date-ordinal scheme, provided the id is stable across autodream passes.
- `kind` (required): drives the update policy. `state` may be superseded; `knowledge` is additive (§14).
- `Confidence-Scheme`, when `Confidence` is present, is `epistemic-status-v1`. `confirmed` means authoritative, repeated, or independently corroborated for the stated scope; `observed-once` means one direct bounded observation; `inferred` means derived rather than directly observed; `unknown` means available evidence cannot support a stronger classification. `confirmed` does not mean permanent.
- `subject` (required for `state`): a stable key naming *what* this is the current value of (e.g. `host:public-ip`, `nightly-job:schedule`). Supersede matches on `subject`, deterministically — never on fuzzy text similarity, which would be unsafe.
- `Status`: a closed token enum, not free prose. A `[待清理]`-style marker written as prose cannot be processed reliably by a machine; a `pending-cleanup` token can. Token semantics:
  - `active` — current; default for any newly captured item.
  - `superseded` — a newer `state` row exists for this `subject`; this row is retained as history. Set by autodream supersede (§14.2). Always paired with `superseded_by`.
  - `pending-cleanup` — autodream marked this item as needing human attention (typically a `knowledge` item that a later observation appears to refute, §14.3). Cleared by review (§16).
  - `stale` — a *human reviewer* has judged the item no longer applicable but has not yet decided whether to merge, demote, or replace it. Autodream MUST NOT assign `stale` on its own (autodream uses `superseded` for `state` and `pending-cleanup` for `knowledge`); `stale` is the human-only intermediate state that arises during review (§16) when judgment is needed but the resolution is not yet known.
- `inspired_by` (optional): when this item was created by a walk discharge (auto-walk §6.2.1), it carries the discharged hypothesis id here, and *only* here. Putting the hypothesis id into `Source` is forbidden — that would let a lateral artifact impersonate evidence (auto-walk §6.2 invariant).
- `corroborating_refs` (optional): when `Source` names a non-corpus event (typically a user statement, see auto-walk §6.2.2), `corroborating_refs` MAY enumerate corpus items that corroborate the fact but did not by themselves justify it. This keeps the primary `Source` honest about what actually made the fact true.
- `Source` (required): prefer the **smallest stable addressable unit**, and **prefer anchoring into an append-only layer** (e.g. `archive/YYYY-MM-DD.md`) over a mutable one (`topics/X.md#heading`). Mutable files get rewritten by later distillation, so any anchor into them — heading *or* line range — corrodes over time. In ordinary operation the archive does not move; an authorized §12.3 erasure may deliberately invalidate an anchor and MUST leave only allowed content-free lineage plus a disclosure of the lost audit/recovery capability. (This is why a rigid `#L<start>-<end>` requirement is *not* mandated: line numbers drift at least as often as headings; the durable fix is anchoring the ordinary immutable layer, not picking an addressing scheme.)

Examples:

```md
- [2026-05-11] [mem-2026-05-11-001] (knowledge) In a containerized agent deployment, mutable instruction state should live on writable persistent storage rather than a read-only configuration mount. Source: archive/2026-05-11.md#instruction-mount-test.
```

```md
- [2026-05-21] (state) Local default model is `<model-id-A>`.
  - id: mem-2026-05-21-001
  - kind: state
  - subject: local:default-model
  - Scope: environment
  - Status: superseded
  - superseded_by: mem-2026-06-01-001
  - Source: archive/2026-05-21.md
  - Confidence-Scheme: epistemic-status-v1
  - Confidence: observed-once
```

```md
- [2026-05-11] (knowledge) User prefers English responses, but may discuss architecture in Chinese.
  - id: mem-2026-05-11-002
  - kind: knowledge
  - Scope: user preference
  - Status: active
  - Source: explicit user preference
  - Confidence-Scheme: epistemic-status-v1
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
5. Include date, stable `id`, and `Source` (required, §9).
6. Do not copy full chat logs.
7. Do not treat one-time emotion as long-term knowledge.
8. Do not overwrite `knowledge` directly. `state` is updated by the autodream supersede protocol (§14), not by raw inbox overwrites.
9. Prefer add-first; cleanup of `state` is owned by autodream (§14); cleanup of `knowledge` is reviewed by humans (§16).

### 12.1 "Forget" is a routing request, not one destructive verb

Natural-language requests such as "forget that exploration" cross three governance surfaces. Before claiming completion, the Agent MUST inspect and report each surface separately:

| Surface | Default effect | Required disclosure |
| --- | --- | --- |
| Current conversation / Active Workspace | Stop relying on the bounded exploration, close or redirect the workspace, and emit no withdrawn conclusion into Memory. | This protocol does not provide selective model-context erasure. Unless the runtime exposes and the binding verifies such a capability, closing a workspace removes future task influence but does not remove tokens already present in the conversation. |
| External and separately governed persistent effects | Inventory project files, commits, branches, pushes, services, any isolated temporary workspace or worktree, and any conclusion already promoted into Conventions, Steering, or another protocol artifact. Rollback, disposal, revision, or revocation follows each owning surface's authority and destructive-action rules. | Memory withdrawal does not undo code or silently revoke separately governed artifacts. Report the original project, temporary exploration location, and known promoted or derived artifacts separately. |
| Durable Memory | Use non-admission when nothing was captured. If the scope already entered Memory, use §12.2 withdrawal. Use §12.3 only after an explicit erasure request and authorization. | Report `no capture`, the withdrawn item/source scope, or the authorized erasure scope. State whether retained content remains recoverable. |

An isolated temporary workspace is still part of the external-execution surface, not Memory. Its exploratory code is normally discardable runtime/workspace state and MUST NOT be captured merely because it exists. Isolation must be verified: uncommitted files inside the temporary location, commits on a temporary branch, commits on an original-project branch, and pushed effects have different cleanup paths. If the temporary location contains unique uncommitted work, enumerate it and obtain the confirmation required for destructive disposal. A plain `forget` request from an authority over the bounded Memory scope authorizes removal of the exploration's future influence; otherwise it is a proposal for that authority. It never silently authorizes destruction of unique bytes.

A rule already promoted from Memory into Conventions or Steering is no longer controlled solely by the Memory item. The Agent MUST surface that derived artifact and its source relationship, then apply the owning artifact's revision or revocation authority. Until that separate effect is resolved, the receipt must say that complete influence removal remains partial; Memory withdrawal alone MUST NOT be presented as revoking an authorized standing rule.

The response to a forget request is a **surface receipt**, not the phrase "forgotten" by itself:

```text
Context / Workspace: <closed or redirected; no selective context erasure claimed without verified runtime support>
Original project: <clean, or exact residual effects and separately authorized action>
Temporary exploration workspace: <absent, retained, safely disposable, disposed, or awaiting destructive confirmation>
Promoted / derived artifacts: <none found, exact governed artifacts and disposition, or unevaluated>
Memory: <no capture, withdrawn scope, reinstated scope, or authorized erasure receipt>
```

### 12.2 Reversible withdrawal

Withdrawal is an attributable control event that removes a bounded scope from ordinary retrieval, activation, distillation, surfacing, and action while preserving allowed history for audit and possible reinstatement. It does not declare the withdrawn content false, and it is not deletion. Use it for abandoned or confused exploration, an owner decision to stop using a conclusion, or another bounded influence-removal request.

If the scope has not entered Memory, **non-admission is the complete Memory action**. A `WithdrawalRecord` is optional unless another residual influence path exists. Do not copy the failed exploration into Memory merely to say that it was withdrawn.

If an item, archive segment, source scope, or derived artifact already entered Memory, append a content-minimal `WithdrawalRecord`:

```yaml
withdrawal_id: memwd-YYYY-MM-DD-NNN
record_type: withdrawal-control-v1
action: <withdraw | reinstate>
scope:
  memory_item_ids: []
  archive_refs: []
  source_or_run_refs: []
reason: failed-exploration
decided_by: <attributable owner or authority reference>
decided_at: <timestamp>
effect: <exclude-from-influence | restore-eligibility>
supersedes: <required for reinstate; optional prior control event for withdraw>
```

The record MUST contain at least one scope selector and identify a bounded scope without restating withdrawn content. Selector arrays denote the union of their stable identifiers; order and duplicate identifiers are semantically irrelevant, and empty selector arrays are absent for normalization. Two records have the same exact scope only when their normalized selector categories and identifier sets are equal. `decided_by` MUST identify an actor authorized for the selected scope. `reason` is explanatory metadata, not a truth verdict. Bindings MAY define a closed reason vocabulary, but MUST NOT reinterpret withdrawal as `Confidence: unknown`, `Status: stale`, or `pending-cleanup`: those fields express different epistemic or review states. `action: withdraw` requires `effect: exclude-from-influence`. `action: reinstate` requires `effect: restore-eligibility`, the same exact normalized scope as its controlling withdrawal, and a `supersedes` reference to that withdrawal. Reinstatement removes that withdrawal gate; it does not make an item current, true, or otherwise exempt from its ordinary `Status`, `Confidence`, retrieval, and review rules. Control records are append-only; their causal supersession chain, not wall-clock last-writer-wins, determines the latest applicable effect. A new event for the same exact scope MUST reference the prior controlling event. When multiple scopes apply to an item or source, any applicable causally unresolved withdrawal keeps it excluded. Conflicting applicable events without one causal order therefore fail closed to exclusion and require attributable reconciliation.

Before using dependent content, every Memory consumer MUST apply the latest applicable withdrawal or reinstatement event. In particular:

- retrieval and Active Workspace activation exclude actively withdrawn items from factual, historical, analogy, and action-premise roles unless the user explicitly requests an audit of the withdrawal;
- Autodream skips withdrawn archive/source scopes before extracting, merging, cooling, or updating index/topics;
- review does not mistake a withdrawn archive segment for an undistilled segment;
- Auto-Walk must not use a withdrawn item as seed, neighbor, support, or discharge target while the event is active;
- backup, export, migration, and replication preserve the applicable control event with the affected content, so a target or returning replica applies it before exposure.

This is the anti-resurrection rule. A copy, old archive, review pass, re-distillation, derived topic, generated index, import, or offline replica MUST NOT restore current influence merely because the underlying bytes still exist. A binding that cannot keep an applicable withdrawal event with retained content must exclude that content from transfer or fail closed.

The protocol does not add `withdrawn` to the §9 item `Status` enum in `memory@0.2.0`. A future version MAY materialize the control event as an item status after a real durable-item withdrawal validates the need. Until then, `WithdrawalRecord` is the authoritative lifecycle effect and avoids overloading `stale` as a terminal state.

### 12.3 Authorized erasure

Erasure is the exceptional irreversible path for an explicit, scoped user, rights, or compliance requirement. It is not the default interpretation of `forget`, `withdraw`, `retire`, `revoke`, `supersede`, or ordinary cleanup. The Agent MUST obtain or cite attributable erasure authority and enumerate the affected scope before destructive execution.

The scope analysis covers, as applicable:

- inbox and item-store records;
- index and topic projections;
- source anchors and archive segments;
- operation logs or findings that may quote the content;
- Conventions, Steering, policy proposals, or other promoted/derived artifacts that quote or depend on the covered content;
- generated caches, embeddings, and other rehydratable projections;
- backups, exports, replicas, and offline holders.

Every affected holder must remove content covered by the authorization, prevent re-distillation or other resurrection, and record only a permitted content-free `erasure_tombstone` or digest. The minimum tombstone/receipt shape is:

```yaml
erasure_id: memerase-YYYY-MM-DD-NNN
record_type: erasure-tombstone-v1
scope_refs: []                 # opaque ids or anchors; never erased content
authority_ref: <attributable authorization>
decided_at: <timestamp>
executed_at: <timestamp>
holders:
  - holder_ref: <stable holder or path reference>
    result: <completed | partially-completed | unevaluated>
    limitation_ref: <optional content-free explanation or policy reference>
sanitized_replacement_refs: []
```

The tombstone MUST select at least one bounded scope, enumerate every known holder, and MUST NOT reproduce erased content. A digest of erased content is retained only when the authorization and binding threat model permit it; a low-entropy or otherwise identifying digest is not automatically content-free. If one archive object mixes erased and retained scopes, the binding must use deletable storage or create a new sanitized identity that preserves allowed material and lineage without retaining erased bytes. Dependent records must replace covered quotations or anchors with an allowed content-free `source-erased` reference and disclose lost audit/recovery capability. A promoted rule whose authority remains independently valid may be revised to remove the covered source/content rather than silently revoked; if that cannot be completed, its holder remains `partially-completed` or `unevaluated`. Append-only is the ordinary Memory rule; authorized erasure is its only destructive exception.

Backups and migrations follow the deletion-semantics requirement in the [Governed Artifact Portability and Recovery Guide](governed-artifact-portability-recovery.md#9-consistency-storage-and-recovery-evidence). Replicated surfaces follow the erasure, rejoin, suspension, and exit rules in the [Governed Artifact Replication and Exchange Guide](governed-artifact-replication-exchange.md#74-erasure-suspension-and-exit). A holder that cannot satisfy the declared erasure obligation must suspend the affected surface rather than claim success.

An erasure receipt MUST distinguish `completed`, `partially-completed`, and `unevaluated` holders or paths. It must not claim that current model context was selectively erased or that external project mutations were rolled back unless those separate surfaces were actually verified.

## 13. Archive protocol

Archive should be deterministic and should not require AI.

Steps:

1. Check whether `memory.md` has substantive content.
2. Move or append it to `archive/YYYY-MM-DD.md`.
3. Recreate a blank `memory.md` with a date header.
4. Append an archive entry to `log.md`.
5. Rotate long logs if needed.

Each `archive/YYYY-MM-DD.md` file is the protocol's `archive_snapshot` artifact: one durable capture that is append-only in ordinary operation for that date.

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
2. The archive layer is **append-only in ordinary operation**, which makes it the durable substrate for two later guarantees: it is the recovery floor for autodream's `state` supersede operations (§14), and it is the preferred anchor target for `Source` references (§9). Uncontrolled mutation breaks both. The only destructive exception is an authorized erasure under §12.3; it replaces covered references with permitted content-free lineage and records the resulting degradation rather than pretending the original recovery path still exists.

## 14. Autodream protocol

Autodream is the AI distillation stage. It operates on the two epistemic kinds (§4) under different rules — and that asymmetry is the heart of this protocol. Treating both kinds with one universal `additive-only` rule is what causes `Pending Cleanup` to grow without bound; treating both with one universal `synthesize-and-rewrite` rule is what causes hard-won lessons to disappear silently. Autodream takes the middle path: **selective supersede** for `state`, **additive plus cooling** for `knowledge`.

Inputs:

- Today's archive
- Current `index.md`
- Relevant topic pages
- Applicable withdrawal/reinstatement control records
- Memory protocol

Outputs:

- Updated `index.md`
- Updated `topics/*.md`
- `log.md` entry, with explicit records of any `supersede` and `cool` operations

### 14.1 General rules

- Preserve `Source` and source dates on every item touched.
- Resolve applicable withdrawal/reinstatement control records before reading archive content or derived items; skip every scope whose latest control effect is `exclude-from-influence`.
- Do not invent facts not present in the archive.
- Do not promote a one-off incident into a universal rule unless explicitly confirmed.
- Keep `index.md` concise.
- Split or merge topics when useful.
- Never write to `conventions.md` or to `memory/memory.md`. Autodream reads `memory.md`'s already-archived form, never the live inbox.

### 14.2 `state` items: non-destructive supersede

When today's archive contains a new value for an existing `state` `subject` (§9), autodream MAY supersede the prior value — under all four of the following constraints. Missing any one collapses this back to "blind rewrite," which is exactly what §4 warns against.

1. **Non-destructive in ordinary operation.** The prior row is not deleted. Its `Status` is updated to `superseded`, and a `superseded_by` pointer is added. The newer row appears as a fresh entry with its own date and `Source`. Recovery from an ordinary supersede misjudgment remains possible — the archive (§13) holds the original, and the prior row remains in `index.md`/`topics/*.md` as history. An authorized §12.3 erasure may intentionally remove that recovery path and MUST disclose the resulting loss. This is the SCD type-2 shape, not type-1.
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
- applicable withdrawal/reinstatement records

Tasks:
0. Resolve withdrawal/reinstatement records and exclude every actively withdrawn item, archive segment, source, or run from all later tasks.
1. Extract long-term reusable items from the eligible archive scope. Tag every new item's `kind` and `Source` (required, §9). Use `subject` for `state` items.
2. For each new `state` item:
   a. Look for an existing item with the same `subject` AND `kind: state`.
   b. If found, mark the existing row `Status: superseded`, set `superseded_by` to the new row, and add the new row dated today.
   c. Log the supersede (subject, prior date/value, new date/value) in `memory/log.md`.
   d. Never delete the prior row. Never supersede across kinds. Never supersede on text similarity.
3. For each new `knowledge` item: append it. Do not overwrite. If it appears to refute an existing `knowledge` item, set the existing item's `Status: pending-cleanup` and append the new one — do not delete.
4. Cooling pass (optional, low-risk): identify `knowledge` items unused for a long span and demote their position. Do not delete; log each demotion.
5. Resolve any `pending-cleanup` `state` items whose `superseded_by` is now known.
6. Update `index.md` as a navigation index, not a content dump. Keep it concise.
7. Append an autodream entry to `memory/log.md` summarizing exclusions, supersedes, cools, merges, and additions.
```

## 15. Retrieval protocol

Retrieval has two halves: *when* to read (§15.1, traditional retrieval-trigger logic), and *how skeptically* to read once a memory item is in context (§15.2, the trust-calibration discipline). The second half is where most retrieval protocols silently fail. An agent's blind trust in its own past records (§1) lives precisely in the gap between "I retrieved this row" and "I am about to act on what it says."

### 15.1 When to retrieve

Retrieval order:

```text
1. Hot instruction file
2. Applicable withdrawal/reinstatement control records
3. memory/index.md
4. Relevant memory/topics/*.md
5. memory/archive/*.md only for audit or source tracing
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

1. **Apply influence controls first.** Resolve the latest applicable withdrawal/reinstatement chain before exposing item text. An actively withdrawn scope is unavailable for ordinary retrieval or historical context; only an explicit audit of the withdrawal may inspect retained content under its audience and authority rules.
2. **Read the metadata next.** `kind`, `Source`, `Status`, source date, and `Confidence` when present (§9) calibrate the item. An item missing required metadata — or with a very old date and no recent corroboration — is not automatically false, but it is not load-bearing. Down-weight it and queue schema repair.
3. **Down-weight stale and superseded.** A row whose `Status` is `superseded`, `stale`, or `pending-cleanup` MUST not be used as a current factual basis. It MAY be cited as historical context if explicitly framed as such. For a `superseded` `state` row, follow the `superseded_by` pointer to the live row.
4. **Prefer the most recent `state` row by `subject`.** When two `state` rows share a `subject` and have not been reconciled by autodream, treat the older one as `superseded` and surface the discrepancy to the user (Reconcile, §15.2.1).
5. **Reconcile before acting.** If two retrieved items appear to contradict each other on the same subject — whether by `subject` collision in `state`, or by direct contradiction in `knowledge` — the agent MUST surface the conflict in its response, not silently pick one. Suppressing a conflict is the dominant blind-trust failure mode. Conflict resolution is a first-class step, not a fallback.
6. **Honour the asymmetry between memory and walk.** Auto-Walk hypotheses are already read with explicit suspicion (zero-trust gating, §12 of the walk protocol). This protocol now applies the *same* suspicion to memory itself. The previous gap — walks doubt themselves, memory does not — is the exact unguarded seam in which blind-trust failures live.

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

For `knowledge` contradictions, both items remain visible until review (§16), and the agent's response cites both rather than picking. Resolution requires evidence appropriate to the claim or a decision by the authorized owner when the conflict is about values/policy. A user's action choice does not by itself prove an external factual claim.

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
5. Resolve withdrawal/reinstatement chains and confirm that withdrawn scopes are absent from ordinary index, topic, Auto-Walk, and action paths.
6. Check whether eligible archive files were not distilled; never treat an actively withdrawn segment as missing work.
7. Verify `Source` and source dates are present (both required by §9).
8. Verify each item carries a `kind`; classify any legacy items missing it.
9. Identify missing triggers for important topics.
10. Propose cleanup before any destructive change. For erasure, require the §12.3 authority, scope, holder, and receipt checks.

Review should produce a plan before destructive changes. The default action on any ambiguous item is to retain it and lower its retrieval weight (cooling, §14.3), not to delete it.

## 17. Promotion path

Memory items can be promoted through layers as they prove stable:

```text
Memory → Conventions → Steering
```

### Eligibility vs authority

The criteria below establish promotion *eligibility*: evidence that a rule is stable enough to promote. Eligibility does not create promotion *authority*:

- Writing to Conventions or Steering requires an attributable human decision or a pre-existing constitutional grant that covers the change.
- An Agent-initiated path — live session, autodream, or metamemory — MUST NOT write Conventions or Steering directly on the strength of repeated evidence. It emits a governed promotion proposal (the §23.5 shape, which applies beyond metamemory) and waits for review.
- An Agent MAY apply the edit as the executor of a recorded authorizing decision. The authority lies in that decision, not in the Agent or in the volume of evidence.

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
3. Record the authorizing decision: the explicit human approval, or the pre-existing constitutional grant that covers this change.
4. Add it to the appropriate file only after that decision is recorded.
5. Leave a pointer or note in memory if useful.
6. Remove or mark duplicate wording to avoid contradiction.

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
| Unauthorized or premature promotion | One incident — or the Agent's own repeated observation — becomes a standing rule without an authorizing decision | §17 eligibility/authority separation; Agent paths emit §23.5 proposals |
| Archive not distilled | Knowledge stays hidden | Log archive/autodream status |
| Failed exploration is captured as durable knowledge | Confused conclusions survive task closure and influence later work | §12.1 non-admission; Active Workspace close/expiry and selective durable routing |
| "Forgotten" is claimed across the wrong surface | The user believes model context was erased or project changes were rolled back | §12.1 surface inventory and receipt; keep workspace, external effects, and Memory actions separate |
| Withdrawn content is re-distilled or re-imported | A review, Autodream pass, generated view, backup, migration, or replica silently restores influence | Apply the latest §12.2 control event before exposure and preserve it with retained content |
| Withdrawal is encoded as falsity or cleanup | Owner choice silently changes epistemic status, or a terminal decision clogs the review queue | Keep `WithdrawalRecord`, `Status`, and `Confidence` separate; `stale` remains intermediate |
| Retirement or withdrawal is encoded as erasure | Allowed history is destroyed and an ambiguous request becomes irreversible | Default to §12.2; require explicit authority and scope for §12.3 |
| Erasure leaves quoted or derived copies | Covered content survives in archive, topics, logs, embeddings, backups, or replicas | Enumerate holders, remove covered content, retain only allowed content-free tombstones, and report incomplete paths |
| Duplicate rules | Contradictions | Single source of truth; surface via Reconcile (§15.2) |
| Secrets in memory | Security leak | Never store credentials or tokens |
| Mutable-anchor `Source` corrosion | `Source` references break as mutable files get rewritten by later distillation | Prefer anchoring `Source` into the append-only archive layer (§9, §13) |

## 19. Agent-specific mapping

The table below shows common binding choices, not guaranteed current product features. Product-native entry files and hook behavior change; a binding MUST verify its runtime before claiming support. Except where a product explicitly provides storage, the `memory/` paths are created by the binding.

| Agent | Typical hot entry | Possible warm workflow | Binding-owned memory root / notes |
| --- | --- | --- | --- |
| Kiro | `.kiro/steering/*` | scripts / launchd / wrappers | `~/.kiro/memories/` |
| Codex | `AGENTS.md` | `.codex/skills/*` | `memory/` |
| Claude Code | `CLAUDE.md` | commands/hooks when available | custom `memory/` or topic files |
| Gemini | `GEMINI.md` | scripts/extensions when available | custom `memory/` |
| Copilot | `.github/copilot-instructions.md` | path-specific instructions | repo docs/memory |
| OpenCode | `AGENTS.md` | custom commands/hooks | `memory/` |
| OpenAB-hosted agent | `AGENTS.md` or agent-specific entry | usercron / skills / CLI | persistent volume or mounted workspace |

The mapping can vary. The invariant is the protocol: Hot entry, inbox capture, raw archive, distilled topics, navigable index, explicit review.

## 20. Implementation levels

| Level | Name | Capability |
| --- | --- | --- |
| `memory:L0` | Manual memory | Agent writes minimum-schema, source-aware items to `memory.md` when asked and routes a bounded forget request through the §12.1 surfaces without false completion claims. |
| `memory:L1` | Structured memory | Adds the structured item store guaranteeing stable-id persistence (§7.2), `index.md`, `topics/`, ordinary append-only `archive/`, operation log, and §12.2 withdrawal control records. |
| `memory:L2` | Scheduled archive | Raw inbox is archived automatically. |
| `memory:L3` | Autodream | AI distills archive into index/topics. |
| `memory:L4` | Review + validation | Explicit audit, cleanup, and fresh-session tests. |
| `memory:L5` | Metamemory feedback | Retrieval and decision outcomes calibrate review priority and produce governed memory-policy proposals. |

A system can start at `memory:L0` and evolve. Do not block adoption on full automation.

## 21. Validation checklist

Verify the items applicable at the claimed level and under the conditions the binding has enabled; untagged items apply from `memory:L0`.

1. A fresh session can locate the memory root.
2. (`memory:L1+`) The agent knows when to read `index.md`.
3. The agent can write a distilled note to `memory.md`.
4. (`memory:L3+`) Archive preserves `memory.md` before distillation.
5. (`memory:L3+`) Autodream does not delete existing knowledge.
6. (`memory:L1+`) `index.md` links to relevant topics with clear triggers.
7. (`memory:L1+`) A topic page has source dates.
8. (`memory:L1+`) Raw archive is not loaded by default.
9. (`memory:L4+`) `review memory` produces a cleanup plan before deletion.
10. (`memory:L4+`) A known high-risk rule still works in a fresh session.
11. Every captured item has date, stable `id`, `kind`, and `Source`; every `state` item also has `subject`.
12. An Agent-initiated Conventions or Steering change remains a proposal until an attributable human decision or an applicable constitutional grant is recorded; repeated evidence alone never authorizes the write (§17).
13. (`memory:L5`) A retrieved item's later outcome can be recorded without rewriting the original source.
14. (`memory:L5`) A single helpful or misleading outcome cannot automatically change the memory constitution.
15. (`memory:L5`) Policy changes are emitted as reviewable proposals with supporting references.
16. (`memory:L5`) Transient traces from other protocols, when present, are not persisted wholesale as Memory.
17. A bounded `forget` request produces a §12.1 receipt that distinguishes current context/workspace, external effects, and durable Memory.
18. A failed or abandoned exploration that never entered Memory remains non-admitted; the binding does not create a copy merely to withdraw it.
19. (`memory:L1+`) A `WithdrawalRecord` excludes its bounded scope from retrieval, activation, Autodream, review re-distillation, and Auto-Walk until an attributable reinstatement event supersedes it.
20. (`memory:L1+`) Backup, export, migration, and replication keep applicable withdrawal/reinstatement controls with retained content or fail closed.
21. An authorized erasure distinguishes every covered holder and path as `completed`, `partially-completed`, or `unevaluated`; retained lineage contains no erased content.

## 22. Practical use cases

Concrete implementations of this architecture:

- [Kiro Local Memory](../usecases/memory/kiro-local-memory.md)
- [OpenAB + Codex + k3s Memory](../usecases/memory/openab-codex-k3s-memory.md)
- [Failed Exploration Withdrawal](../usecases/memory/failed-exploration-withdrawal.md)

## 23. Memory evolution and metamemory feedback

Dependency boundary:

- `memory:L0`–`memory:L4` are fully standalone and do not require Active Workspace, Inner Speech, Council, Steward, or Auto-Walk.
- `memory:L5` can operate from Memory's own retrieval and outcome events. The cross-protocol connections in §23.7 are optional producers/consumers, not conformance dependencies.
- When another protocol is absent, its ids and traces are simply omitted; a binding MUST NOT fabricate them.

Memory maintenance and memory development are not the same thing.

The protocol already supports two kinds of evolution:

| Evolution | Existing mechanism | What changes |
| --- | --- | --- |
| Content evolution | capture, `state` supersede, additive `knowledge` | What the agent retains about the world and experience |
| Structural evolution | archive → topics, merge, cooling, Memory → Conventions → Steering | How experience is organized and how stable lessons gain behavioral influence |

A third kind is optional at `memory:L5`:

| Evolution | Mechanism | What changes |
| --- | --- | --- |
| Policy evolution | metamemory outcome feedback + governed proposal | How the system decides what to capture, retrieve, verify, cool, and review |

This third layer is **metamemory**: memory about how memory performed.

### 23.1 Developmental analogy and limit

Humans have memory abilities before language, but autobiographical memory develops together with language, narrative, self-understanding, time, and social remembering. Inner speech later helps maintain task goals and regulate action.

An LLM agent begins from a different condition:

> It may be linguistically mature at first run while autobiographically new.

It can explain and reason before it has durable experience with this user, project, environment, or its own recurring failures. The useful developmental path is therefore not to replay childhood language acquisition. It is to add continuity and calibration:

```text
pretrained language/world knowledge
  → captured experience
  → source-aware episodic record
  → consolidated lessons and current state
  → retrieval into Active Workspace
  → Inner Speech / Council / action
  → observed outcome
  → metamemory feedback
  → reviewed content or policy adjustment
```

The analogy motivates staged learning. It does not justify copying human reconstructive forgetting, confabulation, or identity narratives into the agent.

### 23.2 Retrieval and feedback events

A binding MAY record the retrieval itself as a `retrieval_record`:

```yaml
retrieval_id: memret-2026-07-15-001
task_id: task-001
memory_item_ids:
  - mem-2026-06-01-003
use_role: action-premise
retrieved_at: 2026-07-15T10:00:00+08:00
```

It MAY then record how a retrieved memory item participated in a later action. A feedback event MAY reference the originating `retrieval_id` instead of restating retrieval details:

```yaml
event_id: memfb-2026-07-15-001
task_id: task-001
retrieval_ref: memret-2026-07-15-001
memory_item_ids:
  - mem-2026-06-01-003
workspace_id: ws-2026-07-15-001
use_role: action-premise
action_or_decision: "Used the recorded deployment path"
outcome: "Path matched the live host and the diagnostic completed"
verdict_scheme: intervention-outcome-v1
verdict: helpful
attribution_confidence_scheme: ordinal-confidence-v1
attribution_confidence: medium
evidence_refs:
  - runtime:host-check-2026-07-15
observed_at: 2026-07-15T12:00:00+08:00
```

Allowed `use_role` values SHOULD be a closed set such as:

- `background`
- `action-premise`
- `constraint`
- `analogy`
- `conflict-source`
- `verification-target`

Allowed verdicts:

- `helpful` — materially supported a successful or better-calibrated action.
- `misleading` — materially pushed the action in a wrong direction.
- `neutral` — was used but did not affect the outcome.
- `unknown` — outcome or causal contribution cannot yet be judged.

The event references the original item. It does not rewrite history or replace `Source`.

### 23.3 Evidence discipline

Outcome feedback is itself testimony and must be treated skeptically.

1. **Use is not usefulness.** Frequent retrieval may indicate a broad trigger, not high value.
2. **Success is not causation.** A successful task does not prove every retrieved item helped.
3. **Failure is not item falsity.** Execution may fail for unrelated reasons.
4. **Self-rating is weak evidence.** An agent saying that its memory helped is `inferred` until supported by an observable outcome or human confirmation.
5. **One event is not a policy.** Individual feedback changes review priority at most; repeated patterns support proposals.

### 23.4 Allowed content effects

Metamemory feedback MAY:

- raise review priority for a repeatedly misleading item;
- add `corroborating_refs` from a genuine external confirmation;
- propose a confidence change with cited evidence;
- suggest cooling an item that repeatedly activates but never affects action;
- suggest widening or narrowing an index trigger;
- create a conflict requiring Reconcile;
- propose a new capture or verification rule.

It MUST NOT:

- silently delete `knowledge`;
- supersede `state` without the §14.2 exact-kind/exact-subject rules;
- convert peer agreement into factual confirmation;
- treat retrieval frequency as truth;
- persist a full Active Workspace or Inner Speech stream as Memory;
- change Conventions, Steering, or the Memory protocol automatically.

### 23.5 Policy proposal

The governed proposal is the single shape for any Agent-initiated change to memory policy or promotion into Conventions/Steering (§17). Metamemory feedback is one emitting path; a live session proposing a stable rule from repeated experience is another. `supporting_refs` cites whatever evidence the emitting path actually has — metamemory feedback events, memory item ids, archive anchors, or recorded user statements:

```yaml
proposal_id: mempolicy-2026-07-15-001
target: retrieval-trigger:environment-state   # a memory-policy element, or a proposed Conventions/Steering rule
proposed_change: "Require live verification when source age exceeds 30 days"
supporting_refs:
  - memfb-2026-06-02-004
  - memfb-2026-06-19-002
  - memfb-2026-07-15-001
expected_benefit: "Reduce actions based on stale host state"
risk: "Adds verification latency to stable environments"
status: pending-review
```

Proposals follow the §17 promotion discipline:

```text
supporting evidence accumulates
  → candidate proposal in the review queue
  → repeated evidence establishes eligibility only
  → an attributable human decision or pre-existing constitutional grant authorizes the write
  → Convention when stable
  → Steering only if it must change every relevant action
```

The memory system may learn about its own performance. It may not amend its own constitution without governed review.

### 23.6 Optional binding capabilities

A `memory:L5` binding SHOULD expose:

```text
record_retrieval(task_id, memory_item_ids, use_role)
record_outcome(task_id, outcome, evidence_refs)
attribute_feedback(task_id, memory_item_ids, verdict, attribution_confidence)
list_feedback(memory_item_id)
propose_policy_change(target, supporting_refs, expected_benefit, risk)
```

These operations are optional below `memory:L5`. A conforming `memory:L0`–`memory:L4` binding remains valid without them. `record_retrieval` emits the `retrieval_record` artifact (§23.2).

`attribution_confidence` uses `ordinal-confidence-v1` (`low | medium | high`) and measures confidence that the cited memory item materially contributed to the outcome. It does not change the original item's `epistemic-status-v1` value.

### 23.7 Connections to other protocols

- [Active Workspace](agent-first-active-workspace.md) records which memory items became action premises and emits task outcomes.
- [Inner Speech](agent-first-inner-speech.md) may challenge a stale or misleading activation; only the later observable result becomes feedback.
- [Council](agent-first-council.md) may compare conflicting memory claims, but its vote is not confirmation. A verified DecisionRecord/outcome enters through capture.
- [Auto-Walk](agent-first-auto-walk.md) remains lateral. Its hypothesis lifecycle and feedback cannot be used as a shortcut to improve memory confidence.

### 23.8 Final metamemory boundary

```text
Memory may evolve its contents.
Memory may evolve its organization.
Memory may evaluate how retrieval performed.
Memory may propose changes to its own policy.

Memory may not silently redefine what counts as truth,
what may be deleted,
or what controls the agent.
```

## 24. Final rule

Agent-first memory is not a file. It is a pipeline whose product is calibrated trust:

```text
Hot controls behavior.
Conventions stabilize rules.
Inbox captures, with kind.
Archive preserves, append-only except for authorized erasure.
Withdrawal removes bounded influence without rewriting truth or external effects.
Autodream distills — supersedes `state`, accumulates `knowledge`.
Index navigates with trust signals visible.
Topics retain knowledge.
Retrieval reads skeptically, surfaces conflicts.
Review corrects drift; humans hold the erasure key.
```

The adversary is not forgetting. It is the agent's blind trust in its own past records. Every field on every item — `kind`, `Source`, `Status`, source date — exists to keep that trust honestly calibrated. Lose the calibration and `additive-only` is no longer a memory system; it is a hoard.
