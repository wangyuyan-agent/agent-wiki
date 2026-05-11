# OpenAB + Codex + k3s Memory Use Case

## 1. Context

This use case describes an agent memory system for a long-running OpenAB + Codex environment on k3s.

The system must let an agent:

- Keep memory across sessions.
- Preserve memory across Pod restarts, Deployment rollouts, and version upgrades.
- Separate short-term notes, long-term knowledge, and operational pitfalls.
- Distill memory automatically without letting it grow into a mess.
- Preserve a manual audit path without requiring daily human curation.

The design is a practical implementation of [Agent-first Memory Architecture](../../docs/agent-first-memory.md).

## 2. Design philosophy

This design combines several ideas:

1. **OpenAB steering-design-guide** — Hot / Warm / Cold memory layering.
2. **Local Kiro memory pipeline** — `memory.md` + archive + autodream + topics.
3. **Codex instruction and skill model** — `AGENTS.md` as the hot entry and `.codex/skills/*` as triggered workflow bodies.

Final principles:

- `AGENTS.md` stores soul, rules, and memory entry points, not short-term memory bodies.
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

Autodream is conservative.

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

## 11. Essence

One-sentence version:

> Daytime notes enter the hot inbox, nighttime archive preserves them losslessly, the agent conservatively distills them, and the result becomes persistent, searchable, auditable cold knowledge.

Metaphor:

```text
AGENTS.md is the soul.
memory.md is the temporary box.
index.md is the signpost.
topics/ is the shelf of artifacts.
archive/ is raw evidence.
log.md is the footprints.
archive + autodream is the daily mechanism that maintains the tomb.
```
