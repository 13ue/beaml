# GREEN output: RECORD FORMAT v3 (EXPERIMENT 0005 prerequisite P2)

**[Observed]** GREEN phase, 2026-11-07. Inputs: [plan.md](plan.md) with "Plan repair", [decisions.md](decisions.md), [red-plan.md](red-plan.md), [red-output.md](red-output.md), [red-review.md](red-review.md) (PASS, medium O1 and O2).
By: Opus (GREEN record-v3). No commit (the main agent commits).

## Base

- `P2_BASE` = `545dded0` (HEAD at GREEN start; RED used `31d83754`). The 6d TEST repair `f9b9083c` and the 6d TEST re-check are in it; no EFFECT byte change between them.
- HEAD moved during GREEN to `eb6def2c` (multi-effect RED, test files only). `experiments/0001-syntax-to-beam/src` at `eb6def2c` equals `545dded0`.
- Toolchain: cargo 1.94.0, Elixir 1.18.1 (OTP 27), Python 3.13.12. `record_v3_test.py` sha256 `fe5dd911…` (after the O1 and O2 tests).

## Diff summary (`main.rs`, +52 −15)

| Place | Change |
|---|---|
| `emit_effect`, `Replay.record/3` | `version: 3`; `span_id` for `client_span_id`; one `case @parent.__beaml_decode_E(bytes)` gives `{unknown_fields, outcome, reason}` (`accepted`/`null`, `rejected`/`decode`, `rejected`/constructor reason when the TYPE has constructor fields); then status != 200 gives `rejected`/`status`; `unknown_fields`, `outcome`, `reason` keys always |
| `emit_replay_entry`, `Replay.entry_record/2` | `version: 3`; `span_id` for `server_span_id` |
| `check_entries` | version check before the `outcome` read: `stored ENTRY RECORD has record version V; this build reads record version 3 only (DL-143)` |
| `check_stored` | version text 3 and DL-143; `outcome` read (else the DL-138 text with RESPONSE); counts; QV3-8 B: a rejected record runs the held check and the orphan check, then skips the W2 `oldest`, the literal and constructor checks and the TYPE path group; on success with M > 0 two notes: `N records, K checked, M rejected at capture` and `digest not verified (P2b)` |

- No change: the live EFFECT function, `__beaml_result_E`, `Replay.run/3`, `body/1`, `digest/3`, `Replay.entry/2`, the DRIVER, every block text.
- Output order (Change 5): the RESPONSE notes push in `check_stored`, before `main` pushes the ENTRY count line.

## Diff proof V18 and hunk list (pin sites 2 to 4)

- **[Observed]** V18 over all tracked sources (`--stored stored/empty.jsonl`, `545dded0` compiler vs GREEN): exit and stderr equal; every hunk owner is `def record(request, status, bytes)` or `def entry_record(bytes, decoded)`; both writers changed wherever present.
- **[Observed]** Re-pin script (scratch, compiles each pinned source with the `545dded0` build and the GREEN build, asserts the old digest first): 78 changed pinned outputs, the only hunk owner of every one is `def record(request, status, bytes) do`. No pinned source has an ENTRY LINE.
- Site 2, `tests/slice6_pipe_test.py` `EFFECT_OUTPUTS`: 2 digests moved (`arms/gen/orders.beaml`, `slice2/reuse/orders.beaml`).
- Site 3, `tests/slice6_host_struct_test.py` `BYTE_GUARD`: 36 digests moved (the rows with an EFFECT); exit codes unchanged.
- Site 4, `slice6/effect-reach/byte-guard.json`: 42 `sha256` values moved; `code` and `changed` unchanged, so the `(71, 40)` setup invariant holds.
- `payments.generated.snapshot`: unchanged (no EFFECT).

## Pin sites 1 and 5 (and a sixth)

- Site 1, `tests/slice5_syntax_test.py` `PIN`, and site 5, `tests/slice6_entry_test.py` `BASE` (N13): both are commit hashes, not digests. There is no PIN digest value to report. Left failing on purpose; the main agent sets both to the GREEN commit hash (RV3-14). No placeholder: `git archive` of a placeholder fails, so a placeholder gives an error, not a pass.
- **[Observed]** Sixth site: `tests/slice6_multi_test.py` `BASE` (N13, line 41, `545dded0`, RED of the multi-effect step, committed in `eb6def2c`). Its comment already says it moves to the P2 pin. Its N13 fails now for the same reason. The main agent moves it with sites 1 and 5.

## Medium notes closed (test tightening)

- **O1:** `test_O1_orphan_check_reads_a_rejected_record`: a rejected 503 record of an undeclared operation gives exit 1 and the DL-040 orphan text (expected text from the `545dded0` compiler over the v2 twin).
- **O2:** `test_O2_missing_or_unknown_outcome_blocks` (2 subtests: missing, unknown word): exit 1, empty stdout, the exact DL-138 RESPONSE text.
- **[Observed]** Mutation check: with a skip of rejected records before the EFFECT lookup and with "not accepted = rejected", both tests fail (3 failures). Restored after the check.

## One-time rewrite

- `convert_v3.py` ran once in place, last change step: 15 files converted. `git diff --stat -- '*.jsonl'` names exactly the 15 listed files (33 lines changed).
- Existing assertions moved (plan table): `drift_test.py` (`!= 3`), `arms_test.py` (`"version": 3`), `redteam_c1_test.py` `TEMPLATE` (version 3, `span_id`, `outcome`, `reason`), `slice6_entry_test.py` `ENTRY_KEYS` and N8 (`span_id`, 3), `slice6_record_test.py` (`RECORD_KEYS` = 16 keys, `P1_version_is_3`, P4 `== 3`, `version_error` text, test names), `stored_types_test.with_value` (version 3).
- Not in the plan table, found by the run: `slice5_syntax_test.py` `test_A3_stored_fixtures_are_unchanged` now applies `convert_v3.convert` after `st.with_value` (the chain BASE v1 → v2 → v3).

## Test results (GREEN build, repository root)

| Check | Result |
|---|---|
| `cargo fmt --check` | pass |
| `cargo clippy --offline --all-targets -- -D warnings` | pass |
| `cargo test --offline --no-fail-fast` | 21 + 14 pass |
| `record_v3_test.py` | 26 tests OK |
| `slice5_syntax_test.py` | 60 tests, 33 fail: 31 A2 + 2 F01_B5, all against `PIN` (site 1); A3 pass |
| `slice6_entry_test.py` | 19 tests, 54 fail: all `test_n13_*` subtests against `BASE` (site 5) |
| `slice6_constructor` 25, `decode_ctor` 8, `decode` 10, `effect_reach` 8, `enum` 20, `failure` 22, `fmt` 25, `host_struct` 3, `int` 16, `pipe` 12, `record` 5, `redacted_failure` 8, `redacted` 20, `stored_elixir` 15, `struct_order` 3 | all OK |
| `stored_types` 33, `redteam_b3` 1, `redteam_c1` 8, `drift` 7, `arms` 11 | all OK |
| `redteam_c3_test.py` | 5 tests, 1 fail: `test_c4_full_run_lists_every_slice6_file_and_drift_test` names the untracked RED files `slice6_multi_test.py` / `slice6_db_test.py` of other workers, not this change |
| `slice6_multi_test.py` (other RED) | red as expected, plus its N13 against `545dded0` (sixth pin site) |

- Not run: `run.py` (task rule), `slice2_replay`, `slice3_replay`, `slice4_retire` (release trees; they build records from `st.v1_record()`, now v3, and the REPLAY RUN reads no `version`). **[Inference]** They stay green; TEST should run them.
- Raw logs stay in the scratch directory (they may hold stored values, DL-124).

## Decisions

**Repair**
→ One `case` on the decode, then the status override statt status-first nesting, weil `unknown_fields` keeps its decode source on non-200 (as at the base). Class Repair. → By: Opus (GREEN record-v3)
→ Count lines as two `snapshot.notes` statt one joined note, weil every note prints as its own line. Class Repair. → By: Opus (GREEN record-v3)
→ `checked` = accepted records of an operation with an EFFECT statt total − rejected, weil it mirrors the 6d ENTRY count. Class Repair. → By: Opus (GREEN record-v3)
→ Count lines only on success statt also beside a block, weil `without_counts` allows both and Err returns early. Class Repair. → By: Opus (GREEN record-v3)
→ A3 chains `convert_v3.convert` statt a new pinned v3 list, weil it keeps the record-history proof. Class Repair. → By: Opus (GREEN record-v3)
→ Sites 1 and 5 left failing statt a placeholder, weil a placeholder commit errors in `git archive`. Class Repair. → By: Opus (GREEN record-v3)

**Undo**
→ `P2_BASE` = `545dded0` (HEAD at GREEN start). → By: Opus (GREEN record-v3)
→ O1, O2 tests added to `record_v3_test.py`. → By: Opus (GREEN record-v3)
→ Old docstring line 1 of `slice6_record_test.py` (version 2, history) kept. → By: Opus (GREEN record-v3)

**Migrate-looking**
→ Sixth pin site `slice6_multi_test.py` `BASE` moves with sites 1 and 5 (default, open). → By: Opus (GREEN record-v3)
