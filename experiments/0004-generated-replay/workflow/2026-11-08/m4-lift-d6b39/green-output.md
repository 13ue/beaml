# GREEN output: M4 step 1, lift D6B-39, migrate first

**[Observed]** GREEN phase, 2026-11-08, HEAD `2dcefcdd`, no commit. Plan: [plan.md](plan.md) with "Plan repair after plan
check". RED: [red-plan.md](red-plan.md), [red-output.md](red-output.md), [red-review.md](red-review.md).
Decisions: [decisions.md](decisions.md) PM4-20 to PM4-27. By: Opus (GREEN m4-lift) for every line in this file.

## RED repairs (applied before any main.rs change)

| Repair | Change in `tests/slice6_m4_test.py` | HEAD (`ce7cd3d6…6f34`) | Probe (`f916fe6f…a0e5`, rebuilt, hash equal to red-output.md) |
|---|---|---|---|
| R8b (O1) | `test_chained_constructor_output_reads_a_v1_body`: decode-ctor source with `note: String` and `migrate Payment v1 -> v2 { add note: String = "" }`; v1 body with `amount.extra` and top-level `extra`; exact return with `["amount.extra", "extra"]` | fail: build stops at D6B-39 (constructor field `Payment.state`) | fail: `got R8b: :error` (per-version check) |
| R14 (O2) | `test_redacted_output_field_with_a_chain_still_rejects`: `output_redacted.beaml` + `migrate Payment v1 -> v2 { add status: String = "x" }` gives the exact redacted D6B-39 text | pass (guard) | pass (guard) |
| R13 (O3) | `body.count(put) == 1` and no body line starts with `#` | fail: D6B-39 | fail: `(True, True, True) != (True, False, False)` (the count check passes, the order check fails) |
| Limits | red-plan.md Limits: R8b covers the nested join; R5 to R6b cannot tell migrate-first from check-first (PM4-08); R12 fails at HEAD on three steps from one cause | | |

Key order of R8b checked against the HEAD plain decode of the same body without the chain:
`elem(__beaml_decode_payment(body), 2) == ["amount.extra", "extra"]` passes at HEAD.

Repaired RED at HEAD: 14 tests, 14 failures (13 methods fail, R2 counts 2 subtests; R14 passes). With the probe: 12 failures.

## fmt of the new fixtures

The HEAD release `fmt` exits 1 on all three (D6B-39 runs before the layout). The probe release `fmt` (only the two
branches deleted, layout code equal to HEAD) changed all three: `order_v2/orders.beaml` (Amount, Channel, Order blocks,
the `fn Amount` columns, the db EFFECT columns), `bad_rename/row_rename_enum.beaml` (Channel, Order blocks),
`bad_rename/row_rename_constructor.beaml` (Amount, Order blocks, `fn Amount` columns). A second run printed nothing (exit 0).
The fmt output is now in the tracked files. N15 `test_N15_fmt_keeps_the_fixtures` read none of them; it now also reads
`ORDER_V2` (passes on GREEN). The `bad_rename/` files cannot join N15: after GREEN `fmt` rejects them with the rename text.
Hashes: `order_v2/orders.beaml` `4d9f29f1…5f31`, `row_rename_enum.beaml` `f3e46246…ce9`, `row_rename_constructor.beaml`
`09fd3323…7c14`.

## main.rs (`experiments/0001-syntax-to-beam/src/main.rs`)

- `output_fields`: the two `if self.versioned(output)` D6B-39 branches are gone. Each literal enum field and each
  constructor field calls the new `renamed_onto`. The DL-065 and `ctor_keeps` checks stay.
- `renamed_onto` (new): a `rename old -> FIELD` in a MIGRATE STEP of the output is the QM4-1 A error
  (`migrate T vA -> vB: rename old -> new names the enum|constructor field T.f; ... (M3, DL-152)`); the enum help keeps the
  `, or make f a String field` tail.
- The redacted D6B-39 branch (PM4-05) and the two DL-122 help texts (QM4-3 A) stay; R14 pins the first.
- `versioned_decode(ty, declared, literal_map, tail)`: when `literal_map` is not empty (PM4-06: the TYPE has a literal enum
  or constructor field), the per-version list writes `:raw` for those fields, the check runs on
  `Enum.reject(fields, fn {_, type} -> type == :raw end)` (PM4-20), the MIGRATE CHANGES run on the raw map, then
  `shape = Map.take(value, declared)`, the literal map and the DL-101 tail of `decode_parts`. In the tail the top-level key
  list `Map.keys(Map.drop(value, declared))` becomes `unread` (PM4-21); the nested keys still come from the raw `value`.
  Every other versioned TYPE gets the old bytes.
- The two callers (http EFFECT, db ROW TYPE) pass `literal_map` and `tail`. One comment line at the http caller.

Checks in `experiments/0001-syntax-to-beam`: `cargo build --release` and `cargo build` pass; `cargo test` 22 + 14 passed;
`cargo clippy -- -D warnings` exit 0 (one `collapsible_if` fixed with a let chain); `cargo fmt --check` passes.
Binaries: debug `6118f4c4…0d71`, release `526670ba…8d61`. rustc 1.94.0, Python 3.13.12, Elixir 1.18.1 (OTP 27).

## Test repair found in GREEN

`N33_v1_unknown_channel` could never pass: `want` writes `r = ACTUAL; ...`, and its actual held
`l = ...; [rec] = resp.(); {l, ...}`, so `r` was the list result only. The list call and the record read moved into the
setup (PM4-24). Probe: `{{:error, %Orders.StoreError{reason: "decode"}}, []}` (still RED for the planned reason). GREEN: pass.

## Retired D6B-39 cases

- `tests/slice6_db_test.py`: `d6b_39`, the `BAD_CASES` rows `row_enum_chain`, `row_constructor_chain`,
  `test_N12_order_v2_chain_with_constructor_and_enum_fields`; files `slice6/db/bad/row_enum_chain.beaml`,
  `row_constructor_chain.beaml` deleted (staged as deletions, not committed).
- `tests/slice6_decode_test.py`: `VERSIONED`, `test_enum_output_field_with_a_chain`, `test_enum_output_field_with_a_version_mark`.
  `CHAIN` and `MARK` stay (used by `slice6_m4_test.py`).
- `bad_rename/` stays (PM4-22).
- 0004 `run.py`: `slice6_m4` joins `SLICE_TESTS` (DL-147), step `slice6-m4`.

## Per-file test counts (GREEN debug binary)

| File | Result |
|---|---|
| `tests/slice6_m4_test.py` | 14 tests, OK |
| `tests/slice6_db_test.py` | 15 tests, OK (1 skip: N2c, 0005 only, pre-existing) |
| `tests/slice6_decode_test.py` | 8 tests, OK |
| `tests/slice6_db_stored_test.py` | 49 tests, OK (3 skips: N28b, N30, N30b, blocked, pre-existing) |

## 0005

- `app/beaml/variants/note_v2/` deleted (staged). `run.py` already held `order_v2` (RED).
- README lines 39, 53, 59 kept true with short notes (PM4-27); the docs phase rewrites them.
- `python3 -B run.py db-up`: pass. `python3 -B run.py run`: **pass**, `results/20261108T074255898677Z`, compiler
  `6118f4c4…0d71`. Every step passes, among them `compile` and `compile-order_v2` (`mix compile --force
  --warnings-as-errors`), `test` (`mix test --warnings-as-errors`: 29 tests, 0 failures, 10 excluded, 1 skipped),
  `test-n7_seed`, `test-n7_read`, `test-n8` (29 tests, 0 failures each, phase filter). Use cases: 21 pass, 1 blocked (N9).
  Acceptance: no problem.
- Plan repair 8: the never-match `{:error, reason}` warning is gone in the generated code (PM4-26).
- `app/lib/generated/orders.ex` regenerated by the run: output `0cf174da…8df2`; the diff to HEAD is the 14 pre-existing
  `beaml-declaration-v1` offset lines only (PM4-25). `gen-order_v2` output `3302ade3…fa04`.

## 0004 full run

`python3 -B experiments/0004-generated-replay/run.py` (about 17 min): `{"run": ".../results/20261108T074403452811Z", "status": "pass"}`,
exit 0. 39 steps (38 plus `slice6-m4`), all pass. `slice6-m4`: 14 tests OK. `redteam-c3`: 5 tests OK (C4 passes again).
`slice6-db`: 15 OK (1 skip); `record-v3`: 26 OK (1 skip, pre-existing).

## Byte pins

No pin moved. `git diff` shows no change to `slice6/effect-reach/byte-guard.json`, `slice6_pipe_test.py`,
`slice6_host_struct_test.py`, `slice5_syntax_test.py`, `slice6_entry_test.py`, `slice6_multi_test.py`, or `P4_BASE` in
`slice6_db_test.py`. The pin-site steps of the full run pass: `slice6-pipe` (EFFECT_OUTPUTS) 12 OK, `slice6-host-struct`
(BYTE_GUARD) 3 OK, `slice6-effect-reach` (byte-guard.json) 8 OK, `slice5-syntax` (PIN) 60 OK, `slice6-entry` 20 OK,
`slice6-multi` 14 OK, `slice6-db` (P4_BASE) 15 OK, `record-v3` (V18) 26 OK.
