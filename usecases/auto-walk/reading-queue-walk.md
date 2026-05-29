# Reading Queue Walk Use Case

## 1. Context

This use case describes a standalone Auto-Walk binding for a personal reading queue — daily or weekly digests of articles, HN posts, blogs, papers, and newsletters. The walk runs over digested article summaries, produces cross-article associations, and writes Walk reports for periodic reading.

The design is a practical implementation of [Agent-first Auto-Walk Architecture](../../docs/agent-first-auto-walk.md), specifically the standalone mode in §14. No agent-wiki memory is required.

This binding differs from [Kiro Local Walk](kiro-local-walk.md) and [Obsidian Notes Walk](obsidian-notes-walk.md):

- The corpus is **external content** (others' writing), not your own.
- Items are **short digests**, not full notes or distilled memory.
- Discharge does not produce "facts about yourself" — it produces "pattern observations across what you've read."
- Cadence may be **tighter** (every 3–7 days), because the queue itself moves daily.

## 2. Design philosophy

This binding borrows from:

1. **Agent-first Auto-Walk Architecture** — protocol §5, §8, §14.
2. **The "commonplace book" tradition** — recording readings and noticing cross-reading patterns has been a creative practice for centuries (Darwin's notebooks, Bacon's *Commonplaces*, Locke's reading method).
3. **Modern personal-digest patterns** — RSS reader + summarization, "newsletter of newsletters," daily-digest skills like Kiro's `x-digest`.

Core claim:

> Give your reading queue a periodic process that finds patterns across what you've read in the last several weeks — not just trending topics, but structural bridges (same problem reappearing in different domains, opposing claims about a shared question, emerging consensus you hadn't named yet).

## 3. Corpus layout

The queue and walks share one root:

```text
~/reading-queue/                           # or wherever
├── inbox/                                 # raw saves before digestion
│   └── <url-or-clip-files>
├── digests/                               # per-day or per-week digest files
│   ├── 2026-05-22.md
│   ├── 2026-05-23.md
│   └── ...
└── walks/
    ├── reports/
    ├── active/
    ├── discharged/
    ├── rejected/
    ├── archived/
    ├── noteworthy/
    ├── log.md
    └── scripts/
        └── walk-run.sh
```

The `inbox/` → `digests/` flow is the user's existing reading workflow. The walk runner only reads `digests/`.

## 4. Digest item format

Each entry in a digest file is one item. Recommended format:

```md
## <article title>

- **Source**: https://news.ycombinator.com/item?id=12345
- **Type**: hn-thread | paper | blog | newsletter | video-transcript
- **Tags**: ai-agents, memory, walking-creativity
- **Read**: 2026-05-28

### One-line ELI5
<one sentence>

### Top 3 worth noticing
1. ...
2. ...
3. ...

### My note (optional)
<your reaction or follow-up question>
```

Items can be produced by:

- Manual save + summarize while reading.
- An LLM-driven daily digest of saved URLs.
- Existing tooling: Readwise export, RSS reader + auto-summarize.
- The user's own `x-digest`-style skill (see Kiro skills).

The walk runner does not care about the production path. It only requires that digest files exist with parseable item blocks.

## 5. Item model

| Aspect | Choice |
| --- | --- |
| Item granularity | One `## <article title>` block = one item |
| Metadata | From the structured fields per item |
| Neighbors | Tags + co-occurring keywords in ELI5/top-3 + temporal proximity |

Neighbor retrieval (§11.3 of protocol):

- **Near**: shares ≥ 2 tags with seed item
- **Middle**: shares 1 tag, or appears in the same digest week as items sharing seed tags
- **Far**: shares no tags but appears in the last N weeks; sample with weight **against** the most frequent tags in the queue

## 6. Walk runner

Walk every **3–7 days** — tighter than the memory-coupled binding because the queue moves faster. Recommended starting cadence: weekly Friday, with optional mid-week light walks if the queue is very active.

Steps:

1. Skips if `digests/` covers fewer than ~7 days, or fewer than ~15 items total.
2. Picks one **propositional** seed:
   - Default: a tag or theme that appeared in ≥ 3 items in the last 2 weeks.
   - Alternative: a "cross-week recurrence" — a theme that surfaced in non-consecutive weeks (suggests latent attention you may not have named).
3. Retrieves near/middle/far items per §11.3.
4. Runs INVENTORY → ROAM → CRITIQUE per §11.4.
5. Writes hypotheses to `walks/active/`. Routes critic-rejected-but-noteworthy candidates to `walks/noteworthy/`.
6. Writes a report to `walks/reports/YYYY-MM-DD.md`.
7. Appends to `walks/log.md`.

The runner is generic; any LLM tooling works.

## 7. Output mode — Walk Report with a reading agenda

The Walk Report follows the same shape as `obsidian-notes-walk.md` §7, with one addition: a **Reading agenda** section.

```md
# Walk Report — 2026-05-28

## Seed
"Recurring tension between local-first and cloud-first design across agent tooling articles in May"

## Inventory
- HN thread on local LLMs (2026-05-15)
- Cloud-coupled agent memory announcement (2026-05-18)
- Privacy considerations blog (2026-05-22)
- ...

## Candidate associations

### hyp-2026-05-28-001 — Three articles converge on the same trade-off...
- **Refs**: digest/2026-05-15.md#hn-thread, digest/2026-05-18.md#announcement, digest/2026-05-22.md#blog
- **Applies when**: future articles about agent architecture appear in queue
- **Confidence**: medium
- **Why it may matter**: ...

## Critic rejections
- R3 — <claim> → rejected: single-source generalization
- ...

## Noteworthy
- ...

## Reading agenda (suggested follow-ups)

- The HN thread cites paper X — worth adding to queue.
- Open question across these articles: <one sentence>.
- A digest tag that should split: `agents` is too broad; consider splitting into `agent-memory` / `agent-tooling`.
```

The **Reading agenda** is the standalone analog of "side-note in conversation." It is the actionable output the user can immediately use without any agent loop.

## 8. Lifecycle adaptations

### 8.1 Discharge is observational, not factual

A confirmed hypothesis here is "a pattern across articles I've read," not "a fact about my own work." There is no agent memory inbox. The confirmation step:

- The user writes a personal note (in their notes vault, journal, or follow-up digest).
- The user moves the hypothesis from `active/` to `discharged/`.
- The discharged YAML carries an optional `note_link` field.

### 8.2 Decay is faster

Articles age out faster than personal notes. Recommended:

- `expires_after_walks: 6` for normal items (vs 12 in memory-coupled).
- The superseded path (§13.4) sees more use — a fresh walk often produces a more general version of a prior bridge.

### 8.3 No A mode

Same as `obsidian-notes-walk.md` §8.2. The report is the surface.

## 9. Key design decisions

### 9.1 Why a queue, not a full library

The walk works best on **recently-read** material. A queue of "this week's reading" is the right unit, not "everything I've ever read." Older digests can be moved to `digests/archive/` to keep the active scope tight.

### 9.2 Why tighter cadence (3–7 days, not weekly)

Reading queues turn over faster than personal notes. A weekly walk over the last 4 weeks of reading produces fresh bridges; a monthly walk would miss most.

### 9.3 Why include a Reading agenda in reports

The user's natural question after seeing a pattern is "OK, now what?" The Reading agenda answers that without requiring any conversation: "read X next," "split tag Y," "watch for Z."

### 9.4 Why human-curated digests, not pure LLM summarization

LLM-only summarization tends to flatten differences across articles. Human curation — even just deciding which articles to digest at all — preserves attention signal, which becomes input to seed selection. The walk works better when the queue itself was curated.

## 10. Testable rollout

### 10.1 L1 — Build the queue and one manual walk

1. Set up `~/reading-queue/digests/` and add 1–2 weeks of digest files. Use existing tooling (`x-digest`, manual saves, etc.) — do not block on a perfect digest pipeline.
2. Pick a propositional seed by hand.
3. Run the multi-pass prompt; write hypotheses to `walks/active/` and a report to `walks/reports/`.
4. Read the report.

Pass criterion: at least one hypothesis names a real cross-article bridge that you had not consciously noticed.

### 10.2 L2 — Scheduled

Same as obsidian §10.2 but with the tighter cadence (3–7 days).

### 10.3 L3 — Not applicable

No A mode in standalone.

### 10.4 L4 — Optional feedback loop

Similar to obsidian §10.4: track confirmation rates per topic over time.

## 11. Integration with existing tooling

If the user already has personal-digest patterns:

- **`x-digest`** (Kiro skill): outputs daily tech-news summaries. Pipe its output directly into `digests/`.
- **Readwise / Reader**: export to Markdown into `inbox/`, transform via a daily script into `digests/`.
- **RSS reader + auto-summarize** (Feedly + LLM): same pipeline.
- **Hypothesis.is / web annotations**: extract highlights as digest items.

The walk does not care about the production path. It only requires the structured digest format in §4.

## 12. Pitfalls (provisional)

| Pitfall | Cause | Mitigation |
| --- | --- | --- |
| Walks restate trending tags | Seeds picked only from most-frequent tags | Force one weekly seed from rarely-tagged items |
| Reading agenda ignored | No follow-through habit | Bundle agenda with calendar/task system; treat unread agendas as a system smell |
| Stale digests | User stops digesting articles | Skip walks when no new digests in last 14 days; log skip event |
| Cross-domain bridges feel like horoscopes | Topics too distant in language | Tighten near/middle/far ratios toward more near |
| Privacy leak in digest | Personal context bleeds into shared dotfiles | Keep `digests/` outside dotfiles by default; tag sensitive items |
| Digest format drift | Tooling produces inconsistent items | Lint pass over `digests/` before each walk |

## 13. Essence

```text
The queue holds what you've read.
The walk reads your readings periodically.
The walk produces bridges, not summaries.
The Reading agenda turns bridges into next actions.
```

Auto-Walk for a reading queue turns passive consumption into latent insight production.
