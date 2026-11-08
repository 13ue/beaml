# TEST and review: RED TEAM 01 repairs C1/B3 and C3/C4

**Verdict: PASS.** By: Opus (TEST slice6d/red-team), 2026-11-07, HEAD 35c7e3bf. No commit.

## Checks (observed)

| Check | Result | Evidence |
|---|---|---|
| `python3 run.py` (0004), 34 steps incl. 16 `slice6-*`, `redteam-c1`, `redteam-b3`, `redteam-c3`, `drift-test` | pass, 34 of 34 | `results/20261107T220212948306Z/result.json` |
| Wall time of the full run (C4 asked) | **1058 s (17 min 38 s)**; `drift-test` 7 tests in 107.6 s, one more DRIFT run | same run, `drift-test.stderr` |
| `drift` step | pass; R, N `correct_accept / false_reject / typed_reject`, Q `correct_accept / typed_reject / typed_reject`, `repaired_all` true | `results/20261107T220254343850Z/drift.json` |
| 0001 `run.py`, `cargo fmt --check`, `clippy -D warnings`, `cargo test` | pass, clean, clean, 21 + 14 | `experiments/0001-syntax-to-beam/results/20261107T222001827189Z/` |
| `scripts/lint_wiki.py` | 0 errors | scratch log |

The GREEN worker's first `drift_test.py` crash (no `drift.json`) did not recur in this run. **[Unknown]** Its cause.

## Probes

- **C3 [Observed].** Scratch copy of the retained `results/20261107T215918107971Z/drift.json`, `run.drift_status` called directly: original `pass`. `untyped_crash` in each of `build`, `new_live`, `pre_change` for each of R, N, Q (9 cases): `fail`. `repaired_all` false or `1`, Q row missing, `gen` null, freeze `fail`: `fail`. `run.py drift` exits 1 on `fail` (main block). Pass.
- **C1 [Observed].** The DRIVER adds one clause `{:ok, {^type, variant, payload}} when is_binary(variant) and is_list(payload)`; no `rescue`. C1g (3 shapes) and C1h (7 wrong shapes) pass in the full run.
- **B3 [Observed].** One `format!` plus one `write_all` on an `O_APPEND` file; `redteam-b3` passes in the full run. Ceiling named in a `ponytail:` comment.
- **C4 [Observed].** `SLICE_TESTS` lists all 16 `tests/slice6_*_test.py` files (glob count 16) and the three red-team files; `drift-test` runs last.

## Objections

None critical or high.

- **N1 · medium.** The full run starts two DRIFT runs (`drift` and `drift_test.py` setUpClass); about 108 s of the 1058 s is the second one. Accepted cost under D6B-190. No action.

## Decisions

**Repair**
→ PASS statt BLOCK, weil every C3 crash class fails and the full run passes with slice 6 included. By: Opus (TEST slice6d/red-team)

**Undo**
→ N1 noted, not blocking. By: Opus (TEST slice6d/red-team)
