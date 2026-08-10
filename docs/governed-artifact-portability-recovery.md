# Governed Artifact Portability and Recovery Guide

- Document ID: `governed-artifact-portability-recovery`
- Version: `0.1.0`
- Maturity: `design-only`
- Evidence scope: No documented cross-host restore, cross-tool migration, or restore drill yet.
- Scope: backup, restore, export, and migration semantics for governed artifacts; no standalone protocol, conformance level, or multi-writer synchronization design
- Last updated: 2026-08-10

## 1. Purpose

This guide defines how an Agent or binding should reason about governed artifacts when work must be backed up, recovered, or moved to another host, tool, runtime, or storage form.

It has two first-class paths:

- **Recovery** preserves a binding through a checkpoint, binding-native backup, restore, reauthorization, and validation.
- **Portability** frees selected governed artifacts from source-tool internals so a target binding can reconstruct, stage, validate, and activate them.

The core rule is:

> A backup preserves a binding. An export frees governed artifacts from it. Neither copies authority, credentials, or a complete Agent state.

The portable unit is a declared set of governed artifacts plus the binding declarations needed to interpret them. A target binding is reconstructed for its own environment; it is not produced by copying a source tool's physical directory layout.

This is a cross-cutting guide rather than a standalone protocol. It preserves the identities, provenance, status, authority boundaries, and evidence semantics defined by existing protocols. It defines no independent artifact lifecycle, capability ladder, or conformance claim.

## 2. Vocabulary and operation boundary

These terms are distinct because their success criteria differ:

| Term | Meaning | Success criterion |
| --- | --- | --- |
| `checkpoint` | An immutable reference to one consistent source revision or consistent set of revisions for the declared scope. | The selected state can be reconstructed without observing a torn semantic update. |
| `backup` | A recovery representation of one binding at a checkpoint. It may be binding-native and opaque to other tools. | The declared recovery target can restore it. |
| `restore` | Reconstruction of the same logical binding contract from a backup, on the same host or a declared replacement host. | The restored binding passes its declared recovery validation. |
| `export` | A source-tool-independent representation of selected governed artifacts, their protocol versions, identities, provenance, and reference closure. | A target binding can interpret it without reading undocumented source-binding internals. |
| `migration` | Export, target binding reconstruction, reauthorization, staged import, validation, cutover, and source decommissioning for a declared scope. | The target becomes the only active binding authorized to mutate that scope. |
| `rehydration` | Regeneration of derived runtime state from governed artifacts and declared external sources. | The regenerated state can be discarded and reproduced without becoming a new source of authority. |
| `cutover` | An attributable event that transfers active responsibility for the declared scope to the target binding. | Source and target roles after the event are explicit and auditable. |
| `decommission` | Removal of a source binding's active role after cutover, normally by making it read-only, archival, or retired. | A returning source cannot silently resume mutation authority. |
| `clone` or `fork` | Creation of another live binding while the source remains active. | The new binding receives a new identity or an explicit successor/fork relationship. |

A same-host disaster restore preserves the binding shape and normally continues the binding identity. A replacement-host restore may also continue that identity when all of the following are true:

1. The logical binding contract is unchanged.
2. At most one live instance claims the identity at any time.
3. The host succession is recorded.
4. A source that later returns is decommissioned or read-only before it can act.

When the source may remain active, its liveness is unknown, or the target intentionally diverges, the target must use a new binding identity and an explicit relationship to the source.

This guide stops at single-target recovery or migration. The [Governed Artifact Replication and Exchange Guide](governed-artifact-replication-exchange.md) covers only ongoing one-way replication and attributed append-only exchange. If source and target remain authorized to modify the same semantic state after cutover, the operation is a multi-writer synchronization problem outside both guides. The binding must fail closed rather than pretending that migration completed.

## 3. Non-goals

This guide does not define:

- A backup product, archive format, transport, storage vendor, package manager, scheduler, or encryption implementation.
- A universal filesystem layout. A binding may use files, databases, managed stores, object stores, or indirection without changing the protocol artifacts it hosts.
- Migration of model weights, latent state, tool sessions, caches, login sessions, credentials, or a complete Agent mind.
- Credential transfer, account transfer, or a mechanism for copying authority between hosts or tools.
- Active-active replication, writer election, conflict resolution, multi-master merge, or high-availability topology.
- Recovery point or recovery time targets, retention periods, or restore-drill schedules.
- New semantics for Memory, Skills, Workspace, Inner Speech, Council, Steward, or Governed Shared Memory.
- A claim that byte-for-byte copying proves semantic recovery or portability.

Physical storage is evidence about one binding, not a protocol identity. A path, mount, link, database file, or runtime-managed store must not become normative merely because one implementation uses it.

## 4. Four-plane classification

Before backup, export, restore, or migration, the operator must classify the selected state into four semantic planes:

| Plane | Contains | Treatment |
| --- | --- | --- |
| Artifact | Protocol-governed items, versions, records, archives, decisions, and declared provenance. | May enter a backup or export when selected, authorized, and referentially accounted for. |
| Binding | Storage/runtime mappings, discovery entries, schedulers, adapters, paths, and validation declarations. | Record the declaration; reconstruct environment-specific wiring at the target instead of copying it as protocol truth. |
| Authority and secret | Live credentials, private keys, bearer capabilities, host trust, and grants that become effective through possession. | Never enter a package governed by this guide; establish them separately at the target and revalidate protocol authority. |
| Runtime and ephemeral | Tool sessions, caches, transient logs, active process state, generated indexes, embeddings, and other rehydratable state. | Exclude from portable export. A binding-native recovery system may preserve declared runtime state, but that does not make it portable. |

An attributable authority record may itself be a governed historical artifact. Copying that record does not make its grant effective in the target environment. Effectiveness always requires target-side revalidation.

In-flight work is not a fifth plane. It is a consistency condition on one or more planes. An open Workspace, a running Memory consolidation pass, or a partially written event must be closed, checkpointed, or captured by a revisioned tail before activation at the target.

The local binding record in the [Agent Adoption Guide](agent-adoption-guide.md#5-record-the-local-binding) is a useful seed for reconstruction. It describes what was implemented without claiming that source paths or runtime files are themselves portable artifacts.

## 5. Recovery path

The recovery path is:

```text
declare scope
  -> classify four planes
  -> create a consistent checkpoint
  -> create a binding-native backup
  -> verify integrity and declared closure
  -> restore on the same or replacement host
  -> reconstruct host-specific binding surfaces
  -> re-establish credentials and revalidate authority
  -> validate the restored binding
  -> record success, degradation, or failure
```

### 5.1 Recovery requirements

1. The backup must identify its source binding, scope, checkpoint, format or adapter, integrity evidence, exclusions, and intended restore target.
2. A semantic in-place rewrite within the declared scope must not straddle the checkpoint. The whole pass finishes before the checkpoint or begins after it.
3. Append-only writes may continue only when they carry revisions and every post-checkpoint write is captured by a declared incremental tail and reconciled before restored activation.
4. The restore must not treat copied credentials or host trust as valid. Credentials are re-established through a separate authorized path.
5. A replacement-host restore must record host succession and the old host's disposition.
6. The restored binding must validate artifact identities, protocol versions, integrity, required references, binding reconstruction, authority, and degraded exclusions before success is claimed.

A backup may contain binding-native data that another tool cannot interpret. It must not be delivered as an `export` or used to claim cross-tool portability merely because the source tool can restore it.

## 6. Portability path

The portability path is:

```text
declare scope
  -> classify four planes
  -> create a consistent checkpoint
  -> export tool-independent governed artifacts
  -> reconstruct the target binding from declarations
  -> re-establish credentials and revalidate authority
  -> import into a staged, non-active state
  -> validate schemas, identities, references, and transformations
  -> record cutover
  -> decommission or make the source read-only
```

### 6.1 Portability requirements

1. The export must pin every represented protocol and artifact version or content identity.
2. Producer identity, original provenance, source references, historical status, confidence, and authority records must not be rewritten to make the target look native.
3. A transformation that changes semantics or disclosure must mint a new identity and record `derived_from`; the original content hash remains visible.
4. Target paths, schedulers, indexes, discovery entries, and storage adapters are reconstructed as target binding state.
5. Imported artifacts remain staged until validation passes and an attributable activation decision exists.
6. Validation must distinguish structural success from behavioral evidence. A successful import does not prove equivalent behavior under a new model, runtime, tool set, or privilege surface.
7. The source remains an intact rollback target until target validation and cutover complete. Rollback after propagated effects cannot erase those effects.

A portability operation is a material execution-context change. For Skill artifacts, the historical evidence remains true while current applicability is recomputed under [Skill Lifecycle §13.1](agent-first-skill-lifecycle.md#131-historical-truth-vs-current-applicability). Target behavior claims begin as `unevaluated` unless applicable target-context evidence already exists.

## 7. Package manifest semantics

The package manifest is a protocol concept, not a required file format. A binding may encode it as Markdown, YAML, JSON, database rows, or immutable events. It must make the following information recoverable:

- `manifest_id` and operation type;
- source binding identity and binding declaration reference;
- declared scope selector;
- source checkpoint or revision set;
- origin execution-context snapshot or immutable fingerprint for portability operations;
- selected artifact entries or declared aggregate snapshots, each with protocol id/version, artifact type, stable id, content digest, producer, and provenance;
- transformations, original digests, new identities, and lineage;
- referential-closure report;
- exclusions, reasons, and declared degradation;
- target reauthorization and authority-revalidation requirements, containing references but no secrets;
- structural and semantic validation records;
- restore, cutover, rollback, or decommission event references when applicable.

### 7.1 Scope selector

Scope must be declared rather than inferred:

- `full-binding` — all governed artifacts declared by one binding, subject to mandatory exclusions in this guide;
- `protocol-scoped` — all selected artifacts for one or more named protocol bindings;
- `artifact-scoped` — an explicit list of artifact identities or immutable collection snapshots.

Installing or exporting one Skill does not imply exporting its siblings. Exporting Memory does not imply exporting Workspace, runtime sessions, or every artifact visible to the same Agent.

### 7.2 Referential closure

Every outgoing reference from the declared scope must be classified as exactly one of:

1. `included` — the referenced identity is resolvable inside the package;
2. `stable-external` — the reference resolves to a declared external source with preserved identity and access assumptions;
3. `explicitly-excluded` — the package records why it is absent and what capability or claim degrades.

Silent dangling references are invalid. `source-unavailable` means that lineage cannot currently be resolved; it does not mean the source claim is false.

A Memory raw archive must accompany exported items when those items use it as their source anchor. The archive may be explicitly excluded, but affected items then degrade to `source-unavailable` and require re-anchoring or reduced reliance under [Memory §15.2](agent-first-memory.md#152-how-skeptically-to-read-hot-rule-mandatory).

The word `complete` must always name a scope and intended outcome. A manifest can completely account for its references while still declaring exclusions. It must not claim complete semantic restoration when an excluded dependency prevents that result.

### 7.3 Package exclusions

Packages governed by this guide must not contain:

- live credentials, private keys, bearer tokens, or host trust material;
- authority that becomes effective merely through possession of the package;
- inaccessible restricted content that the exporter is not authorized to disclose;
- raw tool chat sessions or private reasoning merely because a runtime retained them;
- caches, generated indexes, embeddings, binaries, or other rehydratable state unless a binding-native recovery manifest explicitly includes and justifies them.

## 8. Existing protocol boundaries

This guide applies existing protocol semantics; it does not redefine them:

- **Memory:** durable items, topics, indexes, conventions, operation records, and required source archives may be selected. Tool sessions are not Memory artifacts. Live mutable input must be archived or checkpointed before recovery or export.
- **Skill Lifecycle:** the procedure body, resources, CandidateRecords, EvidenceRecords, AdoptionDecisions, observations, and lifecycle events may be selected. Installation/discovery is binding state, and evidence applicability is context-dependent.
- **Active Workspace and Inner Speech:** a closed Workspace record may be portable under its retention policy. Open work requires an explicit checkpoint. Expired or purely transient cues are excluded unless another protocol already admitted them as durable artifacts.
- **Council and Steward:** decision, dissent, work, and result records may be portable. A live delegation, standing grant, participant enrollment, or managed-resource capability requires target-side authority validation.
- **Governed Shared Memory:** moving one participant does not migrate the shared space. The participant's target identity must be re-enrolled under the binding's declared membership and identity authority. Migrating the space itself requires an attributable decision from the binding-declared authority for space continuity, must preserve audience and admission-policy history, and remains procedurally deferred by this guide.

These boundaries preserve artifact history without turning copies into current authority, current confidence, or current operational validity.

## 9. Consistency, storage, and recovery evidence

The required result is a consistent boundary, not a particular downtime technique. A binding may use a stopped snapshot, copy-on-write snapshot, transactional export, or snapshot plus incremental tail. The target must not activate until every selected revision through the declared boundary is reconciled.

Checkpoint timing should align with semantic events when possible: after an archive or consolidation pass, after a lifecycle decision commits, after a Workspace closes, or at another binding-declared atomic boundary.

Storage and transport remain binding adapters. Select them by required properties:

- durable recovery outside the source failure domain;
- integrity verification and version retention;
- confidentiality when crossing a trust boundary;
- audience isolation no coarser than the governed content requires;
- deletion semantics compatible with rights or compliance erasure;
- size and write-frequency behavior appropriate to the selected artifacts.

Content subject to erasure must not rely on an immutable history layer that cannot perform the required deletion. Such a layer may retain only an allowed content-free tombstone or digest. High-frequency noisy state, large generated data, restricted audiences, and live runtime databases may require storage separate from versioned text artifacts.

Recovery point, recovery time, retention, and drill frequency are binding-defined. A binding should keep at least one recoverable copy outside the source failure domain and should run periodic restore drills. Until a declared restore path has been exercised, it remains `unevaluated`; the existence of backup bytes alone does not establish recoverability.

## 10. Invariants

1. Logical artifact identity is independent of physical storage layout.
2. A binding-native backup must not be presented as a portable export without satisfying export requirements.
3. Authority effectiveness and secrets never transfer through package possession.
4. Every operation names a scope and one consistent checkpoint or revision set.
5. An in-place semantic rewrite cannot straddle that consistency boundary.
6. Producer, provenance, historical status, confidence, evidence, and authority records remain attributable to their source.
7. Every outgoing reference is included, stable-external, or explicitly excluded with declared degradation.
8. `complete` is a scope-qualified, evidence-gated claim.
9. Target binding wiring is reconstructed; source physical layout is not protocol truth.
10. Staged import is not activation, and copied authority records do not authorize activation.
11. A new execution context preserves historical evidence while requiring current applicability review.
12. The source remains a rollback target until validation and cutover complete.
13. At most one active binding may claim the migrated identity and mutation role after cutover.
14. Moving one participant cannot unilaterally migrate a governed shared space.
15. A restore or migration without executed validation cannot be called verified.

## 11. Failure modes

| Failure | Consequence | Required defense |
| --- | --- | --- |
| Physical directory copied as the whole Agent | Secrets, caches, host wiring, and governed artifacts are conflated | Classify four planes and reconstruct the target binding. |
| Binding-native backup presented as export | Another tool receives opaque state and portability is falsely claimed | Keep recovery and portability paths distinct; validate export semantics. |
| Partial export presented as complete | Missing sources or siblings become silent data loss | Declare scope and produce a three-state closure report. |
| Credentials or authority copied | Possession is mistaken for legitimate target authority | Exclude secrets and reauthorize through a separate path. |
| Rewrite pass crosses checkpoint | Backup or export contains a torn semantic transition | Finish the pass before the boundary or defer it; reconcile revisioned tails. |
| Imported content activates immediately | Unvalidated artifacts influence behavior in a new context | Stage first; require validation and attributable activation. |
| Producer or artifact identity cloned | Two live bindings emit indistinguishable provenance | Continue identity only under single-instance succession; otherwise mint a new binding identity. |
| Source resumes after replacement restore | One logical identity silently gains two writers | Record succession and keep the returning source decommissioned or read-only. |
| Source and target both remain authorized after cutover | Migration has become an undesigned multi-writer system | Fail closed and suspend conflicting mutation; neither this guide nor the Replication and Exchange Guide covers that topology. |
| Immutable history stores erasable content | Retention conflicts with rights or compliance deletion | Keep erasable content in deletable storage; retain only permitted tombstones or digests. |
| Backup exists but restore was never exercised | Recoverability is asserted without evidence | Mark the path `unevaluated` and run a restore drill before stronger claims. |

## 12. Proposed design checklist

This checklist describes what a future binding would verify. Passing it does not establish conformance or raise this guide above `design-only`.

1. The binding declares whether the operation follows the recovery or portability path.
2. Scope uses `full-binding`, `protocol-scoped`, or `artifact-scoped` semantics.
3. Selected state is classified into the four planes before packaging.
4. One immutable checkpoint or revision set identifies the consistency boundary.
5. A binding-native backup is not accepted as an export without independent export validation.
6. The manifest records identities, versions, digests, provenance, transformations, exclusions, and validation evidence.
7. Every outgoing reference appears in the closure report with one of the three declared states.
8. No package contains live secrets, possession-based authority, or unauthorized restricted content.
9. A target binding can be reconstructed without treating source paths or runtime files as protocol identity.
10. Imported artifacts remain staged until structural validation, authority revalidation, and the activation decision complete.
11. Replacement-host identity continuation proves single-instance succession; other clones receive new identities.
12. A migration records cutover and source decommissioning, with an intact rollback target until validation passes.
13. Existing protocol evidence and authority semantics survive without being upgraded by copying.
14. A restore drill or migration rehearsal records exactly which path and scope were exercised and which claims remain `unevaluated`.
15. If two active mutation authorities remain, the binding reports that this guide no longer covers the topology.

Incremental-tail algorithms, archive formats, encryption mechanisms, storage adapters, retention schedules, recovery objectives, whole-space migration procedure, and true multi-writer synchronization remain binding-defined or deferred until practice produces reusable evidence.

## 13. Informative environment-shift checks

The following checks are informative rather than normative. A binding should review the ones relevant to its source and target:

- absolute paths and environment-variable assumptions;
- case sensitivity and filename collisions;
- Unicode normalization and text encoding;
- link, mount, file-mode, and metadata preservation;
- scheduler and service-manager semantics;
- credential-store and host-identity mechanisms;
- database snapshot and write-ahead-log consistency;
- available tools, models, privileges, network access, and source reachability;
- time zone, clock, and event-order assumptions.

The concrete answers belong in the source and target binding records, not in this guide's protocol identity.

## 14. Final rule

> Preserve governed artifacts by meaning, not by accident of storage: back up for recovery, export for portability, rebuild the binding, re-establish authority, validate before activation, and never call an untested copy a migration.
