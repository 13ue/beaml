# RED TEAM 01: consolidated report

Target: git HEAD `7ee5c89e`, branch `main`, 2026-11-07. Review only. No code, test, fixture, grammar, `run.py`, `main.rs` or wiki page changed by the RED TEAM.
Lead: Fable (RED TEAM lead). Workers: Opus `rt-correctness`, `rt-boundary`, `rt-design`. Worker reports: [rt-correctness.md](rt-correctness.md), [rt-boundary.md](rt-boundary.md), [rt-design.md](rt-design.md).
Every judgement in this file carries `By: Fable (RED TEAM lead)` unless it names a worker.

## Scope and method

- Round 1: three angles in parallel, about 40 minutes each. Correctness (false passes in the compiler and the suites), boundary (PII, host boundary, Elixir child, grammar, Pages), design (decision and language consistency).
- Round 2: each worker read the sibling reports, verified or refuted two sibling findings and attacked the opened gaps.
- Lead checks: `.beaml/actions.jsonl` invalid-line count (396 of 13203), DL-032 and DL-124 text, DL-121 text, `run.py:73` to `:90` and `:609`, `main.rs:3851`, the retained run `results/20261107T171545190446Z/drift.json`, DL-116 and DL-125 against `wiki/concepts/migrate-fates.md:66` to `:74`.
- No full `run.py` run. Reason: the retained result directories and the code lines already show C3 and C4; a new run gives no new evidence (rt-correctness decision, accepted by the lead).
- Labels: observed (a command ran or the exact line was read), inferred, unknown. Dispositions of the OWNER are pending; none is inferred.
- The redacted-fields work in progress (`tests/slice6_redacted_test.py`, `slice6/redacted/`, `workflow/2026-11-07/slice6b-redacted-fields/`) was not read.

## Findings ranked

Severity: critical, high, medium, low. Blocking = critical or high, at most three per angle. The rest is noted.

### Blocking: correctness

#### C2 · high · observed · `--stored` blocks on records that the REPLAY RUN never decodes

- Repro: a 503 record with `value {}` or without `value` beside the passing records of `slice6/decode-ctor/stored.jsonl`; `beaml-spike orders.beaml --stored s503.jsonl` gives exit 1 with the DL-102 text and the MIGRATE STEP help. `Replay.run` gives `{:error, :status_mismatch}` for the same record before it reads `value` (rt-correctness R2-3).
- Backing: `check_stored` (`main.rs` about 3788 to 3900) never reads `status`. README `:211` and `:1509`: every status is recorded, the `value` rule is the same for every status. DL-121: "the check result equals the REPLAY RUN result". The claim fails for every non-200 record (lead check of the DL-121 text, rt-design item 1a).
- Consequence: wrong outcome. One recorded Payments outage blocks every later build; the help names a MIGRATE STEP for a record where nothing changed (also D2).
- Root cause shared with C5 and the transport half of D4: the check and the replay have no common rule for "which record is replayable and which fields it reads" (rt-correctness R2-3).
- Smallest resolving test: a mixed snapshot (200, 503, 503 without `value`, tampered digest); for each record the `--stored` verdict equals the `Replay.run` class; a non-200 or bad-digest record gives no DL-102 or DL-122 block.
- Verdict: stands, high. By: Fable (RED TEAM lead).

#### C1 · high · observed · an enum constructor with a failure TYPE makes every `--stored` check with a valid record fail

- Repro: enum `PaymentState` with `fn PaymentState code: String -> PaymentState ! Bad` as a field of the EFFECT output; stored `state: "ok"`; exit 1 "the Elixir run of the generated constructors failed (exit 1)". The `DRIVER` (`main.rs` about 4994) matches only `{:ok, %{__struct__: ^ok}}`; an enum constructor returns a tuple; the `case` raises.
- Round 2: no ledger excludes the case. `slice6b-decode-constructor/notes.md:43` left it open as P9; D6B-104 scopes only enum constructors without `!` (rt-correctness R2-4).
- Consequence: wrong outcome. A correct build blocks; with mixed records the run error hides the DL-102 text. It also hides a literal swap (D1, rt-design item 3).
- Smallest resolving test: `en.beaml` with one record `state: "ok"`, expect exit 0 and an `ok` event; add `state: ""`, expect the exact DL-102 text with `Bad`.
- Verdict: stands, high; a defect, not a doc gap. By: Fable (RED TEAM lead).

#### C3 · high · observed · the DRIFT status ignores outcome classes; a crash run is `pass`

- Repro: `run.py:609` sets `status` from the freeze only. `drift_test.py` checks class membership, not expected classes, and is not in the `run.py` STEPS. The retained run `results/20261107T171545190446Z/drift.json` has `new_live: untyped_crash` for R, N and Q with `status: pass` and `repaired_all: true` (lead check).
- Conflict and resolution: rt-correctness calls this a false pass. rt-design shows that "recorded, not asserted" is the slice 1 Undo D12 and that README `:1561` records "a full-suite `pass` holds no 6a acceptance". The lead splits it: the status rule is a documented limit; the crash run entered the repository with the step 12 GREEN commit and is named nowhere (rt-design item 1b). A compiler regression that crashes the generated flow gives `pass` and nobody reads it. The consequence is the same as a false pass, so the severity stays high. By: Fable (RED TEAM lead).
- Smallest resolving test: pin the observed classes per derivative in `drift_test.py` (R, N: `correct_accept`, `false_reject`, `typed_reject`; Q: `correct_accept`, `typed_reject`, `typed_reject`); make `run.py drift` fail on a build failure or `repaired_all` false. Smallest text step: name the crash run and its cause, or delete it from `results/`.
- Unknown: the cause of the `FunctionClauseError` in that run.

### Blocking: design

#### D1 · high · observed · a swapped ENUM LITERAL passes `--stored` and replays as another variant

- Repro: `slice6/decode/orders.beaml` with `Authorized = "pending"  Pending = "ok"`; `--stored slice6/decode/stored.jsonl` gives exit 0, empty stderr, no `stored-elixir` event; `Replay.run` of line 1 gives `Authorized` on the base build and `Pending` on the swap build (rt-correctness R2-1). The same for an enum constructor with swapped clauses, with and without `!` (rt-design item 3).
- Backing: `main.rs:3851` blocks only a String that is no current literal (lead check). DL-103 limit: "a change that moves a value from one known variant to another ... stays open until a case shows up". README `:1770`: "Lost mappings of constructor enums are not checked (D6B-109)". Neither has a register entry.
- Consequence: false pass. DL-122 reason "yesterday stored, today read differently" applies, and nothing fires.
- Smallest resolving test: the swap fixture with `--stored`; expect exit 1 with the DL-122 text (under option A of M2 below).
- Verdict: stands, high. By: Fable (RED TEAM lead).

#### D2 · high · observed · the DL-102 help line names an exit that the compiler refuses

- Repro: `--stored stored-fail.jsonl` gives exit 1 with the help "declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of Payment (DL-102)"; following it (`add note: String = ""` and `migrate Payment v1 -> v2`) gives exit 1 "the constructor field Payment.state cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)" (rt-correctness R2-2).
- Backing: every DL-102 hit in slice 6b sits on a TYPE with an enum or constructor field; D6B-39 forbids a MIGRATE STEP on exactly those. D6B-39 is a plan default with no DL entry and no line in `migrate-fates.md`.
- Consequence: agent trap. The only exit today is to revert the rule change. The fate grammar alone does not lift the blocks while D6B-39 stands.
- Smallest text step: the DL-102 help names the slice 6b exit, as the DL-122 help does; `migrate-fates.md` names "lift D6B-39" as a prerequisite of every FATE OPERATION.
- Verdict: stands, high. By: Fable (RED TEAM lead).

#### D3 · high · observed (lead upgrade from inferred) · DL-125 misstates DL-116; a FATE OPERATION cannot lift it

- Quote pair: DL-125 question: "a redacted field without a constructor (DL-116)". DL-116 chose: "interim compile error for every redacted output field that is not a String or Int field of a TYPE without a constructor". DL-116 blocks the redacted field on a constructor TYPE; DL-125 names the opposite. `migrate-fates.md:70`: "With a fate for the absent value, the DL-116 limit can be lifted: the rule does not run over an absent value". DL-116 option B, rejected by the OWNER: "replay and DL-102 skipping the rules of a marked field ... B would make a replay silently skip a rule" (lead read of all three texts).
- Consequence: wrong outcome. An agent that lifts the three interim blocks with form 1 builds the silent skip the OWNER rejected.
- Smallest text step: DL-116 leaves the DL-125 list; a separate OWNER question "how does a rule run over an absent value".
- Verdict: stands, high. By: Fable (RED TEAM lead).

### Blocking: boundary

#### B1 · high · observed · equals C1

- rt-boundary found the same DRIVER cause independently (`p2.beaml`, `p2.jsonl`). One finding, counted once. B2 extends it: a non-record failure TYPE (`! String`) gives the run error and the `elixirc` help instead of the DL-102 block; `elixir_results_are_strict` tests only the Rust line parser, never the DRIVER, so no test can catch B1 or B2.
- Verdict: merged into C1; B2 noted at medium. By: Fable (RED TEAM lead).

### Noted: medium

- **C4 · medium · observed** · The full `run.py` PASS covers no slice 6 test (`run.py:73` to `:84`); the step 13 Elixir pass never runs in a full run (`stored/empty.jsonl`); the 172 slice 6 results have no retained `results/<ts>` directory. Resolving test: add the slice 6 files to SLICE_TESTS.
- **D10 · medium · observed** (new in round 2, rt-design) · "full suite 14 of 14" stands beside slice 6 results with no limit line in `wiki/log.md:359`, `:363`, `:371`, `wiki/planning/research-and-development.md:46` to `:49`, README `:1675`, `:1760` and commit `050d6801`. Only README `:1561` and `:1616` state the limit. Consequence: a reader of the log or the register takes slice 6 as covered by the full run. Resolving step: one limit line beside each "14 of 14". The lead merges C4 and D10 as one objection (coverage claim) in the roasting record.
- **D4 · medium · inferred** · The slice 6d REPLAY RUN from the entry diverges from the live call on every domain failure (`:missing_response`, `:status_mismatch` against live `PaymentError`), on every input TYPE change (no MIGRATE CHAIN allowed, no build check) and the `ui_place` name clash. The transport half shares the C2 root cause. Resolving test: N9 plus the N7 closed-port call, replayed.
- **D5 · medium · observed** · `retire f keep N days`: DL-125 says "leave the replay set after N days"; `migrate-fates.md:72` says "not replayable during N days, deleted after". Delete against leave is an Answer-class difference. Under DL-127 the same line would delete domain rows.
- **D6 · medium · observed** · `vertical-integration.md:60` and `:69` ("checks only the stored TYPE VERSIONS", "blocks only when ... cannot reach") contradict DL-102, DL-121, DL-122. No supersede note; plan workers read this page first.
- **D7 · medium · observed** · Slice 6d plans to build the Migrate defaults (D021, D023 "RED and GREEN build A") before the OWNER answers. DL-097 and DL-041 stop at a Migrate question; no entry allows a built default (rt-design item 4).
- **D8 · medium · inferred** · The GLOSSARY definition of RESPONSE RECORD ("one stored line of one EFFECT call") with DL-128 ("the entry is an EFFECT") makes an ENTRY RECORD a RESPONSE RECORD, so D024 reads as answered or open by the reader. ENTRY LINE, ENTRY RECORD, OBSERVATORY have no glossary row; "part 4" means Modules in DL-095 and OBSERVATORY in DL-119.

- **B2 · medium · observed** · A non-record failure TYPE gives the run error instead of the DL-102 block (see B1).
- **B3 · medium · observed** · `.beaml/actions.jsonl` loses events under parallel compiler runs: 396 of 13203 lines at the repo root are not valid JSON (lead count); scratch repro 41 invalid of 400 lines from 40 parallel loops (rt-correctness R2-6). Cause: `writeln!` on an unbuffered File in `fn action` (`main.rs` about 5114). Consequence: the action log that AGENTS.md requires is incomplete. Resolving test: parallel builds, then every line parses. Smallest fix shape: one `write_all` per line.
- **B4 · medium · observed** · The same TYPE has two host shapes: a failure is a struct with atom keys, a value is a map with String keys. A host that passes a failure back into a fn of that TYPE gets "invalid BEAML input"; `%IsZero{}` is rejected while `%{}` passes.
- **B5 · medium · observed** · `%{s | value: 0}` on a `NonZeroInt` struct and a forged `%{__struct__: NonZeroInt, value: 0}` pass the host check (rt-correctness R2-7 probe). README `:1613` and H7 cover only the struct literal; the sentence "stops the accidental forgery" is wrong for the update form, the normal Elixir edit. DL-030 plans to rely on `NonZeroInt`.
- **B6 · medium · observed** · DL-032 ("counts, not record identities", a proposal) against DL-124 (one `S:N` record line per record, no cap). A record line is an identity under DL-032's own wording; no entry reconciles them (rt-design item 5, lead text check).
- **B7 · medium · observed** (D9 merged into it) · `docs/index.html`: the sample source does not compile at HEAD (`redacted` gives `expected ':'`), slice 6a is "in progress" against README Pass, DL-082 to DL-088, DL-092, DL-093 are "decided, not built" and DL-119 "Concept" although slice 6b built them; "action log of every compiler run" is contradicted by B3. DL-095 makes the page the progress view; no rule requires a refresh per DOCS phase (rt-design item 6).

### Noted: low

- **C5 · low · observed** · `--stored` does not verify `value_sha256`; a tampered record passes the check and never replays (`:body_digest_mismatch`). Folded into the C2 root cause and test.
- **R2-5 · low · inferred** (rt-correctness) · Byte guard rows with hand-edited hashes pass while the (71, 40) count stays; `BYTE_GUARD` in `slice6_host_struct_test.py:110` has no count guard. Defence today: the diff at review.
- **B8 · low · observed** · The grammar reserves `with`; the compiler accepts `with` as a parameter or field name; the editor shows ERROR on valid source. All 68 accepted sources parse with 0 ERROR nodes otherwise.
- **B9 · low · observed** · `--stored` trusts the first `elixir` on PATH; a stub that prints `ok` turns a block into exit 0. DL-121 makes the toolchain a host duty, so low.

## Conflicts between workers and resolution

1. C3: false pass (rt-correctness) against documented limit (rt-design). Resolved: both hold; the limit is documented for `repaired_all`, the crash run is undocumented. Severity high stays because the consequence equals a false pass. By: Fable (RED TEAM lead).
2. C1 against D1 on enum constructors: no conflict; rt-design shows that C1 hides D1 under `!` and D1 passes silently without `!`. Merged into one root statement: nothing checks an enum remap today.
3. C2, C5 and D4: three findings, one root cause (no shared replayable-record rule). Kept as separate entries with one resolving test for C2 and C5; D4 stays separate because slice 6d is not built.

4. B1 against C1: one finding; B2 kept as its extension. D9 against B7: one finding under B7.

## Dropped

- Style, naming and wording items in all three reports (per the brief).
- rt-design "near miss" on DL-126 (ENTRY LINE repeats the input TYPE): belongs to D021, not a finding.
- rt-design RED-review gaps (`slice6b-struct-order` without `red-review.md`): no outcome changed.

## Checked and sound (selection)

Nominal checks, constructor bypass, DL-120 reach reject (direct, two helpers, enum, cycle), `T.new/1` key and TYPE cases, `ctor_pick` against the generated `cond`, the Elixir child (absent, endless, crash, partial stdout, all exit 1), `value_sha256` writer and reader, step 12 byte guard derivation, step 12 span assertions (exact clause lines and span trees), `payments.generated.snapshot` P1, exact stderr assertions in slice 6 tests, DL-108 against DL-119, DL-106 against DL-117, DL-105 against DL-124, DL-120 against DL-128, the lost-literal block text (DL-124, no stored String). Details in the worker reports.

## rt-boundary status

`rt-boundary` reported round 1 after the siblings finished round 2. Its findings B3, B5, B6 and B7 were verified in a short round 2b by the siblings; B1 equals C1. Its own round 2 confirmed C2 (a 503 record with full keys goes to the Elixir child: data checked that never replays) and D2 (an empty MIGRATE STEP fails even earlier), and found no ledger line that states the PATH trust of B9 (conflicts with DL-121). No severity changed.
Sound per rt-boundary: the child protocol is strict, stdout and stderr dropped, crash dumps to `/dev/null`, process group kill; no error text, span attribute or event holds a stored value; events and job bus posts hold no paths or source text. Limit: the PII grep could not separate a leak from source text, because the readable fixture values are generic; keys were checked instead. The `"none"` span ids in 0002 host code were not probed: **[Unknown]**.

## Counts

High 6 (C1=B1, C2, C3, D1, D2, D3). Medium 13 (C4, D10, D4, D5, D6, D7, D8, B2, B3, B4, B5, B6, B7=D9). Low 4 (C5, R2-5, B8, B9). Critical 0.

## Decisions (Decision4)

**Undo**
→ No full `run.py` run in this round.
→ Round 2 started with two workers before the third reported.
→ C4 and D10 merged into one roasting objection.

**Repair**
→ C3 kept high statt medium, weil the consequence equals a false pass although the status rule is documented.
→ D3 upgraded to observed statt inferred, weil the lead read all three texts.
→ C2, C5, D4 kept as three entries statt one, weil D4 is plan text and C5 is low.

**Migrate (the OWNER chooses; nothing is decided here)**
→ M1, replayable records in `--stored` (C2, C5): A, the check skips non-200 and bad-digest records as the REPLAY RUN does, with a count line; B, the check blocks as today and DL-121 is narrowed to 200 records; C, the check reads `status` and the digest and gives a separate non-blocking note.
→ M2, known-to-known literal remap (D1): A, block under DL-122 with the DL-124 text; B, count and note under DL-103; C, require a new TYPE VERSION for any literal change.
→ M3, DL-125 scope (D3): A, DL-116 leaves the fates list and a new question "a rule over an absent value" opens; B, keep DL-116 in the list and record that `redact` skips the rule, which reverses DL-116 option B.
→ M4, D6B-39 against the DL-102 help (D2): A, the help names "restore the previous clause or literal" in slice 6b; B, lift D6B-39 as the first slice 6c step before any FATE OPERATION.
→ M5, `retire` semantics (D5): A, out of the replay set after N days, stored; B, deleted after N days; the choice also binds DL-127 rows.
→ M6, slice 6d defaults (D7): A, answer Q6D-1 to Q6D-4 before RED; B, a DL entry that allows a slice to build a Migrate default and pin it.
→ M8, failure struct at the host (B4): A, a failure struct is accepted as a value of its TYPE; B, rejected on purpose and recorded.
→ M9, record lines in the DL-124 text (B6): A, DL-032 allows per-record lines in a build block; B, DL-124 caps the output at the first line plus a count.
→ M7, DRIFT status (C3, C4, D10): A, pin classes and fail on `repaired_all` false, add slice 6 files to `run.py`; B, keep "recorded, not asserted" and put a limit line beside every "14 of 14".

**Answer (evidence only)**
→ The retained crash run `20261107T171545190446Z`: observed `untyped_crash` on R, N, Q with `status: pass`; inferred that it came with the step 12 GREEN commit; unknown cause. No recommendation.
