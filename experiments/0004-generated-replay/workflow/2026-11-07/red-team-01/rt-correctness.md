# RED TEAM 01: correctness (false passes and wrong outcomes)

By: Opus (RED TEAM, rt-correctness). Target: git HEAD 7ee5c89e, branch main. Date: 2026-11-07.

## Scope and method

- Angle: false passes and wrong outcomes in the 0004 test suites and in the 0001 COMPILER.
- Build: a scratch `git archive` copy of `experiments/0001-syntax-to-beam`, `cargo build`, used through `BEAML_SPIKE`.
- Scratch: `/private/tmp/claude-502/-Users-lennart-Projects-beaml/5a9e3a40-d152-4a88-a91b-9ddd9a8f3732/scratchpad/rt/correctness/` (`c1/`, `c2/`).
- Read: `main.rs` (`check_stored`, `ctor_pick`, `ctor_fields`, `DRIVER`, `run_elixir`, `parse_elixir_results`, `REPLAY_HELPERS`), `run.py`, `tests/drift_test.py`, the slice6 tests for steps 11, 12, 12b and 13, `byte-guard.py`, DL-119 to DL-122.
- Ran: probe sources against the scratch binary; `tests/slice6_stored_elixir_test.py` with `BEAML_SPIKE` (15 of 15 OK).
- Read retained `results/*/drift.json` and `results/*/result.json` files.
- I did not read or use `tests/slice6_redacted_test.py`, `slice6/redacted/` or `workflow/2026-11-07/slice6b-redacted-fields/`.
- Labels: observed = I ran it or read the exact line. Inferred = reasoning from observed facts.

## Findings (ranked)

### C1 · high · observed · an ENUM constructor with a failure TYPE makes every `--stored` check with a valid record fail

- Reproduction: `c2/cwd/en.beaml` (enum `PaymentState` with `fn PaymentState code: String -> PaymentState ! Bad`, a field `state: PaymentState` of the EFFECT output). Stored record `c2/en-ok.jsonl`, value `state: "ok"`.
- `beaml-spike en.beaml --stored ../en-ok.jsonl` gives exit 1: "the Elixir run of the generated constructors failed (exit 1)".
- Cause: `DRIVER` in `main.rs` (about line 4994) matches only `{:ok, %{__struct__: ^ok}}`. An enum constructor returns `{:ok, {"PaymentState", "Authorized", []}}` (observed in Elixir). The `case` raises, the child exits 1.
- The same source builds with an empty snapshot (exit 0). The runtime decode `__beaml_from_PaymentState` accepts the value.
- Consequence: wrong outcome. A correct build blocks for every snapshot with one passing record of that field. With mixed records, the run error hides the DL-102 message. No test has an enum constructor with a failure TYPE under `--stored` (E1 to E9 use record constructors only).
- Smallest resolving test: in `slice6_stored_elixir_test.py`, build `en.beaml` with one stored record `state: "ok"`. Expect exit 0 and an `ok` event. Add one record `state: ""`. Expect the exact DL-102 text with `Bad`.

### C2 · high · observed · the `--stored` check blocks on non-200 RESPONSE RECORDS that the REPLAY RUN never decodes

- Reproduction: take line 1 of `slice6/decode-ctor/stored.jsonl`. Set `status` 503, `value` `{}`, `unknown_keys` `["reason"]`, recompute `value_sha256` (`c2/s503.jsonl`).
- `beaml-spike slice6/decode-ctor/orders.beaml --stored s503.jsonl` gives exit 1: "matches no signature of Amount for field amount" and "matches no signature of PaymentState for field state". The help says: declare a MIGRATE STEP.
- The same with `slice6/decode/orders.beaml` (literal enum field) gives exit 1: "has no variant of PaymentState for field state" (`c2/l503.jsonl`).
- Cause: `check_stored` (`main.rs` about lines 3788 to 3900) never reads `status`. The writer records every status (`Replay.record(a0, status, bytes)` before the status check; README line 90 and line 211 "Case L2 needs one record for a 503"). The REPLAY RUN checks `status` before it reads `value` (`slice6b-redacted/decisions.md` line 120).
- The same holds for a 200 record whose live decode failed at capture (P3 shape): the check blocks, the REPLAY RUN gives the same decode failure as live. Inferred.
- Consequence: wrong outcome. One recorded failure response of a Payments outage blocks every later build. The suggested fix (MIGRATE STEP) cannot help, because nothing changed. DL-121 says the check result equals the REPLAY RUN result; here it does not.
- Smallest resolving test: one 503 record with `value` `{}` beside the passing records of `slice6/decode-ctor/stored.jsonl`. Expect exit 0 and no DL-102 or DL-122 message.

### C3 · high · observed · the DRIFT step and `drift_test.py` pass with any outcome class

- Reproduction: `run.py` line 609: `summary["status"] = "pass" if summary["freeze"]["status"] == "pass" else "fail"`. No row class, no `repaired_all` and no build exit code enters the status.
- `drift_test.py` checks that each class is a member of CLASSES and fits its evidence family. It never compares a class with an expected class ("The outcomes are recorded, not asserted", line 5).
- Evidence: the retained run `results/20261107T171545190446Z/drift.json` has `new_live` `untyped_crash` for R, N and Q. Note: "flow raised FunctionClauseError", `expected_accept` true. Its status is `pass`. All other retained runs have `false_reject` / `typed_reject` there.
- A row with `compile_error` for all of R, N and Q also passes the drift step. `evidence_problems` accepts it when the exit code agrees.
- `drift_test.py` is not in the `run.py` STEPS list. So `repaired_all` is never read by any step of the full run (D6B-96 is checked only when `drift_test.py` runs by hand).
- Consequence: false pass. A COMPILER regression that crashes the generated flow gives a PASS of `run.py` and of `drift_test.py`.
- Smallest resolving test: pin the observed classes per derivative (R, N: `correct_accept`, `false_reject`, `typed_reject`; Q: `correct_accept`, `typed_reject`, `typed_reject`) in `drift_test.py`. Make `run.py drift` fail on a build failure or `repaired_all` false.

### C4 · medium · observed · the full `run.py` PASS covers no slice 6 test

- Reproduction: `run.py` lines 73 to 84. STEPS = compiler, lib-freeze, arms, drift and ten slice 2 to 5 files. No `slice6_*_test.py`, no `drift_test.py`, no `overlay_diff_test.py`.
- The slice 6 byte guards (`slice6/effect-reach/byte-guard.json`, `BYTE_GUARD` of `slice6_host_struct_test.py`) run only by hand. `run.py` builds use `stored/empty.jsonl`, so the step 13 Elixir pass never runs in a full run.
- The `cargo test` step runs U1 (`elixir_results_are_strict`) and `effect_reach_is_transitive`. These are the only step 12 and step 13 checks in the full run.
- Consequence: false pass of the retained result dir. "full 0004 suite 14 of 14" says nothing about slice 6b. The 172 slice 6 results have no `results/<ts>` directory with commands, versions and hashes (AGENTS.md R&D rule). Inferred from the commit text and the result dirs.
- Smallest resolving test: add the slice 6 test files to SLICE_TESTS; check that `--list-steps` names each file.

### C5 · low · observed · the `--stored` check does not verify `value_sha256`

- Reproduction: line 1 of `slice6/decode-ctor/stored.jsonl` with `value_sha256` set to 64 zeros (`c2/tamper.jsonl`). The check gives exit 0.
- The REPLAY RUN gives `:body_digest_mismatch` for that record (`REPLAY_HELPERS`, `body/1`). So a record with an edited `value` passes the DL-102 check and never replays.
- The digest covers `value`, `unknown_keys` and `redacted` only. `status`, `request`, `operation`, `type` and `unknown_fields` are outside it. `unknown_fields` decides the DL-103 note and the DL-122 block.
- Consequence: the build check and the REPLAY RUN disagree on edited records. Low, because the snapshot is trusted input.
- Smallest resolving test: the tampered record above. Expect exit 1 with a digest message, or record the limit in the README.

## Checked and sound

- Nominal TYPE checks: same-shape `Raw` never passes where `NonZero` (constructor TYPE) is expected (direct, pipe, pattern). Failure TYPES compare by name in a `!` list.
- Constructor bypass by record literal outside `fn T`: rejected (D6B-18 code path read).
- DL-120 reach reject: direct, two helpers, enum, cycle, equal paths in the tests; call position and nested pipe are rejected by earlier rules (probed).
- An EFFECT always has a failure TYPE (parser), so a reaching call is always a pipe step.
- `T.new/1` (DL-117): wrong, extra, string and missing keys, wrong value TYPE, naked value, nested maps and enum payload maps are tested with exact results.
- `ctor_pick` matches the generated `cond` of `__beaml_from_T` (signature order, extra keys, one-parameter String form). E9a and E9b test it.
- Int and nested record fields of an EFFECT output are rejected at compile time, so the check has no unchecked depth today.
- Elixir child: absent (exact message, exit 1, event `error` ms 0), endless (limit, process group kill, no leftover), crash, extra or partial stdout, unknown failure name: all give exit 1. U1 covers the parser. No false pass found.
- Static errors stop the check before Elixir starts (E6). A constructor without a failure TYPE gives no call (L2).
- `value_sha256`: writer and reader share `digest/3`; `slice6_record_test.py` compares it with an independent Python helper, also for non-ASCII.
- Step 12 byte guard: `byte-guard.py` derives the expected bytes from the pre-step compiler with a text transform, not from GREEN. The (71, 40) count guard rejects a table that a GREEN build regenerates.
- Step 12 spans: tests assert exact clause lines and runtime span trees with parents, not only the presence of a span.
- `payments.generated.snapshot`: P1 compares it with the base commit (one changed line) and with the build. A regenerated file fails P1.
- Stderr assertions in slice 6 tests are exact strings; I found no loose substring check that a different error passes.

## Limits

- About 40 minutes. I read `main.rs` only around the stored check, the DRIVER, the reach map and the decode.
- I did not run the other slice 6 test files, `drift_test.py` or `run.py`.
- C2 uses a hand-made 503 record. I did not capture one from a live Payments outage. The writer code and README line 211 show that such records exist.
- C1: I did not check whether a decision excludes enum constructors with a failure TYPE from slice 6b. The COMPILER accepts the source.
- Byte guard rows with `changed` can still be edited by hand with new hashes while the count stays (71, 40). Not tested.

## Decisions

- Did not run the full `run.py` (about 13 minutes). Reason: the retained `results/*/drift.json` files and `run.py` line 609 already show C3. A new run gives no new evidence. By: Opus (RED TEAM, rt-correctness).
- Did not run `drift_test.py`. Reason: it starts a full DRIFT run; its asserts are read, and C3 needs no run. By: Opus (RED TEAM, rt-correctness).
- Ran `slice6_stored_elixir_test.py` once against the scratch binary to confirm the base state (15 of 15 OK). By: Opus (RED TEAM, rt-correctness).
- Kept probe sources in scratch only; no repository file except this report changed. By: Opus (RED TEAM, rt-correctness).

## Round 2

By: Opus (RED TEAM, rt-correctness). Input: `rt-design.md` (rt-boundary.md was not in the folder at the start).
Scratch: `rt/correctness/r2/cwd/` (`swap.beaml`, `swap.ex`, `base.ex`, `recs.json`, `rp.exs`, `mig.beaml`, `novalue503.jsonl`).
Replay probe: `elixirc` of the generated module plus the `slice6_decode_test.STUBS`, then `BeamlSpike.Replay.run/3` over each record.

### R2-1 · D1 confirmed · observed

- `swap.beaml` = `slice6/decode/orders.beaml` with `Authorized = "pending"  Pending = "ok"`.
- `beaml-spike swap.beaml --stored slice6/decode/stored.jsonl` gives exit 0, empty stderr.
- The Elixir pass of step 13 does not start: no `stored-elixir` event. The enum has literals and no constructor with `!`, so `calls` is empty (D6B-104).
- `Replay.run` over line 1 (`state: "ok"`): base build gives `Authorized`, swap build gives `Pending`. Line 2 (`"pending"`): `Pending` becomes `Authorized`. Line 3 (`"refunded"`): `Unknown` in both.
- Verdict: false pass. The stored meaning changes, and no static or Elixir check fires. D1 stays high.

### R2-2 · D2 confirmed · observed

- Step 1: `beaml-spike slice6/decode-ctor/orders.beaml --stored slice6/decode-ctor/stored-fail.jsonl` gives exit 1: "2 stored RESPONSE RECORDS ... fail the constructor of Amount for field amount with NoCurrency". Help: "declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of Payment (DL-102)".
- Step 2: follow the help in `mig.beaml` (`note: String` plus `migrate Payment v1 -> v2 { add note: String = "" }`). Same `--stored` file. Exit 1: "effect payments.authorize: the constructor field Payment.state cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)". Help: "remove the MIGRATE CHAIN and the VERSION MARK of Payment".
- Verdict: the help line names an exit that the next build refuses. D2 stays high.

### R2-3 · D4 and C2 · partly the same root cause · observed

- `Replay.run` for a 503 record with no `value` key gives `{:error, :status_mismatch}`. A 503 record with a valid `value` gives the same. `expect(record["status"], 200, :status_mismatch)` comes before `body(record)`, so the REPLAY RUN never reads `value` of a non-200 record.
- `beaml-spike slice6/decode/orders.beaml --stored novalue503.jsonl` gives exit 1: "has no variant of PaymentState for field state" (DL-102 block).
- Shared root cause: the build check and the REPLAY RUN use no shared rule for "which record is replayable and which field it reads". The check never reads `status`. The replay reads `status`, `request`, `attempt`, `operation` and the digest first. C2 (status), C5 (digest) and the transport and status half of D4 are instances of this.
- Not the same: the D4 ENTRY RECORD and input-TYPE part is plan text for slice 6d, not built. I did not probe it.
- Smallest resolving test (one test for C2 and C5): for each record of a mixed snapshot (200, 503, 503 without `value`, tampered digest), the `--stored` verdict equals the `Replay.run` class. A non-200 record and a record with a bad digest give no DL-102 block.
- C2 stays high.

### R2-4 · C1 re-check against the ledgers · not excluded · C1 stays high

- `slice6b-decode-constructor/notes.md:43`: "P9 [Unknown, Repair] An enum constructor clause whose body can fail (`!`). Not in the fixture." The case was named and left open.
- `slice6b-stored-elixir/decisions.md` D6B-104 scopes only "Sources with only enum constructors without `!` start no Elixir". `plan.md:84` says "the enum-constructor-only outputs" start no Elixir. That is true only without `!`.
- No D6B, DL or spec line excludes an enum constructor with a failure TYPE from an EFFECT output. The COMPILER accepts the source (exit 0 with `stored/empty.jsonl`).
- Verdict: C1 is a defect, not a doc gap. P9 became a live case in step 13 and nobody closed it. Severity stays high.

### R2-5 · byte guard rows changed by hand · inferred (code read)

- `tests/slice6_effect_reach_test.py:332-342` checks only `(len(table), sum(changed)) == (71, 40)`, then compares each row `sha256` with the build.
- A worker that replaces `sha256` values with the hashes of a new build, and keeps `changed` unchanged, passes the test. `byte-guard.py` refuses to write with a GREEN build (assert of 40 changed), but a hand edit does not go through it.
- The same holds for the `BYTE_GUARD` dict in `tests/slice6_host_struct_test.py:110` (no count guard there at all).
- The only defence is the git diff of the guard file at review. No probe needed: the test reads the repository path, and changing it is outside this review.
- Severity: low. Smallest resolving test: pin the SHA-256 of `byte-guard.json` itself in the test, or compare it with `git show <RED commit>:slice6/effect-reach/byte-guard.json`.

### Severity changes

- None. C1, C2 and C3 stay high; C4 medium; C5 low. C5 now joins the C2 root cause (R2-3), at the same severity.

### Round 2 decisions

- Used stubs for `ProbeSupport` and OpenTelemetry from `slice6_decode_test.STUBS`, not a release. Reason: `Replay.run` needs only them. By: Opus (RED TEAM, rt-correctness).
- Did not probe the slice 6d ENTRY RECORD part of D4. Reason: not built. By: Opus (RED TEAM, rt-correctness).
- Did not edit a repository byte guard to probe R2-5. Reason: review only. By: Opus (RED TEAM, rt-correctness).

### R2-6 · B3 confirmed · observed

- Repo-root `.beaml/actions.jsonl`: 13203 lines, 396 are no JSON (count only, content not printed).
- Scratch repro (`rt/correctness/par/`): 40 parallel loops of 10 builds of `slice6/host-struct/nonzero.beaml` in one cwd give 400 lines, 41 no JSON.
- Cause as B3 states: `writeln!` on an unbuffered `File` in `fn action` writes in pieces, so `O_APPEND` does not keep a line whole. Severity medium, as B3.

### R2-7 · B5 confirmed · observed · the limit is stated only for the struct literal

- Probe (`rt/correctness/b5/b5.exs`, generated `nz.ex`): `{:ok, s} = NonZeroInt.new(%{n: 3})`, then `keep(%{s | value: 0})` returns `%BeamlSpike.NonZeroInt{value: 0}`. `unbox(%{"n" => %{__struct__: BeamlSpike.NonZeroInt, value: 0}})` returns the same.
- Known-limit text: README line 1613 and test H7 (`test_limit_deliberate_struct_literal_is_not_caught`, `slice6_host_struct_test.py:78`, 216) record only the struct literal `%NonZeroInt{value: 0}` as "deliberate". No README line or test names the update form `%{s | value: 0}` or a `%{__struct__: ...}` map.
- Verdict: B5 holds. The README sentence "The check stops the accidental forgery, not a deliberate one" is wrong for the update form, the normal Elixir edit. Severity medium, as B5.
