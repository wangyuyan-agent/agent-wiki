# Kiro Local Steward Use Case

- Use case ID: `steward.kiro-local`
- Protocol: `steward@0.1.0`
- Evidence: `field-tested`
- Conformance: `partially-verified` — `steward:S1` explicit delegation, participant and managed-resource registries, standing-authority gates, and two ordinary-work durable workspace records were observed; complete `steward:S2` WorkOrder/result artifacts and checklist coverage, `steward:S3` per-order revocable `AuthorityGrant` artifacts, and `steward:S4` heterogeneous-participant operation within this binding plus formal takeover/handoff remain declared gaps
- Validation scope: the historical `1:1:N` relationship (one Principal, one primary Steward agent, five local role-specialized sub-agent participants, six managed resources) operated in ordinary daily work; two ordinary multi-step tasks later used durable workspace records through closure; the binding was not re-executed as a formal per-level conformance run
- Reproducibility: `partial` — architecture, registry shape, delegation primitive, and authority model are documented; exact agent definitions, skill files, credentials, and private environment assets are intentionally omitted
- Level namespace: `steward`
- Deployment status: `retired` — the local Kiro binding was retired on 2026-08-25; this page preserves historical evidence only
- Last reviewed: 2026-08-25

## 1. Context

This use case describes a historical local Steward binding that ran on the Kiro CLI on macOS. A single human (the Principal) interacted with one primary control agent (the Steward). Behind that one relationship surface, the Steward dispatched five local role-specialized sub-agents and operated six managed remote resources. Agent bots hosted on some of those resources are separate bindings and are not counted among these five participants.

It is the first documented binding of [Agent-first Steward Architecture](../../docs/agent-first-steward.md).

### Protocol alignment note

The `steward` protocol was designed protocol-first. Its author did not have access to this deployment, which is why the manifest labelled it `design-only` ("no documented binding yet") until this page existed. This use case is submitted as the protocol's first binding evidence: the topology is not merely a proposal, it has been operated as ordinary daily practice. The same change that adds this page records the evidence-backed maturity transition from `design-only` to `practiced`; maintainer review accepted that transition on 2026-07-20.

This deployment nonetheless **predates** the `steward@0.1.0` artifact schema and does not use it literally:

- Delegation is expressed as a natural-language task prompt to a sub-agent spawner, not as a serialized `WorkOrder` document.
- Authority is expressed as a standing, reviewable risk policy plus confirmation gates, not as per-order `AuthorityGrant` records with explicit `expires_at`.
- Result integration is performed by the Steward in-context, not through a serialized `ResultEnvelope` with a fixed `claims`/`evidence_refs`/`unresolved_dissent` shape.
- During the earlier field-tested period, coordination state lived in the Steward's live context plus an ephemeral task list rather than a durable, independently inspectable canonical task record.

A local Active Workspace candidate was added after that earlier period and first passed a bounded cross-session lifecycle probe. It later carried two ordinary multi-step tasks through durable revisioned records and closure. This closes the absolute "no durable ordinary-work record" gap and supplies a separate [Active Workspace use case](../active-workspace/kiro-local-active-workspace.md). It does **not** make the Steward binding `steward:S2`-complete: the tasks did not materialize or validate the complete `WorkOrder` → progress → `ResultEnvelope` artifact path, and the applicable `steward:S2` checklist was not executed end to end.

Before this binding can claim conformance above `steward:S1`, those artifacts must be materialized. The `field-tested` label describes real operation of the topology, not certification of the artifact schema. See §11 for the level-by-level assessment and §13 for protocol feedback the deployment produced.

## 2. Topology

```text
Relationship topology:   Principal 1  ↔  1 Steward (primary Kiro CLI agent)
Execution topology:      Steward 1    ↔  N participants + N managed resources

                         ┌───────────────── participants (agents) ─────────────────┐
Principal ── 1:1 ── Steward ── strategy · execution · debugging · architecture · cognition
                         └───────────────── managed resources ─────────────────────┘
                                   3 cloud VPS · 1 home router/NAS · 1 shared seedbox · 1 pocket router
```

The Principal maintains one conversation. The Steward absorbs routing, context distribution, supervision, and result integration, and is the only participant holding the delegation, introspection, and session tools.

## 3. Relationship roles

| Protocol term | Local realization |
| --- | --- |
| Principal | The human owner of the machines and the relationship. Source of goals, values, permissions, and risk choices. |
| Steward | One persona-stable primary Kiro CLI agent. Holds the sub-agent spawner, introspection, and session tools; no sub-agent holds them. Single accountable interface. |
| Participant | Five local role-specialized sub-agents (see §4). Same-model-family by default; correlated priors disclosed. Hosted agent bots are outside this binding's registry and count. |
| Managed resource | Six remote hosts (see §5), registered in a skill file the Steward loads. |
| Relationship state | A version-controlled memory layer (rules, distilled index, topic pages) supplies continuity across sessions. See §8. |
| Work graph | The dependency edges of a sub-agent dispatch (see §6). |
| Binding | This single-agent Kiro CLI deployment; no external Steward service. |

## 4. Participant registry (capability cards)

Participants are registered in a dispatch guide the Steward loads every session. Each entry is a `steward:S2`-style participant capability card in prose form. Tools are bounded per role; only the Steward holds delegation/introspection/session tools.

| Participant role | Capability lens | Tool envelope (bounded) | Independence |
| --- | --- | --- | --- |
| Strategy | Research, option comparison, planning | read/search/fetch, report, knowledge, task-list | shared model family |
| Execution | Bulk, repetitive, high-volume delivery | read/write/search/fetch, report, task-list | shared model family |
| Debugging | Root-cause analysis, incident triage | read-only (no write), search/fetch, report, knowledge | shared model family |
| Architecture | System design, technical selection, review | read/code (no web), report, knowledge | shared model family |
| Cognition | Assumption audit, framing calibration | minimal read/code/search only, report | shared model family |

`independence_group`: all five default to one shared base-model family. The delegation primitive can pin a different model per participant, but heterogeneous-model execution was not validated in this assessment. Remote agent hosts (see §5) may run heterogeneous runtimes, but those agent processes belong to separate bindings.

## 5. Managed resource registry

Resources are registered in a version-controlled skill file with connection method, capabilities, and running services. **No secret is embedded**: connection is via an external SSH key agent and password manager; the registry carries only opaque references, never keys, tokens, or credentials.

| Resource class | Count | Capabilities | Mutation risk | Notes |
| --- | --- | --- | --- | --- |
| Independent cloud VPS | 3 | general compute, proxy/tunnel services, container orchestration, agent hosting | medium–high | Some also host participant agents — see §5.1 |
| Home router / NAS appliance | 1 | LAN gateway, local git mirror, file shares | high (network path) | privileged access |
| Shared seedbox | 1 | download/media, userland services | low–medium | no root; cron-only persistence |
| Pocket travel router | 1 | edge networking, on-network access | medium | reachable over an overlay network |

### 5.1 Observation: a host can be both a managed resource and a participant host

Several of these VPS simultaneously (a) are managed resources the Steward inspects and operates directly, and (b) host one or more independent agent bots reachable through chat frontends. Within the topology in general, the machine is a managed resource and an agent process running on it may be a participant under a separate binding; the two roles can coexist on one host but carry different authority scopes. This use case's participant registry and conformance assessment cover only the five local sub-agents in §4, not those hosted bots. Operating the host (restart a service, read logs) is not the same authority as commanding the hosted agent, and vice-versa. This distinction fed a proposed protocol clarification (§13, item 1).

## 6. Delegation mechanism

The Steward's delegation primitive is a sub-agent spawning tool with these inputs, which map cleanly onto the protocol's coordination artifacts:

| Tool input | Protocol analogue |
| --- | --- |
| task prompt | `WorkOrder.task` + the bounded `context_refs` slice |
| assigned participant/role | `WorkOrder.assigned_to` |
| optional per-stage model | participant descriptor / `independence_group` selection |
| `depends_on` edges | the `work_order.dependencies` forming a DAG work graph |
| `loop_to` (trigger + max iterations) | a bounded review→revision cycle (separation of duties, §15.6 of the protocol) |
| blocking mode | synchronous supervision; Steward waits and integrates |

A dispatch can therefore be a single bounded task, several parallel tasks, or a dependency DAG with a review loop (for example: implement → review → loop back on `NEEDS_CHANGES`). The `loop_to` review edge is how the deployment realizes independent verification without a separate framework, and it composes with the [local Council binding](../council/kiro-local-council.md) when the decision (not just the execution) needs plural review.

## 7. Standing-authority model

Authority is realized as a **standing, reviewable policy**, not per-order grants. It has three sources the Steward loads every session:

1. A risk-tiered action policy: reversible/local actions proceed without confirmation; medium-risk actions proceed with a note; irreversible, destructive, spending, production, and security-control actions always require explicit Principal confirmation.
2. Stable conventions (identity/credentials discipline, environment rules, mandatory security scan before touching this public wiki, post-action sync chains).
3. Version-control safety rules (no direct push to protected branches; destructive VCS operations require explicit permission).

This is the practical substrate the deployment uses to satisfy authority-awareness. It maps to the protocol's `standing_authority` block (`allowed_without_confirmation` / `always_confirm`) in the relationship contract, rather than to per-`WorkOrder` `AuthorityGrant` records. The deployment's real experience is that a reviewable standing policy plus confirmation gates carries most of the `steward:S3` weight for a single-writer, human-in-the-loop environment; per-order expiring grants were not needed for routine work. This fed a proposed protocol clarification (§13, item 4).

## 8. Continuity, inspection, export, and bypass

- **Continuity** is supplied by a composed Memory binding ([Kiro Local Memory](../memory/kiro-local-memory.md)): stable rules are hot-loaded; a distilled index and topic pages carry project continuity; the Steward captures only reusable outcomes back through the ordinary Memory capture path. The Steward coordinates Memory through its public surface and does not mutate its internal lifecycle.
- **Inspection / export** is git: the relationship rules, dispatch guide, resource registry, memory index, and topic pages are all version-controlled, so another authorized agent could read and resume the relationship without a chat transcript. Sub-agent sessions and shell history give a partial delegation/audit trail.
- **Bypass** is default and frequent: the Principal routinely operates any managed resource directly (direct shell access) and can invoke any participant directly. The Steward is the default interface, not a gatekeeper. This fed a proposed protocol note about concurrent Principal action (§13, item 6).

## 9. What this evidence supports

- The `1:1:N` topology is operable as an ordinary daily practice by a single capable agent with no external Steward service — the protocol's `§18` minimal binding is real, not hypothetical.
- A prose participant capability registry plus a prose managed-resource registry are sufficient to route `steward:S1` delegation reliably.
- A standing risk-tiered authority policy plus confirmation gates is a workable authority substrate for a single-writer, human-in-the-loop environment.
- A sub-agent spawner with a dependency DAG and a review-loop edge already provides a work graph and independent-verification cycle.
- Git-versioned relationship/registry/memory state provides real exportability and inspectability.
- The earlier absence of a durable canonical record exposed the protocol's `information monopoly` (§16.4) and `single point of failure` (§16.9) risks; later ordinary-work records showed that durable closure is practical without proving complete `steward:S2` artifacts.

## 10. What it does not establish

- Conformance with the `steward@0.1.0` artifact schema (`WorkOrder`, `AuthorityGrant`, `ProgressEvent`, `ResultEnvelope`, `StewardDigest` are not serialized).
- `steward:S2` completeness: two ordinary-work durable workspace records exist, but they are not serialized `WorkOrder`, `ProgressEvent`, and `ResultEnvelope` chains, and the complete `steward:S2` checklist was not validated.
- `steward:S3` completeness: authority is a standing policy, not per-order revocable grants with expiry and a dedicated audit log.
- `steward:S4` completeness: review-loop verification and git-exportable state exist, but heterogeneous-participant operation within this binding and a rehearsed Steward takeover/handoff procedure remain unvalidated.
- `steward:S5`: the persistent agent bots on managed resources are independent bindings, not one unified hosted Steward service.
- Current runtime health or continued deployment; the local Kiro binding is retired.

## 11. Conformance level assessment

| Level | Status | Evidence / gap |
| --- | --- | --- |
| `steward:S0` | met | One Principal, one accountable Steward interface. |
| `steward:S1` | met | Bounded delegation via the sub-agent spawner; participant registry drives routing; results integrated by the Steward. |
| `steward:S2` | partial | Participant registry ✅, managed-resource registry ✅, result integration ✅, two ordinary-work durable workspace records ✅. **Gap:** complete `WorkOrder`/progress/`ResultEnvelope` artifacts and the applicable end-to-end checklist were not validated. |
| `steward:S3` | partial | Standing risk-tiered policy ✅, always-confirm gates ✅, credential references kept outside artifacts ✅. **Gap:** no per-order revocable `AuthorityGrant` with `expires_at`; audit is partial (session/shell/git history). |
| `steward:S4` | partial | Review-loop independent verification ✅, git-exportable state ✅. **Gaps:** heterogeneous-participant operation within this binding was not validated; no rehearsed takeover/handoff; failure recovery is ad hoc. |
| `steward:S5` | not claimed | Persistent bots are separate bindings, not one unified Steward service. |

Honest summary: **`field-tested` at `steward:S1`, with substantial `steward:S2` coverage and partial `steward:S3`/`steward:S4` elements; not `steward:S2`-complete, and not `steward:S5`.**

## 12. Mapping to protocol artifacts

| Steward protocol object | Local realization |
| --- | --- |
| `StewardRelationship` | Version-controlled rules + dispatch guide + memory conventions |
| `standing_authority` | Risk-tiered action policy + conventions + VCS safety rules |
| Participant capability card | Dispatch-guide role entries (§4) |
| Managed resource card | Skill-file host entries (§5) |
| `IntentRecord` | Preserved Principal request in context (not serialized) |
| `WorkOrder` | Natural-language sub-agent task prompt (not serialized) |
| `AuthorityGrant` | Standing policy + confirmation gate (not per-order) |
| Work graph | Sub-agent `depends_on` DAG |
| Review/verification cycle | Sub-agent `loop_to` edge; composed Council for decisions |
| `ResultEnvelope` | Steward in-context synthesis with manual provenance |
| `StewardDigest` | Ad-hoc Principal-facing summary |
| Continuity | Composed Memory binding |

## 13. Protocol feedback: proposed adjustments

These are field-evidence-driven proposals for the protocol author to accept or reject. Per the repository model, a use case is evidence and does not redefine the protocol. Maintainer triage on 2026-08-03 recorded a disposition for each proposal below; accepted clarifications were applied to the protocol document in that same change. The dispositions do not alter this page's evidence or conformance labels.

1. **Dual-role host (refine §9.2 / §12.5).** §9.2 states "A VPS is a managed resource, not an agent." The deployment confirms this but shows a host can *simultaneously* be a managed resource and the host of one or more agent processes. Proposed clarification: the machine is a managed resource; an agent process it hosts may be a participant under its own binding; one host may carry both roles at once, and operating the host is a distinct authority from commanding the hosted agent. This refines, and does not contradict, the existing rule.

   *Outcome (2026-08-03): accepted — protocol §9.2 now names the dual-role host and the distinct host/agent authorities.*

2. **Registry drift as a failure mode (add to §16).** The participant/resource registry silently diverges from reality (addresses, running services, health change). Routing on a stale card causes wrong action. Proposed new failure mode "Registry drift": mitigate with a `last_verified_at` discipline (the field already exists in §9.1/§9.2) plus mandatory re-verification before high-risk operations on a resource whose card is stale.

   *Outcome (2026-08-03): accepted, merged with item 6 into the protocol's new stale-view failure mode (§16.11).*

3. **Sharpen the S1/S2 boundary on the canonical task record (§11, §18.3, §19).** The deployment satisfies `steward:S1` with only an in-context/ephemeral task record, but that is precisely what makes §16.4 (information monopoly) and §16.9 (single point of failure) bite. Proposed clarification: an in-context record satisfies `steward:S1`; `steward:S2` requires the canonical task record to be **durable and inspectable independently of the Steward's live context**. This makes the ladder's real inflection point explicit.

   *Outcome (2026-08-03): accepted — protocol §18 and the `steward:S2` row now require the canonical task record to be durable and inspectable independently of the live context.*

4. **Standing policy as a first-class S3 substrate (clarify §10.4 / §19 S3).** §10.4 reads as if per-order `AuthorityGrant`s are the norm. Field evidence: a reviewable standing policy plus confirmation gates carries most of the authority-awareness weight for a single-writer, human-in-the-loop binding, and per-order expiring grants were unnecessary for routine work. Proposed clarification: a binding MAY satisfy `steward:S3` primarily through a reviewable standing policy, reserving per-order `AuthorityGrant`s for actions that exceed standing policy.

   *Outcome (2026-08-03): accepted with guardrails — protocol §10.4 admits a standing policy only if attributable to an explicit Principal decision, reviewable, revocable, bounded with explicit always-confirm classes, and audited; per-order grants remain required beyond it, and the `steward:S3` audit requirement is not waived. This acceptance does not upgrade this binding's conformance.*

5. **Delegation primitive → work graph mapping (non-normative note).** A spawner exposing a `depends_on` DAG and a `loop_to` review edge already realizes the §11 work graph and a §15.6 separation-of-duties cycle without extra infrastructure. Proposed: cite this as a concrete minimal realization in §12 or §18.

   *Outcome (2026-08-03): retained as a non-normative use-case observation; not added to the protocol.*

6. **Concurrent Principal action (add to §15.5 or §16).** Bypass (§15.5) is treated as a preserved capability; in practice the Principal operates managed resources directly and in parallel very frequently. Proposed note: the Steward MUST NOT assume exclusive control of a managed resource or that its cached view is current; concurrent Principal (or other-agent) writes are normal and healthy.

   *Outcome (2026-08-03): merged into item 2's accepted stale-view failure mode (§16.11).*

## 14. Reusable lessons

1. A single capable agent can run `1:1:N` today; the topology's value does not depend on a hosted butler service.
2. Prose registries are enough to start; formal schemas earn their cost only when the work graph outgrows one context.
3. The real `steward:S1`→`steward:S2` jump is externalizing the task record, not adding more roles.
4. For a single-writer, human-in-the-loop environment, a standing authority policy beats per-order grants on effort-to-safety ratio — match the protocol's rigor to the binding's actual concurrency and blast radius.
5. Keep credentials in an external secret boundary; the registry holds references only.
6. Treat the registry as a fact that drifts: re-verify before acting on anything high-risk.
7. Preserve bypass and direct inspection as first-class, not emergency-only — it is the main defense against the Steward becoming an information monopoly.

## 15. Local binding record

```yaml
binding_id: kiro-local-steward
protocol: steward
protocol_version: 0.1.0
level: steward:S1
storage_or_runtime: single Kiro CLI agent (no external Steward service)
deployment_status: retired
artifact_locations:
  - version-controlled relationship rules and conventions
  - version-controlled participant dispatch guide
  - version-controlled managed-resource skill file
  - composed Memory binding for continuity
deviations:
  - delegation is a natural-language task prompt, not a serialized WorkOrder
  - authority is a standing policy, not per-order AuthorityGrant records
  - ordinary-work durable workspace records exist, but not as complete serialized WorkOrder-to-ResultEnvelope chains
  - result integration is in-context, not a serialized ResultEnvelope
validation:
  checklist_completed:
    - one logical relationship and accountability interface
    - original Principal intent preserved through decomposition
    - every participant and resource has a known scope and capability
    - Steward cannot expand its own authority (standing policy + gates)
    - Principal can interrupt, revoke, bypass, or take over
    - simple tasks are still executed directly
  evidence: field-tested
  conformance: partially-verified
  gaps:
    - complete serialized WorkOrder, progress, and ResultEnvelope path plus end-to-end steward:S2 checklist
    - per-order revocable AuthorityGrant with expiry + audit log (steward:S3)
    - heterogeneous-participant operation within this binding (steward:S4)
    - rehearsed takeover/handoff procedure (steward:S4)
last_reviewed: 2026-08-25
```
