# Decisions: M4 step 1, lift D6B-39, migrate first

**[Proposal]** PLAN phase, 2026-11-08, HEAD `ffb7605e`. Plan: [plan.md](plan.md).
Basis: [DL-152, DL-153](../../../../../wiki/planning/decision-log.md) (By: 13ue). Earlier form: PDB-09, PDB-31, PDB-32, QDB-8 in
the [db-transport decisions](../../2026-11-07/db-transport/decisions.md).
Undo and Repair defaults below run through (DL-041, DL-144). Migrate questions are for the OWNER, with a built default marked
`(default, open)`; nothing here closes them.

## Undo and Repair defaults

**PM4-01 · Repair · One behavior step, one ledger.**
Chose: the compiler change, the 0004 fixtures and the 0005 move in one RED / GREEN pair. Over: a second step for 0005.
Because: the 0005 tests need the compiler change; split, the 0005 half has no behavior of its own. Commits us to: one GREEN
worker does the compiler first, then 0005.
→ By: Opus (PLAN m4-lift)

**PM4-02 · Undo · The first EFFECT in source order owns the new compile error.**
Because: PDB-31 default for D6B-39; the same check site (`output_fields`).
→ By: Opus (PLAN m4-lift)

**PM4-03 · Repair · Only `rename` gets the new error; `add` and `drop` keep their texts.**
Chose: a new check for `rename old -> new` onto an enum or constructor field. Over: one new text for all three forms.
Because: `add` and `drop` already reject every non-String TYPE (slice 3 texts, pinned elsewhere). Commits us to: QM4-1 decides
the wording; QM4-4 decides whether `rename` stays an error at all.
→ By: Opus (PLAN m4-lift)

**PM4-04 · Undo · A VERSION MARK alone (no chain) on a TYPE with an enum field builds.**
Because: DL-152 lifts D6B-39 in full; the mark case (`MARK` in `slice6_decode_test.py`) has no step to name a field.
→ By: Opus (PLAN m4-lift)

**PM4-05 · Repair · The redacted D6B-39 branch stays.**
Chose: keep the error for a redacted field in a versioned output TYPE (main.rs line 1642). Over: lift it too.
Because: DL-152 names constructor and enum fields; the versioned decode marks no redacted field, and that lift waits for the
`redact` form (DL-125). Commits us to: the text keeps the ID D6B-39; the docs phase notes that D6B-39 now covers the redacted
field only.
→ By: Opus (PLAN m4-lift)

**PM4-06 · Repair · The new decode form only for versioned TYPES with an enum or constructor field.**
Chose: every other versioned TYPE keeps today's `versioned_decode` bytes. Over: one form for every versioned TYPE.
Because: no pin site moves (six sites, two missed re-pins on 2026-11-07); the String-only form is a special case of the new
form with an empty literal map and no constructor fields. Commits us to: two templates in `versioned_decode` until a later
re-pin step joins them (`ponytail:` comment at the branch).
→ By: Opus (PLAN m4-lift)

**PM4-07 · Repair · The per-version check takes enum and constructor fields raw.**
Chose: no `__beaml_valid__` for those fields before the steps; the DL-101 tail checks them after. Over: a wire check per field
(`is_binary` for a literal enum, a String map for a constructor).
Because: the tail already rejects every bad wire value (`__beaml_literal_E(_)` is `:error`, the constructor `cond` falls to
`:error`, the shape check needs every key). A second check adds code and no outcome. Commits us to: R8 and the N33 cases
`v1_constructor_reject` and `v1_row_without_amount` prove the tail runs.
→ By: Opus (PLAN m4-lift)

**PM4-08 · Repair · `--stored` gets no code change in step 1.**
Chose: keep `value_checks` as built. Over: migrate the stored value first, then check.
Because: step 1 forbids every step that names an enum or constructor field, so both orders read the same keys (plan,
"The `--stored` path"). Commits us to: R4 to R6b pin the result; the M3 / DL-140 step must add the migrate-first order there.
→ By: Opus (PLAN m4-lift)

**PM4-09 · Undo · Delete `bad/row_enum_chain.beaml` and `bad/row_constructor_chain.beaml`.**
Because: both build now; `order_v2/` covers an enum and a constructor field beside `add`. `test_N12_rejects` requires `bad/`
and its table to agree.
→ By: Opus (PLAN m4-lift)

**PM4-10 · Undo · The DL-122 swap case uses an unkept non-literal String, not a new `no_app` chained fixture.**
Because: the checker treats a String that is no current literal and is not kept the same way in both cases (`value_checks`);
no new fixture is needed.
→ By: Opus (PLAN m4-lift)

**PM4-11 · Repair · 0005: one variant `order_v2` with both chains replaces `note_v2`.**
Chose: `variants/order_v2/` = the `note_v2` source plus `Order v2`; the Note cases stay as the String-only control.
Over: keep `note_v2` and add a second variant phase. Because: one `gen` step and one compile keep the run as long as today;
when the Order cases fail and the Note cases pass, the fault is in the enum or constructor path. Commits us to: new EXPECTED
names in `run.py`; `stored-order_v2` replaces `stored-note_v2` in the acceptance check.
→ By: Opus (PLAN m4-lift)

**PM4-12 · Undo · `Order` in `order_v2` has no VERSION MARK (built default of QM4-2).**
Because: the `note_v2` and `plain_v2` forms; `fmt` writes a mark after a SQUASH only (DL-081, form b).
→ By: Opus (PLAN m4-lift, default, open)

**PM4-13 · Undo · A RED depth probe in a scratch tree is required.**
Because: every new test fails today at the D6B-39 compile error; the probe shows the decode change is needed too.
→ By: Opus (PLAN m4-lift)

**PM4-14 · Undo · New test names, no renumbering.**
Chose: N33 (0004 live decode of `order_v2`), N34 (`--stored` over chained `Order`), R3 and R3b by name in the decode test.
Because: N1 to N32 are taken in the db tests.
→ By: Opus (PLAN m4-lift)

## OWNER questions (Migrate)

**QM4-1 · Migrate · The error text for a MIGRATE STEP that names an enum or constructor field.**
→ A: an effect-scoped text in the D6B-39 style, with the step, the field and the wait for M3:
`error: effect orders.save: migrate Order v1 -> v2: rename via -> channel names the enum field Order.channel; a MIGRATE STEP on an enum or constructor field waits for the fate forms (M3, DL-152)`
`  help: remove rename via -> channel from the MIGRATE STEP, or make channel a String field`
→ B: a step-scoped text in the slice 3 K style, with no EFFECT and no M3 reference:
`error: migrate Order v1 -> v2: rename via -> channel: rename supports String fields only`
→ Built default: A (default, open). Pins: the two new N12 rows and R3. Undo cost: one text and three test strings.
→ By: Opus (PLAN m4-lift, default, open)

**QM4-2 · Migrate · The VERSION MARK on the 0005 `Order`.**
→ A: `type Order v2 { ... }` with the chain (the mark agrees with the chain; legal under DL-080).
→ B: no mark, the chain alone (the `note_v2` and `plain_v2` form).
→ Built default: B (PM4-12). Both build after this step (R3b covers a mark). The OWNER chooses the form the PROTOTYPE shows.
→ By: Opus (PLAN m4-lift, default, open)

**QM4-3 · Migrate · The help texts that still name D6B-39.**
The DL-122 help (ENTRY RECORDS, RESPONSE RECORDS, ROWS) reads: "slice 6b has no MIGRATE STEP form for an enum field (D6B-39), so
restore the removed or changed ENUM LITERAL of Channel". The rule is lifted; the form still does not exist (M3, DL-140).
→ A: keep the texts in step 1 (no pin moves; four tests pin them).
→ B: name the real wait: "... no MIGRATE STEP form for an enum field yet (M3, DL-140), so restore ...".
→ Built default: A (default, open). B moves four test strings, no byte pin.
→ By: Opus (PLAN m4-lift, default, open)

**QM4-4 · Migrate · Does `rename` of an enum or constructor field stay an error in step 1?**
With the steps first, `rename via -> channel` only moves the raw value to the new key; the literal map and the constructor run
after it. So it would work without M3.
→ A: an error in step 1 (DL-152 Effect (2), the task text). It waits for M3 with `map` and the fate forms.
→ B: allow `rename` now; only `map`, a fate form or a TYPE change waits for M3. Cost: one more runtime test, `--stored` must
   then migrate first (PM4-08 no longer holds).
→ Built default: A (default, open).
→ By: Opus (PLAN m4-lift, default, open)
