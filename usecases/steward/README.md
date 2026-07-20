# usecases/steward/

Concrete bindings of [Agent-first Steward Architecture](../../docs/agent-first-steward.md) — the `1:1:N` topology in which one Principal keeps one relationship with a Steward that coordinates many participants and managed resources.

Use this directory for real Steward deployments: how the relationship, participant registry, managed-resource registry, delegation, authority model, and result integration were actually realized, and what the topology exposed in practice.

## Current use cases

- [Kiro Local Steward](kiro-local-steward.md) — evidence `field-tested`, conformance `partially-verified`; a single Kiro CLI agent operating one Principal, five role-specialized sub-agent participants, and six managed remote resources at `steward:S1` with substantial `steward:S2` coverage and a declared field-tested canonical-task-record gap.

This is the first documented binding of the Steward protocol. It does not define the protocol by itself.
