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
