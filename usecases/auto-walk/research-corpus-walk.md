# Research Corpus Walk Use Case

## 1. Context

This use case describes a standalone Auto-Walk binding for a mixed research corpus — papers, CVE entries, and personal research notes — focused on a single long-running research domain (security research, agent systems, ML, distributed systems, etc.).

This differs from [Reading Queue Walk](reading-queue-walk.md) in that items are heterogeneous (different types, different shelf lives), and from [Obsidian Notes Walk](obsidian-notes-walk.md) in that material is mostly external (others' work) annotated with personal notes.

The design is a practical implementation of [Agent-first Auto-Walk Architecture](../../docs/agent-first-auto-walk.md), specifically standalone mode (§14). No agent-wiki memory is required.

## 2. Design philosophy

This binding borrows from:

1. **Agent-first Auto-Walk Architecture** — protocol §5, §8, §11.4, §14.
2. **Research-notebook traditions** — Darwin's notebooks, Faraday's, modern academic literature reviews; the discipline of recording readings alongside one's own reactions.
3. **Security-researcher workflow patterns** — CVE tracking + technique tagging + cross-reference between primary literature and operational notes.

Core claim:

> Give a long-running research corpus a periodic process that bridges papers, CVE entries, and your own notes — surfacing "this technique reappears across these contexts" or "this paper actually answers a question that was raised in this CVE."

## 3. Corpus layout

```text
~/research/<domain>/                       # e.g., ~/research/agent-systems/
├── papers/
│   ├── 2024-claude-memory.md              # extracted summary + your notes
│   ├── 2025-attention-revisited.md
│   └── pdfs/                              # optional, original PDFs
├── cves/
│   ├── CVE-2026-12345.md
│   └── ...
├── notes/
│   └── <freeform research notes>.md
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

**One walk runner per research domain.** Do not mix `~/research/security/` walks with `~/research/agents/` walks. Cross-domain mixing dilutes bridges.

## 4. Item model

Three first-class types:

| Type | Granularity | Required metadata |
| --- | --- | --- |
| Paper | One file per paper | title, authors, year, venue, tags, links_to |
| CVE | One file per CVE | id, year, cvss, affected, tags, related_papers |
| Note | One file or section | date, tags, optional `linked_papers` / `linked_cves` |

Recommended frontmatter for papers:

```yaml
---
type: paper
title: ...
authors: [...]
year: 2025
venue: ...
tags: [memory, agent, llm]
links_to:
  - cves/CVE-2026-12345.md
  - notes/2026-03-15-agent-design.md
---
```

Recommended frontmatter for CVEs:

```yaml
---
type: cve
id: CVE-2026-12345
year: 2026
cvss: 7.5
tags: [container-escape, kubernetes]
affected: [k3s, k8s 1.28-1.31]
related_papers:
  - papers/2024-container-isolation.md
---
```

Recommended frontmatter for notes:

```yaml
---
type: note
date: 2026-05-15
tags: [agent-design, memory]
linked_papers:
  - papers/2025-claude-memory.md
linked_cves: []
---
```

Neighbor retrieval (§11.3 of protocol):

- **Near**: shares tags or has explicit `links_to`/`related_papers`/`linked_papers`/`linked_cves` references with the seed.
- **Middle**: shares one tag with seed but no explicit link.
- **Far**: same year, different topic — or cross-type (a paper near a CVE that's topically far).

## 5. Walk runner

Cadence: **weekly Friday**, same as memory-coupled. Research corpora move slowly; tighter cadence wastes work.

Steps:

1. Skips if any type has fewer than 3 items (cross-type bridges need at least minimal coverage in each type).
2. Seed selection biased toward **cross-type opportunities**:
   - A note that references a paper that touches a CVE-relevant technique.
   - A CVE family with both academic literature and operational notes.
   - A paper that has CVE applications but no notes yet (signals a gap).
3. Wander policy **mandates cross-type sampling**: at least 1 paper, 1 CVE, 1 note per walk if all three types exist.
4. INVENTORY highlights item type explicitly in the listing.
5. ROAM prompt is asked to **favor cross-type bridges** over within-type.
6. CRITIQUE adds two domain-specific rejection rules:
   - Reject hypotheses that only connect items of the same type (those are Dream-style consolidations).
   - Reject hypotheses that **infer the intent of paper authors** (same family as personality inference, §11.5).
7. Writes hypotheses to `walks/active/`. Routes critic-rejected-but-noteworthy to `walks/noteworthy/`.
8. Writes a research-flavored report to `walks/reports/YYYY-MM-DD.md`.

## 6. Walk procedure

Identical to protocol §11.4 with the cross-type bias above.

The noteworthy escape valve (§11.6) is **especially valuable** here: research domains generate many "this paper's technique might apply to this CVE class" speculations, which by nature are single-source generalizations from one paper. The `noteworthy/` bucket preserves these for explicit investigation rather than discarding them.

## 7. Output mode — Walk Report with research framing

```md
# Research Walk Report — 2026-05-28 — agent-systems

## Seed
"Long-context handling failures in agent systems may share structure with memory-leak patterns in long-running container processes"

## Inventory

**Papers**
- papers/2025-context-window-bottlenecks.md — claims: ...
- papers/2024-claude-memory.md — claims: ...

**CVEs**
- cves/CVE-2026-12345.md — memory leak in container memory manager

**Notes**
- notes/2026-03-15-agent-design.md — observations on session context drift

## Candidate associations

### hyp-2026-05-28-001 — Cross-type bridge: <claim>
- **Refs**: papers/2025-context-window-bottlenecks.md, cves/CVE-2026-12345.md, notes/2026-03-15-agent-design.md
- **Why it may matter**: ...
- **Applies when**: future paper reading on long-running processes; future CVE triage on memory management
- **Confidence**: medium

## Critic rejections
- R3 — <claim> → rejected: only connects items of the same type
- R5 — <claim> → rejected: infers author intent

## Noteworthy
- hyp-2026-05-28-006 — <single-source cross-type analogy worth investigating>

## Open questions

For research corpora, the report ends with **explicit open questions worth pursuing**:

- Does technique A from paper X actually apply to CVE class Y in practice?
- Has anyone tested the bridge proposed in hyp-001?
- Which of these hypotheses are testable in a 1-day experiment?

## Suggested next reads

- Paper P (cited by X but not yet in corpus)
- CVE family Q (referenced by note Z)
```

The **Open questions** and **Suggested next reads** sections turn the walk into a research agenda the user can act on immediately.

## 8. Lifecycle adaptations

### 8.1 Discharge takes longer

A research-corpus hypothesis is often "this bridge between paper X and CVE Y deserves investigation." Investigation can take weeks or months. Recommended:

- `expires_after_walks: 24` for research items (long shelf life — months, not weeks).
- Add an `investigation_status` field to the hypothesis schema: `unstarted | in-progress | confirmed | disconfirmed`.

### 8.2 Discharge produces new corpus items

Unlike obsidian or reading-queue walks, research-corpus discharge often produces:

- A new paper-summary file (if confirmed by literature search).
- A new note file (if confirmed by your own experiment).
- An updated CVE file (if confirmed via attack technique).

The walk runner **does not** auto-create these. The user does, then moves the hypothesis from `active/` to `discharged/`.

### 8.3 Cross-type discharge

When a hypothesis is confirmed and it bridged multiple types, the discharged YAML records all spawned artifacts:

```yaml
discharged_at: 2026-06-15
spawned_artifacts:
  - papers/2026-06-15-new-summary.md
  - cves/CVE-2026-12345.md          # updated with new technique reference
  - notes/2026-06-15-experiment-results.md
```

### 8.4 No A mode

Same as the other standalone bindings. The report is the surface.

## 9. Key design decisions

### 9.1 One walk per domain, not one walk for all research

Mixing security CVE research with ML papers in one walk dilutes bridges. Run separate walks per domain (`~/research/security/` vs `~/research/agents/`).

### 9.2 Cross-type bias is mandatory

The whole point of mixing papers + CVEs + notes is to find connections that don't exist within any single type. Without explicit cross-type bias, the walk degrades into within-type consolidation — which Dream-style processes already do better.

### 9.3 Why CVEs get equal weight to papers

CVE entries are short and dense; papers are long and broad. Without explicit equal-weight rules, the walk would systematically miss CVE-anchored bridges. The wander policy mandates at least 1 CVE per walk if CVEs exist.

### 9.4 Why no auto-classification

Items are typed by user-managed frontmatter (`type: paper | cve | note`). Auto-classification by filename or content guessing introduces failure modes that compound across the walk pipeline.

### 9.5 Why investigate-status matters

Research bridges have long investigation horizons. Without explicit status tracking, hypotheses either expire silently (lost) or stay forever (clutter). The status field is the discipline that makes long-horizon walks usable.

## 10. Testable rollout

### 10.1 L1 — Build the corpus and one walk

1. Create `~/research/<domain>/{papers,cves,notes,walks}/`.
2. Add 5–10 papers (extracted summaries with frontmatter), 3–5 CVEs, 5–10 notes.
3. Run a manual walk. Pick a seed that **explicitly spans types** (e.g., a tag that appears in at least one paper and one CVE).

Pass criterion: at least one cross-type bridge survives in `active/`.

### 10.2 L2 — Scheduled

Weekly Friday. Same skeleton as `kiro-local-walk.md` §11.2.

### 10.3 L3 — Not applicable

### 10.4 L4 — Investigation tracking

Add the `investigation_status` field. The walk runner can periodically surface active hypotheses with `investigation_status: unstarted` older than N weeks ("you flagged this in March; is it still interesting?").

## 11. Pitfalls (provisional)

| Pitfall | Cause | Mitigation |
| --- | --- | --- |
| Bridges all within-type | No cross-type bias enforced | Wander policy mandates 1 item per type |
| Author-intent inference | Walk reads "what authors meant" into papers | Critic gate explicit ban (§5 step 6) |
| CVE-driven over-claiming | Single CVE generalized to entire category | Single-source rejection; route to noteworthy if value high |
| Corpus type imbalance | Many papers, few CVEs | Skip walk until minimum coverage per type |
| Domain leakage | Walks span security + ML produce shallow results | One walk per domain, no mixing |
| Frontmatter drift | Inconsistent metadata across items | Per-type templates; lint pass before walks |
| Old hypotheses linger | No `investigation_status` discipline | L4 adds explicit status tracking |
| PDF-only items invisible | Walk reads Markdown, not PDFs | Pre-extract each PDF into a Markdown summary file with frontmatter |

## 12. Essence

```text
The corpus holds a research domain.
The walk reads across paper / CVE / note types weekly.
Cross-type bridges are the value.
Confirmed bridges become new corpus items by your own hand.
Open questions become your research agenda.
```

Auto-Walk on a research corpus is the cross-type analog of memory-coupled Auto-Walk: same protocol, same lifecycle, different item model and longer investigation horizon.
