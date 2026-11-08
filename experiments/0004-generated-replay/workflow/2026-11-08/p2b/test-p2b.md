# TEST + review: P2b (DL-164, a wrong digest blocks the build)

**[Verified]** TEST run, 2026-11-08, HEAD = GREEN `372b2ee1`. By: Opus (TEST P2b). No commit.
Inputs: [plan.md](plan.md) with Repairs, [red-review.md](red-review.md), [green-output.md](green-output.md),
main-agent rulings (By: Fable). Toolchain: rustc 1.94.0, Python 3.13.12, Elixir 1.18.1 on Erlang/OTP 27.
Job bus: job `p2b-test`, title "Test step P2b (wrong digest blocks the build)".

## 1. Untracked dir `results/20261108T131849495580Z`

→ Origin: sub-run of the GREEN full run `results/20261108T130322009076Z`. **[Verified]**
⠀⠀↳ Step `drift-test` (last of 40) runs `tests/drift_test.py`.
⠀⠀↳ That test starts `run.py drift` once (`setUpClass`).
→ Evidence: start 13:18:49 UTC, inside the parent run (13:03:22 to 13:20:33); test took 104 s.
→ Contents match a `run.py drift` dir: `drift.json` (status pass), `R/ N/ Q/ gen/`.
→ Not a stray run, not another session. Kept. Its siblings `13032464…` to `13141849…` are the other step sub-runs.
  This TEST run made the same kind: `132359…` to `133920…` (0004), all untracked, all kept.

## 2. Runs

| Run | Command | Result dir | Result |
|---|---|---|---|
| 0004 full | `python3 -B experiments/0004-generated-replay/run.py` | `0004-generated-replay/results/20261108T132357983680Z` | pass, 40/40 steps |
| 0005 db | `cd experiments/0005-prototype-fullstack && python3 -B run.py db-up` | `0005-prototype-fullstack/results/20261108T134104326498Z` | pass |
| 0005 run | `python3 -B run.py run` | `0005-prototype-fullstack/results/20261108T134104848998Z` | pass, 19/19 steps; n8 30 tests, 0 failures; N15 pass |
| probe | `python3 -B experiments/0004-generated-replay/workflow/2026-11-08/p2b/test-probe/probe_control_chars_test.py` | (stdout only) | Ran 58 OK (3 skip): 56 inherited + 2 probes |

P2b files inside the 0004 run: db_stored Ran 56 OK (3 skip), record_v3 Ran 29 OK (1 skip: V18, old one-time
skip), entry Ran 23 OK, stored_types Ran 33 OK, drift_test Ran 7 OK.
0005 compiler: `0001…/target/debug/beaml-spike`, sha256 `823bfbd1…`.

## 3. Review of `git show 372b2ee1` against the plan and the rulings

→ **Digest error first and alone.** Holds. **[Verified]** in `main.rs`.
⠀⠀↳ All three streams return `digest_errors` before orphan, path, value and held errors.
⠀⠀↳ Inside the loops only shape errors come first (not JSON, record version, outcome, `stored_version`).
⠀⠀↳ Rows: digest before `stored_version` and value checks (PDB-15); a bad row `continue`s.
→ **Canonical hex upper case = Erlang `:json`.** Holds. **[Verified]**
⠀⠀↳ `:json.encode` of every char 0x00..0x7F: escapes only 0x00..0x1F, `"` and `\`; `\b \t \n \f \r` short; rest `\u00XX` upper.
⠀⠀↳ Not escaped: 0x7F, U+00E9, U+2028, U+2029, U+FEFF, U+1F600, `/`. Same as Rust `canonical`.
⠀⠀↳ Probe `test_probe`: 5 rows with these chars; digest from the generated `digest/3` code in elixir (`digest.exs`); build exit 0, `counted(5, 5, 0)`.
⠀⠀↳ Probe `test_probe_lower_hex_blocks`: Python lower-case `\u001a` digest gives the digest error.
→ **Every item that reaches `body/1` is checked; nothing else blocks.** Holds. **[Verified]** against the emitter.
⠀⠀↳ db step: `body(record)` after the request check, before the outcome: all db records checked.
⠀⠀↳ http step: `expect(status, 200)` before `body(record)`: only status 200 checked (R9, G1 503).
⠀⠀↳ `Replay.entry/2`: `body(record)` whatever outcome (R10); RETIRE LINE ops have no clause (G1 retired).
⠀⠀↳ `row_<type>/1`: `body(core)` whatever outcome (R6); no-reader TYPE not checked (G1).
→ **Plural grouping.** Holds: one block per (TYPE, place), count, first line (R7, R10 count 2).
→ **N15 no false pass.** Holds.
⠀⠀↳ HEAD~ compiler run `0005…/results/20261108T132136459464Z`: N15 fails, exit 0, Elixir on stdout.
⠀⠀↳ GREEN compiler: pass, plus control (row deleted, exit 0, `counted(0, 0, 0)`).
→ **Pins.** No pin constant or `byte-guard.json` in the diff; pin steps pass; V18b passes in record-v3.
→ **Good data that now blocks.** None found: full 0004 and 0005 runs pass with no recomputed digest.

## 4. Objections (max three; none blocks)

1. **Medium.** Build accepts a non-list `unknown_keys` whose digest holds; run-time `body/1` needs `is_list(keys)`.
   Wrong outcome: build passes, replay gives `:body_digest_mismatch`. Needs a crafted record (hand edit plus a new
   digest). Smallest test: a row with `unknown_keys: null` and a matching digest must block. Not in P2b scope.
2. **Medium (docs).** `experiments/0004-generated-replay/README.md` line 2105 still lists the note
   `digest not verified (P2b)`. GREEN removed it. Fix in the docs phase.
3. **Low, noted only.** The 0005 use-case formatter logs N15 start and finish 42 ms apart. The times are formatter
   times, not test times (N8c: 22 ms). The HEAD~ failure shows N15 really builds. No action.

## Verdict

**PASS.** GREEN meets the plan, the Repairs and the RED-review rulings. No critical or high objection.

## Decisions

**Undo**
→ Probe kept in the ledger (`test-probe/`), not as a new test in `tests/`. By: Opus (TEST P2b)
→ All new result dirs kept untracked, as found. By: Opus (TEST P2b)
→ Objection 1 noted, not blocking: crafted input only, run time still stops. By: Opus (TEST P2b)
