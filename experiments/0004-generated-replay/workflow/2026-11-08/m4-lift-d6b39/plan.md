# Plan: M4 step 1, lift D6B-39, run the MIGRATE STEPS first and the checks after

**[Proposal]** PLAN phase, 2026-11-08, HEAD `ffb7605e`. Task records only. No production file, no test, no commit, no run.
Decision basis: [DL-152 and DL-153](../../../../../wiki/planning/decision-log.md) (OWNER, walk-through D037 page 2).
Earlier form: PDB-09 and QDB-8 in the [db-transport decisions](../../2026-11-07/db-transport/decisions.md).
Defaults and OWNER questions: [decisions.md](decisions.md) (PM4-01 to PM4-14, QM4-1 to QM4-4).
By: Opus (PLAN m4-lift) for every proposal in this file.

## Scope

1. Remove the D6B-39 compile error for enum and constructor fields in a TYPE with a MIGRATE CHAIN or a VERSION MARK.
2. The versioned decode runs the MIGRATE CHANGES on the raw wire values first, then the DL-101 tail (literal map, constructor, shape).
3. A MIGRATE STEP that names an enum or constructor field stays a compile error (new text for `rename`; `add` and `drop` already fail).
4. `--stored` keeps its checks. In step 1 they read the same keys before and after the steps (see "The `--stored` path").
5. The 0005 chain test moves to the real `Order` (variant `order_v2`). `Note` stays as the small String-only control.

**Test-first rule: applies.** The change alters compile acceptance and generated decode behavior.

## Facts the step builds on (observed at HEAD `ffb7605e`)

- **[Verified]** `output_fields` (main.rs lines 1652 to 1684) raises the two D6B-39 texts for an EFFECT output or ROW TYPE.
  It is called from `effects()` for every EFFECT; the first EFFECT in source order owns the error (PDB-31 default).
- **[Verified]** A third D6B-39 text guards a redacted field in a versioned output (line 1642, ponytail comment, DL-125).
- **[Verified]** The DL-122 help names D6B-39 in two places: ENTRY RECORDS (line 4631) and RESPONSE RECORDS / ROWS (line 5693).
- **[Verified]** `versioned_decode` (line 4263) types the body per TYPE VERSION with `__beaml_valid__(Map.get(body, f), T)` before the steps.
  For `Channel` this needs an enum tuple and for `Amount` a struct, so a raw `"web"` or a raw map fails. It ends with `__beaml_valid__(shape, T)`.
  It never runs the literal map or `__beaml_from_<T>`; only `plain_decode` gets `literal_map` and `tail` from `decode_parts`.
- **[Verified]** Two callers: the http EFFECT (line 3745) and the db ROW TYPE decode (line 3887). The db `row_<t>` and the http
  result already accept `{:error, "constructor"}` when the TYPE has constructor fields (lines 4063, 3797).
- **[Verified]** `type_versions` (lines 936 to 1000): `add` and `drop` already reject every non-String TYPE ("add supports String
  fields only", "drop supports String fields only"). `rename old -> new` does not check the TYPE. So in step 1 only `rename`
  can name an enum or constructor field.
- **[Verified]** Untouched fields keep their TYPE in every TYPE VERSION (the versions are built back from the newest TYPE).
- **[Verified]** An ENTRY LINE with a versioned input TYPE is a separate error (D6B-130, line 2668). Out of scope.
- **[Verified]** Tracked sources that hit a D6B-39 text today (compiler run over `git ls-files '*.beaml'`): only
  `slice6/db/order_v2/orders.beaml`, `slice6/db/bad/row_enum_chain.beaml`, `slice6/db/bad/row_constructor_chain.beaml`.
  All three hold a db EFFECT. Inline sources: `CHAIN` and `MARK` in `tests/slice6_decode_test.py`.

## The rule change

### Compile checks (main.rs `output_fields`)

- Delete the two `if self.versioned(output)` D6B-39 branches (enum and constructor). The DL-065 and constructor checks stay.
- New check, only when `self.versioned(output)`: a `rename old -> new` in a MIGRATE STEP of `output` whose `new` is a literal
  enum field or a constructor field is an error. Default text (QM4-1 option A, PM4-03):

```
error: effect orders.save: migrate Order v1 -> v2: rename via -> channel names the enum field Order.channel; a MIGRATE STEP on an enum or constructor field waits for the fate forms (M3, DL-152)
  help: remove rename via -> channel from the MIGRATE STEP, or make channel a String field
```

  Constructor form: `names the constructor field Order.amount`, help without the String tail (as the D6B-39 texts today).
- Keep the redacted D6B-39 branch (line 1642) and its text (PM4-05).

### Live decode in the generated Elixir (`versioned_decode`)

Only for a versioned TYPE with at least one literal enum field or constructor field (PM4-06). Every other versioned TYPE keeps
its bytes exactly. Order inside `__beaml_decode_<t>(bytes, type_version)`:

1. Pick the TYPE VERSION by `{version, fingerprint}` (unchanged).
2. Per-version wire check: String, Int and list fields keep `__beaml_valid__`. A literal enum field or a constructor field is
   taken raw (key present or absent), with no check here (PDB-09 "per-version wire TYPE checks").
3. The MIGRATE CHANGES on the raw map (unchanged code; step 1 lets them name String fields only).
4. `shape = Map.take(value, declared)`, then the `literal_map` and the `tail` of `decode_parts`, as in `plain_decode`.
5. The unknown key list is the per-version `unread` list plus the nested constructor keys (`amount.extra`). The tail today
   computes top-level keys from `value`; after the steps that list is empty, so the GREEN must join `unread` (test R8).

The http EFFECT and the db ROW TYPE share this function, so both live paths and both REPLAY RUN paths change together.

### The `--stored` path (RESPONSE RECORDS and STORED ROWS)

- **[Inference]** No code change is needed. In step 1 no MIGRATE STEP may name an enum or constructor field, so the stored
  value holds those fields under the newest name in every TYPE VERSION. `value_checks` reads `literal_fields(ty)` and
  `ctor_fields(ty)` by the newest names, and the P4c String check already uses the fields of the stored TYPE VERSION.
  "Check after the steps" and "check before" read the same keys and give the same result.
- The tests R4 to R6 pin this. When M3 or DL-140 adds a step that names such a field, `value_checks` must migrate first (PM4-08).

## Callers, fixtures and tests that change

| Site | Today | After |
|---|---|---|
| main.rs `output_fields` | two D6B-39 errors | rename check only |
| main.rs `versioned_decode` and its two callers | wire values fail the pre-step check | wire check, steps, DL-101 tail |
| `slice6/db/order_v2/orders.beaml` | N12 reject | builds; header comment updated |
| `slice6/db/bad/row_enum_chain.beaml`, `row_constructor_chain.beaml` | N12 rejects | deleted (PM4-09) |
| `slice6/db/bad/row_rename_enum.beaml`, `row_rename_constructor.beaml` | absent | new N12 rejects |
| `tests/slice6_db_test.py` | `d6b_39`, BAD_CASES rows, `test_N12_order_v2_...` | rename texts, N33 runtime |
| `tests/slice6_db_stored_test.py` | no chained Order | N34 tests |
| `tests/slice6_decode_test.py` `CHAIN`, `MARK`, `VERSIONED` | both reject with D6B-39 | CHAIN: rename text; MARK: builds |
| 0005 `app/beaml/variants/note_v2/` | Note chain only | replaced by `variants/order_v2/` (PM4-11) |
| 0005 `app/test/prototype/notes_test.exs` | N7, N7b on Note | Order cases added, Note kept |
| 0005 `run.py` | `gen("note_v2")`, EXPECTED, acceptance | `gen("order_v2")`, new names |

Not touched: `lib/generated/orders.ex` (built from `orders.beaml`, Order v1, bytes unchanged), the `stricter` and `no_place`
variants, the ENTRY LINE decode (D6B-130), the DL-102 constructor help that N18 pins (PDB-32 text unchanged, QM4-3).

### Fixture sources (corpus syntax only, `//` comments)

`slice6/db/order_v2/orders.beaml`: body unchanged, header line becomes
`// Slice 6 db variant order_v2: Order with constructor and enum fields at TYPE VERSION 2; v1 rows migrate on read (DL-152).`

`slice6/db/bad/row_rename_enum.beaml` (one-line bodies as the other `bad/` files):

```
// Slice 6 db reject (N12): a MIGRATE STEP that names an enum field waits for M3 (DL-152 step 1).
enum Channel { Web = "web"  App = "app"  Unknown(String) }
type Order { order_id: String channel: Channel }
migrate Order v1 -> v2 { rename via -> channel }
type StoreError { reason: String }
effect orders.save Order -> Order ! StoreError = db.put("records")

fn save o: Order -> Order ! StoreError = o |> orders.save
```

`row_rename_constructor.beaml`: the `Amount` lines of `row_constructor_chain.beaml`, `type Order { order_id: String amount: Amount }`,
`migrate Order v1 -> v2 { rename price -> amount }`.

0005 `app/beaml/variants/order_v2/orders.beaml`: the `note_v2` source plus these changes (no VERSION MARK, PM4-12, QM4-2):

```
// EXPERIMENT 0005 variant order_v2: Order and Note at TYPE VERSION 2; v1 rows migrate on read (N7, N7b, DL-153).
type Order {
  order_id: String
  amount: Amount
  channel: Channel
  note: String
}
migrate Order v1 -> v2 { add note: String = "" }

fn to_order PlaceForm { order_id, amount, channel } -> Order =
  Order { order_id: order_id, amount: amount, channel: channel, note: "" }
```

The source is written in `beaml fmt` form (DL-148 layout); the RED worker checks `fmt` keeps it.

## RED tests

Expected values come from the plan and the tests' own digest and fingerprint code, never from the new compiler.
"RED today" names the observed failure the RED worker must record.

**0004 compile (`tests/slice6_db_test.py`, `tests/slice6_decode_test.py`)**

- **R1 `test_N33_order_v2_builds`** (replaces `test_N12_order_v2_chain_with_constructor_and_enum_fields`): `order_v2` exits 0 with
  `defmodule Orders do`. Proves `add` beside an enum and a constructor field builds. RED today: exit 1, D6B-39 text.
- **R2 `test_N12_rejects`** (table updated): `row_rename_enum` and `row_rename_constructor` give the exact QM4-1 A texts.
  Proves a step that names an enum or constructor field still errors. RED today: the D6B-39 text, not the rename text.
- **R3 `test_enum_output_field_rename_in_a_chain`** (was `test_enum_output_field_with_a_chain`, http stream): `CHAIN`
  (`rename status -> state` on `PaymentState`) gives the rename text with owner `effect payments.authorize`. RED today: D6B-39 text.
- **R3b `test_enum_output_field_with_a_version_mark_builds`** (was `..._with_a_version_mark`): `MARK` (`type Payment v3`, no
  chain) exits 0. RED today: exit 1, D6B-39 text.

**0004 live decode over the fake `BeamlDb` (`tests/slice6_db_test.py`, `ORDER_V2_CASES`, `test_N33_order_v2_runtime`)**

`ORDER_V1` = `ORDER_TYPE`; `ORDER_V2_TYPE` = `type_of("Order", 2, [..., ["note", "String"]])`; `MIGRATED_O1` = typed `o1.()` with `"note" => ""`.

- **N33_v1_row_lists_migrated**: a seeded v1 row (`WIRE1`) lists as `MIGRATED_O1` (Amount struct, `Web` tuple, note `""`).
  This is "the generated Elixir decodes a v1 row of `Order` into v2".
- **N33_v1_row_loads_migrated**: the same through `db.get`.
- **N33_v1_row_stays_v1**: `BeamlDb.rows()` keeps the v1 type and bytes after the read (DL-127 lazy).
- **N33_save_writes_v2**: a save puts head `{"Order", 2}` and the v2 `type` with its fingerprint.
- **N33_list_holds_both_versions**: one v1 row and one v2 save list as two v2 values, newest first.
- **N33_v1_unknown_channel**: a v1 row with `"tv"` lists as `Unknown("tv")`; the db record lists `channel` in `unknown_fields`.
- **N33_v1_constructor_reject**: a v1 row with currency `""` (rehashed) fails with reason `constructor`.
- **N33_v1_row_without_amount**: a v1 row without `amount` (rehashed) fails with reason `decode` (the shape check runs after the steps).
- **N33_replay_list**: the `orders.list` record of a v1 read replays without `BeamlDb` to the same value (newest-version path).

RED today for all N33 cases: the build fails (D6B-39), so `runtime` stops at setup. That is shallow. **RED depth probe**
(required, scratch tree only): in a `git archive HEAD` copy, delete only the two D6B-39 branches, build, and run N33. The
RED worker records that N33_v1_row_lists_migrated and N33_replay_list fail with reason `decode`. This proves the decode
change is needed, not only the lifted check. The probe changes no tracked file.

**0004 live decode, http stream (`tests/slice6_decode_test.py`)**

- **R8 `test_chained_enum_output_reads_a_v1_body`**: source `CHAIN_ADD` = `PS_LITERALS` + `type Payment { order_id: String state: PaymentState note: String }`
  + `migrate Payment v1 -> v2 { add note: String = "", drop legacy: String }` + `REST`. A v1 body
  `{"order_id": "o-1", "state": "ok", "legacy": "x", "extra": "y"}` with its v1 type decodes to `order_id`, the
  `Authorized` tuple, note `""`, no `legacy`; `unknown_keys` is `["extra"]`. Proves `add` and `drop` beside an enum field
  and the joined key list. RED today: build fails (D6B-39); the probe build fails with reason `decode`.
  (Comma-separated changes are corpus syntax: `migrate Payment v2 -> v3 { drop channel: String, add status: String = "migrated" }`.)

**0004 `--stored` (`tests/slice6_db_stored_test.py`)**

- **R4 `test_N34_order_v2_rows_of_both_versions_build`**: rows `row(WIRE1, ORDER_V1)` and `row(WIRE2 + note, ORDER_V2_TYPE)`
  under `ORDER_V2` exit 0 with `counted(2, 2, 0)`. RED today: exit 1, D6B-39.
- **R5 `test_N34_v1_row_lost_literal_blocks`**: a v1 row with `channel: "tv"` and no `unknown_fields` blocks with the N19
  text for `TYPE Order v1` and `LITERAL_HELP`. Control `test_N34_control_kept_v1_value_builds`: the same row with
  `unknown_fields: ["channel"]` builds. Proves the literal swap on a chained TYPE still follows DL-122. RED today: D6B-39.
- **R6 `test_N34_v1_row_constructor_blocks`**: a v1 row with currency `""` blocks with the DL-102 constructor text
  (`fails the constructor of Amount for field amount with BadAmount`, `HELP_PREFIX`). RED today: D6B-39.
- **R6b `test_N34_v1_record_of_a_chained_output_builds`** (RESPONSE RECORDS stream): a v1 `orders.load` db call record of
  `WIRE1` with `ORDER_V1` builds with the P2 count lines. RED today: D6B-39.

**0005 (`app/test/prototype/notes_test.exs`, `run.py`)**

- **R9 N7 (n7_seed) "N7 order_v2 builds against a live Order v1 row and a Note v1 row"**: replaces the `note_v2` build case;
  `live_build("order_v2", "n7")` gives `{0, [counted(2, 2, 0)]}`. RED today: exit 1, D6B-39.
- **R10 N7 (n7_read) "N7 the v1 Order row lists through the MIGRATE CHAIN with note empty and stays version 1"**: the list page
  shows `order-1`; `through_beaml!("ui.orders", "orders.list", marks)` holds the item with `"note" => ""`; the row stays version 1.
- **R11 N7b "N7b a place submit under v2 writes a version 2 Order row and the list shows v1 and v2"**: one submit, one ENTRY
  RECORD and one `orders.save` record with one trace; rows hold Order v1 and v2; the list shows both; a rebuild gives `counted(4, 4, 0)`.
- **Kept as control:** the two Note cases (N7 tag, N7b Note) unchanged in content, now under the `order_v2` module.
- **N11** also asserts Order rows of versions `[1, 2]` in the table.
- **R12 `run.py run` use case**: steps `gen-order_v2` and `compile-order_v2` replace the `note_v2` steps; EXPECTED holds the
  new names; acceptance reads `stored-order_v2` (row_count 2) and `gen-order_v2.stderr` (no DEAD LINE). Pass needs every
  N-TEST but N9 (blocked: M3) to pass. RED today: `gen-order_v2` fails, the run is `fail`.

The 0005 RED needs the local `pg_ctl` cluster (`run.py db-up`, trust auth, no secret). The RED worker starts and stops it.

## Byte-pin impact

**[Inference]** No pin site moves, under PM4-06 (new decode form only for versioned TYPES with enum or constructor fields).
No tracked source outside the three db sources above has such a TYPE, and those three are outside every pin.

| Site | Kind | Moves? | Proof |
|---|---|---|---|
| `tests/slice6_pipe_test.py` EFFECT_OUTPUTS | digest | no | test passes unchanged |
| `tests/slice6_host_struct_test.py` BYTE_GUARD | digest | no | test passes unchanged |
| `slice6/effect-reach/byte-guard.json` | digest | no | no `slice6/db` row in it |
| `tests/slice5_syntax_test.py` PIN | hash | no | R-EQ against PIN passes |
| `tests/slice6_entry_test.py` BASE, `tests/slice6_multi_test.py` BASE | hash | no | N13 guards skip db sources |
| `tests/slice6_db_test.py` P4_BASE | hash | no | N13 skips db and LIST TYPE sources |

`record_v3_test.py` V18 must also pass unchanged. A GREEN that changes the bytes of any pinned source stops and reports a
blocker. It does not re-pin in this step. If the OWNER later wants one decode form for every versioned TYPE, that is a
separate re-pin step: digest pins in its GREEN, hash pins in the commit after.

## Acceptance criteria

1. R1 to R12 pass; the RED depth probe was observed and recorded before GREEN.
2. `slice6_db_test.py`, `slice6_db_stored_test.py`, `slice6_decode_test.py` pass in full (no new skip).
3. Every byte guard above passes with no pin change; `git diff` shows no change to any pin constant or `byte-guard.json`.
4. `cargo fmt --check`, `cargo clippy -- -D warnings` and `cargo test` in `experiments/0001-syntax-to-beam` pass.
5. The 0004 full run `python3 -B experiments/0004-generated-replay/run.py` passes all steps (38 today).
6. The 0005 `python3 -B experiments/0005-prototype-fullstack/run.py run` is `pass`: N9 blocked, all others pass.
7. No main.rs text names D6B-39 for an enum or constructor field. The redacted and DL-122 help texts stay (QM4-3, QM4-4).
8. Events in `.beaml/actions.jsonl` hold no source text, path or stored value (N14, N27 pass).

## Exclusions

- Steps that name an enum or constructor field (`rename` now; later `map`, fate forms): M3, DL-116, DL-140.
- A redacted field in a versioned TYPE (DL-125 `redact` form).
- A versioned input TYPE of an ENTRY LINE (D6B-130).
- A MIGRATE CHAIN on a constructor TYPE nested inside a field (for example on `Amount`): unchanged behavior, not tested here.
- One decode form for String-only chained TYPES (byte change, PM4-06).
- The public projection per TYPE (DL-154) and the visibility rule (D040): next steps.
- Wiki, README and register updates: the docs phase after TEST.

## Phase order

PLAN (this) → plan check (fresh agent) → proposals ultra / lite → RED (R1 to R12 and the depth probe) → RED review (main
agent, then fresh agent) → GREEN (compiler; 0004 fixtures; 0005 variant, tests and `run.py`) → TEST → review (Devil's
Advocate, final slice review) → repair if needed → verify → docs. The 0005 part needs the compiler GREEN first, so one
GREEN worker does both in that order; no second behavior step is needed.

## Plan repair after plan check, 2026-11-08

Source: [plan-review.md](plan-review.md), repairs 1 to 10 (O1 to O3, medium).
By: Fable (ruling): all 10 accepted, repair 10 optional. Text applied by Opus (RED m4-lift).
The sections above stay as written; where they disagree, this section wins.

1. **0005 test order (O1).** Definition order in `NotesReadTest`: R10, Note N7, Note N7b, R11, N11 (`--seed 0`).
   Note N7b changes only `live_build("note_v2", "n7b")` to `live_build("order_v2", "n7b")`; its count stays
   `counted(3, 3, 0)`. R11 then sees Order v1, Note v1, Note v2, Order v2: `counted(4, 4, 0)`.
2. **0005 Order v2 guard (O1).** The Order v2 guard checks the module, not the encoder on an empty map: for example
   `Map.has_key?(Orders.__beaml_encode_order(o), "note")` with a full Order value, or `function_exported?`.
3. **R13 (O2).** Add **R13 `test_N33_order_v2_steps_before_the_tail`**: in the generated `__beaml_decode_order/2`,
   the line `Map.put(value, "note", "")` stands before the first `__beaml_literal_Channel` and `__beaml_from_Amount`;
   the per-version field list holds no `Channel` and no `Amount` check. RED today: build fails (D6B-39). Pins DL-152
   effect (1), which no runtime case can observe in step 1.
4. **R8 key list (O3).** `unknown_keys` means the third element of `__beaml_decode_payment(bytes, v1_type)`, not the
   RESPONSE RECORD key (that one comes from the projection and stays unchanged, QV3-6).
5. **Nested keys (O3).** Item 5 of "Live decode": nested keys are computed from the raw constructor map as today;
   not tested in step 1 (the db path drops decode keys, and no http case has a chained constructor field).
6. **N33_v1_unknown_channel (O3).** The `orders.list` record lists `items.0.channel` in `unknown_fields` (PDB-18).
7. **`--stored` path.** [Observed, plan check] with only the two branches deleted, R4, R5, R5 control, R6 and R6b
   already give the planned results; they turn RED only through D6B-39.
8. **Depth probe.** Observed in the plan check: the probe build compiles (elixirc 1.18.1 exits 0 with
   unused-function warnings for `__beaml_literal_Channel` and `__beaml_from_Amount`); v1 and v2 rows list with reason
   `decode`. The GREEN must leave no such warning: the 0005 `mix compile --warnings-as-errors` fails on it.
9. **Docs row.** "Callers, fixtures and tests that change" gets the row: 0005 `README.md` lines 39, 53, 59
   (`note_v2`, output hash): docs phase.
10. **Optional low case (taken in RED).** N33_v1_amount_no_signature: a v1 row with `amount: "12.50"` (a String, not
    a map; rehashed) fails with reason `decode` (the `__beaml_from_Amount` no-match branch).

RED placement (Opus, RED m4-lift; see decisions.md PM4-15 to PM4-19): the 0004 compiler-side cases stand in the new
file `tests/slice6_m4_test.py`, not in the three old files. The old cases that pin D6B-39 stay until GREEN retires them.
