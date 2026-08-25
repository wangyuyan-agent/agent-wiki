# usecases/active-workspace/

Concrete bindings of [Agent-first Active Workspace Architecture](../../docs/agent-first-active-workspace.md).

Use this directory for bounded task-state implementations that keep goals, constraints, evidence, assumptions, risks, actions, revisions, and closure visible without storing raw private reasoning.

## Current use cases

- [Kiro Local Active Workspace](kiro-local-active-workspace.md) — evidence `field-tested`, conformance `mapped`; a historical retired local binding with two ordinary-work durable closed records and an earlier lifecycle canary. It supports `practiced` protocol maturity but does not claim `active-workspace:L1` because schema tokens, audited-completion coverage, and checklist requirements were not validated.

Use cases in this group are evidence, not schema extensions. A durable YAML-shaped record does not establish a protocol level unless the binding validates the current version's required fields, closed vocabularies, and applicable checklist.
