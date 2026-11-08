# TEST and review: RECORD FORMAT v3 (EXPERIMENT 0005 prerequisite P2)

**[Observed]** TEST plus normal review, 2026-11-08, HEAD b3e75b6e (GREEN ca09d361, pin commit b1879fa8). Fresh-context reviewer, no worker context reused. No code changed, no commit.
By: Opus (TEST v3/multi).

## Verdict: PASS

No critical or high objection. No medium objection kept for this result (the full-run status note is in the [multi-effect review](../multi-effect-module/review.md), because that GREEN added the files to `run.py`).

## Checks (shared with the multi-effect review)

| Check | Result |
|---|---|
| `python3 -B experiments/0004-generated-replay/run.py` | status `fail`; 38 steps; 36 pass; only `slice6-db` (16 tests, 40 failures, 1 skipped) and `slice6-db-stored` (40 tests, 43 failures, 3 skipped) fail, equal to the P4a and P4b RED counts; `record-v3` 26 tests OK (1 skipped: V18); run time 976.6 s real; result dir `results/20261107T230714580577Z` (DRIFT dir `results/20261107T230745518303Z`) kept |
| 0001 `run.py` | pass, `results/20261107T232343288668Z` |
| `cargo fmt --check` | pass |
| `cargo clippy --offline --all-targets -- -D warnings` | pass |
| `cargo test --offline` | 22 unit + 14 cli pass |
| `python3 scripts/lint_wiki.py` | 0 errors (85 files) |
| tree-sitter parse (`integrations/zed-beaml`) | `slice6/multi/` 7 files, `slice6/entry/two_entries.beaml` and a scratch source: no ERROR. `slice6/record-v3/` has no `.beaml`. `slice6/db/`: 10 of 23 ERROR at the `[Order]` list TYPE (open P4 RED, not this step) |

## Probes (own scratch sources, compiler at HEAD)

Over copies of tracked fixtures with changed `outcome`, `reason`, `status` keys. Every stderr was scanned for the string leaves of `value` and `request`; the only hits were one-digit numbers that also stand in fixed text (`DL-102`, line numbers). No stored String in any text (DL-124).

| Probe | Result |
|---|---|
| constructor-fail file, accepted (control) | exit 1, the DL-102 block |
| same file, 200 rejected at capture (`constructor`) | exit 0, `3 records, 0 checked, 3 rejected at capture`, `digest not verified (P2b)` |
| same file, 503 `status` | exit 0, same two lines |
| good file + one rejected record | exit 0, `5 records, 4 checked, 1 rejected at capture` + P2b line |
| clean accepted file | exit 0, no count line (QV3-7 A) |
| held record (`stored-held-rejected`, as is / accepted twin / 503) | exit 1, the D6B-72 text in all three |
| held field in `value` (`output_redacted`), rejected `decode` and 503 | exit 1, the D6B-72 text; a block prints no count line |
| missing `outcome`; unknown word | exit 1, empty stdout, `error: stored RESPONSE RECORD has no capture outcome accepted or rejected (DL-138)` + `record source: F:1 (line 1)` |
| v2 file | exit 1, `error: stored RESPONSE RECORD has record version 2; this build reads record version 3 only (DL-143)` + `record source: F:1 (line 1)` |
| rejected 503 record of an undeclared operation | exit 1, the DL-040 orphan block (RED review O1 holds) |
| `convert_v3.py --base 545dded0 --out <scratch>` | 15 files, all byte-identical to the tracked files |

## Rule check

- DL-136, QV3-8 B: a rejected record skips the value, literal and TYPE path checks; orphan and held checks still read it. **[Observed]**
- DL-138, DL-141: `outcome` and `reason` read on every RESPONSE RECORD; a missing or unknown value blocks (RED review O2 holds). **[Observed]**
- DL-142, DL-143: 16-key RESPONSE and 14-key ENTRY sets pinned by V2, V11, V17 (run green). **[Observed]**
- DL-124: no stored value in any probe text. **[Observed]**
- Pin sites: `PIN` = ca09d361; `EFFECT_OUTPUTS`, `BYTE_GUARD`, `byte-guard.json` unchanged since ca09d361; `PIN` unchanged since b1879fa8. **[Observed]**
- V18 retired by `@unittest.skip` with a reason (one-time P2 diff proof, passed at ca09d361; ENTRY LINE sources change by design after ce190054). **[Observed]** Its successor guard: own comparison of the ca09d361 and HEAD compilers over 2092 tracked sources without an ENTRY LINE gives equal stdout, stderr and exit (see multi review).

## Dropped (low)

- `1 records` (no singular, RV3-16).
- A rejected record of an old TYPE VERSION that holds a field the newest TYPE dropped builds green (probe over `stored-unredacted`); this is the recorded QV3-8 B challenge, already on the OWNER list.
- An edited `outcome` is not in `value_sha256` (recorded QV3-6 challenge).

## Decisions

**Repair**
→ PASS statt BLOCK, weil no probe shows a wrong outcome against DL-136, DL-138, DL-141 to DL-143. → By: Opus (TEST v3/multi) · Repair
→ Run-status note filed under multi statt here, weil the multi GREEN added the RED files to `run.py`. → By: Opus (TEST v3/multi) · Repair

**Undo**
→ QV3-8 B and QV3-6 challenges dropped as known, not new evidence. → By: Opus (TEST v3/multi) · Undo
→ Raw probe outputs kept in scratch only. → By: Opus (TEST v3/multi) · Undo
