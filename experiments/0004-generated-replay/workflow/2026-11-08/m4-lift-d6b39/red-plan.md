# RED plan: M4 step 1, lift D6B-39, migrate first

**[Proposal]** RED phase, 2026-11-08, HEAD `7fe4806b`. Plan: [plan.md](plan.md) with "Plan repair after plan check".
Evidence: [red-output.md](red-output.md). Decisions: [decisions.md](decisions.md) PM4-15 to PM4-19.
By: Opus (RED m4-lift) for every line in this file.

## Where the tests stand

| Stream | File | Joins `run.py` |
|---|---|---|
| 0004 compiler, db and http | `experiments/0004-generated-replay/tests/slice6_m4_test.py` (new) | GREEN commit (DL-147) |
| 0005 host | `experiments/0005-prototype-fullstack/app/test/prototype/notes_test.exs` | already (phases n7_seed, n7_read) |
| 0005 use case | `experiments/0005-prototype-fullstack/run.py` (gen, compile, EXPECTED, acceptance) | is the run |

Fixtures: `slice6/db/order_v2/orders.beaml` (header line only), new `slice6/db/bad_rename/row_rename_enum.beaml` and
`row_rename_constructor.beaml` (PM4-15), new 0005 `app/beaml/variants/order_v2/orders.beaml` (`fmt` keeps it, checked
with the probe binary; the HEAD `fmt` stops at D6B-39). `variants/note_v2/` stays until GREEN deletes it.

## Test list and the proof each gives

**0004, class `M4Db` (db stream, fake `BeamlDb`, `--stored`)**

| Plan ID | Test | Proof |
|---|---|---|
| R1 | `test_N33_order_v2_builds` | `add` beside an enum and a constructor field builds (D6B-39 lifted) |
| R2 | `test_N12_rename_rejects` (2 subtests) | a `rename` onto an enum or constructor field stays an error, exact QM4-1 A texts |
| R13 | `test_N33_order_v2_steps_before_the_tail` | the MIGRATE CHANGE stands before the literal map and the constructor call; the per-version list holds no `Channel` or `Amount` check (DL-152 effect (1), PM4-07) |
| N33 | `test_N33_order_v2_runtime` (10 cases) | the generated Elixir decodes a v1 `Order` row into v2, list and load; the row stays v1; a save writes v2; both versions list; a kept channel lists as `Unknown("tv")` with `items.0.channel`; the tail rejects a bad currency (`constructor`), a missing amount and a String amount (`decode`); the REPLAY RUN gives the live value |
| R4 | `test_N34_order_v2_rows_of_both_versions_build` | `--stored` counts a v1 and a v2 row of a chained `Order` |
| R5 | `test_N34_v1_row_lost_literal_blocks` | the DL-122 swap on a chained TYPE blocks with the N19 text for `TYPE Order v1` |
| R5 control | `test_N34_control_kept_v1_value_builds` | a kept value does not block, so R5 fails for the literal only |
| R6 | `test_N34_v1_row_constructor_blocks` | the DL-102 constructor text over a v1 row |
| R6b | `test_N34_v1_record_of_a_chained_output_builds` | a v1 `orders.load` db call record builds (RESPONSE RECORDS stream) |

**0004, class `M4Decode` (http stream, `slice6_decode_test` harness)**

| Plan ID | Test | Proof |
|---|---|---|
| R3 | `test_enum_output_field_rename_in_a_chain` | `CHAIN` gives the rename text with owner `effect payments.authorize` |
| R3b | `test_enum_output_field_with_a_version_mark_builds` | `MARK` (no chain) builds (PM4-04) |
| R8 | `test_chained_enum_output_reads_a_v1_body` | `__beaml_decode_payment(v1 bytes, v1 type)` returns `{:ok, value, ["extra"]}`: `add` and `drop` beside an enum field and the joined `unread` key list (plan repair 4) |

**0005 (`notes_test.exs`, definition order of plan repair 1)**

| Plan ID | Test | Proof |
|---|---|---|
| R9 | n7_seed "N7 order_v2 builds against a live Order v1 row and a Note v1 row" | the live build over Order v1 and Note v1 rows: `counted(2, 2, 0)` |
| R10 | n7_read "N7 the v1 Order row lists through the MIGRATE CHAIN with note empty and stays version 1" | the host runs Order v2 (plan repair 2 guard); the page and the `orders.list` record show the v1 row with `note: ""`; the row stays v1 |
| control | "N7 the v1 row lists ... tag empty ..." (Note, unchanged) | the String-only chain under the same module |
| control | "N7b a submit under v2 writes a version 2 row ..." (Note, `live_build("order_v2", "n7b")`, `counted(3, 3, 0)`) | the String-only chain write path |
| R11 | n7_read "N7b a place submit under v2 writes a version 2 Order row and the list shows v1 and v2" | one ENTRY RECORD and one `orders.save` record with one trace; rows Order v1 and v2; the list shows both newest first; rebuild `counted(4, 4, 0)` |
| N11 | "N11 a TYPE change reached the table ..." | also Order rows of versions `[1, 2]` |
| R12 | `run.py run` | steps `gen-order_v2`, `compile-order_v2`; EXPECTED holds the new names; acceptance reads `stored-order_v2` and `gen-order_v2.stderr` |

Test count: 12 test methods in `slice6_m4_test.py` (R2 has 2 subtests, N33 has 10 cases), 3 new and 2 changed 0005
tests (R9, R10, R11 new; Note N7b and N11 changed), 1 use case change (R12).

## Retired by GREEN (not changed in RED)

These cases pin the D6B-39 form today and pass at HEAD. The GREEN deletes or rewrites them in the same commit:
- `tests/slice6_db_test.py`: `test_N12_order_v2_chain_with_constructor_and_enum_fields`; `BAD_CASES` rows
  `row_enum_chain` and `row_constructor_chain` with their `bad/` files (PM4-09); `d6b_39` if unused then.
- `tests/slice6_decode_test.py`: `test_enum_output_field_with_a_chain`, `test_enum_output_field_with_a_version_mark`,
  `VERSIONED` (replaced by R3 and R3b in the new file).
- 0005 `app/beaml/variants/note_v2/` (PM4-11); the 0005 README rows (docs phase, plan repair 9).
- `run.py` of 0004: add `tests/slice6_m4_test.py` (DL-147).

## Limits

- R13 is structural: a GREEN that moves the tail into a helper function fails it without a wrong outcome.
- The nested `amount.extra` key join: tested by R8b on the http stream (RED repair 1); the db path drops decode keys.
- R5 to R6b cannot tell migrate-first from check-first in `--stored` in step 1 (PM4-08).
- R12 fails at HEAD on three steps (test-n7_seed, gen-order_v2, test-n7_read) from one cause (D6B-39).
- RED repairs (GREEN worker, before main.rs): R8b, R14 (guard), R13 tightened; see green-output.md "RED repairs".
- R6b asserts exit 0, the module, the rows count line and no `error` line; it does not pin the P2 count lines exactly.
