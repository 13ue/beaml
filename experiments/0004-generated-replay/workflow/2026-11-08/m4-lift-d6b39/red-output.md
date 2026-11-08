# RED output: M4 step 1, lift D6B-39, migrate first

**[Observed]** RED phase, 2026-11-08, HEAD `7fe4806b`, `main.rs` unchanged in the working tree. Plan: [plan.md](plan.md).
Test list: [red-plan.md](red-plan.md). By: Opus (RED m4-lift).

## Toolchain and binaries

- rustc 1.94.0, cargo 1.94.0, Python 3.13.12, Elixir 1.18.1 (OTP 27), psql 17.11.
- HEAD debug `experiments/0001-syntax-to-beam/target/debug/beaml-spike` sha256 `ce7cd3d6…6f34` (the binary `st.compiler()` uses).
- HEAD release `target/release/beaml-spike` sha256 `b3f60ef3…5d01` (same 12 tests fail, same texts).
- Probe release (scratch, `git archive HEAD`, only the two D6B-39 branches of `output_fields` deleted; diff sha256
  `304baa1c…6db7`, 10 lines removed, 3 D6B-39 texts left: redacted branch and the two DL-122 helps) sha256 `f916fe6f…a0e5`.
- Inputs: `slice6_m4_test.py` `afa5e54e…cc3d`, `order_v2/orders.beaml` `0017628f…809d`, `bad_rename/row_rename_enum.beaml`
  `096208a0…0a81`, `row_rename_constructor.beaml` `f60ca7c3…db20`, 0005 `variants/order_v2/orders.beaml` `2cebe886…443b`.

## Commands

```
cargo build --offline --quiet && cargo build --offline --quiet --release      # in experiments/0001-syntax-to-beam
python3 -B experiments/0004-generated-replay/tests/slice6_m4_test.py           # HEAD debug: exit 1, 12 tests, 13 failures
BEAML_SPIKE=<HEAD release> python3 -B .../slice6_m4_test.py                    # exit 1, 13 failures
BEAML_SPIKE=<probe release> python3 -B .../slice6_m4_test.py                   # exit 1, 11 failures (depth probe)
python3 -B experiments/0005-prototype-fullstack/run.py db-up                   # pass
python3 -B experiments/0005-prototype-fullstack/run.py run                     # HEAD debug: fail, results/20261108T071807583197Z
BEAML_SPIKE=<probe release> python3 -B experiments/0005-prototype-fullstack/run.py run   # fail, results/20261108T071859360642Z
```

Both 0005 runs rewrite the tracked `app/lib/generated/orders.ex` in their last `gen-orders` step. The rewrite differs
from HEAD in 14 `beaml-declaration-v1` offset lines (2 bytes each); I restored the HEAD bytes with `git checkout`.
**[Inference]** the HEAD module is 2 bytes behind `app/beaml/orders.beaml`: a pre-existing drift, not this RED.

## 0004 at HEAD (debug): every test fails at the D6B-39 compile error

| Test | Exit | Failing assertion (short) | Why this is the right failure | False pass risk |
|---|---|---|---|---|
| R1 `test_N33_order_v2_builds` | 1 | `(0, True) != (1, False)`; stderr `the constructor field Order.amount cannot stand in a TYPE with a MIGRATE CHAIN ... (D6B-39)` | the lift is missing | a GREEN that builds a wrong module; R13 and N33 catch it |
| R2 `test_N12_rename_rejects` [row_rename_enum] | 1 | expected `migrate Order v1 -> v2: rename via -> channel names the enum field Order.channel; ...`, got `the enum field Order.channel cannot stand ... (D6B-39)` | the rename check is missing | none: exact text |
| R2 [row_rename_constructor] | 1 | expected `rename price -> amount names the constructor field Order.amount`, got the constructor D6B-39 text | as above | none: exact text |
| R13 `test_N33_order_v2_steps_before_the_tail` | 1 | `built()`: `(0, True) != (1, False)`, D6B-39 | shallow at HEAD; the probe shows the real reason (below) | a GREEN that checks before the steps and also emits a dead `Map.put` first; low |
| N33 `test_N33_order_v2_runtime` | 1 | setup `built()`: `(0, True) != (1, False)`, D6B-39 | shallow at HEAD; the probe shows the decode reason | none for the value cases: exact `==` |
| R4 `test_N34_order_v2_rows_of_both_versions_build` | 1 | `(0, True, ['rows: 2 rows, 2 checked, 0 not decodable']) != (1, False, [D6B-39 text])` | D6B-39 only; the probe passes (plan repair 7) | the D6B-39 order: `--stored` is not changed (PM4-08) |
| R5 `test_N34_v1_row_lost_literal_blocks` | 1 | expected the N19 text for `TYPE Order v1` + `LITERAL_HELP`, got the D6B-39 text | D6B-39 only | none: exact lines |
| R5 control `test_N34_control_kept_v1_value_builds` | 1 | `(0, True, [counted(1, 1, 0)])` vs exit 1, D6B-39 | D6B-39 only | none |
| R6 `test_N34_v1_row_constructor_blocks` | 1 | expected `TYPE Order: 1 stored ROW of table records fails the constructor of Amount ...`, got D6B-39 | D6B-39 only | help line by prefix only |
| R6b `test_N34_v1_record_of_a_chained_output_builds` | 1 | `(0, True, True, []) != (1, False, False, [D6B-39 line])` | D6B-39 only | P2 count lines not pinned exactly |
| R3 `test_enum_output_field_rename_in_a_chain` | 1 | expected `migrate Payment v1 -> v2: rename status -> state names the enum field Payment.state; ...`, got `the enum field Payment.state cannot stand ... (D6B-39)` | the rename check is missing | none: exact text |
| R3b `test_enum_output_field_with_a_version_mark_builds` | 1 | `(0, True) != (1, False)`, D6B-39 | the lift is missing | none |
| R8 `test_chained_enum_output_reads_a_v1_body` | 1 | `run_runtime` setup: `(0, True) != (1, False)`, D6B-39 | shallow at HEAD; the probe shows `:error` | none: exact `==` on the decode return |

## Depth probe (PM4-13): only the two D6B-39 branches deleted

Results with the probe binary (11 failures, 7 tests pass):
- R1, R3b, R4, R5, R5 control, R6, R6b: **pass**. The lift alone builds them; `--stored` needs no change (PM4-08 holds).
- R2 both subtests and R3: exit 0 with the module and a DEAD LINE warning, not the rename text. So the rename check is needed.
- R13: `(True, True, True) != (True, False, False)`: the `Map.put(value, "note", "")` line is there, but the decode body
  calls neither `__beaml_literal_Channel` nor `__beaml_from_Amount` (the DL-101 tail is not in the versioned decode).
- R8: `got R8: :error` (the per-version check wants an enum tuple for `"ok"`).
- N33 (the module builds; `elixirc --warnings-as-errors` exits 0 with warnings):

```
got N33_v1_row_lists_migrated: {:error, %Orders.StoreError{reason: "decode"}}
got N33_v1_row_loads_migrated: {:error, %Orders.StoreError{reason: "decode"}}
got N33_list_holds_both_versions: {:error, %Orders.StoreError{reason: "decode"}}
got N33_v1_unknown_channel: {:error, %Orders.StoreError{reason: "decode"}}
got N33_v1_constructor_reject: {:error, %Orders.StoreError{reason: "decode"}}
got N33_replay_list: {{:error, %Orders.StoreError{reason: "decode"}}, {:error, %Orders.StoreError{reason: "decode"}}, []}
N33_v1_row_stays_v1 PASS, N33_save_writes_v2 PASS, N33_v1_row_without_amount PASS, N33_v1_amount_no_signature PASS
```

**[Inference]** The four passing N33 cases are guards: the write path and the lazy read already work, and the two
`decode` rejects already hold. They stay so a GREEN cannot pass by a looser tail. N33_v1_constructor_reject gives
`decode`, not `constructor`, so it proves the tail runs after the steps.

## 0005 at HEAD (debug), `results/20261108T071807583197Z`

Steps: cargo-build, truncate, stored-orders, gen-orders, compile, test, test-n8 pass; **test-n7_seed fail (2)**;
stored-order_v2 pass; **gen-order_v2 fail (1)** with the D6B-39 constructor text; compile-order_v2 pass (old module);
**test-n7_read fail (2)**; final truncate and gen-orders pass. Status `fail`. Use cases: 15 pass, 6 fail, 1 blocked (N9).

| Test | Failing assertion | Why right | False pass risk |
|---|---|---|---|
| R9 N7 order_v2 builds ... | `left: {1, [D6B-39 constructor text, help]}`, `right: {0, ["rows: 2 rows, 2 checked, 0 not decodable"]}` | the lift is missing | none |
| R10 N7 the v1 Order row ... | `the host runs no Order v2 module` (`order_v2!()`) | gen-order_v2 failed, the v1 module stayed | the guard checks the encoder only; the page and record asserts follow |
| Note N7 (control) | `the host runs no Note v2 module` | same cause (one module) | none |
| Note N7b (control) | `the host runs no Note v2 module` | same cause | none |
| R11 N7b a place submit ... | `the host runs no Order v2 module` | same cause | none |
| N11 | `left: [1]`, `right: [1, 2]` (Note versions) | no v2 write ran | none |
| R12 acceptance | 6 `fail: ExUnit.AssertionError` problems; `stored-order_v2` holds 2 rows | the use case fails | none |

Definition order observed: R10, Note N7, Note N7b, R11, N11 (plan repair 1).

## 0005 with the probe binary, `results/20261108T071859360642Z`

- test-n7_seed **pass** (R9: the lift alone builds `counted(2, 2, 0)`), gen-order_v2 pass.
- compile-order_v2 **fail (1)**: `warning: the following clause will never match: {:error, reason}` and
  `Compilation failed due to warnings while using the --warnings-as-errors option` (plan repair 8).
- test-n7_read fail (2): R10 `assert has_element?(view, "[data-order]", "order-1")` is false (the list decode fails);
  R11 at line 159, `through_beaml!` of the list: `[{3, "accepted"}, {3, "rejected"}]`. The submit and the v2 row passed.
  Note N7, Note N7b and N11 pass. Acceptance: N7 and N7b fail.

## Other observations

- `redteam_c3_test` C4 (in the 0004 full run) fails while `slice6_m4_test.py` is not in `run.py`:
  `['experiments/0004-generated-replay/tests/slice6_m4_test.py'] : files that no full-run step runs`. DL-147 names this;
  the GREEN commit lists the file and C4 passes again. Until then the 0004 full run is `fail` on C4 only.
- `slice6_db_test.py -k N12` passes after the fixture changes (3 tests).
- No compiler event was checked by hand; every compile in both harnesses asserts no path, no source text, no stored value.
