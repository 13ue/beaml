---
id: concept-vertical-integration
title: Vertical integration, the owner goal
kind: synthesis
status: owner-requirement
updated: 2026-11-06
---

# Vertical integration

**[Requirement]** Owner statement, 2026-11-06. BEAML owns the whole path from source to production, so that agents make fewer errors. The advantage is that one language and one compiler know every stage.

- A type system and compiler with Rust-level diagnostics, and compile times faster than Go.
- Types persist at runtime. No `any`, no casts.
- Typed errors and statically analysed failures.
- The file system describes modules and namespaces.
- Built-in tests and an eval framework for agents.
- Typed traces, dashboards, alerts and feature flags in production, from the same types.

**[Verified]** BoundaryML states the same reason for BAML: one toolchain from build to feature flags instead of a separate product per stage. See the [homepage capture](../../raw/research/baml/homepage-vertical-2026-11-06.md).

**[Inference]** A comparison that counts only hand edits against a shared library cannot show this advantage. A library with no TYPE facts needs no edit on a field change, but it also cannot type the trace or fail the build. EXPERIMENT 0004 slice 1 hit exactly this limit (see `experiments/0004-generated-replay/workflow/2026-11-06/notes.md`, final review).

## Type changes against deployed data

**[Requirement]** Owner decisions, 2026-11-06:

- The compiler knows the TYPE version of every stored record in every deployed environment (for example production, staging, demo).
- A rename is declared in the source (an alias in the style of "renamed from"). Old records then read without a migration function.
- A change of shape needs a migration function from the old version to the new version. The compiler checks that it covers every old value and returns the new TYPE or a typed migration error.
- The check runs the migration over the stored records of each environment and reports the values that fail.
- V1: any migration failure in any environment blocks the build. Later, an environment can be declared as lower priority, so that its failures do not block.

**[Proposal]** Sketch syntax, not decided: versioned TYPES (`Payment@1`), a `migrate Payment@1 -> Payment@2 ! MigrationError` form, and `case ... do ... end`. The grammar does not support these forms yet.

**[Unknown]** How each environment reports its TYPE versions and records (distributed nodes or an export). Whether the compiler proposes the rename alias as a fix.
