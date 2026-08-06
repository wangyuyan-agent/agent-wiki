# Governed Shared Memory Composition Profile

- Document ID: `governed-shared-memory`
- Version: `0.1.0`
- Maturity: `design-only`
- Evidence scope: No documented binding yet.
- Scope: governed shared standing over existing artifacts; no standalone protocol or conformance level
- Last updated: 2026-08-06

## 1. Purpose

This guide defines a composition profile for several participants that need durable, inspectable shared standing over artifacts they already produce.

The core rule is:

> Admission grants standing in one declared space. It does not make the admitted artifact true, consensual, more confident, or jointly owned.

The profile is perspective-preserving. A Memory item remains testimony from its original producer. A DecisionRecord remains a decision made under its original authority. A ConflictMap remains a record of disagreement. The shared space governs whether and how another participant may cite, rely on, or attest to that artifact; it does not replace the artifact's original semantics.

This is a composition guide rather than a standalone protocol. It governs artifacts from existing protocols or bindings and defines no independent content taxonomy, capability ladder, or conformance claim.

## 2. When to use it

Use this profile when all of the following are true:

1. Two or more participants need durable access to the same governed standing.
2. The artifacts already have immutable version identity or a content digest, producer, and source or provenance references.
3. Mere file visibility is insufficient because audience, admission authority, or permitted reliance must be explicit.
4. Preserving different perspectives matters more than synthesizing a single shared conclusion.

Do not use it when a direct handoff, one bounded response, one canonical Steward record, or an ordinary read-only corpus is sufficient.

An Agent MAY discover this guide through `protocols.yaml` and decide that the profile appears applicable. Discovery is not activation. An Agent MUST NOT silently create a shared space, widen its audience, appoint an authority, or admit an artifact unless an existing binding explicitly grants that action.

For an existing declared space, an Agent MAY retrieve, cite, challenge, or propose artifacts only within its granted role. When no declared space exists, it may recommend or propose one and must wait for the required authority decision.

A minimal declaration is:

```yaml
profile: governed-shared-memory@0.1.0
space_id: team:research
audience_ref: group:research-participants
admission_authority_ref: user:owner
```

A durable binding MUST additionally expose a monotonic revision or equivalent freshness token. It MAY declare storage, writer, rendering, erasure, and audit policies. These operational choices do not change the three logical identifiers above.

## 3. Non-goals and relationship to Memory

This profile does not define:

- A collective brain, shared truth, consensus store, or last-writer-wins database.
- A new `SharedMemoryItem` type or a copy of every participant's private Memory.
- Direct multi-participant writes to any participant's Memory store.
- A replacement for Memory retrieval, capture, archive, or Autodream.
- A mandatory Council, Steward, service, daemon, transport, database, or model provider.
- A way for repeated Agent output to create authority or constitutional rules.

Each participant's Memory binding retains its own ownership and single-writer rules. Its Autodream may maintain its private retained testimony under the Memory protocol. The shared space is never an Autodream target.

A participant MAY read admitted artifacts and capture a derived lesson into its own Memory through the normal private capture path. That new Memory item must preserve references to the shared-space artifact and must not claim that admission verified the source claim.

## 4. Core model

### 4.1 SpaceDescriptor

A governed shared space has three logical identifiers:

```yaml
space_id: <stable space identifier>
audience_ref: <who may discover or read the space>
admission_authority_ref: <who may grant or withdraw standing>
```

Audience and admission authority are different resources. Read access does not imply admission authority. A binding MUST define attributable authority for changes to membership, audience, admission policy, and erasure policy.

Revision mechanics belong to the binding, not to the logical identifier set.

### 4.2 AdmissionRecord

An AdmissionRecord is an attributable statement that one artifact has a named standing in one space:

```yaml
admission_id: <stable identifier>
space_ref:
  space_id: <stable space identifier>
  expected_revision: <policy revision evaluated by the authority>
  policy_snapshot_ref: <immutable snapshot reference or content digest>
target_artifact_ref: <immutable version identity or content digest>
admitting_authority_ref: <attributable authority>
granted_standing: <epistemic-citation | operational-binding | existence-attestation>
rendering_type: <null | verbatim | redacted | existence-only>
rendering_ref: <null or derived artifact reference>
occurred_at: <timestamp>
```

The local closed standing values mean:

- `epistemic-citation` — participants may retrieve and cite the artifact as attributable testimony; confidence is unchanged.
- `operational-binding` — participants may rely on the artifact only within its original authority and validity window.
- `existence-attestation` — participants may assert that the artifact or admission exists, not disclose or rely on its content.

Admission and verification MUST be recorded separately. Evidence supporting admission MAY be referenced by a binding, but an AdmissionRecord MUST NOT silently inherit, raise, or translate the target artifact's confidence.

`rendering_type` MUST be consistent with `granted_standing`. An `existence-only` rendering may be paired only with `existence-attestation`; `epistemic-citation` and `operational-binding` require content that their authorized audience can actually inspect.

Before admission, the authority MUST compare the proposal's expected space policy revision and policy digest with the current policy. A stale proposal must be rejected or revalidated when audience, authority, or admission policy changed. `policy_snapshot_ref` must resolve independently of mutable current metadata to the exact policy representation used for the decision; a scalar revision alone is insufficient.

An AdmissionRecord binds to the exact admitted artifact identity. Any semantic in-place mutation must mint a successor identity, and every successor version must enter through a fresh proposal and admission decision; it does not inherit the predecessor's standing. Revocation and supersession are attributable event-log entries that reference the prior `admission_id`; they do not erase the historical fact that the admission occurred.

### 4.3 Rendering and lineage

No rendering is required when the audience can resolve `target_artifact_ref` directly. When `rendering_ref` is present, the AdmissionRecord is also the explicit grant for that exact rendering identity and the declared space audience. A new rendering identity or a changed audience or disclosure policy requires a fresh authority decision. A materialized rendering follows one of three rules:

1. `verbatim` MAY preserve the original claim identity only when wording, semantics, producer, source lineage, and disclosure scope are unchanged. Otherwise it receives a new identity.
2. `redacted` MUST receive a new artifact identity and a `derived_from` reference because redaction changes what can be asserted or verified.
3. `existence-only` MUST receive a new artifact identity. It is a meta-claim about existence or admission, not a content-preserving copy.

Restricted provenance must remain explicit. A participant without access to a target may receive an existence-only rendering only when the AdmissionRecord grants `existence-attestation` for that rendering and audience; the system MUST NOT replace an inaccessible reference with silent or fabricated lineage.

Immediate sources and root sources are distinct. Several artifacts or assertors that resolve to the same root source do not constitute independent corroboration. Admission logic and later audits SHOULD compare resolved source roots when corroboration is claimed.

## 5. Lifecycle and read discipline

The lifecycle is:

```text
artifact exists in its home system
  -> participant proposes standing in a declared space
  -> admission authority accepts, rejects, or defers
  -> admitted artifact is retrieved, cited, or acted on within granted standing
  -> participants may challenge provenance, validity, rendering, or standing
  -> authority may revoke or supersede the admission
```

Automated capture may append to a proposal inbox. It MUST NOT bypass the admission decision.

Retrieval MUST distinguish authorization from availability:

- When the requesting identity is not authorized to resolve the target, record `access-restricted` and expose only an explicitly granted existence-only rendering. Do not relabel the target `source-unavailable`.
- When the identity is authorized but the target or its source cannot be resolved, record `source-unavailable` and cite the admission only as historical or existence-level context.
- When the target is resolvable, evaluate both the AdmissionRecord and the target artifact's current metadata.

- `operational-binding` standing MUST NOT outlive the underlying DecisionRecord or authority grant.
- An expired or revoked target must not be used as a live operational basis merely because its AdmissionRecord remains in history.
- A superseded target may be cited as historical context, but its successor requires a new admission.
- `source-unavailable` means lineage cannot currently be resolved; it does not mean the claim is false.
- Audit findings are attributed testimony, not authority decisions.

## 6. Shared-Space Audit, not Autodream

Maintenance is optional. A minimal manual binding is valid without a background process.

A binding MAY run a `Shared-Space Audit` to inspect referential integrity and emit append-only findings. It MAY deterministically flag:

- `target-superseded`
- `lapsed-on-expiry`
- `access-restricted`
- `source-unavailable`
- `suspected-echo`

Each finding must identify its producer, source references, observation metadata, time, and epistemic status. Findings and event records MUST contain only references, digests, and metadata outside the erasure scope; they must not copy verbatim or otherwise erasable target content. A retrieval path MUST NOT treat a finding as if the admission authority had revoked, retargeted, or downgraded the artifact.

Shared-Space Audit MUST NOT:

- Admit, revoke, or retarget an admission.
- Change `granted_standing` or any artifact's confidence.
- Synthesize admitted perspectives into an official common conclusion.
- Expand membership, audience, admission authority, or its own read scope.
- Verify restricted content on behalf of an identity that cannot access it.

Every maintenance write MUST atomically commit its materialized change, the next space revision, and the append-only event, using one transaction or compare-and-swap operation. If the storage cannot provide atomicity, the binding MUST define idempotent recovery and a committed marker; readers must reject an incomplete revision or an event that cannot reproduce the exposed state. A proposal inbox and event log need no Autodream of their own. Mechanical rotation or digests may compress presentation, but they must not replace traceability or become a semantic distillation stage.

The only permitted destructive path is an explicitly authorized rights or compliance erasure. It is not an audit decision. The admission authority, or a separate erasure authority declared by the binding, executes it and records a content-free tombstone:

- Verbatim content covered by the erasure MUST be removed.
- Redacted and existence-only artifacts normally remain with `source-erased`, unless the authorized erasure scope also covers their remaining content.
- Ordinary source deletion or loss records `source-unavailable`; it never implies claim falsity.

## 7. Invariants

1. Standing is not truth, consensus, confidence, importance, or ownership.
2. Admission is not verification; both remain separately attributable.
3. Original artifact type, producer, status, authority, and confidence remain authoritative.
4. An Agent proposal cannot create its own admission authority.
5. A successor artifact cannot inherit standing by lineage alone.
6. Renderings preserve explicit lineage, require an audience-scoped grant, and mint new identity whenever semantics or disclosure changes.
7. Multiple assertors with one root source do not create independent evidence.
8. Restricted references remain explicit and fail closed.
9. Private Memory stores remain private capture targets; the shared space is not a multi-writer Memory store.
10. Shared-Space Audit may observe and flag but cannot decide or expand its authority.
11. Materialized state, space revision, and append-only event commit atomically or remain unreadable until recoverable.
12. Rights and compliance erasure is explicit, scoped, attributable, and distinguishable from ordinary source loss.

## 8. Failure modes

| Failure | Consequence | Required defense |
| --- | --- | --- |
| Shared database treated as truth | Perspective and uncertainty disappear | Preserve original artifacts; grant standing only. |
| Standing copied into confidence | Institutional admission becomes false epistemic certainty | Keep admission and verification separate. |
| Automatic successor retargeting | Maintenance process manufactures authority | Require a fresh proposal and admission. |
| Echo laundering | One source looks independently corroborated | Resolve and compare source roots. |
| Access denial labeled unavailable | Readers confuse authorization with source loss | Distinguish `access-restricted` from `source-unavailable`; expose only granted renderings. |
| Audit flag treated as verdict | Auditor becomes a shadow authority | Treat findings as testimony and require authority action. |
| Stale operational binding | Participants act on expired or revoked decisions | Check target validity at retrieval and action time. |
| Authority or audience creep | Automation widens its own powers | Require attributable constitutional changes. |
| Partial maintenance commit | Readers observe a revision that its event cannot reproduce | Atomically commit state, revision, and event or reject incomplete revisions. |
| Erasure confused with source loss | Content is deleted unnecessarily or retained unlawfully | Separate authorized erasure from `source-unavailable`. |

## 9. Proposed design checklist

This checklist describes what a future binding would verify. Passing it does not establish conformance or raise this guide above `design-only`.

1. A declared `space_id`, `audience_ref`, and `admission_authority_ref` exist.
2. One participant can propose without being able to admit its own proposal.
3. One attributable authority can admit an immutable artifact identity against a resolvable immutable snapshot of the current space policy with one local standing value.
4. Another authorized participant can retrieve the admission and the target's current metadata.
5. A redacted or existence-only rendering receives a new identity, explicit lineage, and an audience-scoped rendering grant.
6. Two apparent corroborations with one root source remain non-independent.
7. A superseded target produces review-needed state rather than automatic successor admission.
8. An expired or revoked operational target cannot remain an actionable basis.
9. Audit read scope is no wider than the identity running it.
10. Every audit finding is attributed, metadata-only, non-authoritative, and atomically revisioned with its event.
11. Access restriction, authorized erasure, and ordinary source unavailability take three distinct paths.
12. The binding can degrade to participants' private stores without losing the historical admission log.

Membership and identity mapping, physical storage topology, transport, freshness intervals, dispute procedure, multi-space federation, and richer source graphs remain binding-defined until practice produces reusable field evidence.

## 10. Final rule

> Share governed standing, not a merged mind: preserve each artifact's origin, require declared authority for admission, and let automation flag uncertainty without manufacturing truth or power.
