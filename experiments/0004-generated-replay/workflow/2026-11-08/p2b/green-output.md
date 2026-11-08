# GREEN output: P2b (DL-164, a wrong digest blocks the build)

**[Verified]** GREEN run, 2026-11-08, HEAD `bfefecbb` (RED `53aed354`). By: Opus (GREEN P2b). No commit.
Inputs: [plan.md](plan.md) with Repairs, [red-plan.md](red-plan.md), [red-output.md](red-output.md),
[red-review.md](red-review.md), main-agent rulings (By: Fable). Toolchain: rustc 1.94.0, Python 3.13.12,
Elixir 1.18.1 on Erlang/OTP 27.

## RED repair before GREEN (main-agent rulings on the RED review)

New tests, run at HEAD with a `git archive HEAD` scratch build (`BEAML_SPIKE=<scratch>/…/target/debug/beaml-spike`):

| Test | File | At HEAD | After GREEN |
|---|---|---|---|
| `test_P2b_R7_two_wrong_digest_rows_group` (objection 1: rows at lines 2 and 3, `2 stored ROWS … have`, line 2) | `slice6_db_stored_test.py` | FAIL: exit 0, no error | pass |
| `test_P2b_R8_rejected_db_record_wrong_digest_blocks` (objection 2: rejected `orders.list` record) | `slice6_db_stored_test.py` | FAIL: exit 0, `digest not verified (P2b)` | pass |
| `test_P2b_R9_rejected_200_record_wrong_digest_blocks` (objection 2: rejected http record, status 200) | `record_v3_test.py` | FAIL: exit 0, Elixir on stdout | pass |
| `test_P2b_R10_rejected_entry_records_wrong_digest_block` (objection 2 rule on the ENTRY stream, lines 4 and 5) | `slice6_entry_test.py` | FAIL: exit 0, Elixir on stdout | pass |
| `test_P2b_G1_rejected_response_record_is_not_verified` (503: `:status_mismatch` before `body/1`) | `record_v3_test.py` | pass (guard) | pass |
| `test_P2b_G1_retired_entry_records_are_not_verified` (was the retired half of the old entry G1) | `slice6_entry_test.py` | pass (guard) | pass |

Rule applied (objection 2, "same as R6"): a stored item is digest-checked at build time when the generated replay
reaches `body/1` for it. [Verified] in the emitter (`main.rs`): db replay step `body(record)` before the outcome;
http step `expect(status, 200)` before `body(record)`; `Replay.entry/2` `body(record)` before the decode;
`row_<type>/1` `body(core)` without the outcome. A RETIRE LINE operation reaches no `body/1`.

## Build (`experiments/0001-syntax-to-beam/src/main.rs`)

→ `canonical` writes `\u{:04X}` (Erlang `:json` form). `json_string` (another use) unchanged.
→ New `digest_errors` formatter: one block per (TYPE, place), first line, plural, the help text as `st.digest_error`.
→ `check_stored`: db records, and http records with status 200, whatever the outcome; TYPE = `effect.output`.
→ `check_entries`: every record of an ENTRY LINE operation, whatever the outcome; TYPE = entry input.
→ `check_rows`: every row of a read TYPE, whatever the outcome, before `stored_version` (PDB-15: name, digest, version).
→ Each stream returns the digest error first and alone (before orphan, path, value and held checks).
→ The line `digest not verified (P2b)` is removed.

## 0005 use case N15 (DL-158)

→ `app/test/prototype/stored_test.exs` phase n8, `@tag use_case: "N15"`: `jsonb_set` changes `value.amount.value` to
  `"99.00"`; `live_build` → exit 1, no stdout, first non-count line is the digest error; `99.00`, the order id, trace id
  and span id are absent; `assert_no_ddl!()`; control: `DELETE` the row, build again → exit 0, `counted(0, 0, 0)`.
→ `run.py` `EXPECTED` gets the N15 pair.

## Checks

| Check | Command | Result |
|---|---|---|
| debug build | `cargo build --offline` | ok |
| release build | `cargo build --release --offline` | ok |
| unit tests | `cargo test --offline` | ok (22 + 14 passed) |
| clippy | `cargo clippy --offline --all-targets -- -D warnings` | ok |
| fmt | `cargo fmt --check` | ok (after one `cargo fmt` of the new key tuple) |
| P2b files | `python3 -B tests/<file>.py` | db_stored Ran 56 OK (3 skip); record_v3 Ran 29 OK (1 skip); entry Ran 23 OK; stored_types Ran 33 OK |
| 0004 full | `python3 experiments/0004-generated-replay/run.py` | pass, 40 steps: `results/20261108T130322009076Z` |
| 0005 db | `python3 -B run.py db-up` | pass: `0005…/results/20261108T130355743008Z` |
| 0005 run | `python3 -B run.py run` | pass, 19 steps, N15 pass; n8 30 tests 0 failures: `0005…/results/20261108T132048167719Z` |
| 0005 run, HEAD compiler (N15 genuine) | `BEAML_SPIKE=<HEAD scratch> python3 -B run.py run` | fail as expected: n8 1 failure = N15 (exit 0, Elixir on stdout): `0005…/results/20261108T132136459464Z` (kept) |

Pins: digest pins (EFFECT_OUTPUTS, BYTE_GUARD, `byte-guard.json`) and hash pins (PIN, entry/multi BASE, P4_BASE) are
untouched and their steps pass in the 0004 run (slice5-syntax, slice6-pipe, slice6-host-struct, slice6-effect-reach,
slice6-entry, slice6-multi, slice6-db). V18b passes (record-v3 step). **No pin moved.**
Plan risk R1 (hidden stale digests in test records): none found; the full 0004 run needed no recomputed digest.
`red-output.md` `Ran` column corrected to 54 / 28 / 22 / 33.

## Decisions

**Undo**
→ R7 to R10 as new tests beside the stream harness, not new files. By: Opus (GREEN P2b)
→ The old entry G1 split: rejected half became R10, retired half stays a guard. By: Opus (GREEN P2b)
→ A HEAD-compiler 0005 run kept as N15 RED evidence. By: Opus (GREEN P2b)

**Repair**
→ Objection 2 rule applied to ENTRY RECORDS too (rejected ones block), over response records only, because
  `Replay.entry/2` reads `body(record)` before the decode, whatever the outcome. By: Opus (GREEN P2b); part of the
  OWNER card P2B-SCOPE.
→ http records: digest-checked only with status 200, over every http record, because a non-200 record stops at
  `:status_mismatch` before `body/1`. By: Opus (GREEN P2b)
→ A bad-digest row skips all later row checks (`continue`), over checking it on, because the digest error stands
  alone (PDB-15). By: Opus (GREEN P2b)

**Migrate (OWNER chooses; defaults built)**
→ P2B-SCOPE: verify only accepted items, or every item that reaches `body/1` (built). Includes rejected db, rejected
  http 200 and rejected ENTRY RECORDS.
