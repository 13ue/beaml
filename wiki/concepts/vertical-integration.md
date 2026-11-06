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

## Totality, unknown values and migration runs

**[Requirement]** Owner decisions, 2026-11-06, after two Devil's Advocate reviews of the migration chain:

- A `migrate` chain with `rename`, `add` and `drop` holds the TYPE history. Only the newest `interface` is declared. `drop` names the TYPE of the removed field, so that every old version is fully typed.
- No guessing fallback. A step may not invent a value for a case it does not know.
- A closed TYPE (an `enum`) is matched exhaustively.
- An open TYPE (`String`, `Int`) is matched with a last branch that keeps the original value, for example `other -> Unknown(other)`. The target TYPE then has an `Unknown` variant, and every use of that TYPE must handle it.
- `add` with a constant is allowed. It is an explicit statement about the old data, not a guess.
- Unknown values stay visible through the stack. The check reports per environment how many values are `Unknown`.
- Privacy is the highest goal. A field of an `interface` can be declared as PII. The compiler keeps that value out of logs, traces and reports across the stack. See [information-flow security](information-flow-security.md).
- By default the compiler checks only the stored TYPE VERSIONS. A run of the migrations over stored values is a separate step per environment, started on request.

**[Verified]** Review round 1 found that a chain with guessing fallbacks cannot fail a build on bad data. Review round 2 found that an agent that may accept its own fallback hits turns the check into a formality. The rules above remove both: there is no guessing fallback, so there is nothing to accept.

**[Proposal]** The value run executes inside each environment and returns counts only, not record identities. A record identity can link to a person, and the fact that a record reached `Unknown` says something about its values.

- The compiler checks PII flow in both forms: a PII value that reaches an effect, and a value derived from PII by a branch (implicit flow). This is a target for the compiler, not the next slice.
- Division offers both forms: a function can return a typed `DivByZero` failure (`!`), or declare the divisor as a non-zero integer TYPE, so that the caller must prove it.
- A deploy blocks only when an environment stores a TYPE VERSION that the `migrate` chain cannot reach. `Unknown` counts are reported, not blocking.

- An `effect` that leaves the source while an environment stores its records blocks the build until `retire <effect> keep <duration>` is declared. Retired records are kept for the duration and then deleted; `keep 0 days` deletes at deploy and the report says so.
- The compiler warns about dead `retire` lines and dead `migrate` steps (no stored records left in any environment), and a command removes them on request.

**[Verified]** On the BEAM, integer division by zero raises (`badarith`). Plain arithmetic therefore breaks "no crash" without one of the two forms above.

**[Unknown]** Research items:

- Lazy migration on read or eager rewrite. The owner expects both, chosen by the kind of data.
- Large stores: migration runs in batches or as a stream of batches.
- Rollback: a lossy step (`drop`) needs a declared rollback window, or a statement that rollback past that version is not possible.
- Novelty against schema registries, Ecto migrations and lens-based migration. Not checked.
