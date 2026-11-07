# Slice 6b step 6a: notes

## Solve / RED

By: Opus (RED, slice6b-records-v2) for every entry in this file, unless an entry names another author.
Inputs: [plan](../slice6b-redacted/plan.md) with its Plan repair section, [decisions](../slice6b-redacted/decisions.md) D6B-52 to D6B-72, [plan review](../slice6b-redacted/plan-review.md), DL-031, DL-040, DL-043, DL-102, DL-105, DL-107, DL-109, DL-110, DL-115, the step 7 and step 8 ledgers, `experiments/0001-syntax-to-beam/src/main.rs` (`emit_effect`, `Replay.record`, `REPLAY_HELPERS` `body/1`, `stored_version`, `check_stored`).
Baseline: HEAD `3b76596d`. `main.rs` is not changed in this phase.

- **[Observed]** `Replay.record/3` writes `version: 1`, `body_base64`, `body_length`, `body_sha256`, and `unknown_keys` only when the decode passes (else `[]`).
- **[Observed]** `body/1` needs the three body keys; any other record gives `{:error, :body_digest_mismatch}`.
- **[Observed]** `check_stored` reads `body_base64` for the DL-102 checks of literal and constructor fields. A record without it counts as a failing value for every such field.
- **[Observed]** `stored_version` does not read the key `version`. A version 1 record builds.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| R1 | Undo | Ledger `slice6b-records-v2/`, as the task names it. | Plan name `slice6b-record/` | The task text is newer than the plan. Only the name changes. |
| R2 | Undo | Take D6B-53 to D6B-61, D6B-68, D6B-69 as written (plan defaults). | Other key names | Plan defaults; DL-105 calls the names a sketch. |
| R3 | Undo | `with_value(record, value, unknown_keys=(), redacted=())` and `value_sha256(...)` in `tests/stored_types_test.py` (D6B-68). `with_value` sorts both lists. | A helper per test file | One rule for the digest; the new test and the converted fixtures use it. |
| R4 | Repair | **Chose:** keep the version 1 record for P6 and the P2 second guard as a new fixture `slice6/record/stored-v1.jsonl` (a byte copy of `stored/v1.jsonl` at `3b76596d`). **Over:** read it from git history in the test; build it in Python. **Because:** the plan says "taken before the conversion"; a file is stable and visible. **Commits us to:** one new fixture although the plan says "6a: none new". | `git show` in the test | D6B-59, plan repair O1. |
| R5 | Undo | The fixture conversion keeps `unknown_keys` of the record, sets `redacted: []`, and takes `value` from the body under the fields of the record's own TYPE VERSION. The script asserts that no fixture has an undeclared key, at the top level and inside `state` and `amount`. | A projection by the newest TYPE VERSION | D6B-69 says "by the record's own TYPE VERSION fields". Every fixture body holds declared keys only, so the two rules give the same `value`. |
| R6 | Repair | **Chose:** under DL-110 (option B) remove from `arms_test.py` the 0003 copy run (`run_0003`, class `GenRunner` with cases (c) runner and (d) eight-case matrix) and the class `LibArm` (case (e)), and the `overlay-diff` step from `run.py`. Keep the GEN cases (b), (c) structure, (d2) and the control check. **Over:** keep `LibArm` cases that do not run the 0003 copies (`test_e_lib_form...`, `test_e_lib_type_mismatch...`). **Because:** DL-110 option B text: "`run.py` and `arms_test.py` keep only the GEN-only replay and type cases". **Commits us to:** no LIB case in `arms_test.py`; the LIB freeze step and DRIFT (f) stay in `run.py` (open point O1). | Keep `LibArm` | DL-110, plan Q6B-10 option B. |
| R7 | Undo | The replaced 0003 cases move to `slice6_record_test.py`: a1 becomes `a1_key_order_does_not_matter` (DL-110 has no a1 text; the plan option A text is the source), the body tamper becomes `P2_tampered_value_is_digest_mismatch`. | Drop them | The task names both cases. |
| R8 | Undo | `run.py` `body_json` reads `value` when the record has it, else `body_base64`. The proxy exchanges and LIB records keep the raw body. | Two functions | Plan table row `run.py`; LIB stays frozen on the raw body (DL-110). |
| R9 | Undo | `slice6_record_test.py` uses the step 7 release-free harness: `sd.Slice6Decode.run_runtime` with a new keyword `stored=` (default unchanged). Source `arms/gen/orders.beaml`, `--stored stored/empty.jsonl`. | A copy of the harness | Plan 6a harness line. One harness. |
| R10 | Undo | The runtime cases read each record after `:json.encode` and `:json.decode` (`stored.(status, bytes)`), the encode of the real `ProbeSupport.json/1`. | Read the captured term | The record in a RECORD SNAPSHOT is JSON text. P4 then pins `value` to JSON `null`, not the atom `nil` (which `:json.encode` writes as the string `"nil"`). |
| R11 | Undo | P2 adds a tamper of `unknown_keys` (digest covers it, D6B-58). P3 adds a failed decode with an extra key (`unknown_keys: ["fraud_score"]`, D6B-56). P6 adds a version 1 record at line 2 after a version 2 record, and a guard that a version 2 record builds. | Only the plan cases | Each one is a D6B rule that a GREEN could miss. |
| R12 | Undo | P5 non-ASCII value: `autorisé ✓ 😀` (2-, 3- and 4-byte UTF-8). | One 2-byte letter | Limit L4: more escape paths in one value. Still one value only. |
| R13 | Repair | **Chose:** `slice5_syntax_test.py` A3 "stored fixtures unchanged" now compares each BASE record, converted by `st.with_value` with its body as `value`, to the record now (parsed JSON). **Over:** remove A3; keep byte equality (fails by design). **Because:** D6B-69 converts in place; A3 still guards the record content. **Commits us to:** A3 depends on the 6a conversion rule. | Remove A3 | D6B-69. |
| R14 | Undo | `slice6_decode_ctor_test.py` gets one new live case `record_value_is_the_nested_projection` (DL-099 nesting, stray key `state.extra` not in `value`). | No nested case | `arms/gen/orders.beaml` has no nested field; only step 8 tests D6B-54 nesting. |

### Changed assertions

Class of every change: Repair (our own contract, pre-production, D6B-52), unless the row says otherwise.

| File | Test or place | Before | After |
|---|---|---|---|
| `tests/arms_test.py` | module | `EIGHT_CASES`, `DEFAULT_STEPS`, `with_body`, `run_0003`, imports `base64`, `hashlib`, `REPLAY_PATH` | removed (R6) |
| `tests/arms_test.py` | `GenRunner.test_c_gen_0003_runner_passes_all_five_steps`, `GenRunner.test_d_gen_replay_matrix_eight_cases` | 0003 copy run in the GEN tree | removed, DL-110 (Migrate, OWNER) (R6) |
| `tests/arms_test.py` | `LibArm` (3 tests) | LIB form, LIB 0003 matrix, LIB type mismatch | removed, DL-110 (Migrate, OWNER) (R6) |
| `tests/arms_test.py` | `test_d2_L1_...` | `bytes` == base64 of `UNKNOWN_KEY_BODY` | `version` == 2, `value` == `PAYMENT`, `"low"` not in the record JSON; `record_hint` unchanged |
| `tests/arms_test.py` | `test_d2_L2_...` | `bytes` == base64 of `VALID_BODY` | `value` == `PAYMENT` (D6B-57) |
| `tests/arms_test.py` | `test_d2_L3_...` | `bytes` == base64 of `MISSING_KEY_BODY` | `value` == `{"order_id": "order-1"}` |
| `tests/arms_test.py` | `test_d2_R1_...`, `test_d2_R3_...` | `with_body(L0 record, bytes)` | `st.with_value(L0 record, dict)`; expected `decode_error()` unchanged |
| `tests/arms_test.py` | `test_d2_R2_...` | — | no change; after 6a the hint comes from the record `unknown_keys` (D6B-60) |
| `tests/slice2_replay_test.py` | C11, C12, C13 | `arms.with_body(records(V1)[0], body)` | `st.with_value(records(V1)[0], json.loads(body))`; expected unchanged |
| `tests/slice2_replay_test.py` | `ChainByVersion.test_each_stored_version_replays...` | `arms.with_body(record, body)` | `st.with_value(record, json.loads(body))`; expected unchanged |
| `tests/slice2_replay_test.py` | C2, C3, C9, C14 | — | code unchanged; they read the converted `stored/v1.jsonl`, `stored/v1-v2.jsonl` |
| `tests/slice3_replay_test.py` | `replay` | `arms.with_body(record, json bytes)` | `st.with_value(record, dict)`; D11b, D11c keep their meaning (D6B-60) |
| `tests/slice4_retire_test.py` | `with_body`, `make_record` | raw body per TYPE VERSION | `st.with_value(record, dict)`; `with_body`, imports `base64`, `hashlib` removed |
| `tests/slice5_syntax_test.py` | `make_record` | inline `body_base64`, `body_length`, `body_sha256` | `st.with_value(record, dict)`; import `hashlib` removed |
| `tests/slice5_syntax_test.py` | `test_A3_stored_fixtures_are_unchanged` | byte equality with BASE | equality with the BASE records converted by D6B-69 (R13) |
| `tests/stored_types_test.py` | module | — | new `BODY_KEYS`, `value_sha256`, `with_value` (R3) |
| `tests/slice6_decode_test.py` | `NO_VALUE` | no record key except `body_base64` holds `refunded` | `value` == `{"order_id", "state": "refunded"}`, no `body_base64` key, no other key holds `refunded` |
| `tests/slice6_decode_test.py` | `run_runtime` | `--stored` fixed to `STORED` | keyword `stored=STORED` (R9, Undo) |
| `tests/slice6_decode_ctor_test.py` | `LIVE_CASES` | — | new `record_value_is_the_nested_projection` (R14) |
| `run.py` | `STEPS` | step `overlay-diff` | removed, DL-110 (R6) |
| `run.py` | docstring | "overlay diff ... arms (a-e)" | "arms (GEN cases)" |
| `run.py` | `body_json` | `body_base64` only | `value` of a GEN record, else `body_base64` (R8) |
| fixtures | `stored/v1.jsonl`, `stored/v1-v2.jsonl`, `slice6/decode/stored*.jsonl`, `slice6/decode-ctor/stored*.jsonl` | version 1, raw body | version 2 projection (D6B-69, R5) |
| fixture (new) | `slice6/record/stored-v1.jsonl` | — | version 1 record (R4) |

Not changed: `tests/overlay_diff_test.py` (the file stays; it leaves the check list), `arms/gen/assertion-changes.json`, the GEN 0003 copies in `arms/gen/overlay/`, `arms/lib/`, `tests/cli.rs`, `tests/payments.generated.snapshot`, `tests/slice4_replay_test.py`, `tests/slice5_replay_test.py` (they use the changed `make_record`), the README (text in [readme-change.md](readme-change.md)).

### RED

See [red-output.log](red-output.log) for commands, failing names and output.

### Open points

- **O1 [Open, Repair]** `run.py drift` stays in the check list. Its repair check runs the GEN 0003 copy of `replay_run_test.py` in the repaired tree (`replay_test`). After 6a GREEN this check reads the raw body and fails for GEN. The `drift` step status does not depend on it (`status` = freeze), but `repaired_all` becomes false. DL-110 names the 0003 copy run; whether DRIFT (f) and the LIB freeze step leave too is not stated. Default in this phase: keep both, no change.
- **O2 [Open, Undo]** The plan says "6a: none new" for fixtures; R4 adds one.
- **O3 [Inference]** (diagnostic scripts `diag_runtime.py`, `diag_reason.py` kept in this ledger) The step 7 and 8 runtime tests build with the converted RECORD SNAPSHOTS. Today that build blocks (the DL-102 check reads `body_base64`), so the runtime cases do not run there. A diagnostic run with `--stored stored/empty.jsonl` (red-output.log) shows the runtime RED for each case.

### RED result

- **[Observed]** New `slice6_record_test.py`: 20 failures (17 runtime cases, 3 P6 cases). 6 guards pass today (red-output.log).
- **[Observed]** Adapted files fail only at the changed assertions or the converted fixtures: `slice6_decode_test.py` 7, `slice6_decode_ctor_test.py` 5, `arms_test.py` 5, `slice2_replay_test.py` 11, `slice3_replay_test.py` 22, `slice4_replay_test.py` 6, `slice5_replay_test.py` 6.
- **[Observed]** Compile-only adapted files pass: `stored_types_test.py`, `slice3_types_test.py`, `slice4_retire_test.py`, `slice5_syntax_test.py`, `slice6_struct_order_test.py`.
- **[Observed]** Every failure has one of four reasons: version 1 writer (R-a), `body/1` gives `:body_digest_mismatch` for a version 2 record (R-b, checked by a diagnostic case), `--stored` DL-102 check reads `body_base64` (R-c), `--stored` ignores `version` (R-d). No setup failure.
- Result directories of the release runs: `results/20261107T144334140681Z` (arms), `20261107T144400020205Z` (slice 2), `20261107T144552743415Z` (slice 3), `20261107T144931548015Z` (slice 4), `20261107T145206963003Z` (slice 5).
