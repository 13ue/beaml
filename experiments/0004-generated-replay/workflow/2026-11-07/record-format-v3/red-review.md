# RED review: RECORD FORMAT v3 (EXPERIMENT 0005 prerequisite P2)

**[Observed]** RED review, 2026-11-07, git HEAD f1cc8d61 (P2_BASE 31d83754; `experiments/0001-syntax-to-beam/src` is equal in both). Fresh-context reviewer, no worker context reused.
Inputs: [plan.md](plan.md) (with "Plan repair"), [decisions.md](decisions.md), [plan-review.md](plan-review.md) (with re-check), [red-plan.md](red-plan.md), [red-output.md](red-output.md), [convert_v3.py](convert_v3.py), `tests/record_v3_test.py`, `slice6/record-v3/`. OWNER rules: DL-124, DL-136, DL-138, DL-141 to DL-144 in [the decision log](../../../../../wiki/planning/decision-log.md); D036 M8, M9 in [Decisions to be made](../../../../../wiki/planning/decisions-to-be-made.md#d036--red-team-01-questions-m3-m4-m5-m8-m9-parked-by-the-owner).
By: Opus (RED review record-v3).

## Verdict: PASS

No critical or high objection. Two medium notes (O1, O2). Every RED is genuine.

## Evidence (reproduced)

- Compiler: `git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>`, `cargo build --offline`. `main.rs` not edited (the working copy holds +24 lines of another worker; not used).
- `BEAML_SPIKE=<scratch>/.../beaml-spike python3 -B .../tests/record_v3_test.py`: `Ran 24 tests`, `FAILED (failures=139)`, 0 errors, exit 1. Per-test failure counts equal the red-output.md table (V18 56, V17 15, V17b 15, V18b 15, V1-V10 10, ...).
- **[Observed]** Green today: `test_V8_guard_live_status_reason` and 7 runtime guard cases (`V10_guard_*` 5, `V9_guard_*`, `V11_guard_entry_outcome`) = 8 guards. The commit message says "10 guards green"; red-output.md lists the same 8. Count slip only, no missing guard (low, dropped).
- **[Observed]** Failure reasons, by assertion kind: 55 + 1 "these writers must change" (V18), 16 "fixture is not converted to v3" (V18b, V15), the v2 key and version lists (V17), the HEAD version error or exit 0 (V12, V13, V14*, V22-V25, N2*), missing planned marker (V16), runtime `FAIL` (V1-V11). None is setup, a typo or a wrong expectation.
- **[Observed]** Fixtures discriminate. The v2 twin of each new fixture (`to_v2`) built with the HEAD compiler: `stored-mixed` blocks at line 2, `stored-mixed-fail` blocks at line 1, `stored-accepted-nopath` and `stored-503-nopath` give the TYPE path block, `stored-held-rejected` gives the D6B-72 block. So V14, V22, V23 can turn green only through the outcome skip; V14b, V24, V25 stay red if the skip is too wide.
- **[Observed]** N2 and N2b: HEAD over `slice2/N-chain` with `stored/empty.jsonl` prints the W2 `DEAD LINE: migrate Payment v1 -> v2` warning; with the v2 twin of either w2 fixture, exit 0 and no warning. Both expectations are right.
- **[Observed]** All 21 records in `slice6/record-v3/` pass `st.value_sha256`; the v3 ones have 16 (RESPONSE) or 14 (ENTRY) keys; `entry-v2/entries.jsonl` is the only v2 line (V13 input).
- **[Observed]** Converter: `convert_v3.py --base 31d83754 --out <scratch>` exit 0, 15 files, prints file names only. 28 RESPONSE RECORDS, all `status` 200 → `accepted`/`null`, 16 keys; 5 ENTRY RECORDS keep their 6d outcome, 14 keys. Tracked files unchanged.
- **[Observed]** The tracked non-result `*.jsonl` files with `"version":2` are exactly the 15 converter files plus `slice6/record-v3/entry-v2/entries.jsonl`. The inline v2 writers in tests (`arms_test.py` 373, `redteam_c1_test.py` `TEMPLATE`, `slice6_entry_test.py` N8, `stored_types_test.with_value`) are all in the plan table "Existing assertions that change".
- **[Verified]** The five pin sites exist under the names in the test docstring: `slice5_syntax_test.py` `PIN`, `slice6_pipe_test.py` `EFFECT_OUTPUTS` (read by `slice6_struct_order_test.py`), `slice6_host_struct_test.py` `BYTE_GUARD`, `slice6/effect-reach/byte-guard.json`, `slice6_entry_test.py` `BASE` (N13). Move times match RV3-14.

## Checklist

1. **Run.** 24 tests, 139 red subtests, reproduced. 8 guards green (not 10, count slip).
2. **14-key core.** Exact sorted equality, so no extra and no missing key: RESPONSE `HTTP` = `CORE` + `request`, `status` on a no-enum source (V2), a keep-value source (V2b) and the RESPONSE RECORD of the UI flow; ENTRY `CORE` (V11); every converted fixture (V17). Pinned.
3. **QV3-8 B.** Skip every record → V14b, V24 and N2b fail. Key on `status` only → V23 (200, `rejected`) and V14 line 3 fail. Skip the held check → V25 fails. Skip the W2 count wrongly → N2 or N2b fails. Not covered: the orphan count and an unknown `outcome` (O1, O2).
4. **Diff proof V18.** Testable: it builds `compiler_at(P2_BASE)` and HEAD over 100+ tracked sources with `stored/empty.jsonl`, asserts equal exit and stderr, no hunk owner outside `def record(request, status, bytes)` and `def entry_record(bytes, decoded)`, and a hunk in every writer present (56 sources today). A new helper `defp` is flagged (its own owner line). V18b covers the stderr over each converted fixture (re-check N3). **[Inference]** Lines between the end of `record/3` and the next `def` count as `record/3`; low, dropped.
5. **Converter.** Status-only outcome is honest for the tracked files: all are 200, and the block fixtures (for example `decode-ctor/stored-fail.jsonl`) must stay `accepted` to keep their `--stored` result (RV3-12, plan limit). No converted line reaches a test name, a log or a note: subtest names are fixture paths and fixed case names; the converter prints file names only.
6. **DL-124.** Count and version lines carry counts, versions and paths only. V16 scans 5 stderr outputs for `STORED_WORDS` with a marker precondition. **[Observed]** One string value of `stored-held-rejected.jsonl` (in the `value` place, not the held field) is not in `STORED_WORDS`; the expected texts are fixed, so this is a scan gap only (low, dropped).
7. **M8, M9.** No RED default decides them. No failure struct enters as an input value. Count lines are summary lines; V14b, V24, V25 keep the existing block texts (one first line plus a count, valid under M9 A and B). `without_counts` lets GREEN print the count lines beside a block or not; that follows the 6d `blocked()` precedent and adds no per-record line.

## Objections

### O1 · medium · The orphan count over a rejected record has no test

- **Evidence.** Plan repair O2 table: "Orphan count (DL-040): `rejected` record → run". `check_stored` at HEAD counts orphans in the `else` branch of the EFFECT lookup. V25 proves only the held check. A GREEN that puts `if rejected { held; count; continue }` before the EFFECT lookup passes all 24 tests.
- **Consequence.** A rejected record of an operation with no EFFECT and no RETIRE LINE builds green with only a count line. The DL-040 block (a removed EFFECT asks for a RETIRE LINE) is lost for that record. Wrong outcome, silent.
- **Resolving test.** A one-record file, `rejected`/`status` (503), of an operation that the source does not declare: exit 1 with the existing orphan text (`... has no effect in the source`, the HEAD text over the v2 twin as expected value, as in V24).

### O2 · medium · No test for a missing or unknown `outcome` on a RESPONSE RECORD

- **Evidence.** Plan Change 3: an `outcome` other than `accepted` or `rejected` gives `error: stored RESPONSE RECORD has no capture outcome accepted or rejected (DL-138)` plus the record source line. No test pins it. Every fixture carries a valid `outcome`.
- **Consequence.** A GREEN that checks `outcome == "accepted"` and skips every other value passes all tests. Then a v3 record without `outcome` (hand-edited, or from a future writer bug) skips the constructor, literal, path and W2 checks: a false green. The opposite form (`== "rejected"` skips) is safe, so the test fixes the choice.
- **Resolving test.** A v3 record with no `outcome`, and one with an unknown word: exit 1, empty stdout, stderr exactly the Change 3 text with `S:1 (line 1)`.

## Dropped (low)

- Commit message "10 guards green" vs 8 observed (docs count).
- V18 owner attribution of lines between `def`s.
- V16 `STORED_WORDS` gap for one fixture value.
- **[Inference]** After GREEN the W2 DEAD LINE text over `stored-w2-rejected.jsonl` still says that no stored RESPONSE RECORD of TYPE Payment has v1, although a rejected one exists. Text is unchanged by V21; a docs item for QV3-8 B, not a RED fault.

## Limits

- **[Unknown]** V18 and V18b show only that nothing changed today; GREEN alone proves the allowed hunk set.
- The review ran the HEAD compiler; the uncommitted `main.rs` edits of another worker were not built. If they land before GREEN, `P2_BASE` moves (red-plan default).

## Decisions

**Repair**
→ PASS statt BLOCK, weil no objection is critical or high. → By: Opus (RED review record-v3)
→ O1 medium statt high, weil the natural skip place keeps the orphan branch. → By: Opus (RED review record-v3)
→ O2 medium statt high, weil only hand-edited records lack `outcome`. → By: Opus (RED review record-v3)
→ RV3-12 status-only outcome accepted statt objection, weil all tracked records are 200. → By: Opus (RED review record-v3)

**Undo**
→ Guard count slip (10 vs 8) dropped as low. → By: Opus (RED review record-v3)
→ V16 word-list gap dropped as low. → By: Opus (RED review record-v3)
→ W2 DEAD LINE text noted for docs, not an objection. → By: Opus (RED review record-v3)
→ Raw test log kept in scratch only (holds stored values). → By: Opus (RED review record-v3)
