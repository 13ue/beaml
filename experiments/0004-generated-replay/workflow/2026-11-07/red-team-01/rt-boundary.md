# RED TEAM 01: boundary review (rt-boundary)

By: Opus (RED TEAM, rt-boundary). Target: git HEAD `7ee5c89e` on `main`, 2026-11-07. Review only; no code change.

## Scope and method

- Angle: every boundary. PII and stored values, the host boundary of generated Elixir, the `--stored` Elixir child, the event loggers, the grammar against the COMPILER, and the Pages site against the decision log.
- The COMPILER was built from `git archive HEAD` in the scratch directory (`.../scratchpad/rt/boundary/compiler`). All probes ran there, with the scratch cwd `.../rt/boundary/par`. Probe sources and scripts stay in `.../rt/boundary/` (`p1` to `p6`, `nz.ex`, `nzrun.exs`, `sn/`, `mk.py`).
- Elixir 1.18.1, OTP 27. Tree-sitter 0.26.5 from `/private/tmp/beaml-zed-highlighting/tools/tree-sitter` (the tool the slice 6a ledger uses), on a scratch copy of `integrations/zed-beaml`.
- Not read: `tests/slice6_redacted_test.py`, `slice6/redacted/`, `workflow/2026-11-07/slice6b-redacted-fields/`. No full `run.py` run. No secret read.
- Abbreviation: `S` = `/private/tmp/claude-502/-Users-lennart-Projects-beaml/5a9e3a40-d152-4a88-a91b-9ddd9a8f3732/scratchpad/rt/boundary`. `B` = `S/compiler/experiments/0001-syntax-to-beam/target/debug/beaml-spike`.

## Findings (ranked)

### B1 · high · observed · an enum constructor with a failure TYPE can never pass `--stored`

- Reproduction: `S/p2.beaml` has `fn PaymentState code: String -> PaymentState ! Bad` with three clauses. `S/p2.jsonl` holds one valid record (`state` = a String that maps to `Authorized`). Run `cd S/par && B ../p2.beaml --stored ../p2.jsonl`: exit 1 with `the Elixir run of the generated constructors failed (exit 1)`.
- Cause: the DRIVER in `experiments/0001-syntax-to-beam/src/main.rs` (const `DRIVER`, about line 4983) matches success only as `{:ok, %{__struct__: ^ok}}`. An enum constructor returns `{:ok, {"PaymentState", "Authorized", []}}` (observed in `S/drv.exs`). The `case` raises, the VM exits 1.
- Consequence: wrong outcome. Every build with an enum constructor field that has a failure TYPE and has stored records is blocked, also for valid data. The help line sends the user to `elixirc`, which finds nothing.
- Smallest resolving test: in `slice6_stored_elixir_test.py`, an enum constructor with `! Bad`, one valid record, expect exit 0 and event `result: "ok"`; one record that hits `Bad`, expect the DL-102 block.

### B2 · medium · observed · a non-record failure TYPE gives a run error, not the DL-102 block

- Reproduction: `S/p3.beaml` has `fn Amount value: String -> Amount ! String` with `"" -> "empty"`. `B ../p3.beaml --stored ../p3ok.jsonl` exits 0. `B ../p3.beaml --stored ../p3bad.jsonl` exits 1 with `failed (exit 1)`.
- Cause: the DRIVER matches a failure only as `{:error, %{__struct__: failure}}`. A String, Int or enum failure (allowed after `!`, step 2 G1) is no struct.
- Consequence: wrong outcome. The build blocks, but with the run error text and the `elixirc` help, not the DL-102 text and its MIGRATE STEP help. The unit test `elixir_results_are_strict` checks only the Rust line parser, never the DRIVER, so it cannot see B1 or B2.
- Smallest resolving test: the same source with one `""` record; expect the DL-102 block `fails the constructor of Amount for field amount with String` (or a compile-time reject of a non-record failure on a constructor, if that is the chosen rule).

### B3 · medium · observed · `.beaml/actions.jsonl` loses events under parallel runs

- Observed at the repo root: 396 of 13203 lines are no JSON (interleaved fragments of compile events).
- Reproduction: in `S/par`, 40 parallel loops of 10 COMPILER runs each gave 400 lines, 33 of them no JSON.
- Cause: `fn action` in `main.rs` (about line 5110) uses `writeln!` on an unbuffered `File`. `write_fmt` issues one `write(2)` per format piece, so `O_APPEND` does not keep a line whole.
- Consequence: missing case and false pass risk. Any consumer that counts events (the `stored-elixir` event of D6B-107, the global rule "read the action log before asking") drops or misreads lines. The Pages claim "Action log of every compiler run" does not hold under parallel test runs.
- Smallest resolving test: run the COMPILER 40 times in parallel in one cwd; assert that every line parses and the line count is 40 times the events per run. Fix size: format into one `String`, then one `write_all`.

### B4 · medium · observed · one TYPE has two host shapes: failure struct and value map

- Reproduction: `S/p1.beaml`, `elixir S/p1run.exs`. `fails("r")` gives `{:error, %BeamlSpike.Err{reason: "r"}}`. `takeerr/1` takes `Err` and raises `invalid BEAML input` for that struct. It accepts only `%{"reason" => "r"}`. The same holds for an empty TYPE: the failure is `%BeamlSpike.IsZero{}`, the value check is `map_size(v) == 0` (`nz.ex` line 57), so the struct is rejected and `%{}` passes.
- Consequence: wrong outcome at the host boundary. A host that hands a failure back to BEAML (log it, retry, map it) gets a raise. DL-106 and D6B-79 define the value shapes; no decision states that a failure of a plain record TYPE is no valid value of that TYPE.
- Smallest resolving test: `takeerr(elem(fails("r"), 1))` with the expected result fixed by an OWNER decision (accept the struct, or reject on purpose and record it).

### B5 · medium · observed · the struct update syntax breaks a constructor invariant without a raise

- Reproduction: `elixir S/nzrun.exs` with `nz.ex` from `slice6/host-struct/nonzero.beaml`. `{:ok, s} = NonZeroInt.new(%{n: 3}); keep(%{s | value: 0})` returns `%NonZeroInt{value: 0}`. A forged inner struct in `unbox(%{"n" => %{__struct__: ..., value: 0}})` also passes.
- The README (step 11 limits) states: "The check stops the accidental forgery, not a deliberate one." `%{s | field: x}` is the normal Elixir update form, so it is the accidental case, not a deliberate one.
- Consequence: wrong outcome once code relies on the invariant (DL-030 plans `NonZeroInt` as the guard against division by zero). The nominal check (`is_struct` plus field TYPES, `nz.ex` line 59) does not re-run the constructor clauses.
- Smallest resolving test: `keep(%{s | value: 0})` must raise, or the README limit must name the update form as a known pass. Related: a failure value is never checked on output (`{:error, error} -> {:error, error}` in every wrapper).

### B6 · medium · observed · DL-124 prints record identities that DL-032 excludes; output is unbounded

- DL-032 (`wiki/planning/decision-log.md` line 154): the check "returns counts, not record identities", because "a record identity can link to a person".
- DL-124 (line 688, By: Fable, Repair) prints one `record source: S:N (line N)` line per record and says "DL-032 gets no exception". The code (`main.rs`, the `lost` loop, about line 3930) emits one line per record, with no cap. The DL-102 block prints only the first line.
- Consequence: an unrecorded contradiction. Against a production store (DL-094 live query) a line list is a list of record identities, and 10^6 lost records give 10^6 stderr lines. AGENTS.md requires that contradictions are recorded, not resolved silently.
- Smallest resolving test: a snapshot with 10 000 lost-literal records; assert the stderr line count against a chosen cap (for example the first line plus a count), after an OWNER decision on DL-032 against DL-124.

### B7 · medium · observed · the Pages site states stale and unbacked facts

File: `docs/index.html`.

- "What the source looks like today" shows `card_holder: redacted String` and `add card_holder: redacted String = ""`. The HEAD COMPILER rejects this sample: `B S/sn/sample.beaml --stored empty` gives `expected ':' at byte 172`. No DL entry or README section records `redacted` as built.
- "Grammar for the decided forms (slice 6a, in progress)": the README section Slice 6a says Pass, 12 of 12 checks.
- Items listed as "decided, not built" are built and tested in slice 6b: DL-092 constructors (step 3), DL-082 to DL-088 enum constructors (step 4), DL-086 pipes (step 5), DL-083 `fmt` (step 10), `-> T ! E1 | E2` with DL-093 (step 2). DL-119 (default span set = EFFECT path) is under "Concept", but step 12 built it.
- "Action log of every compiler run" (Verified): B3 shows lost lines. "exact boundary checks": B4 and B5 show gaps beyond the stated DL-106 limit.
- Consequence: wrong outcome for a reader. The page is the public summary.
- Smallest resolving test: a script that compiles the HTML code sample with the HEAD COMPILER and fails on a non-zero exit, plus a check that each "Decided, next" DL id has no passed step ledger.

### B8 · low · observed · the grammar reserves `with`; the COMPILER does not

- `S/sn/s01.beaml` (`fn f with: String -> String = with`) and `S/sn/t02.beaml` (field `with`): COMPILER exit 0, tree-sitter ERROR nodes.
- Consequence: ERROR highlights on valid source. The other direction is expected: the grammar accepts `redacted`, effect `... with f` and `with ... do ... end`, which the HEAD COMPILER rejects (`s21`, `constructors.beaml` byte 728, `forms.beaml` byte 1678).
- Smallest resolving test: one corpus case with `with` as a parameter and as a field, or a COMPILER reject of `with` as a name.

### B9 · low · observed · the `--stored` verdict trusts whatever `elixir` is first on PATH

- Reproduction: `S/fake/elixir` reads stdin and prints `ok`. `PATH=S/fake:/usr/bin:/bin B ../p3.beaml --stored ../p3bad.jsonl` exits 0, although the real run blocks.
- The child also inherits cwd and the whole environment (`ERL_AFLAGS`, `ELIXIR_ERL_OPTIONS`, `ERL_LIBS`). `Command::new("elixir")` sets no `current_dir`. The README limit "asdf reads `~/.tool-versions` in a temporary cwd" describes the test HARNESS (`cwd=self.work / "cwd"`), not the COMPILER.
- Consequence: false pass on a host with a wrong `elixir`. DL-121 makes Elixir on PATH a host duty, so this is a stated trust, not a defect. No version check exists.
- Smallest resolving test: the DRIVER prints a nonce from stdin as its first line; the COMPILER checks it (this also proves that the real driver ran).

## Checked and sound

- Child protocol: success needs exit 0 and exactly one valid line per call (`parse_elixir_results`); stdout and stderr are dropped, never forwarded. Observed in code.
- Crash dump: `ERL_CRASH_DUMP=/dev/null` is set. Time limit: `recv_timeout`, then `kill -KILL -- -pid` on the process group. Observed in code.
- Stdin deadlock: the DRIVER reads all stdin before it writes. Observed in the DRIVER text.
- Run error and static error texts hold no stored value: version, path, orphan, DL-122 and run error texts read.
- Span `:reason` on a constructor failure is the String `"constructor"`, not the failure value (`S/p6run.exs`).
- `.beaml/actions.jsonl` parsable lines: keys only `ts, source, action, target, result` plus counts, `warnings`, `new_live`, `pre_change`, `sites`, `repaired_all`, `step`, `use_case`. `new_live` and `pre_change` hold class names only. No path, no source text.
- Job bus (`run.py` `bus`): `msg`, `pct`, `step`, result directory paths, `meta` counts. Result paths are required by the global job bus rule. No source text or values.
- Span attributes in the step 12 and 13 runs: `order_id`, `outcome`, `function`, `source` (a relative `.beaml` path), `source_hash`, `artifact_id`, `unknown_keys` (names), `reason`. No response value key.
- Host checks: a struct with a missing field, a struct with String keys, an atom-key map for a plain record and a struct for a plain record all raise (`S/nzrun.exs`).
- An Int constructor field in an EFFECT output is rejected at compile time (`S/p4.beaml`), so the String-only `ctor_pick` is consistent with the decode.
- Grammar against COMPILER: all 68 tracked sources that the COMPILER accepts parse with 0 ERROR nodes; whitespace set, string escapes, control characters, comments and `v0` agree (snippets `s*`, `t*`).
- Pages site: DL-126, DL-094, DL-096, DL-128, DL-089, DL-059 exist with the stated content.

## Limits

- PII grep: the readable fixtures hold only generic values (7 distinct Strings of length 5 or more, all also in source text). A grep for them in `results/` (352 MB, 277 directories) cannot separate a leak from source text. The synthetic card-holder values are in the excluded `slice6/redacted/`, so this review cannot check them. A structural check of span and event keys replaced the value grep.
- The 0002 `ProbeSupport.event/2` with `"none"` ids (D6B-127) is host code; not probed.
- The process-group kill and the time limit were read in code, not re-run.
- JSON edge cases (lone surrogates in `value`) were read in the parser, not probed.
- Grammar checks use the CLI only, not the committed `grammars/beaml.wasm` or Zed.

## Decisions

**Undo**

- → Probes in scratch copies only; no repo file except this report.
- → PII check by key structure, not by value grep.
- → B9 rated low: DL-121 assigns Elixir on PATH to the host.

**Repair**

- → B1 high over medium, because valid data can never pass.
- → B7 one finding over six, because one page and one fix.

**Migrate** (OWNER chooses)

- → B4: accept a failure struct as a value of its TYPE, or reject it on purpose and record that.
- → B6: keep per-record lines (amend DL-032), or cap to first line plus count (amend DL-124).

## Round 2

By: Opus (RED TEAM, rt-boundary). Scratch binary as in round 1. Repro files in `S/` (`r2a.jsonl`, `r2b.jsonl`, `orders.beaml`, `orders2.beaml`).

### B1 against C1 · confirmed: one finding

- Same cause (DRIVER success match `{:ok, %{__struct__: ^ok}}`), same repro shape. Merge B1 into C1 and keep the high severity.
- B1 adds two points. (1) B2 shares the same DRIVER: the failure match `{:error, %{__struct__: _}}` fails for `! String`, Int or enum failures, so it gives the run error and not the DL-102 block (`p3.beaml`, `p3bad.jsonl`). (2) The unit test `elixir_results_are_strict` covers only the Rust parser, never the DRIVER. Resolving test: one DRIVER-level test per return shape (record, enum, scalar failure).
- B2 stays medium and separate: it blocks either way, but with the wrong text and help.

### C2 · confirmed, observed; boundary addition

- Repro: line 1 of `slice6/decode-ctor/stored.jsonl` with `status` 503, `value` `{}`, `unknown_keys` `["reason"]` (`S/r2a.jsonl`). Exit 1, two "matches no signature" blocks with the MIGRATE STEP help.
- Writer: `Replay.record(a0, status, bytes)` runs before the status test (generated `p5.ex` line 76). `__beaml_project_*` applies to every status (README step 6a, row `value`: "the same rule for every status"). So a non-200 body keeps the values of its declared keys in `value`, and it may hold them.
- Check: `check_stored` never reads `status`. A 503 record with the declared keys (`S/r2b.jsonl`) passes the static pass, then goes to the Elixir child as a call (event `stored-elixir`, `calls: 1`, `result: ok`). The values of a failure response cross the child boundary. They do not leave it (stdout and stderr dropped), so there is no leak. But the check runs constructors over data that the REPLAY RUN never decodes.
- No severity change. C2 holds for both shapes: an empty `value` gives a false block, and a full `value` gives a check of irrelevant data (this can also block on it).

### D2 · confirmed, observed

- Repro 1: `S/orders2.beaml` (`decode-ctor/orders.beaml` with `type Payment v2`) and `--stored slice6/decode-ctor/stored-fail.jsonl` give exit 1: "the constructor field Payment.state cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)".
- Repro 2: the same file with `migrate Payment v1 -> v2 { }` (`S/orders.beaml`) fails earlier: "a MIGRATE STEP needs at least one rename, add or drop". With a real step, D6B-39 fires as in repro 1.
- Without the change, the build gives the DL-102 block, whose help names the MIGRATE STEP. So the help names an exit that the COMPILER refuses. No severity change.

### B9 · unchanged; no ledger states the PATH trust

- Searched: `slice6b-stored-elixir/` (plan, plan-review, red-review, review, notes), DL-121, `tests/slice6_stored_elixir_test.py`. The PATH appears only as the missing-toolchain case (plan E4, plan-review item 4: "E4 sets the env of the spawned compiler only"). No line states that the verdict trusts the first `elixir` on PATH, and no version check exists.
- DL-121 says "the check result equals the REPLAY RUN result". A stub `elixir` breaks that and no limit records it. Severity stays low (DL-121 makes the toolchain a host duty). The missing limit line is a documentation gap: add it to the README step 13 limits.

### Decisions (round 2)

**Undo**

- → B1 merged into C1; B2 kept separate.
- → No severity changes.
