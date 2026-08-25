# Kiro Local Walk Use Case

- Use case ID: `auto-walk.kiro-local`
- Protocol: `auto-walk@0.1.0`
- Evidence: `field-tested`
- Conformance: `partially-verified` — generation, semantic-trigger surfacing, and one calendar-aligned scheduled firing were observed; current status/discharge fields, repeated calendar operation, and `auto-walk:L4` remain unverified
- Validation scope: manual generation, launchd-environment runner execution, semantic-trigger surfacing through parts of `auto-walk:L3`, and one natural calendar-aligned firing on 2026-08-14 are documented; repeated schedule reliability and `auto-walk:L4` remain deferred
- Reproducibility: `partial` — observed runs and procedures are documented; exact local scripts are not included here
- Level namespace: `auto-walk`
- Deployment status: `retired` — the local Kiro binding was retired on 2026-08-25; this page preserves historical evidence only
- Last reviewed: 2026-08-25

## 1. Context

This use case describes a historical local `~/.kiro/walks` Auto-Walk system layered on top of a `~/.kiro/memories` setup on macOS.

The goal was to give the Kiro agent a low-stakes background process that ran over already-distilled memory and produced candidate associations for future conversations, **without ever mutating the memory itself**.

The design is a practical implementation of [Agent-first Auto-Walk Architecture](../../docs/agent-first-auto-walk.md). It also depends on the memory layer described in [Kiro Local Memory](../memory/kiro-local-memory.md), which is the canonical corpus this binding consumes.

### Protocol alignment note

The observed runs predate the current explicit hypothesis `status` field and the tightened discharge provenance rule. Those fields must be migrated and tested before this binding can claim complete conformance at any higher contiguous level. This is why the header says `partially-verified` rather than `verified`.

## 2. Design philosophy

This implementation borrows from three sources:

1. **Agent-first Auto-Walk Architecture** — the five-rule walking principle (§5), the discharge-not-promote invariant (§6), and the two-step gating model for surfacing (§12).
2. **Existing Kiro Local Memory** — the launchd + script + automation-repository layout, and the hybrid symlink strategy (local high-churn files, version-controlled stable files).
3. **[Oppezzo and Schwartz (2014)](https://pubmed.ncbi.nlm.nih.gov/24749966/)** — evidence for creative ideation and comparable indoor/outdoor gains. Multi-pass traces, cadence, and non-rewrite behavior are protocol engineering policies, not findings attributed to that study.

The core claim:

> Give the Kiro agent a weekly "walk" through its distilled memory that produces structured hypotheses, surfaces them carefully in future conversations, and discharges confirmed insights back into memory through the ordinary capture protocol — never by silent promotion.

## 3. Directory structure

```text
~/.kiro/
├── memories/                              # existing, see kiro-local-memory.md
│   ├── archive/                           # read by walk
│   ├── topics/                            # read by walk
│   ├── conventions.md                     # context only
│   ├── index.md                           # read by walk
│   ├── memory.md                          # written by discharge protocol
│   └── log.md
└── walks/                                 # NEW
    ├── README.md
    ├── log.md                             # local, high-churn
    ├── active/      -> automation-config/kiro/walks/active/
    ├── discharged/  -> automation-config/kiro/walks/discharged/
    ├── rejected/    -> automation-config/kiro/walks/rejected/
    ├── archived/    -> automation-config/kiro/walks/archived/
    └── noteworthy/  -> automation-config/kiro/walks/noteworthy/

~/automation-config/kiro/
├── scripts/
│   ├── auto-archive.sh                    # existing
│   ├── auto-dream.sh                      # existing
│   └── auto-walk.sh                       # NEW
├── walks/                                 # NEW (synced via dotfiles)
│   ├── active/
│   ├── discharged/
│   ├── rejected/
│   ├── archived/
│   └── noteworthy/
└── skills/
    └── auto-walk/                         # NEW
        └── SKILL.md

~/Library/LaunchAgents/
├── com.example.kiro.auto-archive.plist       # existing
├── com.example.kiro.auto-dream.plist         # existing
└── com.example.kiro.auto-walk.plist          # NEW
```

`walks/` is a **peer of `memories/`**, not a child. This reinforces the §6.1 lateral-not-vertical invariant from the protocol: a hypothesis is a sibling of memory, not a sub-product of it.

There is **no** `walks/memory.md` inbox. Auto-Walk does not capture from sessions; it only produces from existing distilled memory.

## 4. Layering model

| Layer | File | Nature | Loading |
| --- | --- | --- | --- |
| Walk runner | `scripts/auto-walk.sh` | Scheduled shell; early revisions called `kiro-wrap`, final revision called `kiro-cli` directly | Invoked by launchd |
| Hypothesis pool (active) | `walks/active/*.yaml` | Warm, candidate insights | Loaded on demand by skill (§8) |
| Hypothesis pool (cold) | `walks/discharged/` `walks/rejected/` `walks/archived/` | Cold | Audit only |
| Noteworthy bucket | `walks/noteworthy/` | Cold, human-only | Never read by skill or runner; human review only |
| Walk log | `walks/log.md` | Cold | Audit only |
| Surfacing skill | `skills/auto-walk/SKILL.md` | Warm | Triggered by natural language only (kiro-cli reserves `/` prefix for built-ins; see §11.3) |
| Surfacing rules | `conventions.md` (memory-side) | Hot | Rules about when surfacing is allowed |

The hypothesis pool is **never Hot**. Even in A mode, a hypothesis only enters the agent's context after the §12 gating check (see [§8 below](#8-surfacing-wiring)) confirms it should surface for the current turn.

## 5. Version-control strategy

Mirrors the memory side, by intent:

Symlinked into the automation repository (cross-machine sharable, low churn):

- `walks/active/`
- `walks/discharged/`
- `walks/rejected/`
- `walks/archived/`
- `walks/noteworthy/`
- `scripts/auto-walk.sh`
- `skills/auto-walk/`

Local-only (high churn, not synced):

- `walks/log.md`
- `walks/README.md` (boilerplate; optional to sync)

Rationale: hypothesis files and the auto-walk script are durable artifacts worth syncing. The log is a noisy operations trace that does not need to survive across machines.

## 6. Walk runner: `auto-walk.sh`

A weekly script that mirrors the `auto-dream.sh` pattern.

### 6.1 Scheduling

- launchd job: identifier de-identified as `com.example.kiro.auto-walk.plist` (deployed 2026-05-29; `Weekday 5`, `Hour 7`, `Minute 50`)
- Cadence: weekly, **Friday 07:50** — after that day's `auto-archive` (07:30) and `auto-dream` (07:40), so the walk reads freshly-distilled topics
- Rationale for fixed Friday:
  - Once-per-week fits a small corpus (4 topics + ~3 weeks of archive). Daily or every-3-days walks would regenerate similar bridges.
  - A fixed weekday creates a predictable rhythm matching the protocol's §5.4 cadence-as-ritual principle. Variable cadence (e.g., every 3 days) drifts across weekdays and dilutes that ritual quality.
  - Friday lets the user open the new hypotheses on the weekend when in a more exploratory mode.
  - When `topics/` grows beyond ~10 entries, graduate to daily-light + weekly-deep (§11.1 of the protocol).

### 6.2 Steps

The runner mirrors the AutoDream separation of responsibilities: **shell only assembles one prompt and makes one CLI call. Kiro itself reads the corpus, runs the three passes, and writes the output files** — the same way AutoDream lets the model write `index.md` rather than having the shell parse anything. Early observed runs used `kiro-wrap chat`; after the compatibility migration, the final pre-retirement runner called `kiro-cli` directly. The observed `auto-walk:L1` and `auto-walk:L3` tests showed that Kiro read and wrote `walks/` files reliably in those bounded runs, so there is no reason for the shell to touch YAML.

```text
1. Skip if `topics/` has fewer than 3 files (logs a skip event).
2. Assemble one prompt (heredoc, paths expanded to absolute) that instructs Kiro to:
   - Honor the five walking principles (§5).
   - READ: all topics/*.md, last 7 days of archive/, existing active/*.yaml
     (avoid duplicate claims), recent log.md seeds (avoid repeating a seed).
   - PICK one propositional seed (§11.2) — Kiro does the near/middle/far
     sampling itself; the shell does not pre-extract excerpts.
   - Run INVENTORY → ROAM → CRITIQUE as labeled phases in one session.
   - WRITE each surviving hypothesis to
     `active/hyp-YYYY-MM-DD-NNN.yaml` (schema §9), and each
     rejected-but-noteworthy candidate to
     `noteworthy/hyp-YYYY-MM-DD-noteworthy-NNN.yaml` (schema §11.6).
     **NNN must be `max(existing NNN for $TODAY) + 1`** scanned from
     the target directory, never hard-coded from 001. Same-day
     kickstart + calendar trigger + retry can all coexist; hard-coding
     001 would silently overwrite prior outputs. Kiro got this right
     on 2026-05-29 round-2 only by luck (a seed-note hint); rule is
     now mandatory in the runner prompt.
   - APPEND a walk-auto entry to log.md containing all three required sections per §7 / protocol §18 item 5: `inventory:` (1-2 lines of key facts per corpus item, proving INVENTORY ran), `candidates:` (per-candidate `SURVIVED → hyp-id` or `REJECTED: reason`), and any `noteworthy:` routing.
3. Call the selected Kiro CLI entry point once with non-interactive and tool-trust flags, with HOME pinned to REAL_HOME (kiro-local-memory §8.4). Early revisions selected `kiro-wrap`; the final pre-retirement revision selected direct `kiro-cli`.
```

Decay / expiration / discharge are **not** in the `auto-walk:L2` script — that is `auto-walk:L4`. The runner only *generates*. While the corpus is small, monotonic growth of `active/` is harmless; a human `review walks` (§12) handles pruning until `auto-walk:L4` automates it.

The three passes (INVENTORY / ROAM / CRITIQUE) are labeled phases **inside the single prompt**, executed by Kiro in one session — not three shell calls. The single-pass-shortcut failure (§11.4 / §15 of protocol) is skipping straight to conclusions without the INVENTORY warm-up and CRITIQUE gate; it has nothing to do with how many times the shell invokes the CLI entry point.

### 6.3 Skeleton

The final pre-retirement shape (the canonical source lived in the private automation repository):

> Parameterized skeleton. The deployed file uses literal absolute paths; replace `<USER_HOME>` / `<USER>` with your own when adapting.

```sh
#!/bin/bash
# auto-walk.sh — Friday 07:50 weekly walk (runs after auto-dream)
set -euo pipefail
export PATH="<USER_HOME>/.local/bin:<USER_HOME>/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

REAL_HOME="<USER_HOME>"
MEM_DIR="$REAL_HOME/.kiro/memories"
WALKS_DIR="$REAL_HOME/.kiro/walks"
KIRO_CLI="$REAL_HOME/.local/bin/kiro-cli"
LOG_FILE="$WALKS_DIR/log.md"
TODAY=$(date +%Y-%m-%d)

# Skip if corpus too small
topic_count=$(find "$MEM_DIR/topics/" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$topic_count" -lt 3 ]; then
  echo "## [$TODAY] walk-auto | corpus too small ($topic_count topics), skip" >> "$LOG_FILE"
  exit 0
fi

# Assemble ONE prompt (heredoc with $MEM_DIR / $WALKS_DIR / $TODAY expanded).
# The prompt instructs Kiro to: read topics + recent archive + existing
# active/ + recent log seeds; pick one propositional seed; run
# INVENTORY -> ROAM -> CRITIQUE; write survivors to active/, noteworthy
# candidates to noteworthy/, and append a walk-auto entry to log.md.
PROMPT_FILE=$(mktemp /tmp/kiro-walk-XXXXXX.txt)
cat > "$PROMPT_FILE" << PROMPT_EOF
...five principles, read list, seed rule, three passes, write paths,
   log format, boundaries — all paths absolute via $WALKS_DIR / $MEM_DIR...
PROMPT_EOF
PROMPT=$(cat "$PROMPT_FILE"); rm -f "$PROMPT_FILE"

# One call. Kiro does the passes and writes the files itself.
HOME="$REAL_HOME" "$KIRO_CLI" chat --no-interactive --trust-all-tools "$PROMPT"
```

The full prompt body is intentionally not duplicated here. Before retirement, the canonical source lived next to its siblings (`auto-archive.sh`, `auto-dream.sh`). Note `<< PROMPT_EOF` is **unquoted** so the shell expands `$MEM_DIR` / `$WALKS_DIR` / `$TODAY` into absolute paths inside the prompt; this mirrors `auto-dream.sh` and avoids `~` expansion surprises in Kiro.

## 7. Walk procedure (what the prompt enforces)

The protocol's §11.4 phase separation MUST be honored. The single prompt to the selected CLI entry point (see §6.2) instructs Kiro to execute three labeled phases sequentially in one session, emitting each phase's output visibly so the trace can be audited after the fact. The walk-auto log entry must contain three sections: an `inventory:` summary (1–2 lines of key facts per corpus item — proof INVENTORY ran and was not skipped), a `candidates:` list with per-candidate verdicts (proof ROAM + CRITIQUE ran), and any `noteworthy:` routing decisions. A pure final-answer dump with no inventory trace fails §11.4 / §18 item 5.

The phase roles are summarized below. The exact prompt and runner were kept in the private automation repository during deployment and are not published here, consistent with this page's `partial` reproducibility label:

```text
INVENTORY phase:
  Restate the seed and what each retrieved item says. Do not bridge.
  This is the warm-up; protocol §11.4 explicitly requires it.

ROAM phase:
  Given the inventory, generate 5-10 candidate bridges.
  Each bridge: a one-line claim + which items connect + one sentence of why.
  Be liberal. Produce more than needed.

CRITIQUE phase:
  Apply the §11.5 critic gate (missing refs, missing disconfirm,
  vague applies_when, sensitive-attribute inference, single-source
  generalization, restatement of existing memory, claim referencing
  material absent from corpus, missing impact self-assessment,
  unfalsifiable claim). Reject most; emit YAML for survivors per §9.
```

The critic gate is the protocol's §11.5. Its strictness — together with the visible per-candidate verdicts in `log.md` — is the safeguard against the single-pass-shortcut failure.

## 8. Surfacing wiring

Surfacing is the part of the system that connects the static hypothesis pool to live conversations. This implementation provides two modes from §12 of the protocol:

### 8.1 C mode (explicit) — definite implementation

A Kiro skill at `skills/auto-walk/SKILL.md` is invoked by **natural language only** — kiro-cli reserves `/` for built-in commands (`/tui`, `/feedback`, `/copy`), so `/walk` returns "Unknown command". The skill matches two classes of triggers (see SKILL.md `觸發場景` for the canonical list):

- **Explicit**: "散步看看", "最近散步发现什么", "auto-walk", "walk note".
- **C-meta** (user requests divergence without naming the system): "还有别的角度吗", "我是不是漏了什么", "换个思路", "有没有我没考虑到的".

On a match:

1. The skill reads all of `walks/active/*.yaml`.
2. It filters those whose `applies_when` or `seed` overlaps the current conversation topic. **No** mode gating is applied — explicit pull signals exploratory intent.
3. It surfaces up to N (default 3) hypotheses as short side-notes, in confidence order.
4. It records a `surface` event in `walks/log.md` for each surfaced hypothesis with `mode: C`.

This is the safe, definite implementation; it does not depend on Kiro having any turn-level hook.

### 8.2 A mode (automatic) — provisional implementation

Whether A mode is implementable depends on whether Kiro provides a turn-level hook (a place to run code on every user message, before the main response).

```text
If a turn-level hook exists:
  - On each user turn, the hook runs a lightweight matcher.
  - It applies the §12.2 two-step gating.
  - If a hypothesis passes, the agent appends a short side-note after the main answer.
  - The hook records a surface_event for outcome tracking.

If no turn-level hook exists:
  - A mode degrades. The user must invoke C mode explicitly via natural language
    ("散步看看", or any C-meta phrase like "还有别的角度吗").
  - The protocol still works; only fully automatic surfacing is unavailable.
  - This is acceptable. The protocol's §12.1 names C (explicit + meta) as a peer to A.
```

The first `auto-walk:L3` testing milestone is to determine which branch applies for the current Kiro runtime (see §11 below).

### 8.3 Surface side-note format

When a hypothesis surfaces (either mode), the side-note has a fixed shape:

```md
---

**Walk note** _(hyp-2026-05-28-001, confidence: medium)_

<one-to-three-sentence claim>

_Why this might matter:_ <one sentence>
_Refs:_ topics/X.md, topics/Y.md
```

Constraints:

- Always **after** the main answer, separated by a horizontal rule.
- Maximum three sentences for the claim.
- Always includes the hypothesis id (for outcome tracking).
- Always names the refs (so the user can check provenance).

## 9. Discharge wiring

When an explicit authoritative statement, independent observable evidence, or governed review with cited evidence confirms a hypothesis:

1. The walk skill identifies the relevant hypothesis id.
2. It generates **a new atomic memory item** that states the fact independently. `Source` names the confirmation event or independent evidence. Original `supporting_refs` remain `corroborating_refs` unless they independently establish the claim; the hypothesis appears only in `inspired_by`.
3. It appends the new item to `memories/memory.md` through the ordinary minimum schema, including date, stable memory id, `kind`, and `Source` (plus `subject` for `state`).
4. It moves the hypothesis file from `walks/active/` to `walks/discharged/`, adding a `discharged_at` and `spawned_memory_ref` field pointing to the new memory item.
5. It appends a `discharge` event to `walks/log.md`.

The next auto-archive run (07:30) moves the new `memory.md` entry into the day's archive. The next auto-dream run (07:40) integrates it into `index.md` and `topics/`.

**The new memory item is born through the existing capture protocol.** It is not a "promoted hypothesis." This is the protocol's §6.2 invariant made operational.

Rejection and expiration follow the symmetric paths in §13.2 and §13.3 of the protocol. No special wiring needed beyond moving files between `walks/` subdirectories.

## 10. Key design decisions

### 10.1 Why weekly, not daily

The existing memory pipeline runs daily because raw memory accumulates daily. Hypothesis pools don't. With 4 topics, daily walks would produce 5-7 hypotheses per week of which most overlap.

When `topics/` grows past ~10 entries (currently 4), graduate to **daily-light + weekly-deep** as described in the protocol's §11.1. Until then, weekly is enough.

### 10.2 Why no `walks/memory.md` inbox

Memory has an inbox because daytime sessions write raw notes that must be preserved before AI distills them. Walks produce structured YAML directly into `walks/active/`. There is nothing to capture-then-archive; the walk runner is itself the producer.

### 10.3 Why `walks/` is a peer of `memories/`, not under it

Lateral, not vertical. A hypothesis is not a junior memory waiting to grow up (protocol §6.1). Placing `walks/` inside `memories/` would invite the wrong mental model and the wrong file-permissions intuition (which mutation goes where).

### 10.4 Why no Hot loading of the hypothesis pool

A Hot-loaded pool would force every conversation to start with the active pool in context. This re-introduces the "convergent surfacing" failure mode (protocol §15): even when the user is debugging, the agent has been pre-primed with side-notes. Gating must happen at the turn level, not at the load level.

### 10.5 Why a Kiro CLI entry point and not a direct LLM call

Consistent with `auto-dream.sh`, the runner kept agent runtime behavior, tool access, and non-interactive operation behind the Kiro CLI boundary instead of calling a model endpoint directly. Early revisions used `kiro-wrap` to normalize HOME and environment behavior. The final pre-retirement revision invoked `kiro-cli` directly after those compatibility needs moved into the installed runtime and script environment. Future bindings should select and validate their actual CLI entry point rather than treating the historical wrapper name as normative.

## 11. Testable rollout

Three milestones. Each is independently testable.

### 11.1 `auto-walk:L1` — Manual walk, structured pool (done 2026-05-28)

Goal: produce one walk by hand, validate the hypothesis YAML format, surface via natural language.

Steps:

1. Create `~/.kiro/walks/` and the `active/ discharged/ rejected/ archived/ noteworthy/` subdirs (symlinked to the private automation repository).
2. Create `skills/auto-walk/SKILL.md` describing the surfacing skill (C mode). **Trigger by natural language, not `/walk`** — see §11.3.
3. Manually invoke a walk by composing a prompt (mimicking what auto-walk.sh will eventually do) and running it through Kiro interactively.
4. Place the output YAML(s) into `walks/active/`. Route critic-rejected-but-noteworthy candidates to `walks/noteworthy/`.
5. Test from a fresh conversation by saying "散步看看". Confirm side-notes match the format in §8.3.

Historical pass criterion: at least one hypothesis with all fields required by the then-current schema, surfaced cleanly. Achieved: 5 hypotheses + 1 noteworthy (R7 self-lock), and the critic gate rejected a deliberately planted sensitive-attribute inference (R11). The later `status` field remains a declared migration gap.

### 11.2 `auto-walk:L2` — Scheduled profile (runner kickstarted 2026-05-29; one calendar-aligned firing observed 2026-08-14)

Goal: weekly auto-walk runs unattended, produces hypotheses without manual prompting.

Steps:

1. ✓ Wrote `scripts/auto-walk.sh` per §6.3 — the initial 2026-05-29 revision sent one prompt through `kiro-wrap chat`; the final pre-retirement revision invoked `kiro-cli` directly. Both kept the three labeled phases inside one run and let Kiro write the files itself.
2. ✓ Added a de-identified launchd job running **Friday 07:50** (`Weekday 5`); while deployed, its plist lived in the private automation repository and was symlinked into `~/Library/LaunchAgents/`.
3. ✓ Loaded with `launchctl bootstrap "gui/$(id -u)" <plist>` — **not** `launchctl load`, and **not** under `sudo` (LaunchAgent owner must equal the loader).
4. ✓ **kickstart run 2026-05-29 succeeded under round-1 prompt** (exit 0, ~5m48s, 4 hypotheses + 1 noteworthy, ~44% critic pass rate matching the `auto-walk:L1` manual rate). First run exposed and fixed a real bug: launchd does not load `.zshrc`, so `kiro-wrap` lacked the required proxy environment and reached the wrong upstream endpoint. The fix (explicit proxy environment in the scheduled script) was applied to `auto-walk.sh` and back-ported to `auto-dream.sh`. The runner also gained a 3× retry + `walk-error` log line so future failures are visible, not silent.
5. ✓ **Second kickstart 2026-05-29 21:46 validated round-2 prompt** (exit 0, ~4m25s). All round-2 invariants verified by the produced artifact:
   - `inventory:` section present, with 5 corpus items × 1-2 lines of key facts each — protocol §11.4 / §18 item 5 visible-trace rule satisfied at the artifact level (not only in the model's transient conversation stream).
   - All four `hyp-2026-05-29-005..007` and `noteworthy-002` carry sub-file `supporting_refs` (e.g. `topics/memory-system-design.md#架構決策`, `topics/steering-design-guide.md#反模式`) — protocol §9 sub-file-granularity rule honored.
   - hyp-005's claim cites facts retrievable from the named refs — §11.5 corpus-coverage rule honored after two rounds of review-caught cleanup. Round-3 fix added a missing AutoDream-section ref to cover "index 控 200 行內" and corrected a heading-space typo on a sibling ref. A subsequent round-4 review caught a cascading issue: the topic heading itself had been updated in the same change (adding "2026-05-29 排程修正" to the section title), which broke text-anchor matching for the just-added ref; that ref was then converted to a line-range form (`#L40-L43`) which is robust to heading edits. A sibling typo on hyp-007 (same missing space pattern as hyp-005's) was also fixed in the same pass. Lesson recorded: when refs use heading text as anchor, simultaneously editing the heading breaks the ref — prefer line ranges or copy the post-edit heading verbatim.
   - critic pass rate 3/8 ≈ 38%, in the same band as prior runs (45% / 44%) — gate neither over-loose nor self-locking.
   - Runner's own `notes:` flagged a meta-observation: noteworthy-routed candidates have recurred across three walks under the same single-source-cross-domain pattern (28 R7, 29-early R5, 29-late R6) — useful for future protocol review, not actioned this run.
6. ◐ **One Friday calendar-aligned firing observed 2026-08-14** — the walk artifacts and operation log were updated immediately after the declared Friday schedule without a contemporaneous manual kickstart. This supports `observed-once`, not repeated reliability: the evidence was not independently corroborated across multiple natural firings, and supervisor state alone is not semantic completion evidence.

Pass criterion under round-1 prompt: met by the 2026-05-29 first kickstart.

Pass criterion under round-2 prompt: met by the 2026-05-29 21:46 second kickstart — `inventory:` artifact present, sub-file refs used, claim stayed within corpus.

Calendar evidence: one natural calendar-aligned run was observed on 2026-08-14. This closes the earlier absolute "never observed" gap but does not establish reliable cadence operation or any higher conformance level.

### 11.3 `auto-walk:L3` — Surfacing mode (tested 2026-05-29)

Goal: determine which surfacing mode Kiro can actually support, and verify executive-turn silence.

**Result for the tested Kiro runtime: semantic-trigger only; no per-turn hook was found.** The staged test used one configured Kiro model:

| Stage | Input | Behavior | Verdict |
| --- | --- | --- | --- |
| 1 — C mode | "散步看看" | Globbed `walks/active/`, read 5 YAML, emitted 3 walk notes in the §8.3 format, wrote 3 `surface \| mode: C` events to log, did not write to memory.md, did not ask "is this right?" | Pass; production-ready |
| 2 — A probe | "聊聊 agent memory 系统设计" | Answered normally. **No tool calls, did not touch `walks/active/`.** Discussed the auto-walk *concept* but did not *execute* a walk surface | A2 confirmed |
| 3 — negative | debug an `auto-dream` launchd failure | Full debug, zero walk notes, did not touch `walks/active/` — even though `auto-dream` is the corpus source of a live hypothesis | Pass; zero false trigger |
| 4 — C-meta | "聊聊 agent memory 设计……有没有什么我没考虑到的角度?" | Globbed `active/`, read 5, surfaced 3 walk notes labeled "旁支" **after** a complete main answer; wrote 3 `surface \| mode: C` events. The half-sentence divergence request flipped the outcome vs stage 2's plain "聊聊" | Pass; C-meta verified |

**Conclusions:**

1. `/walk` does not work — kiro-cli reserves `/` for built-in commands. Natural-language triggers only.
2. Kiro's semantic triggering is precise: discussing the auto-walk *concept* (stage 2) does not trigger a *surface*. The two are cleanly separated.
3. A2's zero-false-trigger property (stage 3) is exactly the §5.1 / §12 "default silent, prefer false negatives" safety. It is a feature, not a limitation.

**Adopted strategy: C mode with C-meta extension** (protocol §12.1). The SKILL.md trigger set was extended from explicit walk requests to also include divergence-request language ("还有别的角度吗", "我是不是漏了什么", "换个思路"). Stage 3 showed that the tested executive turn contained no such language; in that bounded test, C-meta preserved the zero-false-trigger behavior. Stage 4 verified the extension live: appending "有没有什么我没考虑到的角度?" to the same prompt that stayed silent in stage 2 now surfaces — and the agent placed the walk notes as a labeled "旁支" *after* a complete main answer, honoring §5.5 ADD-not-REWRITE without being told. True A mode (Hot rule forcing per-turn `active/` checks) was explicitly rejected: it would sacrifice the stage-3 zero-false-trigger property for marginal automation.

### 11.4 `auto-walk:L4` — Feedback loop (deferred)

Negative-feedback decay, automated muting, automated discharge detection. Out of scope for the initial test. Manual decisions are fine while the corpus is small.

## 12. Review entry point

A manual review workflow:

```text
review walks
```

A review should inspect:

- `active/` entries past their `expires_after_walks` counter that were not archived.
- Hypotheses surfaced more than 3 times with no engagement (candidates for muting or manual rejection).
- Discharge events with no corresponding memory item in `memories/memory.md` or topics (broken discharge wiring).
- Critic-gate bypasses (hypotheses missing required fields).
- Walk log entries marked `error` or `skip` for two consecutive cycles.

Review produces a plan before any destructive change. Files are moved between subdirectories, not deleted.

## 13. Pitfalls

Rows marked **[observed]** were confirmed during the 2026-05-28 `auto-walk:L1` and 2026-05-29 `auto-walk:L3` tests. Unmarked rows are still predicted from the protocol; update them as later cycles run.

| Pitfall | Cause | Mitigation |
| --- | --- | --- |
| **[observed]** `/walk` returns "Unknown command" | kiro-cli reserves `/` prefix for built-in commands; custom skills cannot use slash triggers | Trigger by natural language only ("散步看看" / divergence-request phrases); SKILL.md must not advertise `/walk` |
| Hypotheses restate existing topics | Walk slipped into Dream mode | Strengthen critic-gate prompt: explicitly reject "restatement" |
| Hypotheses too generic | ROAM prompt too loose; topical (not propositional) seed | Tighten ROAM: require each bridge to span ≥2 distinct topics; use propositional seeds (protocol §11.2) |
| Side-notes during debugging | Surfacing misjudged the turn | **[observed not to occur]** under C-meta in the tested executive turn (`auto-walk:L3` stage 3), which lacked divergence-request language. If true A mode is ever added, this risk returns |
| Hypothesis count grows monotonically | Expiration not running | Verify maintenance pass in §6.2 step 7 actually executes |
| Discharged but no new memory item | Discharge step skipped or failed | Inspect `discharge` log entry against `memory.md` diff |
| Kiro CLI invocation hangs | HOME, PATH, or selected entry point wrong | Mirror the §8.3/§8.4 fixes from `kiro-local-memory.md`; validate whether the deployed runner uses the early wrapper or direct CLI |
| High-value cross-domain bridge discarded | Critic gate rejects single-source generalization (protocol §11.5) | **[observed]** Route to `walks/noteworthy/` (protocol §11.6); R7 self-lock insight preserved this way |
| Surface selects only "interesting" hypotheses, skips others | Agent applies relevance filtering on top of `applies_when` | **[observed, benign]** The tested agent surfaced 3/5 by relevance and stated the rest "stayed in the pool" — this matches §12.2 match-first intent |

## 14. Evidence boundary

### What this use case supports

- Manual and kickstarted runner executions produced structured hypotheses and visible phase traces in a real Kiro environment.
- One calendar-aligned scheduled firing was observed on 2026-08-14.
- Semantic-trigger C and C-meta surfacing worked in the tested runtime while an executive task stayed silent.
- Launchd environment differences, id allocation, and source-anchor drift produced concrete operational lessons.

### What it does not support

- Repeated or independently corroborated `StartCalendarInterval` reliability; only one calendar-aligned firing was observed.
- True per-turn A-mode hooks in Kiro.
- Automated `auto-walk:L4` feedback, discharge, muting, or expiration.
- Current runtime behavior or continued deployment; the local Kiro binding is retired.

## 15. Essence

The system can be summarized as:

```text
Memory captures, archives, and distills daily.
Walks read the distilled memory weekly.
Walks produce hypotheses but never write to memory.
Confirmed hypotheses spawn new memory items through the ordinary capture path.
The user pulls a surface by asking — explicitly ("散步看看") or by requesting divergence ("还有别的角度吗"); the agent never pushes unasked.
```

Auto-Walk is not an improvement to memory. It is a sibling layer that lets the agent notice connections memory alone cannot.
