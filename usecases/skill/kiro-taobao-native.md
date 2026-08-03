# Kiro Taobao Native Skill Use Case

- Use case ID: `skill.kiro-taobao-native`
- Protocol: `skill@0.1.0`
- Evidence: `field-tested`
- Conformance: `mapped` — repeated private real-environment activations, a runtime executable fallback, and unrecorded version drift map to Skill Lifecycle concepts; no `CandidateRecord`, `EvidenceRecord`, `AdoptionDecision`, rollback record, or `skill:L0+` conformance was validated
- Validation scope: four private local Kiro CLI session archives dated 2026-03-30 were structurally inspected for skill reads, executable commands, and tool results; the current installed version metadata was inspected separately; private task content and raw transcripts were excluded
- Reproducibility: `partial` — the artifact class, observed behavior categories, lifecycle gaps, and reusable lessons are documented; the regional desktop application, account-bound environment, exact skill bodies, and private session archives are not published
- Level namespace: `skill`
- Last reviewed: 2026-08-03

## 1. Context

This use case records a local Kiro CLI binding of the imported `taobao-native` skill on macOS. The skill routes bounded commerce tasks into a desktop-application command surface for product search, product-option inspection, cart operations, page interaction, and merchant chat.

This page is evidence, not an endorsement of or dependency on Taobao or any commerce platform. The named regional artifact preserves auditability; the reusable value is the region-independent lifecycle problem it exposed: an external procedure can become operational before provenance, version, authority, update, and rollback records exist.

The observed sessions predate `skill@0.1.0`. They therefore provide historical field evidence mapped to the protocol rather than a conforming implementation of it.

### Protocol alignment note

The archived operation did not use the protocol's lifecycle records. In particular, there was no recorded candidate intake, surface review, evidence decision, adoption authority, update decision, or rollback target. This use case does not reconstruct or invent those missing records after the fact.

The same change that adds this page records the evidence-backed maturity transition of the Skill Lifecycle protocol from `design-only` to `practiced`. Maintainer review accepted that transition on 2026-08-03 because a concrete binding and its operational failures now inform the protocol's problem boundary. The transition does not validate any implementation level.

## 2. Observed operation

Four independent private local sessions on 2026-03-30 contain real invocations across several command classes:

- product search;
- product-option or SKU inspection;
- add-to-cart;
- merchant-chat open and send;
- page navigation, inspection, and reading.

The sessions repeatedly encountered an unavailable primary executable and recovered through the skill's alternate application-runner path. This is an execution-context lesson: an adopted procedure may depend on environment state — including whether the primary executable is discoverable — that the skill body and artifact version alone do not capture.

The archived skill material identified version `1.0.35`. The currently installed artifact declares version `1.0.43`. No recorded adoption, update, or rollback decision was found between those observations. This is an observed version transition with a governance gap, mapped to the protocol's **Upstream drift** failure mode; it is not evidence that a particular upstream transport or local modification caused the change.

### Evidence method and privacy boundary

The review structurally traversed tool-use and tool-result records in four private session archives. It did not rely on raw transcript string counts: embedded skill documentation repeats command examples and would overcount actual invocations. Only session-level repetition and behavior-class coverage are claimed.

Session identifiers, absolute home paths, raw logs, account data, products, merchants, and chat content are intentionally omitted. The private archives remain with the maintainer and are not part of this repository.

## 3. Mapping to the protocol

| Skill Lifecycle concept | Observed local evidence | Mapping limit |
| --- | --- | --- |
| Imported procedural artifact | A named third-party commerce skill was loaded and invoked by Kiro | Original acquisition and content-review decision were not recorded |
| Activation boundary | Commerce tasks selected a bounded skill and command surface | No formal catalog decision or routing-conflict review existed |
| Activation observation | Private session archives preserve attributable skill reads, commands, and results | They are raw historical analogues, not protocol `ActivationObservation` records |
| Execution context | macOS desktop application plus primary-command and alternate-runner paths | No immutable `ExecutionContextSnapshot` was recorded |
| Version identity | Archived version `1.0.35`; current declared version `1.0.43` | The older body was not content-addressed here; causality of the transition is not claimed |
| Procedural and routing surfaces | Skill instructions and task routing shaped bounded actions | No independent surface review was preserved |
| Privileged surface | Cart mutation and merchant messaging are consequential external actions | No protocol-level authority/security decision was preserved or retrospectively inferred |
| Candidate, evidence, adoption, rollback records | None found | No `skill:L0+` level can be claimed |

## 4. What this evidence supports

- A pre-existing imported skill can supply useful field evidence even when it predates the protocol and cannot claim conformance.
- Runtime executable discovery and fallback paths belong in execution-context lineage, not only in troubleshooting notes.
- A version transition without a new recorded decision is a concrete lifecycle failure, not merely missing documentation polish.
- Regional or product-specific skills can expose portable authority, provenance, versioning, and privacy problems.
- Private operation can be documented at behavior-class level without publishing raw conversations or account-bound data.

## 5. What it does not establish

- Any `skill:L0+` conformance or compliance with the protocol's current validation checklist.
- That version `1.0.35` was formally adopted, evaluated, security-reviewed, or approved for its observed privileged actions.
- That version `1.0.43` was reviewed as a new candidate or behaves like the archived version; current metadata cannot rewrite historical behavior.
- Any improvement claim, baseline comparison, canary result, standing automation grant, or rollback rehearsal.
- That the local Phase 1 lifecycle store is validated; this historical evidence chain is independent from that work.
- That this product, platform, skill, or command surface is generally recommended or globally representative.

## 6. Transferable lessons

1. **Keep the real artifact name.** A concrete use case stays auditable; the protocol, not the title, carries generality across regions and products.
2. **Record runtime fallback as context.** PATH, executable discovery, application state, and alternate runners can determine whether the same skill version works.
3. **Treat every external version transition as lifecycle re-entry.** A higher version string is not an adoption decision and must not silently replace the active identity.
4. **Separate usefulness from authority.** Successful cart or chat operations do not prove that the privileged surface was independently reviewed or authorized under the protocol.
5. **Minimize private evidence.** Preserve private source archives locally; publish only the smallest behavior classes, gaps, and lessons needed to support the claim.

## 7. Protocol feedback

The observed history supports, rather than revises, the protocol's existing **Upstream drift** failure mode: an active external skill changed without a recorded new decision. It also shows why `ExecutionContextSnapshot` must cover executable discovery and fallback paths when those paths affect activation outcomes.

No normative protocol change is proposed from this single binding. The next conformance-oriented use case still needs to walk one imported skill and one relationship-formed skill through the same recorded lifecycle.

## 8. Local binding record

```yaml
binding_id: kiro-taobao-native-historical
protocol: skill
protocol_version: 0.1.0
artifact_id: skill:taobao-native
acquisition_mode: imported
observed_versions:
  - 1.0.35
  - 1.0.43-current-metadata-only
level_claim: none
storage_or_runtime: local Kiro CLI with a regional desktop application
artifact_locations:
  - private local skill installation
  - private local session archives
mapped_components:
  - bounded activation observations
  - runtime executable fallback
  - version identity drift without a recorded update decision
  - consequential commerce and messaging surfaces
deviations:
  - no CandidateRecord or immutable historical content identity
  - no EvidenceRecord or evaluation baseline
  - no AdoptionDecision or authority record
  - no rollback target or lifecycle event history
  - no immutable execution-context snapshot
validation:
  evidence: field-tested
  conformance: mapped
  method: structured private session inspection; behavior classes only
  privacy: raw sessions, identifiers, account data, and task content omitted
  gaps:
    - every requirement for skill:L0 and above
    - independent content and security review
    - recorded update and rollback decisions
last_reviewed: 2026-08-03
```
