# RED review: RED TEAM 01 repairs C1, B3, C3 (with C4)

Fresh-context agent RED review, 2026-11-07, git HEAD `48858238`. By: Opus (RED review, red-team-01-repairs) on every entry.
Inputs: [spec.md](spec.md) (D6B-187 to D6B-190), [notes.md](notes.md), [red-output.log](red-output.log), the RED TEAM 01 [report](../red-team-01/report.md), [rt-correctness.md](../red-team-01/rt-correctness.md), [rt-boundary.md](../red-team-01/rt-boundary.md), [probe-c3-crash-run.md](../red-team-01/probe-c3-crash-run.md), the three test files, `run.py`, `tests/drift_test.py`, the HEAD DRIVER and `fn action` in `main.rs`, D6B-104, D6B-121, D6B-122 in [slice6b-stored-elixir/decisions.md](../slice6b-stored-elixir/decisions.md).

**Verdict: BLOCK.** Two high objections (O1 for C1, O2 for C3 and C4). One medium (O3). B3 RED passes the review and can go to GREEN now.

## Re-run (observed)

- Compiler: scratch `git archive HEAD experiments/0001-syntax-to-beam`, `cargo build`, `BEAML_SPIKE`. The working-tree `main.rs` (GREEN worker) was not built or read. Binary sha256 `22c5d5de...de0d` (differs from the RED log `cf8fef3e...`; debug build in another path; no `main.rs` change between `acf12d75` and HEAD).
- C1: 6 tests, 4 FAIL (C1a to C1d), 2 ok (C1e, C1f). Same as `red-output.log`.
- B3: 5 of 5 runs FAIL. Invalid lines 23, 52, 77, 62, 75 of 2000; line count 2000 in each. 2.1 to 3.4 s each. RED log: 9 to 40 invalid. Reliable on this host too.
- B3 side effects: repository `.beaml/actions.jsonl` 14015 lines before and after the runs. `beaml-0004-*` temp dirs 119 before and 119 after (all from other work). No file left behind.
- C3 and C4: 5 tests, 10 failures (C3a, C3b, six C3c subtests, C3d, C4). Same as `red-output.log`. No DRIFT run starts.
- C1 cause, by hand: the HEAD DRIVER with `new_PaymentState_1("ok")` exits 1 with `CaseClauseError no case clause matching: {:ok, {"PaymentState", "Authorized", []}}`. With `""` it prints `error Bad`, exit 0. So the call selection of D6B-104 is correct; only the success match fails.
- Slice 6 files timed with the scratch build (for O3): 15 files, about 34 s in total. `slice6_stored_elixir_test.py` 7.5 s. `slice6_redacted_failure_test.py`: 13 failures at HEAD (open step 6c RED).
- DRIFT class rows of 61 retained `drift.json`: 58 equal the D6B-189 pin with `repaired_all` true and freeze `pass`. This includes `180431928222Z`, `173218Z`, `175013Z`, `181807Z` and every later run. The three others: the crash run `171545190446Z` and two older runs with `repaired_all` false (`20261106T123350493778Z`, `20261107T125625718615Z`). The pin gives `fail` for all three.

## Answers to the checks

1. Re-run: matches the RED log (above).
2. C1 proves the DRIVER cause: C1f pins the tuple, C1e proves the enum call runs and gives `Bad`, the hand run shows the `CaseClauseError`. A GREEN that skips enum constructors fails C1b (`calls` 1), C1d and C1e (exit 1 with the DL-102 block and `Bad`). Those three are the guard against that false pass. D6B-122 strictness has no guard: see O1.
3. B3: reliable (5 of 5 here, 9 of 9 for the author). The test checks only parse, key subset and line count. A `flock` fix, a one-`write_all` fix and a one-flush `BufWriter` all pass; a fix that drops events fails the count. The test does not check that events hold no source text or path. No change in D6B-188 touches the event content, and E5 covers the `stored-elixir` keys. Dropped (low).
4. C3: the pin is the observed class set (above). The pin contradicts slice 1 D12 and is the M7 OWNER question: see O2. Added time: see O3.
5. Missed items: C1 "record with a nested enum field" does not apply. An EFFECT output with a nested record field is a compile error (rt-correctness "Checked and sound"), and the enum payload is `String`. B3 names no event-order rule. No other gap found.

## Objections

### O1 · high · C1 · nothing fails when the DRIVER accepts any `{:ok, _}`

- Evidence: D6B-187 says "Every other result still raises (D6B-122 stays)". The only DRIVER guard is U1 (`elixir_results_are_strict`). It checks the first line and the absence of `rescue`, `catch`, `try`. No test calls the DRIVER with a wrong success shape.
- Consequence: the smallest GREEN is `{:ok, _} -> IO.puts("ok")`. It passes C1a to C1f, U1 and E1 to E9. A compiler defect that emits a wrong value (another TYPE name, a struct of another TYPE, a non-list payload) then gives `ok`. That is the false pass that D6B-122 exists to stop, against DL-121.
- Smallest resolving test (RED, before C1 GREEN): run the DRIVER text with a hand-made `BeamlSpike` module whose function returns `{:ok, {"Other", "X", []}}`, `{:ok, {"PaymentState", "X", "p"}}`, `{:ok, :x}`, `{:ok, %{}}`. Expect a non-zero exit for each, and exit 0 with `ok` for `{:ok, {"PaymentState", "X", []}}`. A Rust unit test beside U1 (needs `elixir` on PATH) or a Python case that reads the DRIVER text from `main.rs`.

### O2 · high · C3, C4 · the RED takes M7 option A without the OWNER and without a record

- Evidence: the RED TEAM 01 report lists M7 under **Migrate (the OWNER chooses; nothing is decided here)**: "A, pin classes ... add slice 6 files to `run.py`; B, keep 'recorded, not asserted' and put a limit line beside every '14 of 14'". `wiki/log.md` says "nine Migrate questions wait for the OWNER". `spec.md` line 5 says "None of the three needs an OWNER decision" and records D6B-189 and D6B-190 as Repair defaults. M7 is not named in the ledger. D6B-189 also reverses the slice 1 Undo D12 ("recorded, not asserted", `workflow/2026-11-06/notes.md`, cited by rt-design).
- Consequence: a Migrate decision is lowered to Repair silently (global Decision4 rule: record who lowered it and why). GREEN of C3 and C4 then builds the OWNER's choice for him. The code change is cheap to revert; the wrong outcome is the decision record, not the code.
- The RED itself is correct for option A: the pin matches 58 of 61 retained runs and fails the three bad ones.
- Smallest resolving step: the main agent asks the OWNER M7 (A or B) before GREEN of D6B-189 and D6B-190, or records the class change with `By:` and the reason in `spec.md` and the decision log. C1 and B3 GREEN do not wait for this.

### O3 · medium · C4 · D6B-190 makes the full run fail at HEAD and adds about 3 minutes

- Evidence: `slice6_redacted_failure_test.py` has 13 failures at HEAD (open step 6c RED). D6B-190 adds every `slice6_*_test.py` file, and C4 uses a glob, so that file cannot stay out.
- Added time (estimate): 15 slice 6 files about 34 s; `drift_test.py` one more DRIFT run, about 2 min 15 s (the `drift` step of `results/20261107T180401517724Z` took that) plus its checks; B3 about 3 s; C1 and C3 about 4 s. Total about +3 min on about 13 min (+23 %). **[Inference]** Acceptable without a flag; the full run is not an inner loop.
- Consequence: the full run status is `fail` until step 6c GREEN lands, so a GREEN TEST phase for C4 cannot show a full PASS. Record this in the GREEN and TEST ledgers; do not skip the file.

## Counts

- Tests: 12 (C1 6, B3 1, C3 4, C4 1); RED failures 4 + 1 + 9 + 1 (C3c as 6 subtests: 15 failures in total). Guards 2 (C1e, C1f).
- Objections: 3 (high 2, medium 1). Blocking: O1 (before C1 GREEN), O2 (before C3 and C4 GREEN). B3 is clear.

## M7 note

D6B-189 and D6B-190 are option A of the OWNER question M7. They also reverse the slice 1 Undo D12. The RED does not state this; it says no OWNER decision is needed. The pin itself is correct against the evidence. The question for the OWNER: pin the DRIFT classes and run slice 6 in the full run (A), or keep "recorded, not asserted" with a limit line (B).

## Decisions

Undo:
→ Re-ran the three files with a scratch build of HEAD, not the working tree. By: Opus (RED review, red-team-01-repairs)
→ Timed the 15 slice 6 files with the scratch build for O3; did not run `drift_test.py` or `run.py`. By: Opus (RED review, red-team-01-repairs)
→ Ran the HEAD DRIVER by hand in scratch to confirm the C1 cause. By: Opus (RED review, red-team-01-repairs)

Repair:
→ O2 high statt medium, weil a Migrate question goes to GREEN without the OWNER or a record. By: Opus (RED review, red-team-01-repairs)
→ B3 content check dropped statt kept, weil D6B-188 does not change the event content. By: Opus (RED review, red-team-01-repairs)

## Re-check after repair (98608459)

Fresh-context agent re-check, 2026-11-07, git HEAD `98608459`. By: Opus (RED re-check, red-team-01-repairs) on every entry. One round.
Inputs: this review, [spec.md](spec.md), [notes.md](notes.md), the last section of [red-output.log](red-output.log), `git show 98608459 -- tests/redteam_c1_test.py`, the HEAD DRIVER in `main.rs`, D6B-121 and D6B-122 in [slice6b-stored-elixir/decisions.md](../slice6b-stored-elixir/decisions.md).

**Verdict: PASS.** O1 and O2 are resolved. O3 is recorded. C1 and B3 can go to GREEN. C3 and C4 GREEN wait for the OWNER answer to M7. No new high or critical objection.

### Re-run (observed)

- Compiler: scratch `git archive HEAD experiments/0001-syntax-to-beam`, `cargo build`, `BEAML_SPIKE` to that binary. The working tree was not built. `run.py` was not run.
- `redteam_c1_test.py`: 8 tests, 6 failures. C1a to C1d FAIL (as before). C1e, C1f ok. C1g: `enum_ok` FAIL and `enum_payload` FAIL, each `(1, [])` (exit 1, no `ok` line); `struct_ok` ok `(0, ["ok"])`. C1h ok: each of the 7 wrong shapes gives `(1, [])`. Same as the RED repair log.
- `redteam_c3_test.py`: 10 failures, as before. No DRIFT run starts. `redteam_c3_test.py` and `run.py` have no working-tree change against HEAD.

### Answers to the checks

1. C1g fails today for the two enum shapes and passes for the struct guard. C1h holds 7 guards that pass today (observed, above).
2. The test does not copy the DRIVER. `driver_text()` reads the `const DRIVER` raw string from the `main.rs` beside `BEAML_SPIKE` (`parents[2]/src/main.rs`), else the repo `main.rs`. A raw string has no escapes, so the text equals the const value. **[Observed]** The extracted 447-byte text occurs byte for byte in the scratch binary. The COMPILER passes the same const to `elixir -e` (`.arg(DRIVER)`). So a GREEN that changes the DRIVER is tested by this file. Limits: the test writes the stdin JSON (`module`, `calls` of `[fun, type, args]`) itself. If GREEN changes that protocol, every call raises; C1h then passes for the wrong reason, but the `struct_ok` guard in C1g fails loudly. A change of the const form (`include_str!`, `r##"`) gives "no DRIVER const", also loud. A `BEAML_SPIKE` outside a `<tree>/target/<profile>/` layout reads the wrong `main.rs`. **[Inference]** Acceptable: every drift is a loud failure, not a false pass.
3. A GREEN clause `{:ok, {^type, variant, payload}} when is_binary(variant) and is_list(payload)` (the D6B-187 shape) does not match `two_tuple` (2-tuple) or `other_enum` (`"Other"` against the pinned `"PaymentState"`). Both raise `CaseClauseError`; C1h catches them. A loose GREEN `{:ok, {_, _, _}}` fails `other_enum`, `atom_variant` and `payload_not_list`. `{:ok, _}` fails all 7. `bare_value` catches a clause without `{:ok, _}`. A GREEN that maps a wrong shape to an `error` line with exit 0 fails the exit check.
4. O2: spec.md marks D6B-189 and D6B-190 "Migrate (was Repair)", names M7, says GREEN of C3/C4 waits for the OWNER, cites the slice 1 Undo D12 and records who raised the class. notes.md marks both entries "(now Migrate, M7, waits for the OWNER)" with D12, and "Left for GREEN" puts `run.py` behind the OWNER answer. The repair changes no C3 or C4 test and no `run.py`. The C3 tests stay RED and wait. Nothing forces the pin.
5. O3: spec.md records under D6B-190 that the full run fails while any slice 6 file holds an open RED, and that step 6c is GREEN at `51fd79b2`. Noted. The time estimate of O3 stays an inference.

### Objections

#### R1 · medium · C1 · no guard for an unknown variant or a wrong payload content

- Evidence: the D6B-187 clause checks the TYPE name, a binary variant and a list payload. No case returns `{:ok, {"PaymentState", "Bogus", []}}` or a payload of the wrong length or element TYPE. The DRIVER gets only the TYPE name, not the variant set.
- Consequence: a compiler defect that emits a variant that the enum does not declare gives `ok`. The struct clause has the same limit (it checks the module, not the fields), so this is parity with D6B-122, not a new hole.
- Smallest resolving test (if wanted): pass the variant names per call and add `{:ok, {"PaymentState", "Bogus", []}}` to `RAISES`. Not blocking.

### Counts

- C1 tests: 8 (6 before, plus C1g and C1h). Failures 6: C1a to C1d, C1g `enum_ok`, C1g `enum_payload`. Guards: C1e, C1f, C1g `struct_ok`, C1h (7 subtests).
- C3 and C4: 10 failures, unchanged.
- Objections: 1 (medium 1). Blocking: none.

### Decisions

Undo:
→ Re-ran C1 and C3 with a scratch build of HEAD; did not run `run.py`, B3 or `drift_test.py`. By: Opus (RED re-check, red-team-01-repairs)
→ Checked the extracted DRIVER bytes against the scratch binary. By: Opus (RED re-check, red-team-01-repairs)

Repair:
→ R1 medium statt high, weil the struct clause has the same field limit (D6B-122 parity). By: Opus (RED re-check, red-team-01-repairs)
