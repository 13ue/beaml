# RED plan: P2b (DL-164, a wrong digest blocks the build)

**[Proposal]** RED phase, 2026-11-08, HEAD `0b460f9d` (P2b plan `10d55103`, plan check `65827456`). By: Opus (RED P2b).
Tests only, no production change, no commit. Inputs: [plan.md](plan.md) with "Repairs", [plan-review.md](plan-review.md).
Results: [red-output.md](red-output.md).

## Shared helpers (`tests/stored_types_test.py`)

→ `value_sha256` writes the Erlang `:json` form: `\u00XX` with upper-case hex (Repairs O1). An odd backslash run
  before `u` is an escape; an even run is a plain `u`. No other text changes (`ensure_ascii=False` writes no other
  `\u`).
→ `digest_error(type, count, noun, place, source, line)`: the three expected lines (plan section 4).

## Tests

| Test | File | Expected after GREEN | HEAD |
|---|---|---|---|
| `test_P2b_R1_wrong_digest_row_blocks` | `slice6_db_stored_test.py` | exit 1, exactly the ROW digest error at line 2 | RED |
| `test_P2b_R2_digest_before_type_version` (replaces N29 digest case) | same | digest error, no `cannot read` | RED |
| `test_P2b_R2b_digest_before_the_value_checks` (O2, rows) | same | STRICTER: digest error, no constructor text | RED |
| `test_P2b_R5_erlang_digest_with_control_characters_builds` (O1) | same | `rows: 1 rows, 1 checked, 0 not decodable` | RED |
| `test_P2b_R6_rejected_row_of_a_read_type_blocks` (O3) | same | digest error for a `rejected` row | RED |
| `test_P2b_G1_no_reader_row_is_not_verified` | same | INVOICE row with a wrong digest counted, exit 0 | guard |
| N21 (bad digest case moved to R1) | same | `counted(2, 1, 1)` | guard |
| N25 control without the marker line | same | count lines only | RED |
| `test_P2b_R3_wrong_digest_response_record_blocks` [valid, constructor, held] | `record_v3_test.py` | exactly the RESPONSE RECORD digest error | RED |
| `test_P2b_G1_rejected_response_record_is_not_verified` | same | 503 rejected record, wrong digest: exit 0, count line | guard |
| `count_lines()` without `DIGEST_LINE` (V14, V14c, V22, V23) | same | count line only | RED |
| `test_P2b_R4_wrong_digest_entry_record_blocks` [valid, value_faults] | `slice6_entry_test.py` | exactly the ENTRY RECORD digest error | RED |
| `test_P2b_G1_rejected_and_retired_entry_records_are_not_verified` | same | exit 0 for both | guard |

Every block test asserts: no stdout, the exact lines (so no path, value, held or orphan text beside it), and no
stored value, `99.00` marker, row id or trace id in the text (DL-124).

## R5 digest source (Repairs O1)

The pinned `ERLANG_DIGEST` comes from the HEAD compiler output, not from Python:

```
beaml-spike slice6/db/orders.beaml --stored slice6/db/stored/responses.jsonl > gen.ex
# cut `defp digest(value, keys, redacted) do ... end` from gen.ex, rename to `def`, wrap in `defmodule D`
elixir run.exs '{"order_id":"order-\u000b-\u001b-p2b","amount":{"value":"12.50","currency":"EUR"},"channel":"web"}'
# run.exs: IO.puts(D.digest(:json.decode(v), [], []))
-> 8dd130c3c0a2788a83e23924065d2d87de1930180e977c1f0d6ddec9cecf151a
```

Old Python helper (lower case): `76869440d5a8…`. Rust `digest_holds` agrees with the old helper, so HEAD skips the row.
Toolchain: see [red-output.md](red-output.md).

## Pin check (Repairs O1)

→ Scan: 396 JSONL lines with `value_sha256` outside `results/`, `deps/`, `_build/`: no control character, no `\u00XX`.
→ `rg` over 0004 tests, 0004 `slice6/`, 0005 `app/test`, 0005 `run.py`: no control-character literal.
→ Only one Python canonical helper exists (`stored_types_test.value_sha256`).
→ Result: **no pin moves.** The digest and hash pins stay (plan section 6).

## Not in this RED

→ 0005 N15: plan section 3 does not list it; DL-158 puts the REFERENCE APP use case in GREEN.
→ Rejected db RESPONSE RECORDS: plan check O3 notes `body(record)` runs on them in the db replay step. Ruling O3
  keeps records at "checked items only"; no test pins that case either way (open, with the OWNER card).

## Decisions

**Undo**
→ G1 split over the three files, beside the harness of each stream. By: Opus (RED P2b)
→ Record G1 compares the first stderr line, so the marker line stays with V14. By: Opus (RED P2b)
→ Block tests compare `stdout == ""`, not the full stdout, for short failure text. By: Opus (RED P2b)

**Repair**
→ Help line per stream noun (`restore or delete the RESPONSE RECORD`) over the ROW text only, because plan section 4
  drafts the ROW form and one shape per stream matches the other `--stored` blocks. By: Opus (RED P2b)
→ Helper fixed in RED over GREEN, because it is test code and R5 must fail on Rust only. By: Opus (RED P2b)
→ R5 digest pinned from the generated `digest/3` over a live `elixir` call per test run, because the pin is
  deterministic and needs no Elixir in the compiler test. By: Opus (RED P2b)
→ N15 left to GREEN over RED here, because the plan RED table omits it (DL-158). By: Opus (RED P2b)
