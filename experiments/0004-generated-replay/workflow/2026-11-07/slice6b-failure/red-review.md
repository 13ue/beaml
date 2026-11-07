# Slice 6b step 2: RED review

Reviewer: a fresh-context agent. This is a normal RED REVIEW, not a Devil's Advocate.
Inputs: spec.md, notes.md, red-output.log, plan.md step 2, decisions.md D6B-04 to D6B-10 and D6B-17, plan-review.md (5), DL-092, DL-093, `tests/slice6_failure_test.py`, `slice6/failure/*.beaml`, `src/main.rs` (`failure_types`, `same_type`, `structs`, `emit_effect`, the pipe emit).

## Verdict

**Block.** Two high objections. Each needs one small added test. After that, the RED passes.

## Rerun (observed)

- `python3 -B experiments/0004-generated-replay/tests/slice6_failure_test.py`: 19 tests, 18 FAIL, 1 pass (the guard `test_duplicate_failure_keeps_its_text`). Same as red-output.log.
- Every failure comes from the compiler (exit 1 with a compiler message, or exit 0 with no overlap check). No setup failure.

## Checks that hold (observed)

- Each reject asserts exit 1, empty stdout and the full message. Today's `unknown type: String` cannot give a false pass (plan-review.md (5)).
- The D6B-09 text is asserted. The help line names the overlapping TYPE and suggests a TYPE of its own, or removal after `!` (DL-093). The structural form names `S` (D6B-06). The EFFECT form has no "remove" part, because an EFFECT needs one failure TYPE. Both are Undo choices in notes.md and agree with the plan.
- No runtime subtest can be skipped silently. A build failure fails the test. A missing `PASS` line fails the subtest.
- The runtime cases assert the full `{:ok, _}` or `{:error, _}` value, with the struct for a record failure.
- Each overlap source is minimal. A GREEN that fails earlier for another reason gives another text, so the test fails.

## Objections

### 1. High: a pipe that ends in a record of a failure TYPE is not tested

- **Gap.** D6B-05 lets a whole-body pipe end in a failure TYPE. D6B-07 says a record failure value is the failure struct, "also through a pipe". The only tested pipe ends in `Int` (`piped`). The pipe emit writes `{:ok, last}` today, and the last value of a record is a map with string keys.
- **Wrong outcome.** A GREEN that emits `{:error, %{"reason" => "q"}}` passes all 19 tests. A caller that matches `%BeamlSpike.Bad{}` then misses this failure. One failure TYPE gets two shapes.
- **Smallest test.** Add to `body.beaml`:
  `fn mkbad x: String -> Bad = Bad { reason: x }` and `fn pbad x: String -> String ! Bad = x |> mkbad`.
  Add the runtime case `BeamlSpike.pbad("q") == {:error, %BeamlSpike.Bad{reason: "q"}}`.
- **RED (observed).** Today the source gives `type mismatch: expected String, got Bad`. So the test is genuine.

### 2. High: a program with an EFFECT and a `fn ... ! Int` is not tested

- **Gap.** `emit_effect` calls `self.record(&failure).expect("checked failure")` for each TYPE in `structs()`. After GREEN, `structs()` can hold `Int`, `String` or an enum. notes.md names this risk but adds no test.
- **Wrong outcome.** The compiler panics (exit 101) on a legal program. The pass rule (19 of 19) still passes, and the payments and orders outputs stay byte-identical, because none of them has a non-record failure.
- **Smallest test.** No new snapshot is necessary. Compile `slice2/reuse/orders.beaml` plus the line `fn extra x: String -> String ! Int = 5` with `--stored stored/empty.jsonl`. Assert exit 0 and no `defmodule Int do` line.
- **RED (observed).** Today this source gives `unknown type: Int`. So the test is genuine.

### 3. Medium (note): two failure TYPES with equal fields in one list

- **Ruling.** DL-093 does not settle it: DL-093 is about success TYPE against failure TYPE. D6B-17 makes only TYPES with a constructor nominal (step 3). Other records stay structural (plan.md, D6B-06). So `type A { reason: String }` and `type B { reason: String }` are the same TYPE now. `! A | B` is then the same TYPE two times, like `! String | String`. `unique` compares names only, so it accepts the list.
- **Consequence [Inference].** There is no wrong `{:ok, _}` or `{:error, _}` branch. The struct name comes from the body TYPE, so equal values can arrive as `%A{}` or `%B{}`. That is a shape split, not a crash.
- **Class: Repair.** It is a language rule inside the team. A later reject is one compile check and easy to revert. The consistent rule rejects the pair with `same_type`, as a duplicate failure TYPE. It is not a RED blocker. Record the choice in notes.md and in the decision log at the end of the phase (DL-097). If all records become nominal later (the open D6B-17 question), A and B are legal and distinct.

## Limits

- `run.py` was not run (another worker runs it).
- The two RED probes ran in the scratchpad, not in the test file. No production file or test was changed.
