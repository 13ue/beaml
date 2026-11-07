# Slice 6b step 2: TEST and REVIEW

Reviewer: a fresh-context agent. This is a normal REVIEW, not a Devil's Advocate.
Inputs: spec.md, notes.md (Solve, RED, RED repair, GREEN, Harness repair), red-review.md, green-output.log, plan step 2, D6B-04 to D6B-10, DL-092, DL-093, `git diff 8c687076..HEAD` (main.rs, slice6_failure_test.py, slice6/failure/).

## Verdict

**PASS.** The code meets step 2. One medium ledger defect (decision ID collision) must be repaired in the docs phase. No code change.

## TEST (observed)

Full output: [test-output.log](test-output.log). Summary: [test-result.json](test-result.json). HEAD c3e97430, tree clean at start.

| Command | Result |
|---|---|
| `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` | pass |
| `cargo test --no-fail-fast` | 28 pass (14 unit, 14 CLI) |
| `run.py` (0004, full suite) | 15 of 15 pass, 22 min 44 s, `results/20261107T111726668617Z` and sub-run dirs |
| `run.py` (0001) | pass, `results/20261107T111800449174Z` |
| `slice6_failure_test.py` | 22 of 22 OK |
| `slice6_int_test.py` | 16 of 16 OK |
| stored_types, slice3_types, slice4_retire, slice5_syntax, slice5_squash, slice5_rewrite | 33, 69, 87, 60, 24, 5 OK |
| `scripts/lint_wiki.py` | 81 files, 0 errors |

## Adversarial sources (observed)

Sources and stderr are in test-output.log, section "REVIEW adversarial sources". Runtime builds used `elixirc --warnings-as-errors` with the test stub of `ProbeSupport`.

| # | Source | Result |
|---|---|---|
| 1 | `fn f x: String -> Int ! Int = 5` | exit 1, `error: fn f: the success TYPE Int is also a failure TYPE` and the D6B-09 help line with `remove Int after !` |
| 2 | `-> A ! B`, A and B `{ reason: String }` | exit 1, `... success TYPE A is also a failure TYPE: B has the same fields`, help names B |
| 3 | `-> String ! A \| B`, equal fields | exit 1, `error: fn f: the failure TYPE A is also a failure TYPE: B has the same fields` and `  help: remove B after !` (R3) |
| 4 | `type Ok {..}`, `enum Why { Ok(String) }`, `-> Ok ! Why` | exit 1, `invalid or duplicate constructor: Ok` (earlier check, slice 6a). Also `enum Why { String(String) }`, `-> String ! Why`: exit 0; `f("")` gives `{:error, {"Why", "String", ["e"]}}`, `f("b")` gives `{:ok, "b"}` |
| 5a | `-> String ! String = x \|> up` | exit 1, D6B-09 text at the signature |
| 5b | `-> Int ! String = x \|> up`, `up` gives String | exit 0; `f("q")` gives `{:error, "q"}` |
| 6 | `-> String ! Bad = Bad { reason: x }` (always fails) | exit 0; elixirc prints the typing warning "clause will never match `{:ok, result}`", exit 0; `f("q")` gives `{:error, %BeamlSpike.Bad{reason: "q"}}` |
| 7 | param `c: C`, C equal fields to Bad, `-> String ! Bad = c` | exit 0; `{:error, %BeamlSpike.Bad{reason: "q"}}` (G9, G10 `Map.get` path) |
| 8 | `-> String ! Empty = check(x)`, `check` can fail | exit 1, `check can fail: call it as a pipe step` (slice 1 rule kept) |

## Checks

- **[Verified]** Whole step met: any TYPE after `!` (G1), body TYPE decides (G7, `result`), failure struct also without an EFFECT and through a pipe (G10, G12), `same_type` overlap on `fn` and EFFECT (`overlap`), D6B-09 text, D6B-10 help line, `Int` in EFFECT failure rejected, payments and orders byte-identical (cargo CLI test, slice 5 snapshots, arms suite).
- **[Verified]** `validate` uses `same_type` for the output TYPE, same as `require_type`. No accepted body changes.
- **[Verified]** Nothing beyond need: one new function per concern (`overlap`, `emit_structs`, `failure_of`, `body_type`, `result`). `emit_structs` is the old loop moved, not new code. The `ponytail:` comment marks the per-field `Map.get` limit.
- **[Verified]** The `%@parent.Bad{}` form of the REPLAY RUN (G13) is valid Elixir (scratch module). No compiler source reaches it: payments and orders flows end in the output TYPE.
- **[Inference]** The harness stub cannot hide a wrong span emission in this step. The step changed only the last line of `emit_chain` (`{:ok, p}` to `result(..)`); the span lines are unchanged slice 1 code. The stub still fails on a wrong arity or a non-zero-arity fun (`span/5`, `f.()`). What the stub does not check (name, kind, arguments) the arm tree tests still cover for the EFFECT flows of payments and orders (15 of 15 above), and the CLI test keeps the payments output byte-identical. Not covered: span names inside a pure pipe that ends in a failure TYPE.
- **[Verified]** RED, RED review, RED repair, GREEN, harness repair agree: 19 tests (18 FAIL), then 22 (21 FAIL), then 18 pass and 4 FAIL on the missing `ProbeSupport`, then 22 OK. The 4 failures were the pipe cases, and the stub repair fixed only the harness.

## Defects

### 1. Medium: decision ID DL-097 is already in use

- notes.md R3 and the GREEN limits say "record it as DL-097". DL-097 in decision-log.md is "Build every decided item unattended; record every decision". The highest ID is DL-098.
- Consequence: the R3 language rule (reject `! A | B` with equal fields) gets no log entry, or a duplicate ID.
- Minimum repair (docs phase): give R3 the next free ID (DL-099 or later), add it to decision-log.md, and change the two references in notes.md.

## Notes (low, no repair needed now)

- spec.md pass rule says 19 of 19 and 14 runtime subtests. After the RED repair the file has 22 tests and 15 runtime subtests. The docs phase can update the count.
- Case 6: the Elixir typing warning does not stop `--warnings-as-errors` in Elixir 1.18.1 (observed). A later Elixir can make it an error. GREEN limits already record it.

## Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| V1 | Undo | Verdict PASS with one medium docs defect. | BLOCK | The defect is in the ledger, not in code or tests. The docs phase fixes it. |
| V2 | Undo | Case 4 used a variant named like the success TYPE; the earlier constructor check rejects it. A second source (`enum Why { String(String) }`) tested the accept path. | One source only | The first source never reaches the step 2 code. |
| V3 | Undo | Runtime checks of the adversarial sources used the same `ProbeSupport` stub as the test. | The real `ProbeSupport` | The checks need only the value; the arms suite covers the real spans. |
| V4 | Undo | Result dirs of this run are kept, not committed. | Delete them | Task rule: keep result dirs. The main agent commits. |
