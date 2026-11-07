---
id: concept-vertical-integration
title: Vertical integration, the owner goal
kind: synthesis
status: owner-requirement
updated: 2026-11-07
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

**[Requirement]** Decided forms (DL-022, DL-023, DL-028, DL-061, DL-070 to DL-072, DL-080, DL-081):

- `type Payment v3 { … }` declares the newest record. The VERSION MARK `v3` is optional while the MIGRATE CHAIN is complete; any mark that agrees with the chain is legal.
- `migrate Payment v1 -> v2 { rename status -> state, add f: T = c, drop g: T }` holds the history. `add` needs a constant; `drop` names the TYPE.
- `retire <operation> keep <n> days` releases a deleted EFFECT with stored records (DL-055, DL-057).
- `beaml fmt` writes the default mark form (DL-081, not built).

**[Unknown]** Whether the compiler proposes the rename alias as a fix.

## Totality, unknown values and migration runs

**[Requirement]** Owner decisions, 2026-11-06, after two Devil's Advocate reviews of the migration chain:

- A `migrate` chain with `rename`, `add` and `drop` holds the TYPE history. Only the newest `type` is declared. `drop` names the TYPE of the removed field, so that every old version is fully typed.
- No guessing fallback. A step may not invent a value for a case it does not know.
- A closed TYPE (an `enum`) is matched exhaustively. `Unknown(String)` is a declared variant; the String mapping uses enum literals or an enum constructor (DL-082, narrows DL-062). Records are declared with `type` (DL-061).
- In `migrate` steps and in the decode of data from outside, an open TYPE (`String`, `Int`) is matched with a last branch that keeps the original value, for example `other -> Unknown(other)`. The target TYPE then has an `Unknown` variant, and every use of that TYPE must handle it.
- `add` with a constant is allowed. It is an explicit statement about the old data, not a guess.
- Unknown values stay visible through the stack. The check reports per environment how many values are `Unknown`.
- Privacy is the highest goal. A field of a `type` can be declared as PII with the word `redacted` before its TYPE (`card_holder: redacted String`). The compiler keeps that value out of logs, traces and reports across the stack. See [information-flow security](information-flow-security.md).
- By default the compiler checks only the stored TYPE VERSIONS. A run of the migrations over stored values is a separate step per environment, started on request.

**[Verified]** Review round 1 found that a chain with guessing fallbacks cannot fail a build on bad data. Review round 2 found that an agent that may accept its own fallback hits turns the check into a formality. The rules above remove both: there is no guessing fallback, so there is nothing to accept.

**[Proposal]** The value run executes inside each environment and returns counts only, not record identities. A record identity can link to a person, and the fact that a record reached `Unknown` says something about its values.

- An effect input loses its `redacted` fields unless the effect names them with `with <field>` (DL-089).
- The compiler checks PII flow in both forms: a PII value that reaches an effect, and a value derived from PII by a branch (implicit flow). This is a target for the compiler, not the next slice.
- Division offers both forms: a function can return a typed `DivByZero` failure (`!`), or declare the divisor as a non-zero integer TYPE, so that the caller must prove it.
- A deploy blocks only when an environment stores a TYPE VERSION that the `migrate` chain cannot reach. `Unknown` counts are reported, not blocking.

- An `effect` that leaves the source while an environment stores its records blocks the build until `retire <effect> keep <duration>` is declared. Retired records are kept for the duration and then deleted; `keep 0 days` deletes at deploy and the report says so.
- The compiler warns about dead `retire` lines and dead `migrate` steps (no stored records left in any environment), and a command removes them on request.

**[Verified]** On the BEAM, integer division by zero raises (`badarith`). Plain arithmetic therefore breaks "no crash" without one of the two forms above.

## Language forms (2026-11-07)

**[Requirement]** OWNER decisions, 2026-11-07:

- An `enum` maps a String by literals or by a constructor named like the enum (DL-082). Both at once is an error (DL-088).
- Constructor inputs come from the parameter names of its signature (DL-084).
- The first matching signature or clause wins (DL-085).
- An unreachable signature or clause is a compile error (DL-087).
- The pipe `|>` works in any expression; constructors and variants are steps (DL-086).
- `beaml fmt` aligns the columns of consecutive clauses (DL-083).
- An EFFECT gets a `redacted` field only with `with <field>` (DL-089).
- One type form `type X { … }`; a constructor makes itself the only way in (DL-092).
- `!` marks a position in a signature, not a kind of type (DL-092).
- Success and failure types never overlap: `-> String ! String` is an error (DL-093).

**[Unknown]** Research items:

- O5 is decided (DL-094): start with a live query of the deployed nodes. A registry service and exports follow later. Open: the build's access to the nodes.

- Lazy migration on read or eager rewrite. The owner expects both, chosen by the kind of data.
- Large stores: migration runs in batches or as a stream of batches.
- Rollback: a lossy step (`drop`) needs a declared rollback window, or a statement that rollback past that version is not possible.
- Novelty against schema registries, Ecto migrations and lens-based migration. Not checked.
