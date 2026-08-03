# usecases/

Practical implementation notes, field reports, and explicitly labeled design examples.

Use this directory for documents that answer:

- What was built in a real environment?
- What constraints appeared in practice?
- What pitfalls were discovered?
- What should future agents reuse or avoid?

Unlike `docs/`, this directory may use small topic folders when multiple use cases belong to the same practical domain.

## Evidence labels

Every use case MUST declare one evidence label near the title. The label describes what the page can support; it is not a quality score.

| Evidence | Meaning |
| --- | --- |
| `design-example` | Concrete binding design, but no completed run is claimed. |
| `source-inspected` | Implementation source/configuration was inspected; runtime behavior was not validated in this review. |
| `run-reported` | A specific run and outcome are documented by a cited source; this repository did not independently reproduce it. |
| `reproduced` | The documented path was executed successfully in a bounded validation environment. |
| `field-tested` | The binding operated in a real environment and either supported repeated work or exposed concrete operational lessons. |

These labels are not a total order. For example, a public `run-reported` case may be easier to inspect than a private `field-tested` binding.

`Reproducibility` uses one of these location/access labels:

| Reproducibility | Meaning |
| --- | --- |
| `public-source` | The cited source needed for inspection is publicly available. |
| `self-contained` | The page contains all material needed for a bounded reproduction. |
| `partial` | The architecture is documented, but environment-specific assets or scripts are omitted. |
| `private-source` | The inspected implementation is not published by this repository. |
| `conceptual` | The page is sufficient to design a trial, but no implementation/run artifact is supplied. |

Each use case header MUST include:

- `Use case ID`
- `Protocol` and version
- `Evidence`
- `Conformance`
- `Validation scope`
- `Reproducibility`
- `Level namespace`
- `Last reviewed`

`Level namespace` identifies the protocol-local capability ladder used by the binding for routing and validation. It does not redefine that ladder or make bare level tokens portable; prose and conformance claims MUST still use qualified tokens such as `auto-walk:L3`.

Every use case SHOULD state **What this evidence supports** and **What it does not establish**, or evidence-calibrated equivalent headings. A heading MUST NOT claim more than the declared evidence label: design examples describe proposed contributions, source-inspected cases describe inspected structure, and run-reported cases attribute observations to the cited report. Proposed behavior must not be written as observed behavior.

## Conformance labels

Evidence and protocol conformance are separate. A real historical deployment may provide strong operational evidence while still predating the current protocol schema.

| Conformance | Meaning |
| --- | --- |
| `proposed` | The binding is designed against the protocol but has not been executed. |
| `mapped` | Observed or inspected behavior is mapped to the protocol; conformance was not independently validated. |
| `partially-verified` | Named requirements were executed or inspected, with explicit remaining gaps. |
| `verified` | The claimed level's required checks were executed against the named protocol version. |

A use case MUST NOT claim a verified level merely because its behavior resembles that level. It must name the checks performed and the gaps that remain.

## Current groups

- [memory/](memory/README.md) — Real implementations of agent memory systems.
- [auto-walk/](auto-walk/README.md) — Field-tested and design-example bindings of Auto-Walk over consolidated memory or other structured corpora.
- [skill/](skill/README.md) — Imported and relationship-formed procedural artifacts with explicit lifecycle evidence and governance gaps.
- [council/](council/README.md) — Same-runtime role-diverse and heterogeneous-model Council bindings at explicitly labeled evidence levels.
- [steward/](steward/README.md) — Real `1:1:N` Steward bindings at explicitly labeled evidence and conformance levels.
