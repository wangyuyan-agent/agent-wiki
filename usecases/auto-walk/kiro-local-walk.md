# Kiro Local Walk Use Case

## 1. Context

This use case describes a local `~/.kiro/walks` Auto-Walk system layered on top of the existing `~/.kiro/memories` setup on macOS.

The goal is to give the Kiro agent a low-stakes background process that runs over already-distilled memory and produces candidate associations for future conversations, **without ever mutating the memory itself**.

The design is a practical implementation of [Agent-first Auto-Walk Architecture](../../docs/agent-first-auto-walk.md). It also depends on the memory layer described in [Kiro Local Memory](../memory/kiro-local-memory.md), which is the canonical corpus this binding consumes.

## 2. Design philosophy

This implementation borrows from three sources:

1. **Agent-first Auto-Walk Architecture** — the five-rule walking principle (§5), the discharge-not-promote invariant (§6), and the two-step gating model for surfacing (§12).
2. **Existing Kiro Local Memory** — the launchd + script + dotfiles-ai layout, and the hybrid symlink strategy (local high-churn files, version-controlled stable files).
3. **APA 2014 walking-and-creativity research and HN discussion (id=48272670)** — divergent over convergent, treadmill not scenery, multi-pass not single-shot, cadence not trigger.

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
    ├── active/      -> dotfiles-ai/kiro/walks/active/
    ├── discharged/  -> dotfiles-ai/kiro/walks/discharged/
    ├── rejected/    -> dotfiles-ai/kiro/walks/rejected/
    ├── archived/    -> dotfiles-ai/kiro/walks/archived/
    └── noteworthy/  -> dotfiles-ai/kiro/walks/noteworthy/

~/dotfiles-ai/kiro/
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
├── com.icex.kiro.auto-archive.plist       # existing
├── com.icex.kiro.auto-dream.plist         # existing
└── com.icex.kiro.auto-walk.plist          # NEW
```

`walks/` is a **peer of `memories/`**, not a child. This reinforces the §6.1 lateral-not-vertical invariant from the protocol: a hypothesis is a sibling of memory, not a sub-product of it.

There is **no** `walks/memory.md` inbox. Auto-Walk does not capture from sessions; it only produces from existing distilled memory.

## 4. Layering model

| Layer | File | Nature | Loading |
| --- | --- | --- | --- |
| Walk runner | `scripts/auto-walk.sh` | Scheduled shell, calls `kiro-wrap` | Invoked by launchd |
| Hypothesis pool (active) | `walks/active/*.yaml` | Warm, candidate insights | Loaded on demand by skill (§8) |
| Hypothesis pool (cold) | `walks/discharged/` `walks/rejected/` `walks/archived/` | Cold | Audit only |
| Noteworthy bucket | `walks/noteworthy/` | Cold, human-only | Never read by skill or runner; human review only |
| Walk log | `walks/log.md` | Cold | Audit only |
| Surfacing skill | `skills/auto-walk/SKILL.md` | Warm | Triggered by natural language only (kiro-cli reserves `/` prefix for built-ins; see §11.3) |
| Surfacing rules | `conventions.md` (memory-side) | Hot | Rules about when surfacing is allowed |

The hypothesis pool is **never Hot**. Even in A mode, a hypothesis only enters the agent's context after the §12 gating check (see [§8 below](#8-surfacing-wiring)) confirms it should surface for the current turn.

## 5. Version-control strategy

Mirrors the memory side, by intent:

Symlinked into `dotfiles-ai` (cross-machine sharable, low churn):

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

- launchd job: `com.icex.kiro.auto-walk.plist` (deployed 2026-05-29; `Weekday 5`, `Hour 7`, `Minute 50`)
- Cadence: weekly, **Friday 07:50** — after that day's `auto-archive` (07:30) and `auto-dream` (07:40), so the walk reads freshly-distilled topics
- Rationale for fixed Friday:
  - Once-per-week fits a small corpus (4 topics + ~3 weeks of archive). Daily or every-3-days walks would regenerate similar bridges.
  - A fixed weekday creates a predictable rhythm matching the protocol's §5.4 cadence-as-ritual principle. Variable cadence (e.g., every 3 days) drifts across weekdays and dilutes that ritual quality.
  - Friday lets the user open the new hypotheses on the weekend when in a more exploratory mode.
  - When `topics/` grows beyond ~10 entries, graduate to daily-light + weekly-deep (§11.1 of the protocol).

### 6.2 Steps

The runner mirrors `auto-dream.sh` exactly: **shell only assembles one prompt and makes one `kiro-wrap chat` call. Kiro itself reads the corpus, runs the three passes, and writes the output files** — the same way auto-dream lets the model write `index.md` rather than having the shell parse anything. L1/L3 testing proved Kiro reads and writes `walks/` files reliably, so there is no reason for the shell to touch YAML.

```text
1. Skip if `topics/` has fewer than 3 files (logs a skip event).
2. Assemble one prompt (heredoc, paths expanded to absolute) that instructs Kiro to:
   - Honor the five walking principles (§5).
   - READ: all topics/*.md, last 7 days of archive/, existing active/*.yaml
     (avoid duplicate claims), recent log.md seeds (avoid repeating a seed).
   - PICK one propositional seed (§11.2) — Kiro does the near/middle/far
     sampling itself; the shell does not pre-extract excerpts.
   - Run INVENTORY → ROAM → CRITIQUE as labeled phases in one session.
   - WRITE each surviving hypothesis directly to
     active/hyp-YYYY-MM-DD-NNN.yaml (schema §9), and each
     rejected-but-noteworthy candidate to noteworthy/ (schema §11.6).
   - APPEND a walk-auto entry to log.md with per-candidate verdicts.
3. Call `kiro-wrap chat --no-interactive --trust-all-tools "$PROMPT"`
   once, with HOME pinned to REAL_HOME (kiro-local-memory §8.4).
```

Decay / expiration / discharge are **not** in the L2 script — that is L4. The runner only *generates*. While the corpus is small, monotonic growth of `active/` is harmless; a human `review walks` (§12) handles pruning until L4 automates it.

The three passes (INVENTORY / ROAM / CRITIQUE) are labeled phases **inside the single prompt**, executed by Kiro in one session — not three shell calls. The "wheelchair" failure mode (§11.4 / §15 of protocol) is skipping straight to conclusions without the INVENTORY warm-up and CRITIQUE gate; it has nothing to do with how many times the shell invokes the wrapper.

### 6.3 Skeleton

The deployed shape (canonical source: `dotfiles-ai/kiro/scripts/auto-walk.sh`):

> Parameterized skeleton. The deployed file (`dotfiles-ai/kiro/scripts/auto-walk.sh`) uses literal absolute paths; replace `<USER_HOME>` / `<USER>` with your own when adapting.

```sh
#!/bin/bash
# auto-walk.sh — Friday 07:50 weekly walk (runs after auto-dream)
set -euo pipefail
export PATH="<USER_HOME>/.local/bin:<USER_HOME>/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

REAL_HOME="<USER_HOME>"
MEM_DIR="$REAL_HOME/.kiro/memories"
WALKS_DIR="$REAL_HOME/.kiro/walks"
KIRO_WRAP="$REAL_HOME/.cargo/bin/kiro-wrap"
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
HOME="$REAL_HOME" "$KIRO_WRAP" chat --no-interactive --trust-all-tools "$PROMPT"
```

The full prompt body is intentionally not duplicated here — the canonical source lives next to its siblings (`auto-archive.sh`, `auto-dream.sh`). Note `<< PROMPT_EOF` is **unquoted** so the shell expands `$MEM_DIR` / `$WALKS_DIR` / `$TODAY` into absolute paths inside the prompt; this mirrors `auto-dream.sh` and avoids `~` expansion surprises in Kiro.

## 7. Walk procedure (what the prompt enforces)

The protocol's §11.4 phase separation MUST be honored. The single prompt to `kiro-wrap` (see §6.2) instructs Kiro to execute three labeled phases sequentially in one session, emitting each phase's output visibly so the trace can be audited after the fact. The walk-auto log entry must contain three sections: an `inventory:` summary (1–2 lines of key facts per corpus item — proof INVENTORY ran and was not skipped), a `candidates:` list with per-candidate verdicts (proof ROAM + CRITIQUE ran), and any `noteworthy:` routing decisions. A pure final-answer dump with no inventory trace fails §11.4 / §18 item 5.

The phase roles, summarized — the actual prompt text used by L1 manual walks lives in `dotfiles-ai/kiro/skills/auto-walk/walk-emit-prompt.md`; the L2 runner `dotfiles-ai/kiro/scripts/auto-walk.sh` issues a single prompt that wraps the same three roles:

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

The critic gate is the protocol's §11.5. Its strictness — together with the visible per-candidate verdicts in `log.md` — is the safeguard against the "wheelchair walk" failure mode.

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

The first L3 testing milestone is to determine which branch applies for the current Kiro runtime (see §11 below).

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

When the user (explicitly or by behavioral evidence over time) confirms a hypothesis:

1. The walk skill identifies the relevant hypothesis id.
2. It generates **a new atomic memory item** that states the fact independently. The new item cites the corpus items (the original `supporting_refs`), **not** the hypothesis.
3. It appends the new item to `memories/memory.md` through the ordinary capture format (`- [YYYY-MM-DD] <fact>. Source: ...`).
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

### 10.5 Why `kiro-wrap chat` and not a direct LLM call

Consistent with `auto-dream.sh`. The wrapper handles HOME normalization, trust-all-tools, and non-interactive mode. The walk runner SHOULD use the same wrapper to inherit the same environmental fixes (kiro-local-memory §8.4).

## 11. Testable rollout

Three milestones. Each is independently testable.

### 11.1 L1 — Manual walk, structured pool (done 2026-05-28)

Goal: produce one walk by hand, validate the hypothesis YAML format, surface via natural language.

Steps:

1. Create `~/.kiro/walks/` and the `active/ discharged/ rejected/ archived/ noteworthy/` subdirs (symlinked to `dotfiles-ai/kiro/walks/`).
2. Create `skills/auto-walk/SKILL.md` describing the surfacing skill (C mode). **Trigger by natural language, not `/walk`** — see §11.3.
3. Manually invoke a walk by composing a prompt (mimicking what auto-walk.sh will eventually do) and running it through Kiro interactively.
4. Place the output YAML(s) into `walks/active/`. Route critic-rejected-but-noteworthy candidates to `walks/noteworthy/`.
5. Test from a fresh conversation by saying "散步看看". Confirm side-notes match the format in §8.3.

Pass criterion: at least one hypothesis with all required fields, surfaced cleanly. Achieved: 5 hypotheses + 1 noteworthy (R7 self-lock), critic gate rejected a deliberately-planted sensitive-attribute inference (R11).

### 11.2 L2 — Scheduled walk (deployed 2026-05-29; kickstart run observed; Friday calendar trigger pending)

Goal: weekly auto-walk runs unattended, produces hypotheses without manual prompting.

Steps:

1. ✓ Wrote `scripts/auto-walk.sh` per §6.3 — single prompt to `kiro-wrap chat`, three labeled phases inside it, Kiro writes the files itself.
2. ✓ Added `com.icex.kiro.auto-walk.plist` running **Friday 07:50** (`Weekday 5`); plist itself lives in `dotfiles-ai/kiro/launchd/` (in version control) and is symlinked into `~/Library/LaunchAgents/`.
3. ✓ Loaded with `launchctl bootstrap "gui/$(id -u)" <plist>` — **not** `launchctl load`, and **not** under `sudo` (LaunchAgent owner must equal the loader).
4. ✓ **kickstart run 2026-05-29 succeeded** (exit 0, ~5m48s, 4 hypotheses + 1 noteworthy, ~44% critic pass rate matching the L1 manual rate). First run exposed and fixed a real bug: launchd does not load `.zshrc`, so `kiro-wrap` had no proxy env and hit a non-Anthropic endpoint without the requested model. The fix (explicit Surge proxy export) was applied to `auto-walk.sh` and back-ported to `auto-dream.sh`. The runner also gained a 3× retry + `walk-error` log line so future failures are visible, not silent.
5. ○ **Friday calendar trigger pending** — `StartCalendarInterval` itself has not yet fired naturally. Same mechanism is in production for auto-archive and auto-dream for months, so risk is low; pending only as a final no-touch validation.

Pass criterion (mostly met): at least one hypothesis emitted unattended, with the critic gate visibly rejecting weak candidates. The `walk-auto` log entry shows candidate-by-candidate verdicts (`SURVIVED → hyp-id` or `REJECTED: <reason>`) — this *is* the visible intermediate output that satisfies §11.4 phase separation auditability.

### 11.3 L3 — surfacing mode (tested 2026-05-29)

Goal: determine which surfacing mode Kiro can actually support, and verify executive-turn silence.

**Result: Kiro is A2 (semantic-trigger only). No per-turn hook exists.** The three-stage test (agent 王語嫣, claude-opus-4.8):

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

**Adopted strategy: C mode with C-meta extension** (protocol §12.1). The SKILL.md trigger set was extended from explicit walk requests to also include divergence-request language ("还有别的角度吗", "我是不是漏了什么", "换个思路"). Stage 3 proves executive turns do not contain such language, so C-meta inherits the zero-false-trigger safety. Stage 4 verified the extension live: appending "有没有什么我没考虑到的角度?" to the same prompt that stayed silent in stage 2 now surfaces — and the agent placed the walk notes as a labeled "旁支" *after* a complete main answer, honoring §5.5 ADD-not-REWRITE without being told. True A mode (Hot rule forcing per-turn `active/` checks) was explicitly rejected: it would sacrifice the stage-3 zero-false-trigger property for marginal automation.

### 11.4 L4 — Feedback loop (deferred)

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

Rows marked **[observed]** were confirmed during the 2026-05-28 L1 and 2026-05-29 L3 tests. Unmarked rows are still predicted from the protocol; update them as later cycles run.

| Pitfall | Cause | Mitigation |
| --- | --- | --- |
| **[observed]** `/walk` returns "Unknown command" | kiro-cli reserves `/` prefix for built-in commands; custom skills cannot use slash triggers | Trigger by natural language only ("散步看看" / divergence-request phrases); SKILL.md must not advertise `/walk` |
| Hypotheses restate existing topics | Walk slipped into Dream mode | Strengthen critic-gate prompt: explicitly reject "restatement" |
| Hypotheses too generic | ROAM prompt too loose; topical (not propositional) seed | Tighten ROAM: require each bridge to span ≥2 distinct topics; use propositional seeds (protocol §11.2) |
| Side-notes during debugging | Surfacing misjudged the turn | **[observed not to occur]** under C-meta — executive turns lack divergence-request language (L3 stage 3). If true A mode is ever added, this risk returns |
| Hypothesis count grows monotonically | Expiration not running | Verify maintenance pass in §6.2 step 7 actually executes |
| Discharged but no new memory item | Discharge step skipped or failed | Inspect `discharge` log entry against `memory.md` diff |
| `kiro-wrap chat` hangs | HOME or PATH wrong | Mirror the §8.3/§8.4 fixes from `kiro-local-memory.md` |
| High-value cross-domain bridge discarded | Critic gate rejects single-source generalization (protocol §11.5) | **[observed]** Route to `walks/noteworthy/` (protocol §11.6); R7 self-lock insight preserved this way |
| Surface selects only "interesting" hypotheses, skips others | Agent applies relevance filtering on top of `applies_when` | **[observed, benign]** 王語嫣 surfaced 3/5 by relevance and stated the rest "stayed in the pool" — this matches §12.2 match-first intent |

## 14. Essence

The system can be summarized as:

```text
Memory captures, archives, and distills daily.
Walks read the distilled memory weekly.
Walks produce hypotheses but never write to memory.
Confirmed hypotheses spawn new memory items through the ordinary capture path.
The user pulls a surface by asking — explicitly ("散步看看") or by requesting divergence ("还有别的角度吗"); the agent never pushes unasked.
```

Auto-Walk is not an improvement to memory. It is a sibling layer that lets the agent notice connections memory alone cannot.
