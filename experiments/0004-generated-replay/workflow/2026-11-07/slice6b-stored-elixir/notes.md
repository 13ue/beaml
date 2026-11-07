# Notes: slice 6b step 13 Solve / RED

**[Proposal]** Solve / RED phase, 2026-11-07. By: Opus (RED, slice6b-stored-elixir) for every entry, unless an entry says otherwise.
Inputs: [plan.md](plan.md) (with "Plan repair"), [decisions.md](decisions.md), [plan-review.md](plan-review.md). The ledger holds no `proposal-ultra.md` or `proposal-lite.md`; the task gave this phase the plan cases directly.
Evidence: [red-output.log](red-output.log). Contract and tests: [spec.md](spec.md).

## RED result

- **[Observed]** 15 tests: 9 FAIL, 6 ok. Scratch compiler from `git archive` of HEAD 5110e92f (the 0001 tree is unchanged up to a550fee7).
- **[Observed]** FAIL E1, E2, E4, E8, E9a, L1, L1b: exit 0 and Elixir on stdout where exit 1 and the exact text are expected.
- **[Observed]** FAIL E3 event and E5: no `stored-elixir` event in `.beaml/actions.jsonl`.
- **[Observed]** ok (guards): E3 build, E6, E7, E9b, L2, L3. No setup error, no import error.
- **[Observed]** Generated code today: `new_Amount_1` (signature with `!`) returns `{:ok, struct}` or `{:error, struct}`; `new_Amount_2` (no `!`) returns the bare struct. D6B-104 calls only signatures with a failure TYPE, so the D6B-122 driver match holds for the calls it makes.

## Decisions

Undo:
→ E3 split in two tests: build guard, event RED. Reason: the plan marks only the event part RED. By: Opus (RED, slice6b-stored-elixir)
→ E4 also asserts the event `result: "error"`, `ms: 0` (contract 7). By: Opus (RED, slice6b-stored-elixir)
→ E6 also asserts no `stored-elixir` event (Elixir did not start, D6B-105). By: Opus (RED, slice6b-stored-elixir)
→ Own `compile` with an `env` argument: a copy of `sf.Slice6Failure.compile` with the same event checks, plus a 90 s subprocess timeout so a broken GREEN fails, not hangs. By: Opus (RED, slice6b-stored-elixir)
→ Fixture bodies the plan leaves open: `nested.beaml` signature 2 body `Amount { value: "0", currency: c }`; `rec.beaml` and `order.beaml` keep the one-parameter `Amount` signature for the last pipe step; `order.beaml` signature 1 body `Amount { value: value, currency: currency }`. By: Opus (RED, slice6b-stored-elixir)
→ Record ids: `trace_id` and `client_span_id` 0x1301 to 0x1305, one per record. By: Opus (RED, slice6b-stored-elixir)
→ E8 builds the compiler before the clock starts; `pgrep -f beaml-stored-check` 1 s after exit must find nothing. By: Opus (RED, slice6b-stored-elixir)
→ `red-output.log` is an excerpt: result lines and assertion heads; the printed Elixir bodies are cut. By: Opus (RED, slice6b-stored-elixir)

Repair: none.

## Deferred edits (for GREEN; this phase does not edit existing tests)

1. `experiments/0004-generated-replay/tests/slice6_decode_test.py`, `test_written_record_reports_the_count` (D6B-111). Its runtime build uses the source without `Pending` with `slice6/decode/stored.jsonl`; line 2 `"pending"` blocks under DL-122 (the same build as L1). Change line 201 from

   ```python
   self.run_runtime({"record_written": "true"}, ORDERS.read_text().replace('Pending = "pending"  ', ""), WRITE)
   ```

   to

   ```python
   self.run_runtime({"record_written": "true"}, ORDERS.read_text().replace('Pending = "pending"  ', ""), WRITE,
                    sf.EMPTY_STORED)
   ```

   The assertion stays. **[Inference]** grep of `slice6_*_test.py` finds no other test that removes or changes an ENUM LITERAL against stored records.

## Left for GREEN

- **U1** (D6B-121): Rust unit test of `parse_elixir_results(status, stdout, expected)` in `experiments/0001-syntax-to-beam/src/main.rs` `#[cfg(test)]`. Cases: good lines give the verdicts; one line short; one line extra; a line `okay`; `error` without F; `error Other` with F not in the failure list; exit code 1; signal exit (`ExitStatusExt::from_raw(9)`). Each bad case gives the run error with the right `<why>` (`result lines`, `exit 1`, `signal 9`). GREEN writes it RED first, then the function.
- Run `slice6_decode_ctor_test.py` `test_stored_record_fails_the_record_constructor` and `test_stored_records_pass_the_constructors`: same text, now produced by the Elixir pass.
- Record the `stored-elixir` `ms` of E3 and of the decode-ctor runs (plan "Checks").

## Limits

- **[Inference]** E8 checks the process-group kill on this host only (plan limit, `[Unknown]` on other hosts).
- **[Inference]** E7 checks `EUR` and the `trace_id` only, not every record value; the other values (`12.50`, `""`, `1`) are too short or too common to search for.
- **[Observed]** `run.py` was not run (task rule).
