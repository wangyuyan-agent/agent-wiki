# Agent-first Auto-Walk Architecture

## 1. Purpose

This document defines a portable exploratory association mechanism for LLM agents.

Auto-Walk is a low-stakes, cadence-driven background process. It runs over consolidated memory or any other structured corpus, generates weak but useful associations between distant items, and exposes them as candidate insights for future conversations.

It is the third layer in a stack:

```text
Compaction     — shrinks the active context when it gets too large.
Auto-Dream     — distills raw memory into clean, durable knowledge.
Auto-Walk      — wanders the distilled memory and proposes new connections.
```

The name comes from research on walking and creativity. A 2014 Stanford study found that walking specifically boosts divergent thinking (generating more candidate ideas), but offers no benefit for convergent tasks and may slightly hurt them. Auto-Walk inherits both properties. It is for proposing connections, not for solving problems.

## 2. Design goals

A good Auto-Walk system should:

1. Generate candidate associations that are unlikely to surface during ordinary task work.
2. Never mutate stable memory directly.
3. Default to silence in conversations — opt-in surfacing, not opt-out.
4. Run on a fixed cadence, not on stuck-points or user requests.
5. Treat hypotheses as a lateral artifact, not a junior version of memory.
6. Provide a discharge path so confirmed hypotheses can spawn new memory items without being promoted into memory themselves.
7. Work on any structured corpus, not only agent-wiki memory.

## 3. Non-goals

Auto-Walk is not:

- A problem solver. It must never be invoked to answer a convergent question.
- A memory cleanup process. That is Auto-Dream's job.
- A personality profiler. It must not infer psychological, medical, or other sensitive attributes.
- A promotion pipeline. Hypotheses do not become memory items; they spawn new memory items when confirmed.
- A retrieval trick. The novelty comes from the processing workflow, not from clever input selection.
- A reactive feature. It must not be triggered by failure, user frustration, or the agent feeling stuck.

## 4. Core model

Auto-Walk has one lifecycle and three boundaries.

### Lifecycle

```text
Cadence triggers a walk.
Seed selection picks a starting topic.
Walk pass wanders, bridges, and critiques.
Hypothesis pool stores candidate insights.
Surfacing exposes one hypothesis at a time in future conversations.
Discharge retires a hypothesis when it is confirmed, rejected, or expired.
```

### Boundaries

| Process | Input | Output | Mutates input? | Cadence |
| --- | --- | --- | --- | --- |
| Compaction | Active context | Smaller active context | Yes (replaces) | When context fills |
| Auto-Dream | Raw archive | Clean topics + index | Adds, marks stale | After archive, typically daily |
| Auto-Walk | Clean topics + index | Hypothesis pool | No mutation of input | Cadence, typically weekly |

The three are sequential and non-overlapping. Compaction happens during a session, Dreaming happens between sessions, Walking happens on top of dreamed memory.

## 5. The walking principle

Five rules anchor the entire design. They derive from research on walking and creativity, and they constrain every other section.

### 5.1 Divergent only — never convergent

Walking increases the production of candidate ideas. It does not improve, and may degrade, the ability to converge on a correct answer.

Therefore:

- Auto-Walk must not be invoked to solve a task, answer a question, or pick between options.
- The output of Auto-Walk is always a candidate, never a decision.
- When the user is in a convergent task, Auto-Walk output must remain silent.

### 5.2 Treadmill, not scenery

Indoor treadmill walking and outdoor walking produce equivalent gains. The benefit is in the act of walking, not in external stimulus.

Therefore:

- Auto-Walk's value does not come from clever retrieval (the "scenery").
- Auto-Walk's value comes from the processing workflow (the "treadmill").
- Retrieval can be ordinary near/middle/far sampling. The work happens in the prompt pipeline.

### 5.3 Multi-pass, not single-shot

The first 15 to 25 minutes of a walk are reportedly a "clearing cycle" before deeper association emerges.

Therefore:

- A walk pass must include at least three phases: inventory, roam, critique.
- A single-prompt LLM call labeled "find associations" is not a walk. It is a wheelchair ride.
- The cost of multi-pass is the price of admission.

### 5.4 Cadence, not trigger

Historical practitioners of walking-for-thinking (Darwin, Nietzsche, Jobs) walked on a fixed schedule, not when stuck.

Therefore:

- Auto-Walk runs on a cadence (daily light, weekly deep, milestone-bound).
- Auto-Walk is not invoked by failure, by being stuck, or by user request for help.
- The hypothesis pool is always there for future conversations to dip into.

### 5.5 Add, not rewrite

Walking generates loose associations. It does not replace the working answer.

Therefore:

- An Auto-Walk hypothesis that only adds a sidelong perspective is allowed to surface automatically (in A mode).
- An Auto-Walk hypothesis that would rewrite the main answer must wait for explicit user invocation (in C mode).
- Each hypothesis self-declares its impact level at generation time.

These five rules are the conceptual core. Failure to honor any one of them collapses Auto-Walk back into either a Dream or a wheelchair.

## 6. Boundary with memory

Auto-Walk consumes stable memory but never writes to it.

### 6.1 Hypothesis is lateral, not vertical

```text
Memory says:       "X is true."
Hypothesis says:   "A and B may be related."
```

These are different epistemic kinds. A hypothesis is not an immature memory waiting to grow up. It is a sibling artifact with its own lifecycle.

### 6.2 Discharge instead of promote

When a hypothesis is confirmed (by user statement, by repeated behavioral evidence, or by explicit review), it does not promote into memory. Instead:

```text
1. A new atomic memory item is generated, citing the corpus items
   that support it. The hypothesis is named as inspiration only,
   not as the source of truth.
2. The hypothesis itself is archived to walks/discharged/.
3. The new memory item is added through the ordinary memory capture
   protocol (memory.md inbox), not written directly to topics.
```

This preserves a hard invariant: every memory item has its own provenance and source date. No memory item is "an old hypothesis."

### 6.3 Read-only consumption

Auto-Walk reads from:

```text
- memory/topics/*.md         (stable distilled knowledge)
- memory/index.md            (current navigation)
- memory/archive/*.md        (recent N days, optional)
- memory/conventions.md      (only as situational context, never as walk material)
```

Auto-Walk writes to:

```text
- walks/active/*.yaml        (new hypotheses)
- walks/discharged/*.yaml    (confirmed, retired)
- walks/rejected/*.yaml      (refuted, retired)
- walks/archived/*.yaml      (expired, retired)
- walks/log.md               (walk events)
```

Auto-Walk never writes to `memory/`. Discharge-triggered memory items are written by the memory capture protocol, not by the walk runner.

## 7. Hot / Warm / Cold placement

Auto-Walk artifacts have a different placement profile than memory artifacts.

| Artifact | Layer | Loading |
| --- | --- | --- |
| Hypothesis pool entry (active) | Warm | Loaded on demand when a topic match occurs |
| Hypothesis pool entry (discharged / rejected / archived) | Cold | Loaded only for audit |
| Walk runner script | Cold | Invoked by scheduler, not by agent |
| Walk log | Cold | Audit only |
| Surfacing rules and gating thresholds | Hot, via conventions or steering | Loaded as agent-level rules |

The protocol explicitly forbids placing the hypothesis pool itself in Hot. A pool entry must only enter the agent's context when a gating check confirms it should surface (§12).

## 8. Portable corpus interface

Auto-Walk does not require agent-wiki memory. It requires a corpus that exposes three things:

```text
Item:      a small textual unit with a stable identifier.
Metadata:  date, tags, source, optional confidence.
Neighbors: a way to retrieve items by similarity or topic proximity.
```

Examples of valid corpora:

- `memory/topics/*.md` + `memory/index.md`     (agent-wiki memory binding)
- A personal Markdown notes vault              (Obsidian-style)
- A reading queue of digested articles         (HN, papers, blogs)
- A research corpus of papers + CVEs + notes   (security research, etc.)

Each binding defines:

1. How items are enumerated.
2. How metadata is read.
3. How neighbors are retrieved (embedding, tags, links).
4. Where the hypothesis pool is stored.
5. How (or whether) surfacing happens.

Auto-Walk does not include its own protocol document in any corpus. The protocol is mutable design material, not stable distilled knowledge. Reflection on the protocol happens through human review (§16 / §18) and through explicit conversational discussion, never through self-directed walks.

The protocol does not care about the binding. The walking principle and the lifecycle remain identical.

## 9. Hypothesis item format

A hypothesis is a small structured record. YAML is recommended for machine readability; the body MAY include free-form Markdown notes.

Recommended minimum format:

```yaml
id: hyp-2026-05-28-001
created: 2026-05-28
seed: "agent memory and divergent thinking"
claim: |
  The user may prefer agent designs that separate
  raw context, cleaned memory, and exploratory layers.
supporting_refs:
  - memory/topics/user-preferences.md#L12-L20
  - memory/topics/agent-design.md#L40-L55
confidence: medium
impact: add
applies_when:
  - User discusses agent architecture or memory design.
  - User compares layered vs flat data systems.
never_applies_when:
  - User is debugging a concrete failure.
  - User is choosing between two specific tools to ship today.
disconfirm_if:
  - User explicitly prefers a monolithic context with no separation.
expires_after_walks: 12
```

Field notes:

- `id`: stable identifier; date + ordinal is fine.
- `seed`: the topic that started this walk pass.
- `claim`: the candidate insight, one to three sentences.
- `supporting_refs`: pointers into corpus items. Required. Hypotheses without refs are discarded. **Prefer the smallest addressable unit available** (file + heading / anchor / line range); fall back to file-only when the corpus lacks anchors. File-only refs are valid but make audit and discharge harder; runners should be prompted to cite at sub-file granularity when possible.
- `confidence`: `low | medium | high`. Bias toward `low` and `medium`.
- `impact`: `add | rewrite`. Determines surfacing eligibility (see §12).
- `applies_when`: positive triggers. The conversation must look like one of these for the hypothesis to surface in A mode.
- `never_applies_when`: negative triggers. Surfacing is blocked when any of these match. Negative bounds are easier to write correctly than positive ones.
- `disconfirm_if`: explicit falsifiers. If observed, the hypothesis moves to `rejected/`.
- `expires_after_walks`: integer count of walk cycles after which an unused hypothesis is archived.

## 10. Hypothesis pool layout

A portable layout, placed as a peer of `memory/` rather than under it:

```text
<agent-home>/
├── memory/
│   └── ...
└── walks/
    ├── README.md
    ├── log.md
    ├── active/
    │   ├── hyp-2026-05-28-001.yaml
    │   └── hyp-2026-05-28-002.yaml
    ├── discharged/
    │   └── hyp-2026-05-21-003.yaml
    ├── rejected/
    │   └── hyp-2026-05-20-007.yaml
    ├── archived/
    │   └── hyp-2026-05-01-002.yaml
    ├── noteworthy/
    │   └── hyp-2026-05-28-006.yaml
    └── scripts/
        └── walk-run.sh
```

Folder semantics:

- `active/`: hypotheses currently eligible for surfacing.
- `discharged/`: confirmed; the corresponding memory item is the live artifact.
- `rejected/`: refuted by user or by counter-evidence.
- `archived/`: expired without engagement; kept for audit.
- `noteworthy/`: critic-gate-rejected candidates that a reviewer flagged as high-value (see §11.6). **Never read by the surfacing layer.** Human review only.

`log.md` records walk events: `walk-start`, `walk-emit`, `surface`, `surface-ignored`, `surface-engaged`, `discharge`, `reject`, `archive`, `noteworthy`.

`log.md` is Markdown by design — readable as a narrative trace during L1/L2. When L4 (automated decay and feedback) becomes active, a structured sidecar (e.g., `walks/runs/<date>-record.yaml`) MAY be emitted alongside `log.md` for machine parsing. The narrative log and the structured sidecar are not mutually exclusive.

Placing `walks/` as a peer of `memory/` (not as `memory/walks/`) reinforces the §6.1 invariant: a hypothesis is a lateral artifact, not a sub-product of memory.

## 11. Walk procedure

A walk pass has five phases. They MUST be separated; a single-prompt "find associations" call is not a walk.

### 11.1 Cadence

| Cadence | Trigger | Typical work |
| --- | --- | --- |
| Daily light | Scheduled (launchd / cron / CronJob) | 1 seed, 3-5 candidate hypotheses, critic gate, write 1-3 to `active/` |
| Weekly deep | Scheduled, longer window | 3 seeds, broader retrieval, longer critic pass, rotate `active/` ordering |
| Milestone | Project / task completion | 1 seed bound to the milestone, optional |

A walk runner that fires only on user request violates §5.4.

### 11.2 Seed selection

Pick exactly one seed per walk pass. Sources:

- A topic that appeared frequently in the last N days.
- A topic the user has revisited from different angles.
- A long-running project or open question.
- A randomly sampled forgotten topic (force exploration).

Do not concatenate multiple seeds into one walk pass. Multiple seeds dilute the bridge phase.

Prefer specific propositional seeds over topical labels. "agent memory" is a topic; "decay strategy as an isomorphism across memory, walks, and conventions" is a proposition. Propositional seeds bias the wander phase toward sharper bridges and make the critic gate's `applies_when` reasoning more grounded. Topical seeds tend to produce generic associations that overlap with what Auto-Dream already distilled.

### 11.3 Wander policy

Retrieve three groups of items relative to the seed:

```text
Near:    items strongly related to the seed.                ~ 5-10 items
Middle:  items in a related but distinct domain.            ~ 5-10 items
Far:     items that look unrelated, sampled with low prior. ~ 3-5 items
```

The far group is what makes a walk a walk. Without it, the pass degrades into a Dream-style consolidation. With too much of it, the pass becomes incoherent.

The wander policy is "scenery" in the sense of §5.2: it sets the stage but does not produce the value. The value comes from §11.4.

### 11.4 Multi-pass workflow

The LLM-driven part of a walk runs three sequential phases. The invariant is **phase separation with visible intermediate output**, not the number of model invocations. An implementation MAY run three separate prompt calls, or one prompt with explicitly labeled phases that the model executes and emits in sequence. Either is acceptable provided the intermediate outputs of each phase are visible in conversation, log, or sidecar — so the warm-up and the critic pass can be audited after the fact.

```text
Inventory:  Restate what the seed is, list what the retrieved items say.
            No bridging yet. This is the warm-up.

Roam:       Generate candidate bridges between items.
            Each bridge: claim + which items it connects + why.
            Be liberal here. Produce more than needed.

Critique:   Apply the critic gate (§11.5) to each candidate.
            Reject most. Keep the few that survive with full hypothesis records.
```

What fails: skipping straight to Critique-shaped output without a visible Inventory and Roam (the "wheelchair walk" — see §15). The shape of the trace matters because audit relies on it; the number of shell calls does not.

### 11.5 Critic gate

Reject a candidate hypothesis if any of the following:

- No `supporting_refs` from the retrieved items.
- No falsifiable `disconfirm_if` clause.
- No `applies_when` that points to an identifiable conversational situation.
- It infers a psychological, medical, gender, age, ethnicity, or other sensitive attribute.
- It generalizes from a single source item.
- It restates an existing memory item (this is a Dream-like consolidation, not a walk).
- Its `claim` mentions specific facts (system names, behaviors, citations, prior conclusions) that are not represented in any `supporting_refs`. Walks may not introduce material the corpus does not contain — including the Auto-Walk protocol itself (§8). If a claim wants to reference an external fact, the runner must add that source to the corpus and re-walk, not slip it in via narration.
- Its `impact` is unclear or refuses self-assessment.
- Its claim is unfalsifiable in principle.

The critic gate runs as its own prompt, separate from the roam prompt. The same LLM acting as critic, after being primed with a critic role, is sufficient.

### 11.6 Noteworthy rejections

A candidate that fails the critic gate MAY be moved to `walks/noteworthy/` instead of being silently discarded, when the candidate would otherwise constitute a high-value cross-domain analogy.

The motivation: the strictest critic-gate rule — "reject single-source generalization" — is in tension with the value of walks. Cross-domain analogies are, by nature, frequently single-source (one observation in domain A is generalized into domain B). A blanket rejection eliminates exactly the kind of bridge walks are designed to find.

The noteworthy escape valve resolves the tension without weakening the critic:

- The critic still rejects the candidate (it does not enter `active/`).
- The candidate is preserved in `walks/noteworthy/` with explicit `rejection_reason` and `flagged_value_reason` fields.
- The surfacing layer (§12) **never** reads from `noteworthy/`. The candidate cannot affect any conversation until a human reviewer rewrites it.
- A noteworthy entry becomes a real hypothesis only by being rewritten through a new walk, not by direct promotion.

Schema for a noteworthy entry differs from §9:

```yaml
id: hyp-YYYY-MM-DD-NNN
created: YYYY-MM-DD
seed: "..."
status: rejected-but-noteworthy
claim: |
  ...
supporting_refs:
  - ...
rejection_reason: single-source-generalization | unfalsifiable | ...
flagged_value_reason: |
  Why this rejection is worth preserving despite failing the gate.
human_review_outcome: ""   # filled by reviewer; values: rewrite | archive | leave
```

The `confidence`, `impact`, `applies_when`, `never_applies_when`, `disconfirm_if`, and `expires_after_walks` fields from §9 are absent. Noteworthy entries never surface; their per-conversation context fields are meaningless.

Use noteworthy sparingly. If most rejections are flagged noteworthy, the critic gate is too strict and should be tuned, not bypassed.

## 12. Conversation surfacing

Surfacing has two modes. Default is silent.

### 12.1 Two modes

```text
A — automatic surfacing:
    Agent retrieves matching hypotheses on each user turn.
    Strict two-step gating decides whether to expose.
    Output is a short side-note after the main answer.

C — user-pulled invocation:
    The user signals they want divergence. Two sub-forms:
      C-explicit: "散步看看", "walk note", or invoking the walk skill.
      C-meta:     "any other angle?", "am I missing something?",
                  "what else could this be?" — the user requests
                  divergence without naming the walk system.
    All eligible hypotheses surface (including impact=rewrite).
```

A B (push) mode is intentionally absent. Agents do not get to inject hypotheses without either user invocation or strong gating.

C-meta is the sweet spot between A and C-explicit. It surfaces on natural requests for divergence without requiring the user to know a walk system exists, yet it remains pull (the user asked) rather than push. Crucially, executive turns ("how do I fix this error?") do not contain divergence-request language, so C-meta inherits the zero-false-trigger safety of C-explicit. Whether a given agent runtime can support true A mode (auto-surface with no user request) depends on whether it exposes a per-turn hook; many runtimes are semantic-trigger only, in which case C (explicit + meta) is the production form. See the Kiro use case §11.3 for an empirical determination.

### 12.2 Two-step gating (A mode)

For each user turn:

```text
Step 1 — match (cheap, always run):
    Retrieve hypotheses whose seed or supporting_refs
    overlap with the turn's topic.

Step 2 — gate (asymmetric thresholds):
    Surface only if all of the following hold:
      - hypothesis.impact == "add"
      - any applies_when matches the turn
      - no never_applies_when matches the turn
      - mode_confidence >= exploratory threshold
      - hypothesis not in "muted" state
    Otherwise: silent.
```

The thresholds are deliberately asymmetric. A missed surfacing is recoverable (user can always invoke C mode). A wrong surfacing during a convergent task degrades the answer (§5.1). When in doubt, default to executive mode and stay silent.

### 12.3 Add vs rewrite

```text
ADD     — A side-note that does not change the main answer.
          Eligible for A mode if other gates pass.

REWRITE — A reframing that would change the answer itself.
          Never surfaces in A mode. Waits for C mode invocation.
```

Each hypothesis self-declares its `impact` at generation time. The walk-time prompt MUST ask the LLM to choose one and to justify the choice.

Why this matters: a rewrite-level hypothesis sneaking into A mode would silently change the agent's main answer, bypassing user awareness. This is the worst failure mode in the entire protocol.

### 12.4 Mode signal heuristics

Read from the user's turn structure, not from a session flag:

| Signal | Exploratory | Executive |
| --- | --- | --- |
| Sentence form | "聊聊...", "X 怎么看", "最近一直在想" | "X 还是 Y", "怎么修", "为什么报错" |
| Content carrier | Plain text, conceptual | Code block, stack trace, command |
| Decision distance | Far (thinking phase) | Near (must ship) |
| Pace | Long, exploratory framing | Short, direct |

`mode_confidence` is per-turn, not session-wide. The same conversation can swing between modes. This is intentional. The cost is occasional inconsistency in whether side-notes appear; the gain is correctness in each turn.

### 12.5 Negative feedback

After each surfacing, record a `surface_event`:

```yaml
- hypothesis_id: hyp-2026-05-28-001
  turn_id: ...
  surfaced_at: 2026-05-28T14:32:00
  outcome: engaged | ignored | rejected
```

Outcome detection:

- `engaged`: user references or follows up on the side-note.
- `ignored`: user continues on the main thread without acknowledging.
- `rejected`: user explicitly pushes back or asks to focus.

After N consecutive `ignored` outcomes (default N=3), mark the hypothesis as `muted`. Muted hypotheses are skipped in A mode but remain visible in C mode.

After one `rejected` outcome, move the hypothesis to `rejected/` immediately.

## 13. Discharge protocol

A hypothesis leaves `active/` through one of four paths.

### 13.1 Confirmed → discharged

When a hypothesis is confirmed by explicit user statement or by repeated behavioral evidence:

1. Generate a new atomic memory item that states the fact independently. The memory item cites the corpus items that support it, not the hypothesis.
2. Append the new memory item through the ordinary capture protocol (`memory/memory.md`).
3. Move the hypothesis file to `walks/discharged/`.
4. Log a `discharge` event in `walks/log.md` with a back-pointer from the discharged hypothesis to the new memory item.

This preserves the hard invariant: memory items have first-class provenance and are not "promoted hypotheses."

### 13.2 Rejected

When a hypothesis is explicitly refuted or its `disconfirm_if` clause is observed:

1. Move to `walks/rejected/`.
2. Log a `reject` event including the refuting evidence.

Rejected hypotheses are kept (not deleted) so that future walks can avoid regenerating them.

### 13.3 Expired

When a hypothesis sits in `active/` for `expires_after_walks` cycles without being surfaced or engaged:

1. Move to `walks/archived/`.
2. Log an `archive` event.

### 13.4 Superseded

When a new walk produces a hypothesis that is strictly more general than an existing one, the older one moves to `walks/archived/` with a `superseded_by` pointer.

### 13.5 Noteworthy

When a candidate is rejected by the critic gate but flagged as high-value (§11.6), it moves to `walks/noteworthy/` rather than `walks/rejected/`.

A noteworthy entry has no automatic lifecycle. It stays until a human reviewer takes action:

- **Rewrite**: the reviewer composes a fresh walk-emit pass using the noteworthy entry's claim and `supporting_refs` as seed. If the new walk produces a surviving hypothesis in `active/`, the noteworthy entry is moved to `archived/` with a `rewritten_as` pointer.
- **Archive**: the reviewer judges the entry no longer relevant and moves it to `archived/` directly.
- **Leave**: the reviewer takes no action; the entry remains in `noteworthy/` indefinitely.

Noteworthy entries **do not expire automatically**. The intent is to preserve human-flagged value over long timescales without the surfacing layer ever seeing them.

## 14. Standalone mode

Auto-Walk does not require agent-wiki memory. It can run on any corpus that satisfies §8.

### 14.1 Corpus binding requirements

A standalone binding must define:

1. Item enumeration: how the walker lists corpus items.
2. Metadata extraction: how dates, tags, sources are read.
3. Neighbor retrieval: how the walker finds near/middle/far items.
4. Pool location: where `walks/` lives.
5. Surfacing target: where insights go (a Markdown report, an agent-readable pool, or both).

### 14.2 Output for human consumption

In standalone mode, surfacing often degrades from "inject into conversation" to "write a Markdown report the user can read."

Recommended report format:

```md
# Walk Report — YYYY-MM-DD

## Seed
<one line>

## Inventory
<bullet list of what the seed touched>

## Candidate associations
- [hyp-id] Short claim.
  - Refs: ...
  - Applies when: ...
  - Confidence: ...
  - Why it may matter: ...

## Notes for review
<one paragraph for the user>
```

The report is the surface; the YAML pool is the audit substrate.

### 14.3 Surfacing fallback

If no conversational agent consumes the pool, surfacing degrades to:

- A Markdown report per walk pass (above).
- An optional digest e-mail or push notification with the top candidate.
- A manual review session where the user reads `walks/active/` and decides what to engage with.

The protocol's lifecycle still holds: hypotheses still discharge, get rejected, expire, or get superseded. Only the surfacing wire changes.

## 15. Failure modes

| Failure mode | Symptom | Prevention |
| --- | --- | --- |
| Personality pollution | Hypothesis pool fills with psychological profiling | Critic gate (§11.5) rejects sensitive-attribute inferences |
| Convergent surfacing | Walk insight interrupts user during debugging | Two-step gating + mode signal heuristics (§12.2, §12.4) |
| One-walk overgeneralization | Single corpus item produces a universal rule | Critic gate rejects single-source generalizations |
| Hypothesis pool bloat | Active pool grows without bound | `expires_after_walks` + decay scheduler |
| Stable memory contamination | Walk runner writes directly to `memory/topics/` | Read-only consumption (§6.3); discharge spawns new items, never promotes |
| Wheelchair walks | Single-prompt LLM call labeled "walk" | Multi-pass workflow (§11.4) enforced by walk runner |
| Rewrite leak | Rewrite-level hypothesis surfaces in A mode | `impact` self-declaration (§12.3) + A-mode gate |
| Surfacing fatigue | Agent injects side-notes too often | Negative feedback decay (§12.5); muted state |
| Seed concatenation | Walk pass tries to handle multiple seeds at once | Single-seed rule (§11.2) |
| Trigger-driven walks | Walk runs only when user is stuck | Cadence-not-trigger (§5.4) enforced at scheduler |
| Dream contamination | Walk produces clean consolidations, not bridges | Critic gate rejects "restatement of existing memory" |
| Sensitive inference | Hypothesis infers gender, age, health, etc. | Hard rule in critic gate; reject and log |
| High-value rejection lost | Single-source cross-domain analogy silently discarded by strict critic | Noteworthy escape valve (§11.6) |

## 16. Agent-specific mapping

| Agent | Walk runner | Pool location | Surfacing path |
| --- | --- | --- | --- |
| Kiro | launchd job invoking a walk skill | `~/.kiro/walks/` (or symlinked to dotfiles) | Skill called by agent when match found |
| Codex | usercron / CronJob | `walks/` next to `memory/` | `.codex/skills/walk-surface/SKILL.md` |
| Claude Code | scheduled command or hook | `walks/` in project root or home | Slash command + auto-check hook on user turn |
| Gemini | scheduled script | `walks/` next to `memory/` | Custom command |
| Copilot | external scheduler | `walks/` in repo | Path-specific instruction reference |
| OpenAB-hosted | CronJob with PVC | PVC-mounted `walks/` | Skill triggered by chat node |

The protocol is identical. Only the runner, pool path, and surfacing wiring vary.

## 17. Implementation levels

| Level | Name | Capability |
| --- | --- | --- |
| L0 | Manual walk | Human or agent runs a walk on demand; writes a hypothesis pool by hand. |
| L1 | Structured pool | `walks/` layout, hypothesis format, log present. |
| L2 | Scheduled walks | Cadence runner produces hypotheses without prompting. |
| L3 | Surfacing | A mode gating + C mode invocation wired into the agent. |
| L4 | Feedback loop | Negative feedback decay, discharge protocol, muting, and expiration all automated. |

Start at L0. Each level is testable in isolation.

## 18. Validation checklist

After implementing Auto-Walk for an agent, verify:

1. A walk pass produces at least one hypothesis with all required fields.
2. A walk pass rejects candidates lacking `supporting_refs`.
3. The critic gate rejects sensitive-attribute inferences (test with a deliberately bad seed).
4. Surfacing stays silent during a clearly executive turn (test with a stack trace).
5. Surfacing fires during a clearly exploratory turn (test with "聊聊 X 这个想法").
6. A `rewrite`-impact hypothesis does not surface in A mode.
7. C mode (explicit `/walk`) returns all eligible hypotheses including `rewrite`.
8. An ignored hypothesis is muted after N surfacing attempts.
9. A confirmed hypothesis discharges and spawns a new memory item, without mutating any topic file.
10. The walk runner runs on a cadence, not in response to user requests for help.
11. The `noteworthy/` folder exists, has its own schema, and is **not** read by the surfacing layer.

## 19. Practical use cases

- [Kiro Local Walk](../usecases/auto-walk/kiro-local-walk.md) — Auto-Walk over a local `.kiro/memories` setup. The canonical memory-coupled binding.
- [Obsidian Notes Walk](../usecases/auto-walk/obsidian-notes-walk.md) — Standalone Auto-Walk over a Markdown notes vault.
- [Reading Queue Walk](../usecases/auto-walk/reading-queue-walk.md) — Standalone Auto-Walk over a daily digest of articles.
- [Research Corpus Walk](../usecases/auto-walk/research-corpus-walk.md) — Standalone Auto-Walk over a mixed research corpus.

## 20. Final rule

Auto-Walk is not a process. It is a discipline:

```text
Memory says what is.
Dream cleans what was captured.
Walk wonders what might connect.
Surface adds, never rewrites.
Discharge spawns, never promotes.
```
