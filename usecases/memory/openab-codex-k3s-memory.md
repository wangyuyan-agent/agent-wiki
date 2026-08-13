# OpenAB + Codex + k3s Memory Use Case

- Use case ID: `memory.openab-codex-k3s`
- Protocol: `memory@0.1.0`
- Evidence: `field-tested`
- Conformance: `mapped` — historical lifecycle evidence maps through `memory:L4` against `memory@0.1.0`; the `memory@0.2.0` withdrawal/erasure contract and current item schema were not revalidated
- Validation scope: deployment-derived architecture, scheduling checks, and operational pitfalls; live cluster was not rechecked during the 2026-08-13 withdrawal-protocol alignment review
- Reproducibility: `partial` — the binding is environment-specific and requires an equivalent cluster/runtime
- Level namespace: `memory`
- Last reviewed: 2026-08-13

## 1. Context

This use case describes an agent memory system for a long-running OpenAB + Codex environment on k3s.

The system must let an agent:

- Keep memory across sessions.
- Preserve memory across Pod restarts, Deployment rollouts, and version upgrades.
- Separate short-term notes, long-term knowledge, and operational pitfalls.
- Distill memory automatically without letting it grow into a mess.
- Preserve a manual audit path without requiring daily human curation.

The design is a practical implementation of [Agent-first Memory Architecture](../../docs/agent-first-memory.md).

### Protocol alignment note

This deployment predates `memory@0.1.0`. Its persistence, scheduling, archive-first workflow, distillation, and operational failures are real evidence, but the documented binding still permits direct topic writes and legacy `[待清理]` markers. Before claiming current `memory@0.2.0` conformance, route captures through the inbox, add stable `id`, `kind`, `Source`, and `subject` for `state`, adopt the closed `Status` vocabulary, validate exact-subject non-destructive supersede, and implement withdrawal routing, control records, anti-resurrection, and authorized-erasure receipts. The evidence label does not certify the current schema.

## 2. Design philosophy

This design combines several ideas:

1. **OpenAB steering-design-guide** — Hot / Warm / Cold memory layering.
2. **Local Kiro memory pipeline** — `memory.md` + archive + autodream + topics.
3. **Codex instruction and skill model** — `AGENTS.md` as the hot entry and `.codex/skills/*` as triggered workflow bodies.

Final principles:

- `AGENTS.md` stores the hot behavior contract, rules, and memory entry points, not short-term memory bodies.
- `memory.md` is a hot inbox, not the final knowledge base.
- `index.md` is cold/warm navigation, not a second garbage pile.
- `topics/` stores distilled long-term knowledge.
- `archive/` stores raw snapshots and traceable evidence.
- Archive and autodream must be separated: preserve first, distill second.

## 3. Directory structure

```text
/home/node/
├── AGENTS.md
├── memory/
│   ├── README.md
│   ├── index.md
│   ├── memory.md
│   ├── log.md
│   ├── archive/
│   │   └── YYYY-MM-DD.md
│   ├── topics/
│   │   ├── user-preferences.md
│   │   ├── environment.md
│   │   ├── workflows.md
│   │   ├── decisions.md
│   │   ├── memory-system-design.md
│   │   └── operational-pitfalls.md
│   ├── scripts/
│   │   └── archive-memory.sh
│   └── k8s/
│       └── archive-cronjob.yaml
├── .openab/
│   └── cronjob.toml
└── .codex/
    └── skills/
        └── memory-manager/
            └── SKILL.md
```

## 4. Layering model

| Layer | File | Nature | Purpose |
| --- | --- | --- | --- |
| Hot entry | `AGENTS.md` | Hot | Defines identity, rules, memory protocol, and entry points |
| Hot inbox | `memory/memory.md` | Hot / Inbox | Daytime notes waiting for organization |
| Timeline | `memory/log.md` | Hot / Ops | Records archive, autodream, review, and bootstrap operations |
| Index | `memory/index.md` | Warm / Index | Navigates topic pages and recent activity |
| Raw archive | `memory/archive/*.md` | Cold / Raw | Daily raw snapshots for source tracing |
| Topic pages | `memory/topics/*.md` | Cold / Distilled | Stable distilled knowledge |
| Manager skill | `.codex/skills/memory-manager` | Warm / Workflow | SOP for write, review, and autodream operations |

## 5. File responsibilities

### `AGENTS.md`

`AGENTS.md` only does four things:

1. Defines personality and rules.
2. Tells the agent where the memory system is.
3. Defines when to read memory.
4. Defines when to write memory.

It does not store short-term memory bodies. This avoids bloat and attention dilution.

### `memory/memory.md`

This is the hot inbox.

Use it when:

- The user explicitly says “remember”, “don't forget”, “from now on”, or “this is my preference”.
- A high-value note is discovered but not yet judged worthy of long-term distillation.

Rules:

- Do not store full conversation transcripts.
- Store reusable conclusions only.
- Treat it as an inbox, not a knowledge base.

### `memory/log.md`

This is operational trace, not knowledge content.

It records:

- bootstrap
- archive
- archive-skip
- autodream
- autodream-skip
- review

It is both an audit entry point and a troubleshooting clue.

### `memory/index.md`

This is the wiki homepage.

It should:

- Tell the agent which topic to read first.
- Maintain a recent activity section.
- Track topic status.
- Stay small enough to scan quickly.

It should not:

- Paste archive content back into the index.
- Carry long bodies of text.

### `memory/topics/*.md`

These are the real long-term knowledge pages.

Current topic categories:

- `user-preferences.md` — long-term user preferences, language, style, and tool boundaries.
- `environment.md` — k3s, OpenAB, Codex, PVC, scheduling, and deployment facts.
- `workflows.md` — memory write, archive, autodream, and review SOPs.
- `decisions.md` — confirmed architecture and strategy decisions.
- `memory-system-design.md` — design of the memory system itself.
- `operational-pitfalls.md` — implementation pitfalls and fixes.

### `memory/archive/*.md`

Archive files preserve daily raw memory snapshots.

They are:

- evidence
- source tracing
- distillation input

They should not be loaded first in normal work.

## 6. Memory write rules

The following records the historical binding. Step 3 is a declared deviation from current `memory@0.2.0`, whose capture path writes the inbox first and lets the governed distillation path update topics.

When the user explicitly says:

- remember
- don't forget
- from now on
- this is my preference
- 记住
- 不要忘了
- 以后都这样
- 这是我的偏好

The agent should:

1. Compress the content into a reusable conclusion.
2. Write it to `memory/memory.md`.
3. If it is clearly long-term and stable, optionally update the relevant `topics/*.md`.
4. Append an operation record to `memory/log.md`.

Principles:

- Do not copy entire conversations.
- Do not treat temporary emotion as long-term knowledge.
- Do not directly overwrite old knowledge.
- Add first, clean later.

## 7. Automation

This implementation is hybrid.

### Stage 1: archive

Execution: Kubernetes CronJob

Time: Asia/Shanghai 04:10

Purpose:

- Pure shell, no AI.
- Move substantive content from `memory.md` to `archive/YYYY-MM-DD.md`.
- Recreate a blank hot inbox.
- Update `log.md`.

Why Kubernetes CronJob:

- Archive is mechanical.
- It should not depend on agent judgment.
- Even if AI fails, raw memory is preserved first.

### Stage 2: autodream

Execution: OpenAB usercron

Time: Asia/Shanghai 04:20

Purpose:

- Read today's archive.
- Read `index.md`.
- Read relevant `topics/*.md` on demand.
- Extract long-term reusable knowledge.
- Update `index.md`.
- Create or update `topics/*.md` when needed.
- Leave a distillation record in `log.md`.

Why OpenAB usercron:

- Autodream is essentially “send a prompt to the agent to distill memory”.
- Scheduling this through OpenAB is natural because the work belongs to the agent runtime.

## 8. Flow

```text
Daytime usage                         04:10                    04:20
─────────────────────────────────────────────────────────────────────
session / chat writes memory.md  →   archive preserves it   →   autodream distills it
                                    (CronJob / shell)          (OpenAB usercron / agent)
```

Outputs:

- `archive/YYYY-MM-DD.md`
- recreated `memory.md`
- updated `index.md`
- updated `topics/*.md`
- `log.md` operation trace

## 9. Distillation rules

Autodream is conservative, but these are legacy deployed rules. Free-form `[待清理]` must be migrated to the current closed `Status` vocabulary before claiming protocol conformance.

Rules:

- Incremental updates only.
- Do not directly delete existing knowledge.
- Mark stale items as `[待清理]`.
- Do not paste archive content back into `index.md`.
- Preserve source dates.
- Use `index.md` only for navigation and recent activity.
- Create or update topic pages only when useful.

This prevents two disasters:

1. AI accidentally deleting useful old knowledge.
2. Cold storage growing back into a hot garbage pile.

## 10. Operational pitfalls

### 10.1 ConfigMap-mounted `AGENTS.md` is read-only

If `AGENTS.md` is mounted from a ConfigMap, the Pod can read it but cannot update the true file.

Conclusion:

> If `AGENTS.md` must be mutable, it should live on PVC as the source of truth.

### 10.2 `kubectl` binary does not imply cluster access

Having `kubectl` in `PATH` does not mean it can reach the cluster.

Without `~/.kube/config` or `KUBECONFIG`, it may try:

```text
localhost:8080
```

and fail.

### 10.3 `KUBECONFIG` should not rely on shell profiles

`.profile` and `.bashrc` are not reliable for long-running containers or agent child processes.

More stable options:

- Deployment env
- Helm values
- CronJob env
- OpenAB config

### 10.4 Scheduling must be validated in layers

Do not only check that YAML exists.

Verify:

1. CronJobs appear in the cluster.
2. Deployment logs show usercron loaded.
3. The time window passes.
4. Archive/autodream leaves actual traces in files and logs.

### 10.5 `memory.md` must not become final knowledge

`memory.md` is an inbox, not a wiki.

If it becomes the final knowledge base, the system loses the hot/warm/cold separation.

## 11. Evidence boundary

### What this use case supports

- A real containerized binding separated writable persistent memory from immutable deployment configuration.
- Archive-first scheduling and layered runtime checks exposed concrete k3s, environment, and cron pitfalls.
- The lifecycle survived beyond one chat session and one process lifetime.

### What it does not support

- End-to-end conformance with the current `memory@0.2.0` item, withdrawal, and erasure contract.
- Current cluster health; the live environment was not rechecked during this review.
- A claim that ConfigMap, PVC, CronJob, or OpenAB is required by the general protocol.

## 12. Essence

One-sentence version:

> Daytime notes enter the hot inbox, nighttime archive preserves them losslessly, the agent conservatively distills them, and the result becomes persistent, searchable, auditable cold knowledge.

Metaphor:

```text
AGENTS.md is the hot behavior contract.
memory.md is the temporary box.
index.md is the signpost.
topics/ is the shelf of artifacts.
archive/ is raw evidence.
log.md is the footprints.
archive + autodream is the daily mechanism that maintains the knowledge base.
```
