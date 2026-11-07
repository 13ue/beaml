# Spec: RED TEAM 01 repairs C1, B3 and C3 (with C4)

**[Proposal]** Solve / RED phase, 2026-11-07. By: Opus (RED, red-team-01-repairs) on every entry.
Source findings: [report.md](../red-team-01/report.md), [rt-correctness.md](../red-team-01/rt-correctness.md) C1, C3, C4, R2-4, R2-6; [rt-boundary.md](../red-team-01/rt-boundary.md) B3; [probe-c3-crash-run.md](../red-team-01/probe-c3-crash-run.md) section 5.
None of the three needs an OWNER decision. Each contract below is a default (D6B-187 to D6B-190). Format as in [slice6b-stored-elixir/decisions.md](../slice6b-stored-elixir/decisions.md).
Tests: `tests/redteam_c1_test.py`, `tests/redteam_b3_test.py`, `tests/redteam_c3_test.py`. Evidence: [red-output.log](red-output.log). Notes: [notes.md](notes.md).

## Ownership

| Step | Owner | Repair |
|---|---|---|
| `--stored` Elixir pass, DRIVER text | COMPILER (`main.rs`) | C1 |
| action event write | COMPILER (`main.rs`, `fn action`) | B3 |
| DRIFT status, STEPS list | HARNESS (`run.py`) | C3, C4 |
| Elixir on PATH, parallel test runs | host | none |

## Decisions (defaults)

**D6B-187 · Repair · The DRIVER accepts the enum success tuple as `ok` (C1).**
Chose: the DRIVER prints `ok` for `{:ok, %{__struct__: BeamlSpike.<type>}}` (as now) and also for `{:ok, {<type>, variant, payload}}` with `<type>` equal to the `type` String of the call, `variant` a binary and `payload` a list. Every other result still raises (D6B-122 stays: no `rescue`, `catch` or `try`).
Over: skip enum constructors in the Elixir pass (D6B-104 then misses the `!` clauses of an enum); a `rescue` that maps a `CaseClauseError` to `ok`.
Because: the generated enum constructor returns `{:ok, {"PaymentState", "Authorized", []}}` (observed, test C1f). The DL-102 block for a failing enum record already works (guard C1e). Only the success match is wrong.
Strictness (RED review O1): the new clause matches only that shape. C1h feeds the DRIVER text (read from the `main.rs` of the binary under test) a struct of another TYPE, a bare map, a 2-tuple, another enum name, an atom variant, a non-list payload and a bare value; each must exit non-zero with no `ok` line. The COMPILER maps a non-zero exit to the run error (D6B-121, U1, E8).
Commits us to: the DRIVER mirrors the enum value shape of the emitter. A change of that shape needs a change of the DRIVER and of C1f.
By: Opus (RED, red-team-01-repairs)

**D6B-188 · Repair · One write per action event, a full line (B3).**
Chose: `fn action` formats the whole event with its `\n` into one `String`, then calls one `write_all` on the file opened with `append(true)` (`O_APPEND`). No partial line. Logging still never raises and never stops a build.
Over: a file lock (`flock`) around the write; a log per process.
Because: `writeln!` on an unbuffered `File` issues one `write(2)` per format piece, so parallel runs interleave pieces (observed: 9 to 40 invalid of 2000 lines). One `write(2)` of one short line to an `O_APPEND` file on a local file system lands whole. It is the smallest fix shape the red team names.
Commits us to: an event stays one short line. **[Inference]** One `write(2)` to an `O_APPEND` file is not a documented POSIX atomicity promise for every size and file system; local APFS and ext4 keep short lines whole. The longest line in the repo-root log is 557 bytes. A network file system or a much longer event would need the lock. A `ponytail:` comment names that ceiling.
By: Opus (RED, red-team-01-repairs)

**D6B-189 · Migrate (was Repair) · `drift_status(summary) -> "pass" | "fail"` pins the classes (C3).**
Chose: a module function `drift_status(summary)` in `run.py`. It gives `"pass"` only when all of these hold, else `"fail"`:
1. `summary["freeze"]["status"] == "pass"`;
2. `summary["repaired_all"] is True`;
3. for each derivative, `summary["drift"][d]["gen"]` has `build`, `new_live`, `pre_change` equal to the pin below. A missing row is `fail`.

| Derivative | build | new_live | pre_change |
|---|---|---|---|
| R | correct_accept | false_reject | typed_reject |
| N | correct_accept | false_reject | typed_reject |
| Q | correct_accept | typed_reject | typed_reject |

`drift()` sets `summary["status"] = drift_status(summary)` (test C3d reads that line).
Over: the `new_live` pin only (probe section 5); the weaker "no `untyped_crash`" rule; keep "recorded, not asserted".
Because: the `new_live` pin catches the crash run, but a crash in `pre_change` or a build change would still pass. The full row pin costs the same one line. The values are the observed classes of every retained run after the crash run (`173218Z`, `175013Z`, `180431Z`, `181807Z`; probe section 4) and the rt-correctness C3 proposal. `repaired_all` is `true` in the crash run, so it is needed but not enough.
Commits us to: a deliberate change of a DRIFT derivative changes the pin in the same commit. That is the wanted trigger. The `drift_test.py` header line "The outcomes are recorded, not asserted" is then false for the status; GREEN or DOCS updates it.
By: Opus (RED, red-team-01-repairs)

**Class raised to Migrate (RED review O2, 2026-11-07).** OWNER question M7 in [report.md](../red-team-01/report.md). GREEN of C3/C4 waits for the OWNER. It would reverse the slice 1 Undo D12 "recorded, not asserted" ([roasting-rounds.md](../../../../../wiki/planning/roasting-rounds.md) line 198). The RED tests stay as evidence for option A of M7. Raised by: Fable (RED review, red-team-01-repairs). The Repair class above was the RED default.

**D6B-190 · Migrate (was Repair) · The full run runs every slice 6 file and `drift_test.py` (C4).**
Chose: `SLICE_TESTS` in `run.py` gets every `tests/slice6_*_test.py` (15 files today) and `drift_test.py`, after the slice 2 to 5 files. The `drift` step stays. The three `redteam_*_test.py` files also join (not asserted by C4).
Over: replace the `drift` step with `drift_test.py` (saves one DRIFT run of some minutes, but `execute()` reads the `drift` step summary into `result.json`); a glob in `run.py` (a new file then joins without review).
Because: the full-run PASS then covers slice 6 and the D6B-96 checks. The test uses a glob, so a new slice 6 file that is not listed fails it.
Commits us to: the full run starts two DRIFT runs (the `drift` step and `drift_test.py` setUpClass). **[Unknown]** Total wall time; the GREEN TEST phase measures it.
By: Opus (RED, red-team-01-repairs)

**Class raised to Migrate (RED review O2, 2026-11-07).** OWNER question M7 in [report.md](../red-team-01/report.md). GREEN of C3/C4 waits for the OWNER. It would reverse the slice 1 Undo D12 "recorded, not asserted" ([roasting-rounds.md](../../../../../wiki/planning/roasting-rounds.md) line 198). The RED tests stay as evidence for option A of M7. Raised by: Fable (RED review, red-team-01-repairs). The Repair class above was the RED default.
Effect while a RED is open (RED review O3): with D6B-190 the full run fails while any slice 6 test file holds an open RED. That was expected while step 6c GREEN was pending; 6c is GREEN at 51fd79b2. A new slice 6 RED commit makes the full run fail until its GREEN. **[Inference]**

## RED cases

| Test | Today | Reason |
|---|---|---|
| C1a valid record builds | FAIL | exit 1, run error |
| C1b valid record gives an `ok` event | FAIL | exit 1, run error (build guard first) |
| C1c payload variant builds | FAIL | exit 1, run error |
| C1d mixed records give the DL-102 block | FAIL | run error hides the block |
| C1e failing record alone gives the DL-102 block | ok | guard |
| C1f enum success is a tuple | ok | guard, pins the D6B-187 shape |
| C1g DRIVER accepts struct, enum tuple, enum tuple with payload | FAIL (2 of 3 subtests) | enum tuple raises; struct ok is a guard |
| C1h DRIVER raises on 7 wrong success shapes | ok (guard) | other struct, bare map, 2-tuple, other enum name, atom variant, payload not a list, no `{:ok, _}` |
| B3 parallel runs write whole JSON lines | FAIL | 9 to 40 of 2000 lines invalid, 8 of 8 runs |
| C3a crash run fails | FAIL | no `drift_status` |
| C3b good run passes | FAIL | no `drift_status` |
| C3c six broken inputs fail | FAIL (6 subtests) | no `drift_status` |
| C3d `drift()` uses the rule | FAIL | freeze-only status line |
| C4 STEPS lists slice 6 and `drift_test.py` | FAIL | 16 files missing |

## Exclusions

- No change of `main.rs`, `run.py` or an existing test in this phase.
- No full `run.py` run, no `drift_test.py` run.
- C2, C5, D1 and the other RED TEAM findings stay out.
- The repo-root `.beaml/actions.jsonl` keeps its 396 old invalid lines. B3 stops new ones only; no cleanup of the log.

## Repeatable command

```
BEAML_SPIKE=<scratch>/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/redteam_c1_test.py
BEAML_SPIKE=<scratch>/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/redteam_b3_test.py
python3 -B experiments/0004-generated-replay/tests/redteam_c3_test.py
```

Without `BEAML_SPIKE`, `stored_types_test.compiler()` builds the repository compiler with cargo.
