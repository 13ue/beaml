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
