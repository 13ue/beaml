---
id: concept-vertical-integration
title: Vertical integration, the owner goal
kind: synthesis
status: owner-requirement
updated: 2026-11-08
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

## Design principle: declarative for shape and policy (2026-11-07)

**[Requirement]** DL-126 (OWNER): declarations carry shape and policy, expressions carry computation only, and the COMPILER derives the rest. Today declarative: TYPES and VERSIONS, enum literals, `redacted`, EFFECT signatures with their transport, MIGRATE STEPS and fates (DL-125), RETIRE LINES. Derived, never written: decode, host structs, spans, REPLAY RUN. Expressions: fn bodies, pipes, constructor clauses.

**[Proposal]** Candidates on the roadmap, concept only: entry points declared (`route`, `on`; closes the inward view of D018), policy on EFFECT lines (retry, timeout, idempotent), simple rules on a TYPE field (`where`), examples in the source as tests and replay fixtures, retention per TYPE (`keep N days`), trace resolution per subtree with a time limit (D018). Every new declaration needs a compiler semantics and keeps an expression escape hatch.

## The inbound side (2026-11-07)

**[Verified]** Slice 6d closes the vertical line on the inward side ([EXPERIMENT 0004 slice 6d](../../experiments/0004-generated-replay/README.md#slice-6d-the-entry-line-inbound-effect), DL-128, DL-130 to DL-134, DL-138). A UI EVENT enters through an ENTRY LINE written like an outbound EFFECT; the head TYPES must equal those of the target fn (`test_n10_rejects`). The COMPILER generates one host function `ui_<event>/1` with the root span, the decode and a `Rejected` struct for a bad form (`test_n1_entry_line_gives_one_function`, `test_n5_to_n9_orders_runtime`); a removed ENTRY LINE warns in the host build (`test_h2_host_build_without_the_entry_warns`). Each call of a flow target writes an ENTRY RECORD with its capture outcome, and `--stored` checks the accepted ones against a stricter constructor or a lost ENUM LITERAL (`test_s2_stricter_constructor_blocks`, `test_s3_removed_literal_blocks`); a removed ENTRY LINE with stored records blocks until a RETIRE LINE (`test_s5_removed_entry_line_with_stored_entries_blocks`, `test_s5b_retire_line_frees_the_removed_entry_line`). Limits: one ENTRY LINE per source, `ui.event` only, no enum or constructor field below the top level of the form TYPE, no full run after the TEST repair.

## One record format for every EFFECT stream (2026-11-08)

**[Verified]** Record format v3 gives the outbound and the inbound EFFECT STREAM one RECORD CORE of 14 keys, with `request` and `status` as HTTP extras ([EXPERIMENT 0004 record format v3](../../experiments/0004-generated-replay/README.md#record-format-v3-one-record-core-for-every-effect-stream), DL-143). Both writers emit `version: 3`, one `span_id` and `outcome`/`reason` at capture (`test_V1_to_V10_response_record`, `test_V11_entry_record`); the RESPONSE RECORD `reason` equals the live failure reason (`test_V8_guard_live_status_reason`). `--stored` reads version 3 only on both streams (`test_V12_response_record_version_2_blocks`, `test_V13_entry_record_version_2_blocks`) and skips the value and path checks for records rejected at capture, while the orphan and held checks still read them (`test_V22_status_record_without_a_path_builds`, `test_V24_control_accepted_record_without_a_path_blocks`, `test_V25_held_check_reads_a_rejected_record`). One source may now hold several EFFECTS and ENTRY LINES, with a REPLAY RUN by operation (`test_n3_to_n6_runtime`). Limits: the digest half of DL-136 was open (D035) until step P2b built it (DL-164, 2026-11-08, [P2b](../../experiments/0004-generated-replay/README.md#step-p2b-a-wrong-digest-stops-the-build-dl-164)); the db stream got the core in P4 (2026-11-08, see below).

## The database side (2026-11-08)

**[Verified]** P4 carries the vertical line down to the stored row ([EXPERIMENT 0004 database transports](../../experiments/0004-generated-replay/README.md#database-transports-dbput-dbget-dblist-and---stored-over-rows), DL-127, DL-129, DL-137). Three `effect` lines with `db.put`, `db.get` and `db.list` over one `records` table write a ROW CORE through the host `BeamlDb` as a JSON binary and decode rows by TYPE name, digest, TYPE VERSION and MIGRATE CHAIN (`test_N2_to_N11_orders_runtime`, `test_N29_read_order_digest_before_type_version`). A REPLAY RUN substitutes each db call from its record and never calls the host (`N11_replay_list`). `--stored` checks the ROW SNAPSHOT as it checks stored records: a stricter constructor or a lost ENUM LITERAL blocks the build (`test_N18_stricter_constructor_blocks`, `test_N19_lost_literal_blocks`), a partial snapshot blocks (`test_N24_partial_row_snapshot_blocks`), and two ROW TYPES in one table decode each by its own TYPE (`test_N20b_two_row_types_build`). A TYPE change travels from the source to a stored row with no second migration system: proven at the 0004 level for String-only ROW TYPES (Note, `test_N31_note_chain_read_runtime`, `test_N5_migrate_chain_on_read`), the real `Order` chain waits on M4. Limits: no shape check over rows yet (P4c); fake `BeamlDb` only, real `jsonb` in EXPERIMENT 0005; the RETIRE LINE meaning for rows is M5.

## The first full vertical line: form to row and back (2026-11-08)

**[Verified]** EXPERIMENT 0005 runs the line end to end in a Phoenix LiveView PROTOTYPE on a local Postgres ([EXPERIMENT 0005](../../experiments/0005-prototype-fullstack/README.md#result-2026-11-08), DL-127 to DL-129, DL-144). A form submit enters BEAML only through the generated `Orders.ui_place/1`, which writes the ENTRY RECORD and one STORED ROW through `db.put` and the host `BeamlDb` (N2, N3); the list page reads only through `db.list` and renders the returned BEAML value (N5, N6). A `Note` v1 row is read through the MIGRATE CHAIN after the v2 source ships, and a v2 submit writes version 2 beside it (N7, N7b). `mix beaml.stored` snapshots the live rows, and a stricter `Amount` blocks the build against them until the row is deleted (N8, N8b, N8c). The one Ecto migration did not move (N11). [Run](../../experiments/0005-prototype-fullstack/results/20261108T003740313204Z/result.json): 19 use cases pass, N9 blocked. Limits: the FATE OPERATION that frees the stricter build waits on the fate slice (N9, D036); the real `Order` chain waits on M4; `run.py run` truncates the dev rows (O1); `BeamlDb.get/3` matches raw JSON (O2); the page calls the internal `__beaml_encode_order/1` (O3); local demo only, no deploy.

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
- **[Verified]** Update fates a4: `fmt` drops an implied TYPE VERSION MARK (DL-104 A) except on a chain with a fate line, which keeps it (QA4-1 A, built default, [D052](../planning/decisions-to-be-made.md#d052--fmt-layout-of-fate-chains-and-migrate-step-bodies-fates-a4)).

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
  - **[Verified]** Superseded 2026-11-07 by [DL-102](../planning/decision-log.md), [DL-121](../planning/decision-log.md) and [DL-122](../planning/decision-log.md): the `--stored` check also runs the generated Elixir constructors and the ENUM LITERAL mapping over the stored values at build time. A failing value or a lost literal blocks the build. The text above stays as the 2026-11-06 record (RED TEAM 01, finding D6).

**[Verified]** Review round 1 found that a chain with guessing fallbacks cannot fail a build on bad data. Review round 2 found that an agent that may accept its own fallback hits turns the check into a formality. The rules above remove both: there is no guessing fallback, so there is nothing to accept.

**[Proposal]** The value run executes inside each environment and returns counts only, not record identities. A record identity can link to a person, and the fact that a record reached `Unknown` says something about its values.

- An effect input loses its `redacted` fields unless the effect names them with `with <field>` (DL-089).
- The compiler checks PII flow in both forms: a PII value that reaches an effect, and a value derived from PII by a branch (implicit flow). This is a target for the compiler, not the next slice.
- Division offers both forms: a function can return a typed `DivByZero` failure (`!`), or declare the divisor as a non-zero integer TYPE, so that the caller must prove it.
- A deploy blocks only when an environment stores a TYPE VERSION that the `migrate` chain cannot reach. `Unknown` counts are reported, not blocking.
  - **[Verified]** Superseded 2026-11-07 by [DL-102](../planning/decision-log.md), [DL-121](../planning/decision-log.md) and [DL-122](../planning/decision-log.md): a deploy also blocks when a stored value fails a new constructor or mapping rule, or holds a removed ENUM LITERAL, until a MIGRATE STEP declares its fate. `Unknown` counts stay non-blocking ([DL-103](../planning/decision-log.md)). The text above stays as the 2026-11-06 record (RED TEAM 01, finding D6).

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
  - **[Verified]** Built 2026-11-07 in [EXPERIMENT 0004 slice 6b steps 6b and 6c](../../experiments/0004-generated-replay/README.md#slice-6b-step-6b-redacted-fields): `with` sends the field on the wire only; the record, the span and the event never hold it. A direct copy into a field that is not redacted is a compile error (DL-112). Limit: a derived copy (`+`, a constructor, a fn that builds a record, two hops) builds, and one such path reaches the store in plain form ([step 6c limits](../../experiments/0004-generated-replay/README.md#slice-6b-step-6c-redacted-copies), O1). The flow check stays a target (DL-029).
- One type form `type X { … }`; a constructor makes itself the only way in (DL-092).
- `!` marks a position in a signature, not a kind of type (DL-092).
- Success and failure types never overlap: `-> String ! String` is an error (DL-093).

**[Unknown]** Research items:

- O5 is decided (DL-094): start with a live query of the deployed nodes. A registry service and exports follow later. Open: the build's access to the nodes.

- Lazy migration on read or eager rewrite. The owner expects both, chosen by the kind of data.
- Large stores: migration runs in batches or as a stream of batches.
- Rollback: a lossy step (`drop`) needs a declared rollback window, or a statement that rollback past that version is not possible.
- Novelty against schema registries, Ecto migrations and lens-based migration. Not checked.

See also [syntax sentiment](syntax-sentiment.md): what programmers love and hate in syntax, the BEAML scorecard and the open items D026 to D033.
