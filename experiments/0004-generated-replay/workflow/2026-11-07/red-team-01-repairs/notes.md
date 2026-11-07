# Notes: RED TEAM 01 repairs C1, B3, C3 · Solve / RED

**[Proposal]** Solve / RED phase, 2026-11-07, git HEAD acf12d75. By: Opus (RED, red-team-01-repairs) on every entry.
Inputs: the RED TEAM 01 ledger ([report.md](../red-team-01/report.md) and its finding files). The task gave the cases directly; this ledger has no planner or `proposal-ultra.md` / `proposal-lite.md`. Contract: [spec.md](spec.md). Evidence: [red-output.log](red-output.log).

## RED result

- **[Observed]** Compiler: scratch `git archive HEAD experiments/0001-syntax-to-beam`, `cargo build`, used through `BEAML_SPIKE`. The working-tree `main.rs` (a GREEN worker edits it) was not built or read for the verdict.
- **[Observed]** C1: 6 tests, 4 FAIL, 2 ok. C1a, C1b, C1c: exit 1 with "the Elixir run of the generated constructors failed (exit 1)". C1d: that run error instead of the DL-102 block. Guards C1e (failing record alone gives the DL-102 block with `Bad`) and C1f (the enum success is `{"PaymentState", "Authorized", []}`) pass. Reproduces the red-team repro `c2/en.beaml` exactly.
- **[Observed]** B3: 1 test, FAIL. 40 threads x 50 builds of `slice6/host-struct/nonzero.beaml` in one scratch cwd: 2000 lines, 9 to 40 not valid JSON, in 8 of 8 repeats plus the main run. Line count stays 2000 (one event per build).
- **[Observed]** C3/C4: 5 tests (6 subtests in C3c), 10 failures. C3a to C3c: "run.py has no drift_status(summary)". C3d: `drift()` still sets the freeze-only status. C4: 16 files that no full-run step runs (15 `slice6_*_test.py` and `drift_test.py`).
- **[Observed]** No import error, no setup error. Each RED fails on the missing behaviour. C3 reads only the two retained `drift.json` files; no DRIFT run started.

## Challenge of the RED (own check)

- C1b fails at the build assertion, not at the event assertion. Accepted: the event cannot exist before the build passes; after GREEN the event part decides.
- C1f pins a generated function name (`new_PaymentState_1`). It is the name the DRIVER calls, so a rename breaks both together. Accepted.
- B3 is probabilistic. A GREEN that is still wrong could pass one run by chance. Mitigation: 2000 builds gave 9 or more bad lines in every one of 9 runs at HEAD. A GREEN that drops events (a lock that skips on contention) fails the line count.
- C3b checks the good run passes. Without it, `lambda s: "fail"` would pass C3a and C3c.
- C3d is a text check of `drift()`. Accepted as the smallest proof that the rule is wired; the alternative is a full DRIFT run.
- C4 uses a glob, so it also fails when a later slice 6 file is not added.

## Decisions

Undo:
→ C1 source and records inline in the test, not a fixture dir. Record digests from `stored_types_test.value_sha256`, checked equal to the red-team records. By: Opus (RED, red-team-01-repairs)
→ C1 reuses `compile`, `build` and `events` of `Slice6StoredElixir` (same path and source-text checks of the action log). By: Opus (RED, red-team-01-repairs)
→ B3 N raised from 8 to 40 threads x 50 builds. 8 x 10 failed 1 of 3 runs; 40 x 10 failed 2 of 5; 40 x 50 failed 9 of 9, in about 2 s. By: Opus (RED, red-team-01-repairs)
→ B3 prints counts only, never a log line (AGENTS.md: no source text or path in output). By: Opus (RED, red-team-01-repairs)
→ C3 mutation cases beyond the two retained runs: `repaired_all` false, freeze fail, `wrong_accept`, `compile_error` row, `pre_change` crash, missing row. By: Opus (RED, red-team-01-repairs)
→ `red-output.log`: absolute repository and temp paths replaced by relative or `<tmp>` paths. By: Opus (RED, red-team-01-repairs)

Repair:
→ D6B-187 enum tuple as DRIVER `ok` statt skip enum constructors, weil only the success match is wrong. By: Opus (RED, red-team-01-repairs)
→ D6B-188 one `write_all` per line statt `flock`, weil one write of a short line lands whole. By: Opus (RED, red-team-01-repairs)
→ D6B-189 (now Migrate, M7, waits for the OWNER) full row pin plus `repaired_all` statt `new_live` pin only, weil a `pre_change` crash would pass. By: Opus (RED, red-team-01-repairs)
→ D6B-190 (now Migrate, M7, waits for the OWNER) add the slice 6 files and `drift_test.py`, keep the `drift` step, statt replace it, weil `result.json` reads its summary. By: Opus (RED, red-team-01-repairs)

## RED review repair (O1 to O3), 2026-11-07

By: Opus (RED repair, red-team-01-repairs) on every entry, after the RED review BLOCK by Fable.
- **[Observed]** O1: `RedTeamC1Driver` added to `tests/redteam_c1_test.py`. C1g FAIL for `enum_ok` and `enum_payload` (exit 1, no line); `struct_ok` ok. C1h ok for all 7 wrong shapes (each raises today). No wrong shape passes today, so C1h holds only guards.
- **[Observed]** The DRIVER text of working-tree `main.rs` equals HEAD at this time (diff of the const).
- O2: D6B-189 and D6B-190 are Migrate, OWNER question M7. GREEN of C3/C4 waits for the OWNER. They would reverse the slice 1 Undo D12 "recorded, not asserted". Raised by: Fable (RED review).
- O3: spec.md notes that D6B-190 fails the full run while a slice 6 RED is open (6c is GREEN at 51fd79b2).

Undo:
→ C1g/C1h test the DRIVER text directly, not through the COMPILER: no valid BEAML source makes a constructor return a wrong shape. By: Opus (RED repair, red-team-01-repairs)
→ The DRIVER text comes from the `main.rs` beside `BEAML_SPIKE` (scratch tree), else the repo `main.rs`; no new environment variable. By: Opus (RED repair, red-team-01-repairs)
→ Two more wrong shapes than asked: atom variant, bare value without `{:ok, _}`. By: Opus (RED repair, red-team-01-repairs)

## Left for GREEN

- `main.rs`: D6B-187 DRIVER clause, D6B-188 `fn action`. Coordinate with the GREEN worker who edits `main.rs` now.
- `run.py` (only after the OWNER answers M7): `drift_status`, its use in `drift()`, `SLICE_TESTS` (D6B-189, D6B-190).
- `drift_test.py` header "recorded, not asserted" and the README limit line (C4/D10) go stale after D6B-189 and D6B-190. DOCS phase.
- A decision-log entry for each D6B Repair at the end of GREEN (DL-097 rule).
