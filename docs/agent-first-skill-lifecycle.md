# Agent-first Skill Lifecycle Architecture

- Protocol ID: `skill`
- Version: `0.1.0`
- Maturity: `design-only`
- Evidence scope: No documented binding yet.
- Level namespace: `skill:L0`–`skill:L4`
- Last updated: 2026-08-03

## 1. Purpose

Agents increasingly use procedural artifacts that are loaded or invoked to perform recurring work. Different runtimes call them skills, commands, hooks, prompt modules, workflows, or procedures. They may be installed from an external source, written by the user, or formed by an Agent from repeated tasks and corrections.

These artifacts differ from ordinary memory. A memory item can be retrieved skeptically and discounted before use. A procedural artifact usually shapes behavior as soon as its activation path accepts it. Its trust boundary therefore sits at **adoption and automation**, not only at retrieval.

This protocol defines a portable lifecycle for that boundary:

```text
Acquire or form a candidate.
Stage it outside the active set.
Classify the surfaces it changes.
Record evidence and its scope.
Adopt only through attributable authority.
Observe activations in context.
Supersede, retire, or roll back without erasing history.
```

Its product is **calibrated trust in adopted procedure**.

The protocol does not require a particular file format, package manager, model, runtime, evaluator, or storage layout. One Agent can execute the minimum binding manually. More capable bindings may add scoped evaluation, standing authority, and autonomous candidate formation without weakening the earlier gates.

## 2. Design basis and evidence boundary

Three public lines of work make the problem class and major mechanisms concrete:

- [Hermes Agent skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) demonstrate runtime learning and skill curation from ordinary Agent work.
- [SkillOpt](https://huggingface.co/papers/2605.23904) treats a textual skill as an optimizable external procedural artifact and uses held-out evaluation to gate candidate changes.
- [SkillOpt-Sleep](https://github.com/microsoft/SkillOpt/blob/e7014cd18a18e11e6f6c10b897f7a009960d2e1b/docs/sleep/README.md) demonstrates an offline shape that harvests Agent usage, replays tasks, stages candidates, and separates staging from user adoption.

They are design inputs, not conforming bindings of this protocol. None of them establishes `skill:L0`–`skill:L4` conformance, and none upgrades this document beyond `design-only`.

## 3. Design goals

A good Skill Lifecycle binding should:

1. Accept both externally acquired and relationship-formed skills without creating two incompatible lifecycles.
2. Keep candidate procedure separate from active procedure.
3. Preserve origin, contribution lineage, version, and execution context.
4. Separate proposal, evidence, adoption, and publication decisions even when one Agent executes several roles.
5. Require evidence claims to name their baseline, method, and scope.
6. Prevent an Agent from creating or widening the authority used to adopt its own proposal.
7. Distinguish ordinary procedure changes from routing, privilege, and constitutional changes.
8. Make every adoption reversible without pretending that all downstream effects are reversible.
9. Work manually at `skill:L0` and add automation only after the corresponding authority and evidence gates exist.
10. Remain portable across models, runtimes, file formats, and storage bindings.

## 4. Non-goals

This protocol does not define:

- A skill marketplace, package manager, registry, installer, or update transport.
- A universal `SKILL.md` format or directory layout.
- A skill authoring style, prompt language, diff algorithm, optimizer, or evaluation harness.
- A universal router or an algorithm for optimizing skill selection.
- Automatic composition semantics for several skills.
- A security scanner or proof that a high-performing skill is non-malicious.
- Automatic changes to Steering, Conventions, identity, safety policy, or the protocol's own gates.
- A requirement that every installed procedure be enrolled in this lifecycle.
- A requirement to persist raw private reasoning or complete conversation logs.
- A claim that rollback removes every influence a procedure already had on later data or artifacts.

If a one-time manual installation is adequately governed by a small checklist, a full binding is unnecessary. The protocol becomes useful when procedure adoption is repeated, versioned, automated, evaluated, updated from upstream, or coupled to a local catalog.

## 5. Protocol-local definition of a skill

For this protocol, a **skill** is a procedural artifact whose behavioral effects occur through discrete, attributable activation events.

An activation event may be:

- an explicit invocation;
- a router selecting a procedure;
- a hook matching an event;
- a workflow starting for a bounded task;
- another enumerable transition that lets a binding say when the procedure affected behavior.

The artifact is in scope when each effect can be attributed to a bounded invocation or task. Its metadata may remain loaded continuously; physical residency is not the criterion.

Examples in scope:

- a Markdown skill loaded after a semantic trigger;
- a named command;
- a pre-commit hook whose executions are enumerable;
- a reusable prompt procedure;
- a multi-file workflow activated as one unit.

Continuous influences without enumerable activation episodes are outside this protocol:

- identity and persona;
- always-applicable normative obligations;
- global safety policy;
- the authority rules and gates of this protocol;
- other Steering or Conventions whose effects cannot be isolated to bounded activations.

Those belong to a human-reviewed constitutional path. Packaging an obligation as a skill does not move it into this protocol.

## 6. Skill surfaces and admission boundary

One artifact may contain several surfaces. A binding MUST classify the changed surfaces before adoption.

| Surface | Typical content | Required treatment |
| --- | --- | --- |
| `procedural` | Body logic, steps, examples, resources that shape task execution | Ordinary Skill Lifecycle authority and evidence gates |
| `routing` | Name, description, triggers, selection hints | Ordinary gates plus catalog conflict review |
| `privileged` | Tool permissions, allowlists, dependencies, execution access | Preserved in lineage; requires a separate authority/security decision; no standing auto-adoption |
| `constitutional` | Identity, always-applicable obligations, safety policy, authority grants, lifecycle gate configuration | Outside protocol jurisdiction; split and route to the constitutional path, or reject the whole candidate if it cannot be separated |

The binding MUST fail closed when it cannot distinguish a privileged or constitutional change from ordinary procedure.

A declared privilege surface does not make content review unnecessary. A procedure may instruct the Agent to use undeclared tools or exfiltrate data. Declaration-versus-behavior mismatch is a security-review signal.

The following invariant applies to every transition:

```text
privileged_delta is not empty
  → standing automatic adoption is invalid for this candidate
  → an attributable privilege/security authority must decide
```

A skill may remain one versioned candidate while its surfaces pass through different gates. The protocol does not require splitting one file into several files, but it does require the surfaces and decisions to remain distinguishable.

## 7. Logical organization of skills

This protocol defines a logical organization, not a filesystem standard.

### 7.1 Skill artifact: the lifecycle unit

The smallest lifecycle unit is one addressable activation unit. It MUST have:

- a stable artifact id;
- a version or immutable content identity;
- a declared activation boundary;
- an owner or authority reference;
- surface classification;
- provenance sufficient to distinguish upstream content from later contributions;
- a rollback target once it becomes active.

One skill may be a single file or a directory containing instructions, scripts, templates, tests, and resources. These files share one lifecycle only when they are activated, versioned, and rolled back as one behavioral unit.

### 7.2 Resource boundary

Resources that materially affect behavior belong to the artifact boundary even when stored elsewhere. A binding SHOULD record stable references or content identities for:

- scripts and deterministic tools;
- templates and examples;
- policy or rendering specifications used by the procedure;
- tests and validators shipped as part of the skill;
- external dependencies whose change may alter behavior.

Untracked mutable resources make version claims incomplete. A binding may pin them, snapshot them, or declare them as an explicit evidence limitation.

### 7.3 Bundle or repository: a distribution unit

A repository, plugin, or bundle may distribute many skills. It is not automatically one lifecycle unit.

```text
one repository
  ├── skill A — independently adopted and versioned
  ├── skill B — independently adopted and versioned
  └── skill C — not installed
```

Installing one item does not imply adopting its siblings. A bundle-level release may provide provenance, but each activated skill retains its own adoption decision, evaluation scope, and rollback path unless the binding explicitly declares an inseparable activation unit.

The same repository may be a relationship-formed personal library for its author and an imported source for another adopter. `acquisition_mode` describes the artifact's position relative to the current Principal–Agent relationship, not an intrinsic artifact type.

### 7.4 Catalog: inventory and routing view

The catalog is the binding's current view of candidate, staged, active, and retired skills. At minimum it SHOULD make discoverable:

- artifact id and active version;
- lifecycle state;
- acquisition mode and provenance reference;
- routing surface;
- privilege summary;
- authority owner;
- available rollback target;
- locations of lifecycle records.

The catalog is not a hierarchy of importance and does not need to be one file. It may be a directory scan, manifest, database view, runtime API, or generated index.

### 7.5 Lifecycle store: evidence outside executable instructions

Candidate, evidence, adoption, observation, and rollback records MUST remain distinguishable from the active procedural body. Otherwise the procedure can silently rewrite the record used to justify its own adoption.

A binding may colocate records beside a skill or store them centrally, but active instructions MUST NOT be the sole source of truth for their own authority, evaluation, or history.

### 7.6 Reference logical shape

The following is conceptual, not a required directory tree:

```text
Skill environment
  Catalog
    active and staged artifact references
    routing and privilege summaries

  Skill artifacts
    procedural surface
    routing surface
    privileged declarations
    versioned resources

  Lifecycle records
    candidates and provenance chains
    scoped evidence records
    adoption decisions
    activation observations
    lifecycle events and rollback lineage

  Execution contexts
    append-only snapshots or fingerprints
```

Bindings may map this shape to files, Git commits, database rows, content-addressed storage, or runtime-native objects.

## 8. Two relational acquisition modes

`acquisition_mode` is a closed distinction about where the artifact was formed relative to the current Principal–Agent relationship.

### 8.1 `imported`

The artifact was formed outside the current relationship.

Examples:

- installed from a public repository;
- copied from another user;
- supplied by an organization;
- pasted from a blog or package, even if the current user performs the paste.

The principal threats are hostile instructions, undeclared privilege, dependency drift, upstream replacement, and claims made only by the upstream author.

### 8.2 `formed`

The artifact was formed inside the current relationship.

Examples:

- written directly by the user for this Agent;
- drafted by the Agent from repeated workflows;
- jointly revised from user corrections;
- distilled from local task trajectories.

The principal threats are self-confirmation, poisoned trajectories, private-data capture, premature generalization, and overfitting to one model or environment.

### 8.3 Provenance is a contribution chain

Producer identity is not a single label that can be overwritten by a later edit. A candidate SHOULD retain an append-only contribution chain covering:

- source or upstream reference;
- who drafted, edited, reviewed, or approved each material contribution;
- source trajectory references for formed candidates;
- execution contexts in which source trajectories or evaluation materials were created.

The protocol MUST NOT derive adoption authority merely from producer identity. User editing does not erase an Agent-generated contribution, and Agent involvement does not negate a later explicit user decision.

The two modes merge after candidate creation. From that point onward they share one state machine; their threat reviews and authority policies remain parameterized by provenance.

## 9. Core artifacts

The artifact names below are protocol concepts. A binding may encode them as files, events, database rows, or in-memory records.

### 9.1 CandidateRecord

Records one proposed artifact version and SHOULD identify:

- candidate id, artifact id, proposed version, and base version;
- acquisition mode and contribution lineage;
- changed surfaces and `privileged_delta`;
- source and formation-context references;
- intended activation boundary and expected benefit;
- status: `candidate` or `staged`.

### 9.2 EvidenceRecord

Records one scoped comparison and MUST identify:

- candidate and baseline;
- evaluation method;
- declared scope;
- `execution_context_ref`;
- material-disclosure references;
- evaluation state under `procedure-evaluation-v1`;
- inspectable evidence or a stable reference to it.

Evaluation state belongs to this scoped record, not to the artifact version globally. The same version may be `supported` in one scope and `contradicted` in another.

### 9.3 AdoptionDecision

Records one authority decision and MUST identify:

- candidate and target activation scope;
- decision: adopt, reject, defer, or roll back;
- authority or standing-grant reference;
- EvidenceRecords actually relied upon;
- any explicit evidence limitation or manual override;
- publication status, which is separate from local adoption.

Proposal, evidence, and adoption are separate roles and separate records. One Agent MAY execute several roles, but it MUST NOT collapse their records or create the authority used to approve its own proposal.

### 9.4 ActivationObservation

Records an attributable activation episode:

- artifact id and version;
- task or invocation id;
- `execution_context_ref`;
- observable outcome and evidence references;
- optional `intervention-outcome-v1` verdict;
- attribution limits.

An observation is not automatically an evaluation. It becomes evaluation evidence only through a scoped comparison with an explicit baseline.

### 9.5 LifecycleEvent

Records a state transition or an append-only assessment such as:

- stage, activate, supersede, retire, or roll back;
- upstream update detected;
- compatibility assessment;
- impact-review finding;
- publication decision;
- privilege or constitutional escalation.

Historical EvidenceRecords are never rewritten by later context changes. Applicability changes are expressed through new LifecycleEvents or new EvidenceRecords.

### 9.6 ExecutionContextSnapshot

Records or identifies the append-only context behind an `execution_context_ref`. It MUST preserve a recoverable snapshot or fingerprint of the material execution environment without requiring one physical storage format. §13 defines its required contents, level-specific use, and applicability semantics.

## 10. Lifecycle and state transitions

```text
candidate
  → staged
  → active
  → superseded | retired | rolled-back
```

Rules:

1. A candidate MUST NOT become active merely because it exists.
2. Staging MUST be behaviorally isolated from the active set.
3. Every activation MUST cite an AdoptionDecision.
4. An upstream update or local edit creates a new candidate; it does not silently mutate the active version.
5. One artifact version MAY be active in one scope and staged or retired in another.
6. Supersede and rollback preserve prior versions and lifecycle records.
7. Rollback restores an artifact version; it does not erase effects already propagated into later trajectories, candidates, or evaluation materials.
8. Publishing is not a lifecycle synonym for adoption. It requires its own decision.

## 11. The four gates

### 11.1 Authority gate: entry into the active set

Every activation requires attributable authority:

- an explicit Principal decision; or
- a standing grant created outside the proposal path.

The proposal path MUST NOT create, widen, or reinterpret the authority used to adopt its own candidate.

### 11.2 Evidence gate: automation

Agent-initiated or automatic adoption additionally requires:

- one or more supporting EvidenceRecords whose scopes cover the target execution context;
- a standing grant that explicitly authorizes this class of adoption;
- an empty `privileged_delta` and no constitutional content;
- the required independent security admission.

A candidate with a privileged change uses its own attributable authority/security decision and does not re-enter this standing automatic-adoption path merely because that decision resolves the privilege review.

Evidence insufficient for automation may still support an explicitly authorized provisional adoption.

### 11.3 Claim gate: improvement language

Claims such as `improved`, `better`, `optimized`, or `non-regressing` require a named baseline and supporting comparison evidence within the stated scope.

Authority cannot waive this semantic requirement. A user may adopt an unevaluated candidate, but the system MUST describe it as unevaluated rather than improved.

### 11.4 Publication gate: leaving the local relationship

Local adoption never implies publication. Publication requires:

- separate authority;
- privacy and secret review;
- accurate attribution and licensing review where applicable;
- a statement of whether the change is local specialization or a portable upstream candidate.

## 12. Evidence discipline

### 12.1 Minimum admissibility

Evidence used for automation or improvement claims MUST provide:

1. **Explicit baseline.** Compare with the current active version or the absence of the artifact.
2. **Declared scope.** Name model, runtime, tools, task domain, catalog/combination state, and material environmental constraints.
3. **Reviewability.** Preserve inputs, outputs, verifier results, user comparisons, or stable references sufficient to re-check the conclusion.
4. **Material disclosure.** State which materials shaped the candidate and which shaped the evaluation. Formation context for evaluation tasks, baselines, rubrics, and other measuring instruments is included.

Materials used to form a candidate MAY also appear in an evaluation only when that reuse is disclosed and the evidence is downgraded accordingly. A frozen held-out set is a strong form of independence, not the only valid form.

### 12.2 Evaluation methods

Common methods, roughly from stronger mechanical isolation to more contextual judgment, include:

```text
deterministic verifier
  → frozen held-out replay
  → bounded canary with preset success/stop criteria
  → user pairwise comparison
  → observable outcome from real work
```

The method does not determine truth by itself. A deterministic verifier may cover only format; a human comparison may cover qualities the verifier cannot measure. The EvidenceRecord MUST state what the method establishes and what it leaves untested.

A canary can support provisional, explicitly authorized adoption. It cannot by itself unlock standing automatic adoption because its evidence arrives after activation.

### 12.3 Evaluation state

EvidenceRecords use `procedure-evaluation-v1`:

| Value | Meaning |
| --- | --- |
| `unevaluated` | No comparison outcome is available for the declared scope. |
| `supported` | The cited comparison supports the stated claim within scope. |
| `contradicted` | The cited comparison provides evidence against the stated claim within scope. |
| `inconclusive` | A comparison was attempted, but available evidence does not resolve the claim within scope. |

States from different scopes MUST NOT be collapsed into one global artifact status. Conflicting records in the same scope remain visible and require explicit reconciliation; a binding MUST NOT silently select the convenient record.

### 12.4 Self-assertion is not comparison evidence

The following may motivate review but do not independently satisfy the evidence gate:

- an Agent saying its own candidate is better without inspectable outcomes;
- an upstream README claiming superiority;
- popularity, stars, or install count;
- an undisclosed model judgment;
- successful execution without a baseline.

The same Agent MAY run a deterministic verifier, execute a disclosed replay, or record user feedback. Role separation concerns records and authority, not necessarily different model identities.

## 13. Execution context and applicability

When each mechanism operates, its context obligation begins at its level: every EvidenceRecord (`skill:L2+`), ActivationObservation (`skill:L3+`), and formed candidate source trajectory (`skill:L4`) MUST carry an `execution_context_ref`. Evaluation materials such as task sets and baseline corpora carry the context in which they were formed at `skill:L2+`.

The reference resolves to an append-only snapshot or fingerprint sufficient to recover the material environment, including:

- model and runtime;
- available tools and relevant versions;
- catalog revision or active skill set;
- artifacts actually invoked during the episode;
- other binding-declared factors needed to interpret the result.

The protocol requires recoverability, not an inline list. A content hash, immutable manifest, database snapshot, or append-only record is valid.

Evidence scope MUST be derived honestly from observed contexts. Running in one context does not justify a universal claim.

### 13.1 Historical truth vs current applicability

An EvidenceRecord is not rewritten when the environment changes. The statement "candidate B outperformed baseline in context C" remains a historical observation.

What changes is whether that record applies to current context C′:

- automation and improvement claims MUST cite supporting records applicable to C′;
- a material context change SHOULD trigger impact review for already-active artifacts that relied on C;
- compatibility assessments MAY bridge a change only with an attributable, inspectable reason;
- a standing grant MAY declare context dimensions that cannot be bridged without new evaluation.

Compatibility assessments and adverse impact findings are append-only LifecycleEvents. They do not mutate the original evidence.

### 13.2 Influence propagation and formation monoculture

Active procedures shape later trajectories, candidate formation, and the choice of evaluation tasks. If skill A influenced the context in which skill B or B's measuring materials were formed, that relationship remains visible in their context references.

When A is retired or found unsafe, the binding SHOULD inspect active descendants and evidence formed under contexts containing A. At `skill:L4`, a formed candidate MUST retain these context references and MUST NOT present itself as an independent discovery when its source distribution was shaped by active skills.

Rollback can restore A's artifact version. It cannot automatically remove A's influence from B, historical data, or user habits.

## 14. Imported candidate protocol

An imported candidate enters the same lifecycle but has a distinct intake threat model.

Before activation, the binding MUST:

1. Record origin, version/content identity, and licensing/attribution information when relevant.
2. Review instructions, tool use, dependency paths, and data-flow risks through an independent security admission appropriate to the environment.
3. Treat upstream claims as provenance, not local evaluation evidence.
4. Preserve lineage separability between upstream content and local changes.
5. Treat every upstream update as a new candidate.
6. Apply the privilege gate to any permission or dependency expansion.

Human review is a safe default but not a universal requirement. A binding MAY automatically admit a pinned, trusted source under an explicit standing policy, provided the security admission still occurs and the policy cannot be widened by the candidate path.

## 15. Formed candidate protocol

A formed candidate may begin from:

- repeated successful workflows;
- recurring user corrections;
- stable local constraints;
- repeated failure that has a resolved workaround;
- an explicit user request to preserve a procedure.

The candidate-formation path MUST:

1. Distinguish a reusable procedure from a one-time task, unresolved failure, or temporary preference.
2. At `skill:L4`, record source trajectories and their execution contexts; at lower levels, preserve available source references. No level requires unrestricted private reasoning.
3. Remove secrets and minimize personal data before staging.
4. State whether the candidate is local specialization or intended to be portable.
5. Avoid turning one incident into a universal procedure.
6. Produce a CandidateRecord, not an active skill.

User corrections are strong formation signals but not automatically proof that a generalized candidate improves every task. They may support an explicitly scoped, provisional adoption.

## 16. Evidence-gated evolution

Evidence-gated evolution is the discipline used by `skill:L2+`:

```text
Experience proposes.
Optimization creates a candidate.
Evidence scopes what may be claimed or automated.
Authority decides what becomes active.
Observation may support, contradict, or limit later use.
```

A binding may use an optimizer model, deterministic mutation, human editing, or another method. The optimizer does not own adoption authority.

Offline or "sleep" processing may harvest eligible task records, cluster recurring work, construct replay jobs, and stage candidates. It MUST NOT activate them by bypassing `skill:L0`–`skill:L3` requirements.

## 17. Catalog and routing boundary

Routing metadata is part of the skill artifact. Changing a description or trigger is a behavior change and enters the same candidate lifecycle.

At `skill:L1+`, before adopting a routing change, the binding MUST review detectable conflicts with the active catalog, including:

- stealing prompts from a neighboring skill;
- making two triggers indistinguishable;
- widening a trigger beyond the evaluated task domain;
- shadowing a pinned or higher-authority procedure;
- creating a route that requires a new privilege.

This protocol does not define a routing algorithm or require a global routing benchmark. A scoped EvidenceRecord states whether evaluation was isolated, catalog-aware, or composition-aware.

Skill-to-skill composition semantics and router optimization are v0 non-goals. A binding MUST NOT claim composition non-regression when it evaluated only one skill in isolation.

## 18. Connections to neighboring protocols

### 18.1 Memory

Memory calibrates trust in retained testimony at retrieval. Skill Lifecycle calibrates trust in adopted procedure at activation and automation.

- A lesson about a skill's performance may enter Memory through capture.
- The skill artifact itself does not become a memory item.
- Activation observations may contribute to metamemory or skill evaluation through explicit references.
- Skill Lifecycle never edits Memory directly.

### 18.2 Steering and Conventions

Normative obligations, identity, authority grants, safety policy, and always-applicable rules use the human-reviewed constitutional path described by [Memory's promotion boundary](agent-first-memory.md#17-promotion-path).

```text
Obligation or constitution → Steering / Conventions path
Bounded callable capability → Skill Lifecycle
```

Privilege and constitutional deltas are transferred explicitly; they are never smuggled through ordinary skill adoption.

### 18.3 Active Workspace and Council

Active Workspace may record a current candidate, evaluation task, or adoption action. Council may review candidates or conflicts. Neither protocol becomes mandatory, and neither consensus nor salience is evidence by itself.

### 18.4 Steward

Steward standing authority may authorize bounded lifecycle actions, but it cannot create new authority. A Steward may coordinate evaluation or adoption while preserving the Principal's authority, evidence provenance, and publication boundary.

### 18.5 Composition

Cross-protocol artifacts use the [shared composition envelope](composable-agent-cognition.md#6-shared-artifact-envelope). Protocols read peers through retrieval interfaces and write peers through capture or event interfaces.

## 19. Security and privacy boundary

Behavioral evidence and security evidence answer different questions:

```text
Behavioral evidence: does this procedure help under a declared comparison?
Security review: can this procedure misuse authority, tools, data, or dependencies?
```

A malicious candidate may perform well on every evaluation task. Therefore:

- imported content review is never waived by performance evidence;
- formed trajectory and evaluation-material review is never waived by local authorship;
- privilege changes always leave the standing automation path;
- publication requires explicit privacy and secret review;
- candidates MUST NOT carry credentials or raw sensitive transcripts;
- a candidate cannot modify the gate, standing grant, or security policy used to admit itself.

The protocol defines where the independent security decision is required. It does not define how a security scanner works.

## 20. Failure modes

| Failure mode | Symptom | Prevention |
| --- | --- | --- |
| Persistent prompt injection | Poisoned trajectory becomes a durable formed skill | Review formation sources; keep security admission independent from performance evidence |
| Self-confirmation loop | Agent proposes, praises, and activates its own candidate | Separate records; require attributable pre-existing authority and inspectable evidence for automation |
| Evidence leakage | Formation material silently becomes evaluation material | Material disclosure; name baseline and context; prefer held-out evaluation when practical |
| Goodhart drift | Measurable format improves while caution or boundaries degrade | State method limits; use multiple scoped evidence types; preserve contradicted records |
| Routing capture | One description steals neighboring tasks | Treat routing as a surface; review active-catalog conflicts |
| Privilege creep | Minor update silently expands tools or dependencies | Detect `privileged_delta`; invalidate standing automatic adoption |
| Upstream drift | Active external skill changes without a new decision | Pin identity; treat update as a new candidate |
| Scope laundering | Local result is reported as model-independent | Scoped EvidenceRecords; no global evaluation state |
| Rollback illusion | File rollback leaves derived candidates and evidence trusted | Execution-context lineage; impact review; never claim influence rollback |
| Formation monoculture | Active skills shape all future skills toward themselves | Preserve source-context refs; audit L4 lineage and alternative formation sources |
| Measuring-stick contamination | Biased context shapes the evaluation task set itself | Record formation context for tasks, baselines, and rubrics |
| Publication leakage | Private local specialization is pushed upstream | Separate publication gate with privacy and attribution review |
| Product capture | Protocol becomes a directory, diff, or evaluator specification | Keep physical organization and algorithms binding-specific |

## 21. Degraded operation

Each capability fails independently:

- Without evaluation infrastructure, explicit authority may adopt a candidate with an explicit `unevaluated` status and honest limitations.
- Without automation, the complete lifecycle may run manually.
- Without a catalog API, a binding may maintain a small inspectable manifest.
- Without Memory, formed candidates require explicit local source references or remain unavailable.
- Without post-adoption observation, the binding cannot claim feedback-loop conformance.
- If execution context cannot be recovered, affected evidence is inapplicable to automation or improvement claims.
- If a security gate is unavailable, only the affected candidate is blocked; existing unrelated skills continue.

Degraded operation MUST NOT invent evidence, broaden authority, or silently change the active version.

## 22. Minimal binding

A manual `skill:L0` binding can be small:

1. Select one imported or formed candidate.
2. Give it a stable artifact id and immutable version/content identity.
3. Record acquisition mode, source/contribution lineage, activation boundary, and changed surfaces.
4. Route privileged content through a separate authority/security decision; split constitutional content or reject the candidate.
5. Record an explicit AdoptionDecision.
6. Activate exactly the approved version.
7. Preserve the prior active version or “no skill” state as a rollback target.
8. Record later supersede, retire, or rollback events.

This level does not claim improvement, evidence-gated automation, autonomous formation, or publication.

## 23. Implementation levels

| Level | Name | Capability |
| --- | --- | --- |
| `skill:L0` | Recorded adoption | Imported and formed candidates can be adopted manually with provenance, version identity, attributable authority, surface review, and rollback. |
| `skill:L1` | Staged lifecycle | Candidate/active separation, lineage separability, upstream-update re-entry, privilege-delta detection, and routing conflict review operate. |
| `skill:L2` | Scoped evidence | EvidenceRecords, `procedure-evaluation-v1`, comparison/claim gates, applicability, canary or held-out methods, and contradiction/rollback discipline operate. |
| `skill:L3` | Governed automation | Standing grants permit bounded automatic adoption; privilege changes invalidate automation; activation feedback and context-impact review close the loop. |
| `skill:L4` | Autonomous formation | Offline trajectory mining or runtime review forms and stages candidates with source/context lineage; it never bypasses lower-level gates to activate them. |

Start at `skill:L0`. The levels are cumulative. A system that mines candidates automatically but lacks staged isolation, scoped evidence, or standing authority has an isolated `skill:L4`-style capability; it does not conform to `skill:L4`.

## 24. Validation checklist

Before claiming a Skill Lifecycle level, verify:

1. A skill has a stable artifact id, version/content identity, activation boundary, and owner/authority reference.
2. A repository or bundle does not become one lifecycle unit merely because it distributes several skills.
3. Active procedure and lifecycle records have distinguishable sources of authority.
4. Imported and formed candidates both enter the same state machine while preserving distinct provenance.
5. Surface classification distinguishes procedural, routing, privileged, and constitutional changes.
6. A privileged delta prevents standing automatic adoption.
7. A constitutional change cannot enter through the skill path.
8. Every activation cites an AdoptionDecision and every automatic activation cites a pre-existing standing grant.
9. Proposal, evidence, and adoption remain separate records even when one Agent performs all roles.
10. An upstream update creates a new candidate instead of mutating the active artifact.
11. A local adoption can be rolled back without deleting prior versions or records.
12. Publication requires a distinct decision and privacy review.
13. (`skill:L1+`) Staging is behaviorally isolated and routing changes receive catalog conflict review.
14. (`skill:L2+`) Evidence and evaluation-material context references resolve to append-only snapshots or fingerprints; `skill:L3+` activation observations and `skill:L4` formed trajectories do the same.
15. (`skill:L2+`) Every improvement claim cites a baseline and one or more applicable EvidenceRecords.
16. (`skill:L2+`) The same version may carry different evaluation states in different scopes without flattening them.
17. (`skill:L2+`) Evaluation task, baseline, and rubric formation contexts are disclosed.
18. (`skill:L2+`) Historical evidence is preserved when context changes; applicability is recomputed rather than history rewritten.
19. (`skill:L3+`) Automation cannot create or widen its own standing grant.
20. (`skill:L3+`) Context changes that affect active evidence trigger the binding's declared impact-review policy.
21. (`skill:L4`) Formed candidates preserve source-trajectory and evaluation-material context lineage.
22. (`skill:L4`) Autonomous formation produces staged candidates and cannot directly activate them.
23. No conformance claim depends on raw private chain-of-thought persistence.
24. The binding remains usable without a marketplace, hosted service, or separate optimizer model.

## 25. Practical use cases

No conforming binding is documented yet.

The public systems in §2 motivate the problem and design, but they are not use cases of `skill@0.1.0`. The first use case should manually walk one imported skill and one formed skill through the same lifecycle, then state exactly which checks were reproduced and which remain proposed.

## 26. Final rule

```text
Memory calibrates testimony when it is retrieved.
Skill Lifecycle calibrates procedure when it is adopted.

External skills and personal skills enter through different trust edges,
then share one inspectable lifecycle.

Authority guards entry.
Evidence guards automation and improvement claims.
Security remains an independent gate.
Publication remains a separate decision.

Every version has lineage.
Every claim has scope.
Every activation has authority.
Every automated adoption has applicable evidence.
Every artifact can roll back.
Its past influence cannot be wished away.
```
