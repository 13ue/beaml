# GREEN output: RED TEAM 01 repairs C3 and C4 (DRIFT status, full-run steps)

**[Observed]** GREEN phase, 2026-11-07, base HEAD f16a0f1d. By: Opus (GREEN red-team-01-repairs C3/C4) on every entry.
OWNER decision: [DL-135](../../../../../wiki/planning/decision-log.md) (M7 option A). Contract: [spec.md](spec.md) D6B-189, D6B-190.

## What changed

- `run.py`: `DRIFT_PIN` and `drift_status(summary)` (D6B-189). `drift()` sets `summary["status"] = drift_status(summary)`. `run.py drift` exits 1 on `fail` (existing exit rule).
- `run.py`: `SLICE_TESTS` gains the 16 `slice6_*_test.py` files and `redteam_c1`, `redteam_b3`, `redteam_c3`. A new step `drift-test` runs `tests/drift_test.py` last (D6B-190).
- `tests/drift_test.py`: header line "recorded, not asserted" replaced by the DL-135 rule. `PIN` literal. New tests `test_f_drift_classes_equal_the_pin` (rows equal `PIN`, status `pass`) and `test_f_drift_pin_matches_run_py` (`PIN == run.DRIFT_PIN`).
- `tests/redteam_c3_test.py`: no change.

## Pin and evidence

| Derivative | build | new_live | pre_change |
|---|---|---|---|
| R | correct_accept | false_reject | typed_reject |
| N | correct_accept | false_reject | typed_reject |
| Q | correct_accept | typed_reject | typed_reject |

- **[Observed]** `drift_status` over every retained `results/*/drift.json` before the GREEN runs: 63 files, 60 `pass`, 3 `fail`. The 3: crash run `20261107T171545190446Z` (`untyped_crash`), `20261106T123350493778Z` and `20261107T125625718615Z` (`repaired_all` false). The RED review counted 58 of 61; two later runs (in `results/`, untracked) also match the pin.
- **[Observed]** New DRIFT run `20261107T205918092312Z` (`run.py drift` direct): exit 0, status `pass`, rows equal the pin, `repaired_all` true.

## Test results

- **[Observed]** `python3 -B -m unittest tests/drift_test.py tests/redteam_c3_test.py`, second run: 12 tests OK, 108.6 s (drift_test 7, C3/C4 5).
- **[Observed]** First run of the same command: 4 drift_test failures. `run.py drift` in setUpClass exited 1 with no stdout line; run dir `20261107T205750509480Z` stops in `N/gen/new_live` with no `drift.json`. Retained. **[Unknown]** Cause; stderr was not kept by `drift_test.py`. Other workers ran builds at that time. The C3 tests passed in that run.
- **[Observed]** RED to GREEN: `redteam_c3_test.py` 10 failures before, 0 after.
- Full `run.py` run: not run (another worker edits `main.rs`). Owed to the TEST phase, with the wall time (D6B-190 **[Unknown]**). **[Inference]** About +3 min (RED review O3): 16 slice 6 files, 3 red-team files and one more DRIFT run (about 1 to 2 min here).

## Effects to note

- `slice6_entry_test.py` is an open RED of another worker (untracked). The C4 glob requires it, so it is listed. The full run fails until its GREEN (spec.md O3 note).
- `redteam_c1_test.py` and `redteam_b3_test.py` fail the full run until the C1 and B3 GREEN in `main.rs` lands.

## Decisions

Undo:
→ `drift_test.py` step named `drift-test`, not `drift`: the `drift` name owns `drift.stdout` and the `result.json` summary. By: Opus (GREEN red-team-01-repairs C3/C4)
→ Pin literal in both `run.py` and `drift_test.py`, tied by `test_f_drift_pin_matches_run_py`; two sites move together, as the byte pins. By: Opus (GREEN red-team-01-repairs C3/C4)
→ `slice6_entry` listed although its RED is open: the C4 glob needs every slice 6 file. By: Opus (GREEN red-team-01-repairs C3/C4)
→ Explicit file list, not a glob (D6B-190 "Over"). By: Opus (GREEN red-team-01-repairs C3/C4)

Repair:
→ The crashed first DRIFT run is kept and reported statt rerun silently, weil a crash is the class C3 guards against. By: Opus (GREEN red-team-01-repairs C3/C4)
