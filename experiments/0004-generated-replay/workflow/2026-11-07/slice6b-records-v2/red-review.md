# Slice 6b step 6a: RED review (fresh context)

**[Proposal]** RED review, 2026-11-07. Target: commit `59c5024d` (RED), HEAD `16928894`. One round.
By: Opus (RED review, slice6b-records-v2) for every judgement in this file.

## Verdict

**BLOCK** on objection RR6A-1 (high). RR6A-2 is medium: note it and continue after the repair.
By: Opus (RED review, slice6b-records-v2)

The compiler RED itself is genuine and matches the plan. The block is on the DRIFT change of DL-118: GREEN must change it, but no RED and no acceptance check exists for it.

## Commands and counts (run from the repository root, `main.rs` unchanged)

| Command | Observed | `red-output.log` | Match |
|---|---|---|---|
| `python3 -B experiments/0004-generated-replay/tests/slice6_record_test.py` | 5 tests, FAILED (failures=20): 17 of 22 runtime subtests, 3 P6; guards PASS: `P1_request_unchanged`, `P1_unknown_keys_are_names`, `P1_unknown_value_is_in_no_record_byte`, `P2_replay_of_the_record`, `P3_failed_decode_replays_as_decode`, `test_P6_version_2_record_builds` | 20 (17 + 3), same names | yes |
| same file, `-k P6` | 3 FAIL with `(0, <Elixir>, '')` against expected `(1, '', <D6B-59 text>)` | R-d | yes |
| `python3 -B .../tests/slice6_decode_test.py` | 10 tests, FAILED (failures=7); build blocks with the DL-102 text, counts = full record counts | 7, R-c | yes |
| `python3 -B .../tests/slice6_decode_ctor_test.py` | 8 tests, FAILED (failures=5) | 5, R-c | yes |
| `python3 -B .../tests/arms_test.py` | 11 tests, FAILED (failures=5): L1, L2, L3, R1, R3; R2 and L0 ok | 5 | yes |
| `python3 -B .../slice6b-records-v2/diag_runtime.py` | 13 PASS, 8 FAIL (`replay_*` 6, `record_value_is_the_nested_projection`, `value_only_in_the_typed_field`) | 13 / 8 | yes |
| `python3 -B .../slice6b-records-v2/diag_reason.py` | OK, 2 tests (replay of converted fixture = `:body_digest_mismatch`) | OK | yes |
| `git show 3b76596d:.../stored/v1.jsonl \| cmp - .../slice6/record/stored-v1.jsonl` | byte-equal | R4 | yes |

- **[Observed]** No import error, no setup error, no wrong fixture. Each failure has reason R-a, R-b, R-c or R-d.
- **[Observed]** The commit message says "21 runtime"; the file has 22 runtime cases. Text only, no effect.
- **[Observed]** The `arms_test.py` run wrote `experiments/0004-generated-replay/results/20261107T145809596117Z/` (untracked). It is the evidence of this review run. This review does not delete it.

By: Opus (RED review, slice6b-records-v2)

## Plan coverage (D6B-53 to D6B-69)

| Default | Test | Judgement |
|---|---|---|
| D6B-53 key set | P1 (`version`, `value`, `redacted`, `unknown_keys`, `value_sha256`, no body keys) | partial, see RR6A-2 |
| D6B-54 `value` | P1, P3, P4 (`null`), step 8 `record_value_is_the_nested_projection` | covered |
| D6B-55 `redacted: []` | P1 | covered for 6a |
| D6B-56 `unknown_keys` also on failed decode | P3 `failed_decode_unknown_keys` | covered |
| D6B-57 same projection for 503 | P4 | covered |
| D6B-58 digest | P1, P3, P4, P5 against Python `st.value_sha256`; P2 tamper of `value` and `unknown_keys`; converted fixtures replay with Python digests | covered, independent of the code under test |
| D6B-59 version block | P6 (1, none, line 2, version 2 builds); P2 second guard | covered, exact text |
| D6B-60 decode via `value` | arms R1, R2, R3; slice 3 D11b, D11c; P2, P3 replay | covered |
| D6B-61 `request` unchanged | P1 | covered |
| D6B-62 to D6B-67 | none in 6a | correct: these are 6b defaults; D6B-62, 63, 66 are now Migrate (Q6B-14, Q6B-15, Q6B-11) |
| D6B-68 helper | `stored_types_test.with_value`, used by every adapted file | covered |
| D6B-69 conversion | `convert_fixtures.py` with key asserts; slice 5 A3 (R13) | covered |

- **[Verified]** The version 2 shape (`value` for `body_base64`, `version: 2`, `unknown_keys`, `value_sha256`) agrees with DL-105 and the plan table "RESPONSE RECORD, version 2 (6a)".
- **[Verified]** The DL-110 option B cut is in the diff: `overlay-diff` leaves `run.py` STEPS; the 0003 copy run and `LibArm` leave `arms_test.py`.

By: Opus (RED review, slice6b-records-v2)

## Objections

### RR6A-1 · high · DL-118 commits GREEN to a DRIFT change with no RED and no check that can fail

- **[Observed]** DL-118 (written in the RED commit) says: the 0003 copy replay leaves the DRIFT repair check, the GEN replay of the repaired tree takes its place, `repaired_all` reads that replay, and the LIB arm leaves DRIFT. "Commits us to: the step 6a GREEN changes `run.py` DRIFT repair."
- **[Observed]** `spec.md` acceptance does not name DRIFT. `notes.md` O1 still says "keep both, no change". No test in the RED commit covers it.
- **[Observed]** `run.py drift` sets `status` from the LIB freeze only; `repaired_all` does not change `status`. `tests/drift_test.py` does not read `repaired` and still iterates `ARMS_NAMES = ("gen", "lib")`.
- **[Unknown]** DL-118 does not say which command is "the GEN replay of the repaired tree".
- **Failing scenario A.** GREEN changes the writer and leaves DRIFT. The GEN repair check runs the 0003 copy `replay_run_test.py` over version 2 records and fails. `repaired_all` becomes false. `run.py drift` and `drift_test.py` still pass. The DRIFT (f) repair evidence is wrong, and no check shows it.
- **Failing scenario B.** GREEN removes LIB from DRIFT as DL-118 says. `drift_test.py` then fails on the `lib` rows, and GREEN edits a test without a reviewed RED.
- **Smallest test.** In `tests/drift_test.py`: each DRIFT row exists only for `gen`; each GEN row that builds has `repaired.exit_code == 0`; the repair command is not `.../tests/replay_run_test.py` of the 0003 copy. Today it fails at the `lib` rows and at the command name. Add DRIFT to the `spec.md` acceptance. Alternative: reopen DL-118 and keep DRIFT out of 6a GREEN in writing.

By: Opus (RED review, slice6b-records-v2)

### RR6A-2 · medium · No exact key set; the "no raw byte" guard cannot see an encoded body

- **[Observed]** `P1_unknown_value_is_in_no_record_byte` passes today against the version 1 writer, which stores the full body in `body_base64`. The plain search for `low` cannot see a base64 or hex body.
- **[Observed]** `P1_no_body_keys` checks three key names only. No case pins the D6B-53 key set.
- **Failing scenario.** GREEN keeps the raw body under another key (for example a base64 `raw` or `body`). All P1 cases pass. DL-105 ("the raw body is stored nowhere") is false.
- **[Inference]** The 6b echo test R4 scans base64 and hex forms of the MARKER. It closes this later, but not in 6a.
- **Smallest test.** One P1 case: the sorted keys of `stored.(200, U)` equal the D6B-53 list (`artifact_id`, `attempt`, `client_span_id`, `operation`, `redacted`, `request`, `status`, `trace_id`, `type`, `unknown_keys`, `value`, `value_sha256`, `version`; plus `unknown_fields` only where step 7 writes it). Today it fails on the body keys.
- Disposition: note, do not block. Add it in the RED repair if one runs.

By: Opus (RED review, slice6b-records-v2)

## Open points O2 and O3

- **O2 (new fixture `slice6/record/stored-v1.jsonl`): acceptable.** It is a byte copy of `stored/v1.jsonl` at `3b76596d` (checked with `cmp`). It is the "taken before the conversion" record that P6 needs. It hides no gap. The plan line "6a: none new" is a plan text deviation, recorded as R4 (Repair).
  By: Opus (RED review, slice6b-records-v2)
- **O3 (steps 7 and 8 runtime cases blocked at build): acceptable.** The block is genuine R-c (DL-102 reads `body_base64`; counts equal the full record count). The diagnostic run with `stored/empty.jsonl` shows each runtime case: 13 unchanged PASS, 8 genuine FAIL. After GREEN the same cases run over the converted fixtures, whose digests come from Python, so they also check read-side digest parity for nested values. A GREEN that leaves R-c would keep these files red. No false pass found.
  By: Opus (RED review, slice6b-records-v2)

## False-pass checks done (no objection)

- Digest guards compare with Python `value_sha256`, never with the Elixir output. P2 tamper cases fail for a GREEN without a digest check.
- P4 reads the record after `:json.encode` and `:json.decode`, so an Elixir `nil` (written as `"nil"`) does not pass as `null`.
- The step 7 `NO_VALUE` case now pins `value` exactly and forbids `body_base64`.

By: Opus (RED review, slice6b-records-v2)

## Decisions

**Repair**
- → BLOCK on RR6A-1 instead of a pass with notes, because DL-118 commits GREEN to a change that no check can see. By: Opus (RED review, slice6b-records-v2)
- → RR6A-2 medium instead of high, because 6b R4 scans encoded forms later and no GREEN path points to a second body key. By: Opus (RED review, slice6b-records-v2)

**Undo**
- → O2 and O3 accepted. By: Opus (RED review, slice6b-records-v2)
- → D6B-62 to D6B-67 out of 6a scope, no test needed. By: Opus (RED review, slice6b-records-v2)
- → Leave the review run result directory untracked, not deleted. By: Opus (RED review, slice6b-records-v2)

## Re-check after repair (5dd0f18b)

**[Proposal]** Fresh-context re-check, 2026-11-07. Target: commit `5dd0f18b` (RED repair) only. One round.
By: Opus (RED re-check, slice6b-records-v2) for every judgement in this section.

### Verdict

**PASS** with two medium notes (RC6A-1, RC6A-2). RR6A-1 and RR6A-2 are closed.
By: Opus (RED re-check, slice6b-records-v2)

### Commands and counts (repository root, `main.rs` unchanged)

| Command | Observed | Repair notes | Match |
|---|---|---|---|
| `python3 -B experiments/0004-generated-replay/tests/drift_test.py` | 5 tests, FAILED (failures=2), 293 s. Fail: `test_f_6a_drift_has_gen_rows_only` (7 problems: `lib` in `drift` R, N, Q, `baseline`, `sites`; dirs `lib`, `R/lib`, `N/lib`, `Q/lib`), `test_f_6a_repair_check_is_the_gen_replay_of_the_repaired_tree` (12 problems: per R, N, Q the `replay-run-test` command runs the 0003 copy, `repaired.argv` is `None`, no `record`, no `report`). Pass: fixture guard, freeze case, D24 case | 2 failures, same reasons | yes |
| `python3 -B experiments/0004-generated-replay/tests/slice6_record_test.py` | 5 tests, FAILED (failures=21): 18 of 23 runtime cases, 3 P6. `P1_key_set_is_D6B_53` FAIL. 5 runtime guards PASS | 21 (18 + 3) | yes |

- **[Observed]** Each failure has the stated reason. No import error, no setup error.
- **[Observed]** The DRIFT run wrote `experiments/0004-generated-replay/results/20261107T151614400807Z/` (untracked). This re-check leaves it untracked.

By: Opus (RED re-check, slice6b-records-v2)

### Check 1: RR6A-1 closed

- **[Observed]** Both new DRIFT cases fail today for the stated reasons (table above). Scenario A of RR6A-1 now fails: a GREEN that leaves the 0003 copy run fails the command log check and the `repaired` keys. Scenario B now has a reviewed RED: `ARMS_NAMES = ("gen",)`.
- **[Observed]** `spec.md` section "DRIFT change" names DRIFT in the acceptance.
- **[Observed]** The R and N rows of the earlier run (`results/20261107T150832940455Z`) have a 200 record, flow result `ok` and `host_validation` `ArgumentError` before the repair. The check "`ok` needs `host_validation: ok`" therefore fails for a replay with the unrepaired release. A GREEN that skips the rebuild after the repair (`probe_support.ex` changes) fails for R and N. **[Inference]** Q (record status 400, expected `error`) does not separate repaired from unrepaired; R and N carry that evidence.

By: Opus (RED re-check, slice6b-records-v2)

### Check 2: false-pass hunt on D6B-96

- **[Observed]** Copy of the baseline record fails: the baseline record has the undrifted TYPE, its replay with the drifted runner gives the `pre_change` typed reject (`error`), but the record status is 200, so `ok` is expected.
- **[Observed]** Hidden LIB: the case checks summary keys and the `lib` dirs in the run dir only. A LIB run that writes elsewhere stays invisible. **[Inference]** Consequence is run time only, no wrong evidence: `repaired_all`, `sites` and the rows read GEN only. Dropped (low).
- Two gaps remain: RC6A-1 and RC6A-2.

By: Opus (RED re-check, slice6b-records-v2)

### Check 3: key set

- **[Verified]** `RECORD_KEYS` is a literal list of 13 keys in the test. It equals the plan table "RESPONSE RECORD, version 2 (6a)" (`slice6b-redacted/plan.md`): `version`, the 7 unchanged keys, `request`, `value`, `redacted`, `unknown_keys`, `value_sha256`; body keys removed. The 7 unchanged keys equal the version 1 keys of `slice6/record/stored-v1.jsonl` minus the body keys and `version`. The list does not come from the writer. `unknown_fields` is left out with a reason (no enum in the test source).

By: Opus (RED re-check, slice6b-records-v2)

### Check 4: D6B-96 against DL-118 and the README

- **[Verified]** D6B-96 agrees with DL-118: GEN rows only, GEN replay of the repaired tree, no 0003 copy run, `repaired_all` from that replay. Hunk counting stays (`manual_change_sites` is still asserted).
- **[Observed]** The README (f) DRIFT text says "Per arm", and the slice 1 pass rule compares GEN with LIB sites. `run.py` docstring step 4 and `readme-change.md` line 23 still say the 0003 replay and "no change". DL-118 moves the README text to the docs phase; DL-110 ends the comparison. **[Inference]** GREEN can satisfy D6B-96 and DL-118 at the same time. No contradiction blocks GREEN. The docs phase must update these texts.

By: Opus (RED re-check, slice6b-records-v2)

### Objections

#### RC6A-1 · medium · `repaired` evidence is not tied to a run command or to the repaired live call

- **[Observed]** `repaired_problems` checks the shape of `argv`, but not that this `argv` is in `commands/commands.json` with exit 0. It checks that `record` is a version 2 file in the run dir, but not that its `trace_id` is in the `responses.jsonl` of a live call after the repair. `report` can be any JSON file in the run dir.
- **Failing scenario.** GREEN writes `repaired` with a static `argv` and a hand-written `report.json` (`{"result": {"ok": ...}, "host_validation": "ok"}`) next to a copy of the `new_live` record. All D6B-96 checks pass, and no replay ran in the repaired tree.
- **[Inference]** This needs a deliberate fake; an honest replay without the rebuild fails (check 1). Medium, not high.
- **Smallest test.** In `repaired_problems`: `repaired.argv` equals the `argv` of one entry of the row command log with `exit_code` 0; `report["eval_exit_code"] == 0`; the record `trace_id` differs from the baseline and `new_live` record and is in a `responses.jsonl` under the row dir.

By: Opus (RED re-check, slice6b-records-v2)

#### RC6A-2 · medium · the D6B-96 case passes empty when no GEN row builds

- **[Observed]** The case skips each row with `build_exit_code != 0`. `run.py` computes `repaired_all` as `all(...)` over built rows, which is `true` for none. The D24 case accepts `compile_error` as a class.
- **Failing scenario.** A GREEN change makes the three DRIFT builds fail (for example a generator change hit only by the drifted sources). All DRIFT cases pass, and D6B-96 has no evidence.
- **[Inference]** `arms_test.py` catches a general GEN build break, so only a DRIFT-only break slips through. Medium.
- **Smallest test.** Assert that the R, N and Q GEN rows build (they all built in the earlier runs), or at least R and N, which carry the repair evidence.

By: Opus (RED re-check, slice6b-records-v2)

### Decisions

**Repair**
- → PASS instead of BLOCK, because both objections need a deliberate fake or a DRIFT-only build break; an honest GREEN path cannot pass falsely. By: Opus (RED re-check, slice6b-records-v2)
- → Hidden LIB run dropped (low), because it cannot change any GEN evidence. By: Opus (RED re-check, slice6b-records-v2)

**Undo**
- → README, `run.py` docstring and `readme-change.md` texts left to the docs phase (DL-118). By: Opus (RED re-check, slice6b-records-v2)
- → Leave `results/20261107T151614400807Z` untracked. By: Opus (RED re-check, slice6b-records-v2)
