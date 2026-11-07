# Decisions: slice 6b step 13 (the `--stored` check runs the generated Elixir constructor)

**[Proposal]** PLAN phase, 2026-11-07. Design decisions that DL-121 and DL-122 do not settle.
Classes follow Decision4. Undo and Repair entries give the default that the step worker takes. There is no OWNER question: each real choice has a default with a reason.
Every entry carries a `By:` line (DL-107). The worker records each taken default again in its `notes.md` (DL-097). A Repair that changes a check gets a decision-log entry at the end of its phase.

Format: **ID · class · decision.** Chose / Over / Because. Commits us to (Repair only).

**D6B-102 · Repair · One `elixir -e` process, module and calls as JSON on stdin, compile in memory.**
Chose: the compiler starts `elixir -e <DRIVER>` once per check. `DRIVER` is a const string in `main.rs`. Stdin holds `{"module": <emit output>, "calls": [[fun, [args]], ...]}`, written with `json_string`. The driver runs `Code.compile_string/1`, then `apply(BeamlSpike, String.to_atom(fun), args)` per call.
Over: `elixirc` into a scratch dir and a second `elixir -pa` run; a generated `.exs` file with the values in the code.
Because: one VM start (0.41 s observed) instead of two; no file on disk holds a record value, so nothing to clean up or leak; JSON keeps data apart from code, so a stored value cannot inject Elixir.
Commits us to: the driver text lives in the compiler; the module name `BeamlSpike` is fixed in it (the compiler always emits that name).
By: Opus (PLAN, slice6b-stored-elixir)

**D6B-103 · Repair · The check calls the public `new_T_k` of the first matching signature.**
Chose: the existing Rust signature match of `ctor_fault` (all keys hold Strings, D6B-48) picks the signature and the inputs; Elixir runs `new_T_k(inputs)`, the function that `__beaml_from_T` calls in the runtime decode.
Over: the public decode `__beaml_decode_T` per record (it gives only `constructor`, not the field or the failure TYPE, so the DL-102 text cannot stay); `T.new/1` (DL-117 picks the signature by the exact key set, not by the decode rule).
Because: the constructor body, where P11 lives, runs in the production code; the block text stays byte-equal.
Commits us to: the signature choice stays a Rust mirror of the `cond` in `__beaml_from_T`. A `ponytail:` comment names it. Upgrade path: emit a public `__beaml_from_T` and call it.
By: Opus (PLAN, slice6b-stored-elixir)

**D6B-104 · Repair · Only constructors with a failure TYPE run; the static clause-body check goes.**
Chose: a call is added only when the signature has a failure TYPE (`self.failures[&key]` is not empty). The static `failure_of(body_type)` decision in `ctor_fault` is removed.
Over: run every constructor; keep the static body check as a second verdict.
Because: a constructor without `!` cannot reject in the decode (`__beaml_from_T` returns its value); the compiler rejects non-exhaustive constructors (observed) and DL-120 makes them pure. So the set of failing records is the same. Sources with only enum constructors without `!` start no Elixir. One verdict, one semantics.
Commits us to: a constructor raise is a compiler defect and gives the D6B-106 run error.
By: Opus (PLAN, slice6b-stored-elixir)

**D6B-105 · Repair · Elixir starts only when the static pass gives no error.**
Chose: path, orphan, record version, "no variant", DL-122 and "no signature" errors end the check before Elixir.
Over: run Elixir also then, to report every failure in one build.
Because: DL-121 calls the static check the first pass; a missing toolchain never hides a static error; no VM start for a build that fails anyway.
Commits us to: a constructor failure shows only after the static errors are fixed. Guard E6.
By: Opus (PLAN, slice6b-stored-elixir)

**D6B-106 · Repair · Toolchain errors are build errors, and Elixir output is never forwarded.**
Chose: spawn `NotFound` gives `error: the --stored check runs the constructors over the stored values in Elixir (DL-121): elixir is not on PATH` with `help: install Elixir 1.18 with Erlang/OTP 27 and put elixir on PATH`. A non-zero exit or a wrong count of result lines gives `error: the --stored check: the Elixir run of the generated constructors failed (exit N)` with `help: compile the generated module with elixirc to see the error`. Stdout and stderr of the child are read and dropped.
Over: forward the Elixir stderr; skip the check without Elixir.
Because: DL-121 says no silent pass. A raise prints its arguments, which are record values (DL-032, DL-105).
Commits us to: debugging a run error needs a manual `elixirc` of the output.
By: Opus (PLAN, slice6b-stored-elixir)

**D6B-107 · Undo · One `stored-elixir` event per Elixir run.**
`{"action":"stored-elixir","result":"ok"|"blocked"|"error","ms":N,"calls":K}` through `action()`, with `ms` from `Instant` around spawn and wait. Alternative: a key in the `compile` event (lost on the error path). Reason: the measure exists for passing and blocking builds; no source text, path or value.
By: Opus (PLAN, slice6b-stored-elixir)

**D6B-108 · Repair · DL-122 rule and text in the static pass.**
Chose: a stored String of a literal enum field blocks when it is not in the record's `unknown_fields` and is no current ENUM LITERAL. One message per (TYPE, operation, field, enum, literal), count and first line, text as in plan.md contract 2. The literal is written with `json_string`. A record without `unknown_fields` counts as "kept nothing" (today's `kept` closure).
Over: a check against an earlier source (the compiler has none); counts only (DL-122 rejects B); omit the literal (DL-122 asks for it).
Because: `unknown_fields` already tells which values were literals at capture time (DL-109). One branch beside the "no variant" branch; the help line names the only exit that works today (restore the literal), because D6B-39 forbids a MIGRATE STEP for an enum field.
Commits us to: the literal text appears in stderr; a hand-edited record can put other text there (limit). The interim ends with the fate syntax (DL-122).
By: Opus (PLAN, slice6b-stored-elixir)

**D6B-109 · Undo · Lost mappings of constructor enums are not checked in this step.**
DL-122 names ENUM LITERALS. A constructor enum whose new clauses send an old value to the keep-value variant is the same case in another form. Alternative: compare the Elixir result with `unknown_fields` for constructor enums. Reason: it needs every enum constructor to run in Elixir (against D6B-104) and DL-122 does not ask for it. Recorded as an open point for the next DL-122 step.
By: Opus (PLAN, slice6b-stored-elixir)

**D6B-110 · Undo · Fixtures in `slice6/stored-elixir/`, records copied from step 8.**
`pipe.beaml` (review probe 6), `nested.beaml`, `pipe-fail.jsonl`, `nested-fail.jsonl` as in plan.md. Records are line 1 of `decode-ctor/stored.jsonl` with a new `amount`, `trace_id` and `value_sha256` (`stored_types_test.value_sha256`). DL-122 cases use `slice6/decode/` inline with a text replace. Alternative: inline records in the test. Reason: the step 8 fixture form; the Payment fields stay, so the `type` key stays valid.
By: Opus (PLAN, slice6b-stored-elixir)

**D6B-111 · Undo · `test_written_record_reports_the_count` builds its runtime with `stored/empty.jsonl`.**
Its runtime build uses a source without `Pending` and `slice6/decode/stored.jsonl`, whose line 2 `"pending"` now blocks (DL-122). The test only needs the written record, which it reads in its second build with `Pending`. Alternative: a new stored file without `"pending"`. Reason: one argument changes, the assertion stays.
By: Opus (PLAN, slice6b-stored-elixir)
