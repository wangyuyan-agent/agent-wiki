# Governed Artifact Replication and Exchange Guide

- Document ID: `governed-artifact-replication-exchange`
- Version: `0.1.0`
- Maturity: `design-only`
- Evidence scope: No documented multi-binding replication, attributed append-only exchange, offline rejoin, or erasure-propagation run yet.
- Scope: ongoing one-way replication and attributed append-only exchange of governed artifacts across independently usable bindings; no standalone protocol, conformance level, or multi-master merge design
- Last updated: 2026-08-10

## 1. Purpose

This guide defines when governed artifacts may remain available across two or more independently usable bindings while updates continue after bootstrap and no final cutover is intended.

It permits two bounded modes:

- **One-way replication** — one authoritative writer publishes immutable artifacts, append-only records, or revisioned state to read-only consumers.
- **Attributed append-only exchange** — multiple producers exchange only records that remain owned by their original producer; no producer rewrites another producer's stream.

The core rule is:

> Replication moves governed facts; it does not create writers, authority, freshness, standing, or corroboration.

This is a cross-cutting guide rather than a standalone protocol. It preserves the artifact identities, provenance, evidence states, authority paths, and lifecycle semantics defined by existing protocols. It defines no independent artifact lifecycle, capability ladder, or conformance claim.

Most multi-device or multi-tool arrangements should not use this guide. A canonical binding with remote access, a finite recovery or migration, a Governed Shared Memory admission, or two unrelated bindings is simpler and safer whenever it satisfies the actual need.

## 2. Vocabulary and operation boundary

| Term | Meaning |
| --- | --- |
| `binding` | One declared implementation of one or more protocol surfaces, independent of its tool, host, process, or storage layout. |
| `surface` | An explicitly bounded set of governed artifacts or state with one protocol owner, classification, exchange mode, and writer rule. |
| `authoritative writer` | The only binding role permitted to commit a new revision to a single-authority surface. The role does not create the authority that governs the decision. |
| `producer` | A binding role permitted to append records under its own stable producer identity. |
| `consumer` | A binding role permitted to receive and use a surface under declared audience, freshness, and effect constraints, but not to rewrite the received source. |
| `replication` | Ongoing propagation from an authoritative writer to one or more read-only consumers. |
| `append-only exchange` | Ongoing propagation and idempotent union of producer-attributed records without rewriting their identities or contents. |
| `control event` | An attributable revision, revocation, supersession, policy, or erasure event that changes how dependent content may be served or used. |
| `rejoin` | A binding's return after it could not observe some exchange or control events. |
| `presence and revision reconciliation` | Comparison of artifact identities, stream positions, revisions, digests, and control events; it does not decide semantic truth. |
| `quarantine` | Isolation of one surface or producer stream after an integrity or authority fault until a declared recovery path succeeds. |

No current agent-wiki protocol standardizes a commutatively mergeable or authority-free shared mutable surface. No current protocol grants two independent bindings concurrent write authority to the same semantic revision by default. A protocol may permit a binding-defined concurrency contract, but this guide does not standardize commutative merge, multi-master mutation, or authority-free conflict resolution.

If two bindings must independently mutate the same semantic revision, the topology is outside this guide. The binding must fail closed rather than describing the arrangement as replication or append-only exchange.

## 3. Selection and activation gates

### 3.1 Selection gate

An Agent should select this guide only when all of the following are true:

1. At least two distinct bindings must remain independently usable over time, including a declared offline or disconnection window.
2. Updates after bootstrap must continue to propagate in one or both directions.
3. No acceptable final cutover exists; otherwise use the [Portability and Recovery Guide](governed-artifact-portability-recovery.md).
4. Remote access to one live canonical binding is unavailable or insufficient; otherwise retain one canonical writer and use the relevant protocol's client, proposal, or revision-checked patch path.
5. The need is more than ordinary visibility and is not solely governed shared standing; otherwise use ordinary access or [Governed Shared Memory](governed-shared-memory-profile.md) as appropriate.
6. Every selected surface can be represented as immutable/versioned artifacts, attributed append-only records, or single-authority revisioned state.

If any selected surface requires concurrent independent mutation of the same semantic revision, repartition that surface, retain one authoritative writer, or exclude it. Do not activate exchange while the writer model is ambiguous.

### 3.2 Activation gate

Passing the selection gate does not authorize replication or exchange.

Activation requires:

1. A staged `ExchangeContract` that satisfies §6.
2. Attributable authorization covering every participating binding, every audience or disclosure effect, and every erasure obligation.
3. Recorded consent from every affected governance authority when the bindings do not share one authority.
4. A validated bootstrap boundary and a declared failure, suspension, rejoin, and exit path.

An Agent may discover this guide, evaluate the selection gate, and propose a contract. It must not create participants, widen an audience, assign writer roles, accept erasure obligations for another holder, or activate exchange merely because the guide appears applicable.

## 4. Non-goals

This guide does not define:

- A transport, archive, object store, version-control workflow, database replication product, message bus, cloud vendor, or filesystem layout.
- Anti-entropy, gossip, delta encoding, retry, leader election, failover, tombstone collection, or clock-synchronization algorithms.
- Multi-master mutation, commutative merge, CRDT semantics, generic conflict resolution, or last-writer-wins behavior.
- A shared mutable surface, a second writer for an existing protocol, or automatic promotion of a consumer to authoritative writer.
- High availability, consensus, quorum, recovery objectives, retention periods, or numeric freshness targets.
- Inferred whole-directory or whole-binding synchronization. A declared aggregate is valid only when every included surface is enumerated and classified.
- A whole-space Governed Shared Memory replication or migration procedure; the responsible authority, physical topology, and continuity contract remain binding-declared.
- New semantics for Memory, Skills, Workspace, Inner Speech, Council, Steward, Governed Shared Memory, or their evidence and authority states.
- Credential distribution, account transfer, or copying tool sessions, private reasoning, generated indexes, caches, embeddings, or other rehydratable runtime state.

This guide is intentionally a semantic envelope. Mechanisms remain binding-defined until practice produces reusable evidence.

## 5. Surface classes and exchange modes

### 5.1 Surface classes

Every surface must use exactly one class:

| Class | Required semantics | Permitted propagation |
| --- | --- | --- |
| `immutable/versioned` | A semantic change mints a new identity or version. The same identity must resolve to the same digest. | May accompany either mode. Divergent content under one identity is a fault, not a merge candidate. |
| `attributed append-only` | Every record has a stable event or artifact id, producer identity, provenance, and any required causal or source references. Existing records are not rewritten. | May use one-way replication or attributed append-only exchange. Each producer writes only its declared stream. |
| `single-authority revisioned` | One authoritative writer commits a monotonically advancing revision, snapshot, or accepted delta. Consumers expose the source revision and remain read-only for that surface. | One-way replication only. A consumer proposal uses the owning protocol's separate proposal or patch path. |

Wall-clock timestamps are observations, not a global ordering authority. A surface uses its protocol's revision, producer sequence, immutable identity, causal reference, or declared combination. The guide does not require a total order when the owning protocol does not require one.

### 5.2 One-way replication

One binding is the authoritative writer for the surface. Consumers may materialize the latest validated revision or a disclosed stale revision. They must not edit the received state and publish it back as a source revision.

Promotion, succession, or failover is not an ordinary replication event. It requires an attributable authority decision, a new or revised binding contract, proof that conflicting mutation authority is absent, and a checkpoint or cutover path appropriate to the owning protocol.

### 5.3 Attributed append-only exchange

Two or more producers may exchange records only when producer ownership is disjoint and stable. Receipt is idempotent. A receiver preserves the original record id, producer, source roots, and lineage; it does not reissue the record as a new observation.

A combined view may be generated from the union, but the view is derived state rather than another producer stream. Semantic contradiction between valid records remains visible and is routed to the owning protocol's reconciliation or decision path.

### 5.4 What is not exchange

- Several clients submitting revision-checked patches to one Active Workspace owner are using one canonical binding, not replication.
- Two bindings with disjoint data and no propagation requirement are independent bindings, not exchange.
- Mere visibility without governance is ordinary access; governed standing without ongoing propagation is a Governed Shared Memory concern.
- A finite bootstrap followed by one active target is portability or recovery.

## 6. ExchangeContract semantics

An `ExchangeContract` is a protocol concept, not a required file format. A binding may encode it as Markdown, YAML, JSON, database rows, or immutable governance events. It must make the following groups recoverable:

### 6.1 Identity and authorization

- `contract_id`, contract version, status, and review or invalidation conditions;
- participating binding identities and references to their binding declarations;
- attributable authorization records covering participants, audience effects, and erasure obligations;
- recorded consent from each affected governance authority when authority is not shared;
- no credentials, bearer capabilities, or possession-based authority.

One authorization may cover several bindings. It must not imply that one authority can enroll a binding governed by another authority without that authority's recorded consent.

### 6.2 Surface entries

Each entry names:

- the owning protocol, artifact or state type, and explicit scope;
- one of the three §5.1 classes;
- `one-way-replication` or `attributed-append-exchange` mode;
- each binding's role: `authoritative-writer`, `producer`, or `consumer` as applicable;
- the governing authority references for writer roles, audience, admission or effect, erasure, and topology as applicable, kept separate from binding roles;
- audience, disclosure, retention, and source-access constraints;
- the identity, digest, revision, producer-sequence, or causal basis used for reconciliation.

A declared aggregate may group entries after they are completely enumerated and classified. It must not mean every file, row, session, or artifact a tool happens to expose.

### 6.3 Control, freshness, and rejoin

The contract declares:

- control-event streams for revisions, revocations, supersessions, policy changes, and authorized erasure;
- the revision or checkpoint last applied by each consumer;
- how stale or unknown freshness is disclosed to readers and acting Agents;
- what an offline producer may record, and which effects remain pending until rejoin;
- the requirement to apply relevant control events before serving or submitting dependent content after rejoin;
- quarantine, suspension, recovery, and reauthorization triggers.

### 6.4 Erasure, exit, and validation

The contract declares:

- the binding-declared erasure authority and each holder's propagation and deletion obligations;
- content-free tombstone semantics for authorized rights or compliance erasure;
- the distinct handling of ordinary retirement, revocation, and supersession, which preserve allowed history;
- replica decommissioning, local disposal, or conversion to a portability migration at exit;
- structural checks, offline/rejoin drills, fault-injection checks, and the evidence state of each path;
- mandatory exclusions from §8.

Until a declared bootstrap, exchange, rejoin, erasure, or exit path has been exercised, that path remains `unevaluated`.

## 7. Operation path

```text
establish need
  -> classify and enumerate surfaces
  -> propose and authorize ExchangeContract
  -> create a consistent bootstrap checkpoint
  -> stage and validate consumers
  -> activate declared surfaces
  -> replicate or exchange attributed records
  -> disclose freshness and monitor control events
  -> reconcile presence and revisions
  -> rejoin, quarantine, suspend, or continue
  -> decommission replicas or convert to migration at exit
```

### 7.1 Bootstrap and active exchange

Bootstrap reuses the [Portability and Recovery Guide](governed-artifact-portability-recovery.md): declare scope, classify the four planes, create a consistent checkpoint, reconstruct target binding state, re-establish credentials separately, stage the import, validate it, and activate only through an attributable decision.

After activation:

1. Delivery and replay must be idempotent for the declared identity scheme.
2. A consumer must reject a lower revision and quarantine the same revision with a different digest.
3. An append-only receiver must quarantine one event id with different content or one producer identity that forks its declared stream.
4. A consumer must disclose the last applied checkpoint or equivalent freshness evidence.
5. A received artifact remains attributable to its original producer and root sources.

### 7.2 Offline operation and rejoin

An offline consumer may use a stale replica only under the contract's disclosure and effect limits. It must not imply that stale authority, policy, operational binding, or skill activation is current.

An offline producer may append to its own declared stream when the contract permits. Those records do not acquire current standing, authority effect, or privileged activation merely because they were captured offline.

On rejoin, each affected surface must:

1. Reconcile its last accepted revision, producer positions, identities, and digests.
2. Apply relevant revocation, supersession, policy, and erasure control events.
3. Remove or disable content covered by an authorized erasure before it can be served or exported.
4. Only then expose or submit dependent local content.
5. Quarantine the surface when a gap, fork, identity collision, digest mismatch, or authority ambiguity cannot be resolved deterministically.

The rule is surface-scoped. An unresolved fault on one surface does not require unrelated surfaces to disappear, but it must not be hidden by their continued operation.

### 7.3 Presence and revision reconciliation

Reconciliation compares inventory, revisions, stream positions, digests, and control events. It answers whether the declared records and revisions are present and validly ordered for their protocol.

It does not decide which of two valid claims is true, which preference should win, or which skill is globally better. A semantic contradiction passes through unchanged with both sources visible and enters Memory Reconcile, Council, Skill evaluation, or another owning-protocol path.

Replication faults stop or quarantine the affected exchange path. Epistemic disagreement remains a governed artifact.

### 7.4 Erasure, suspension, and exit

Authorized rights or compliance erasure propagates through a content-free tombstone or another content-free binding-declared control record. A holder that cannot perform the required deletion must suspend the affected surface and exit the contract.

Ordinary retirement, revocation, and supersession are not erasure. Their historical records remain available under the owning protocol's retention and audience rules while their current effect is withdrawn.

Exit either:

- decommissions a consumer or producer, records the last accepted boundary, and disposes of replicas according to authority and retention rules; or
- converts the declared scope to migration, following the portability path through final validation, cutover, and source decommissioning.

## 8. What may travel and what never transfers

Only selected governed artifacts and contract control records are eligible. Apply the four-plane classification from the Portability and Recovery Guide:

| Plane | Replication and exchange treatment |
| --- | --- |
| Artifact | May travel when its surface is enumerated, classified, authorized, and audience-compatible. |
| Binding | Contract and binding declarations may travel as records; local paths, adapters, schedulers, and discovery wiring are reconstructed per binding. |
| Authority and secret | Historical authority records may travel. Credentials, private keys, bearer capabilities, host trust, and effective authority never transfer through replication. |
| Runtime and ephemeral | Tool sessions, private reasoning, transient logs, caches, embeddings, generated indexes, active processes, and other rehydratable state do not travel. |

Propagation preserves producer identity, source roots, lineage, historical status, confidence, evidence state, and authority records. It never upgrades their current effectiveness, standing, confidence, or evidence state.

A replica is not a new source. Repeated copies with one root source remain one evidential source, and transport hops do not create corroboration.

Every target is a new storage location and may create a new disclosure path. Placement must be authorized, and the target's readers must remain inside the artifact's declared audience or receive an attributable audience change before content arrives. Restricted references remain restricted; inability to access them is not ordinary source loss.

## 9. Existing protocol boundaries

This guide applies existing protocol semantics; it does not redefine them:

- **Memory:** Per-binding captures and raw archive additions may be attributed append-only surfaces. The distilled item store, topics, index, conventions, and consolidated views may be single-authority revisioned surfaces. A binding may instead exchange immutable item versions plus lifecycle events only when that representation preserves stable item identity, atomic supersede, and source-anchor rules. Autodream remains single-writer per pass. Multiple bindings may capture under distinct producer identities, but they do not concurrently rewrite one consolidated store.
- **Skill Lifecycle:** Procedure versions and resources may be immutable/versioned; CandidateRecords, EvidenceRecords, AdoptionDecisions, observations, and lifecycle events may be append-only. A replicated active pointer is information about the source binding, not activation in a consumer binding. The consumer makes its own attributable AdoptionDecision and recomputes execution-context applicability. Generated catalog indexes are rehydrated rather than exchanged as authority.
- **Active Workspace and Inner Speech:** An active Workspace snapshot may be one-way replicated as single-authority revisioned state, but every change still enters the owner's revision-checked patch path. A proposal formed from a stale replica receives no special standing and remains subject to the owner's base-revision checks. A closed Workspace record may be immutable/versioned. Transient Inner Speech cues do not travel.
- **Council and Steward:** Completed decision, dissent, work, and result records may travel. A live delegation, grant, enrollment, or managed-resource capability does not become effective in another binding without target-side authority validation.
- **Governed Shared Memory:** Participant-level exchange never implies whole-space replication. A binding must identify attributable authority for replication and space continuity; physical topology remains binding-defined. This guide assigns neither responsibility to the admission authority. Under the declared authorization, a physical replica of the same logical space may preserve existing AdmissionRecords, standing, audience, and policy history. Copying an AdmissionRecord into a different space preserves a historical fact but grants no standing there.
- **Composable Agent Cognition:** Every mutable surface retains a single writer or its owning protocol's declared optimistic-concurrency contract. Last-writer-wins remains invalid.
- **Portability and Recovery:** Its four-plane classification, bootstrap, reauthorization, staged import, validation, cutover, and decommission terms are reused. Exchange creates no exception to its prohibition on copying credentials or authority.

## 10. Invariants

1. An `ExchangeContract` never grants two bindings concurrent write authority to the same semantic revision; that topology remains outside this guide and fails closed.
2. Every surface is explicitly enumerated and classified. A declared aggregate may group entries but must not infer them from a directory, tool, account, or binding.
3. Every surface has one exchange mode and explicit binding roles. A consumer of single-authority revisioned state cannot change that state through the exchange channel.
4. Propagation preserves artifact and producer identity, source roots, lineage, historical status, confidence, evidence state, and authority records.
5. Propagation never upgrades current effectiveness, standing, confidence, or evidence state. Copies do not corroborate their root source.
6. Every consumer discloses freshness evidence and must not present a replica as native, independently produced, or more current than its last accepted boundary.
7. Relevant control events are applied per surface before dependent content is served or submitted after rejoin.
8. A content-free tombstone represents authorized erasure only. Retirement, revocation, and supersession retain their distinct protocol meanings and allowed history.
9. Attributable authorization covers every participant, audience effect, and erasure obligation. One authority cannot enroll another authority's binding without recorded consent.
10. A replication fault quarantines or suspends the affected surface. Semantic contradiction between valid artifacts passes unchanged to the owning protocol.
11. Bootstrap follows staged import, validation, and attributable activation; the existence of copied bytes is not activation.
12. Exit decommissions the replica or producer, or converts to a portability migration with an explicit cutover.
13. Participant-level exchange never implies whole-space Governed Shared Memory replication or assigns space-continuity authority.
14. An unexercised bootstrap, exchange, offline/rejoin, erasure, recovery, or exit path remains `unevaluated`.
15. Discovery is not activation: an Agent may route to or propose this guide but cannot enable exchange without the declared authorization.

## 11. Failure modes

| Failure | Consequence | Required defense |
| --- | --- | --- |
| Whole directories or databases are synchronized bidirectionally | Secrets, runtime state, generated views, and governed artifacts acquire accidental multi-writer behavior | Enumerate and classify surfaces; reconstruct local binding state. |
| A consumer edits a replica and exports it as source state | One single-authority surface silently gains a second writer | Keep consumers read-only; route proposals through the owning protocol. |
| Revoked or superseded content is served as currently effective after rejoin | Stale operational or authority effect is resurrected | Apply control events before dependent content. |
| Erased content returns from an offline replica | Rights or compliance erasure is violated | Reconcile and execute authorized erasure before serving or exporting local content. |
| Retirement is encoded as erasure | Allowed history is over-deleted and auditability is lost | Keep retirement, revocation, supersession, and authorized erasure distinct. |
| A received record is re-captured as a new observation | Echoes acquire false provenance and apparent independent support | Preserve producer and source roots; record receipt without reissuing the claim. |
| Replicas are counted as corroboration | Confidence rises without new evidence | Deduplicate by root source; transport never changes confidence. |
| One event id has two payloads or one producer stream forks | Corruption or identity cloning is silently merged | Quarantine the stream and require declared recovery or a new producer identity. |
| One revision has two digests | A single-authority surface is in split brain | Suspend that surface on all ambiguous paths; do not choose by timestamp. |
| Replica placement expands audience | Restricted content reaches an unauthorized holder | Authorize every target audience before bootstrap or exchange. |
| An AdmissionRecord copied to another space is treated as standing | Space-local governance is bypassed | Preserve it only as a historical fact; require admission in the target space. |
| Wall-clock time selects the winner | Clock skew launders an arbitrary update into authority | Use protocol revisions, producer sequences, identities, and causal references. |
| An Agent auto-enables exchange after discovering the guide | Audience, erasure, and writer obligations appear without authority | Allow proposal only; require the activation gate. |
| An untested path is called reliable | Rejoin, erasure, or exit failure remains hidden until an incident | Keep the path `unevaluated` and run a bounded drill before stronger claims. |

## 12. Proposed design checklist

This checklist describes what a future binding would verify. Passing it does not establish conformance or raise this guide above `design-only`.

1. The selection gate excludes canonical remote access, finite migration, standing-only sharing, and unrelated bindings.
2. Every surface is explicitly enumerated and classified as immutable/versioned, attributed append-only, or single-authority revisioned.
3. Every surface declares one-way replication or attributed append-only exchange and names each binding role.
4. Binding roles and the applicable writer, audience, admission or effect, erasure, and topology authorities are represented separately.
5. Authorization covers every participant, audience effect, and erasure obligation, including consent from distinct affected authorities.
6. Ordering and reconciliation use declared revisions, identities, producer positions, or causal references rather than wall-clock winner selection.
7. Every consumer exposes its last accepted boundary or equivalent freshness evidence.
8. Rejoin applies relevant revocation, supersession, policy, and erasure events before dependent content is served or submitted.
9. Authorized erasure tombstones remain distinct from ordinary retirement and supersession events.
10. Digest mismatch, event equivocation, producer fork, and authority ambiguity have quarantine or suspension paths.
11. Bootstrap uses a consistent checkpoint, staged import, target-side reauthorization, validation, and attributable activation.
12. Credentials, effective authority, physical layout, tool sessions, private reasoning, generated indexes, and other rehydratable state are excluded.
13. Exit defines replica disposal or a conversion to migration with explicit cutover and decommissioning.
14. Any Governed Shared Memory surface has attributable replication and continuity authority declared by the binding without assigning either role to admission authority by default.
15. Exercises name the exact bootstrap, exchange, offline/rejoin, erasure, fault, or exit path tested; all other paths remain `unevaluated`.
16. No surface grants two independent bindings concurrent write authority to the same semantic revision.

Transport and anti-entropy algorithms, delta formats, retry behavior, numeric freshness objectives, tombstone collection schedules, leader election, true multi-master semantics, and whole-space Governed Shared Memory replication procedures remain binding-defined or deferred until practice produces reusable evidence.

## 13. Final rule

> Replicate only declared facts, exchange only producer-owned append-only records, keep every mutable surface under its protocol authority, apply control events before stale content can return, and fail closed before synchronization becomes an accidental second writer.
