# RED TEAM 01: language and decision consistency (rt-design)

Review only, 2026-11-07, git HEAD 7ee5c89e. No code, test, fixture, grammar, wiki or README changed.
By: Opus (RED TEAM, rt-design) on every judgement in this file.

## Scope and method

- Read: AGENTS.md, GLOSSARY.md, `wiki/concepts/vertical-integration.md`, `wiki/concepts/migrate-fates.md`, decision log DL-080 to DL-128, register D002, D003, D018 to D024 and "Answered", README slice 6b sections, `slice6d-inbound-effect/` (plan, plan-review, decisions), `skills/implement-step/SKILL.md`, `docs/index.html`, `experiments/0001-syntax-to-beam/src/main.rs` (`check_stored`, `literal_fields`, `ctor_fields`).
- Probes: a HEAD compiler built from `git archive` in the scratch directory `rt/design/`. Probe sources: `swap.beaml`, `remap.beaml`, `chainctor.beaml`, `nochain.beaml`, `ren.beaml`, `nest.beaml`. Inputs: the tracked fixtures `slice6/decode/stored.jsonl`.
- Not read: the redacted-fields work of the sibling worker. `run.py` not run.
- Labels: observed (exact line read or probe run), inferred, unknown.

## Findings (ranked)

### D1 · high · observed · A swapped ENUM LITERAL changes the stored meaning with no block and no count

- Reproduction: `decode/orders.beaml` with `Authorized = "pending"  Pending = "ok"` (swap). `beaml-spike swap.beaml --stored slice6/decode/stored.jsonl` gives exit 0, no note. The stored `"state":"ok"` record was `Authorized`. Today it replays as `Pending`.
- Quote pair: DL-122 question: "when an ENUM LITERAL is removed, or its String changes ... Chose: A [block]". Code `main.rs:3851`: "a String that is no current literal and was not kept was an ENUM LITERAL at capture". The code blocks only a String that is no literal now. A String that moves to another variant passes.
- DL-103 Limit (decision-log.md line 535): "a change that moves a value from one known variant to another known variant is not covered here ... stays open until a case shows up". The case is here. It has no register entry.
- Same gap, by README line 1770: "Lost mappings of constructor enums are not checked (D6B-109)". Also no register entry.
- Consequence: false pass. A REPLAY RUN of an old record gives another variant. DL-122 reason "yesterday stored, today read differently" applies, and nothing fires.
- Smallest resolving test: the swap fixture with `--stored`; expect exit 1 with the DL-122 text. Smallest text decision: a register entry (OWNER) "known-to-known remap and constructor-enum remap: block under DL-122, or count".

### D2 · high · observed · The DL-102 help line names an exit the compiler rejects

- Reproduction: `chainctor.beaml` and `nochain.beaml` (a TYPE with a constructor field plus a MIGRATE STEP or a VERSION MARK). Exit 1: "the constructor field Payment.amount cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK in slice 6b (D6B-39)". `ren.beaml` gives the same for an enum field.
- Quote pair: the DL-102 block help at `main.rs:3918` and `main.rs:3992`: "declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of {ty} (DL-102)". DL-125 Because: "The three interim blocks need nothing more than 1."
- Every DL-102 hit in slice 6b sits on a TYPE with an enum or a constructor field. D6B-39 forbids a MIGRATE STEP on exactly those TYPES. The DL-122 help names the working exit ("restore the ... ENUM LITERAL"); the DL-102 help does not.
- D6B-39 is a plan default only. No DL entry, no line in `migrate-fates.md`, no register entry.
- Consequence: agent trap. An agent follows the help, writes a MIGRATE STEP, and gets a second error. DL-102 forbids a hand edit of the store, so the only exit is to revert the rule. The fate grammar alone does not lift the blocks.
- Smallest text decision: the DL-102 help names the slice 6b exit ("restore the previous constructor clause"), as DL-122 does. `migrate-fates.md` names "lift D6B-39" as a prerequisite of every FATE OPERATION.

### D3 · high · inferred · DL-125 misstates DL-116; a FATE OPERATION cannot lift it

- Quote pair: DL-125 question: "a redacted field without a constructor (DL-116)". DL-116 chose: "interim compile error for every redacted output field that is not a String or Int field of a TYPE without a constructor". DL-116 blocks the field WITH a constructor; DL-125 names the opposite.
- DL-116 is a declaration limit, not a stored-record block. It fires on a v1 TYPE with no stored record and no MIGRATE STEP. Its exit is "a rule over an absent value" (DL-116 Because), not a fate.
- `migrate-fates.md` line 70: "With a fate for the absent value, the DL-116 limit can be lifted". The OWNER rejected DL-116 option B ("replay and DL-102 skipping the rules of a marked field ... B would make a replay silently skip a rule").
- Consequence: wrong outcome. An agent that "lifts the three interim blocks" with form 1 builds the silent skip that the OWNER rejected, or runs a constructor on `:redacted`.
- Smallest text decision: DL-116 leaves the DL-125 scope. A separate OWNER question: how a rule runs over an absent value.

### D4 · medium · inferred · The slice 6d REPLAY RUN from the entry diverges from the live call on every domain failure and every input TYPE change

- Observed in generated code (`o.ex` from `decode/orders.beaml`): on `:error` (transport) no `Replay.record` is written; `Replay.run` needs `status == 200` (`expect(record["status"], 200, :status_mismatch)`) and one record per trace (`:missing_response`).
- Plan D6B-135 writes an ENTRY RECORD for every call, also before a failure. D6B-137 then calls `run/3`. Live N7 gives `{:error, %PaymentError{reason: "transport"}}`; the replay of that ENTRY RECORD gives `{:error, :missing_response}`. A status 500 gives `:status_mismatch` against live `PaymentError{reason: "status"}`. N9 tests only success and `Rejected`.
- Input TYPE change: D6B-130 forbids a MIGRATE CHAIN on the input TYPE. Plan item 8 does not say whether `Replay.entry` reads the ENTRY RECORD `type`. A plain `add` of a field makes every stored ENTRY RECORD replay as `Rejected{decode}` or fail the version pick. No build check (Q6D-4 B), no way to declare a chain. D024 names only constructor and literal changes.
- Name clash missed by D6B-138: an outbound `effect ui.place ...` generates `ui_place` (as `payments_authorize`), the same name as the entry function for `on ui "place"`.
- Consequence: missing case. An agent builds N9 green and the PROTOTYPE replay disagrees with production for every failed order.
- Smallest resolving test: N9 plus the N7 closed-port call, replayed; expect the live outcome, or a declared typed reason. Add the input-TYPE-change case to D024.

### D5 · medium · observed · The fate concept contradicts DL-125 on `retire` and the RETIRED RECORD definition

- Quote pair: DL-125 option 1: "`retire f keep N days` (such records leave the replay set after N days)". `migrate-fates.md` line 72: "During the N days the record is a RETIRED RECORD: stored, not replayable ... After N days the deploy deletes only those records."
- DL-125 reads as: replayable during the window, out of the replay set after it. The concept reads as: not replayable during the window, deleted after it. Delete versus leave the replay set is an Answer-class difference (nothing unmakes a delete).
- Under DL-127 the same line applies to domain rows in the JSONB table (D020 note: "For those rows a MIGRATE STEP governs stored state"). `retire` then deletes order rows; `quarantine` says only "no REPLAY RUN", not what the live app reads. `migrate-fates.md` line 93 still says "[Verified] ... BEAML owns no persistence".
- Consequence: wrong outcome when the grammar is built: data loss or a live read with no defined result.
- Smallest text decision: the OWNER states "retire = delete after N days" or "retire = out of replay"; the fate concept adds the JSONB row case or limits fates to RESPONSE RECORDS until D020 closes.

### D6 · medium · observed · Owner requirements in `vertical-integration.md` contradict DL-102 and DL-121

- Quote pair: `vertical-integration.md:60`: "By default the compiler checks only the stored TYPE VERSIONS. A run of the migrations over stored values is a separate step per environment, started on request." Line 69: "A deploy blocks only when an environment stores a TYPE VERSION that the `migrate` chain cannot reach." DL-121: "The build compiles the generated decode code and calls it over every stored record". DL-102 and DL-122 block on values.
- The page is the source the plan workers read first (plan.md reads it). No supersede note.
- Consequence: agent trap. A planner takes "blocks only when" as the rule and classes a value block as new scope.
- Smallest text decision: a supersede note on both lines that names DL-102, DL-121, DL-122.

### D7 · medium · observed · Slice 6d builds the Migrate defaults before the OWNER answers

- Quote pair: DL-097: "A step stops at the first Migrate or Answer question and hands it back." D021 and D023: "Not built. RED and GREEN build A." D022 and D024 are Migrate with slice defaults.
- The defaults reserve a keyword (`on`), a TYPE name (`Rejected`) and a host name form (`ui_<event>`), and tests N1, N4, N10, N14 pin them.
- Consequence: rework when the OWNER picks B, C or D; pinned tests then fail for a reason that is no defect.
- Smallest text decision: the OWNER answers Q6D-1 to Q6D-4 before RED, or records that slice 6d may build defaults (a DL entry).

### D8 · medium · inferred · RESPONSE RECORD and EFFECT definitions now cover the ENTRY RECORD; ENTRY LINE and ENTRY RECORD are in use without a glossary row

- Quote pair: GLOSSARY RESPONSE RECORD: "One stored line of one EFFECT call". DL-128: "The entry is an EFFECT in the inbound direction". So an inbound call record is a RESPONSE RECORD by definition. DL-102, DL-122 and DL-125 are scoped on RESPONSE RECORD. D024 asks whether they cover ENTRY RECORDS.
- ENTRY LINE (26 uses) and ENTRY RECORD (24 uses) appear in the register before the glossary (D6B-141 defers them to the docs phase). The JSONB rows of DL-127 are a third stored-record kind with no term.
- OBSERVATORY is not in the glossary. DL-119 places it in "part 4"; DL-095 and `docs/index.html` make part 4 "Modules"; DL-108 uses "modules (roadmap part 4)".
- Consequence: D024 reads as answered (yes, by definition) or open, depending on the reader.
- Smallest text decision: glossary rows ENTRY LINE, ENTRY RECORD, OBSERVATORY; RESPONSE RECORD narrowed to "outbound EFFECT"; D018 and DL-119 say part 6.

### D9 · low · observed · `docs/index.html` shows built items as "Decided, next"

- Built in slice 6b but listed as "Decided, next": DL-092, DL-082 to DL-088, DL-086, DL-083 and `beaml fmt` (DL-081, DL-083), Unknown(String). "Grammar for the decided forms (slice 6a, in progress)" passed. DL-102, DL-121, DL-122 are not on the page.
- Consequence: the OWNER plans from a stale state (DL-095 made this page the progress view).
- Smallest text decision: one docs refresh after each DOCS phase.

## Checked and consistent

- DL-108 versus DL-119: DL-119 narrows "pure steps stay silent" to the default, explicitly.
- DL-106 versus DL-117: DL-117 replaces the `new(3)` example, explicitly; README line 1579 follows.
- DL-105 versus DL-124: no conflict; DL-124 narrows DL-122, not DL-105.
- DL-120 versus DL-128: D6B-129 forbids a constructor target; the entry decode calls constructors through DL-101 only.
- DL-122 lost-literal block: observed exit 1 with the DL-124 text and no stored String (`remap.beaml`).
- DL-102 checks over older TYPE VERSIONS: no false block, because D6B-39 forbids a chain on enum and constructor field TYPES (observed).
- Nested plain records in an EFFECT output: not decodable (observed `nest.beaml`), so `ctor_fields` top level only is no gap today.
- README step 6a, 11, 12, 12b, 13 claims: each names its ledger, test file and result directory; the code paths exist (`check_stored`, DL-120 reject at `main.rs:2275`, DL-122 text at `main.rs:3932`).
- DL-126 against the built forms: no declaration holds computation. One near miss: the ENTRY LINE repeats the input TYPE that the target fn declares (N10 checks that they agree). A form `on ui "place" -> place` would remove the second place; that belongs to D021.
- RED review gaps: `slice6b-struct-order` has no `red-review.md`; its review (N1) confirmed the RED. No step passed on an unreviewed RED.
- Devil's Advocate: used only at the slice 6a final review. Slice 6b has no final review yet, so no gap.
- Verify phase: no slice 6b step has `result.json` or `final-test-output.log`; steps 12 and 13 merge TEST and REVIEW. No outcome change found.
- Six owner bullets (vertical integration), evidence in EXPERIMENT 0004:
  - Diagnostics: yes (help lines). Compile time against Go: none.
  - Types at runtime: TYPE VERSION in records, host structs (DL-106). Plain records stay maps; `:redacted` replaces a String in replay (DL-115, accepted).
  - Typed errors: yes (`!`, DL-093, failure structs).
  - Modules from the file system: none.
  - Tests and evals: none in the language.
  - Typed traces: spans by reach (DL-119). Dashboards, alerts, flags: none.

## Open decisions status

| ID | Status | Where |
|---|---|---|
| D002 | open; text cites 0003 only. In 0004 the decode is generated (DL-101); host validation stays host (README 6a table). | decisions-to-be-made.md D002 |
| D003 | open; the planned ENTRY RECORD has no timestamp either (D6B-135). | D003, slice6d plan item 7 |
| D018 | partly answered. The inward-view bullet is closed by DL-128 ("closes the inward view of D018"); the register still says "not defined yet". Settings stay open. `migrate-fates.md:104` wrongly says "D018 is closed for spans". | DL-128, D018 |
| D019 | open | D019 |
| D020 | partly answered by DL-127 for the JSONB table; the register notes it. `migrate-fates.md:93` is stale. | DL-127, D020 |
| D021 | open; slice default A is planned to be built (see D7). | D021 |
| D022 | open | D022 |
| D023 | open | D023 |
| D024 | open; scope depends on the RESPONSE RECORD definition (D8); misses the input-TYPE-change case (D4). | D024 |
| D007 (closed by DL-122) | closing not met by code for a swapped literal (D1). | DL-122, main.rs:3851 |
| D013 (closed by DL-116) | DL-125 claims to lift it with a fate; that contradicts the DL-116 reason (D3). | DL-116, DL-125 |

## Limits

- About 40 minutes. Probes cover the static `--stored` pass only; the Elixir pass was not run.
- D4 and D5 rest on plan text and generated code, not on a built slice 6d.
- The redacted-fields work in progress was not read; its findings may change D3.
- Glossary check by CAPITAL-word count over the named pages only.

## Decisions

**Undo**
→ Probes in the scratch directory only.
→ Nine findings; style and wording dropped.
→ D9 kept at low.

**Repair**
→ D1 high statt medium, weil DL-122 wording names the case.
→ D4 merges three entry holes, weil one plan item.

## Round 2

By: Opus (RED TEAM, rt-design). Read: `rt-correctness.md` (C1 to C5). `rt-boundary.md` was not in the folder at start. New probe: `ctorswap.beaml` in the scratch directory.

### Item 1a: C2 (`--stored` ignores `status`): confirmed, observed

- No DL entry, README line or ledger decision limits the check to status 200 records. The text says the opposite: README line 1509, key `value`: "the same rule for every status (D6B-54, D6B-57)". So non-200 records hold a `value` by contract.
- README line 211: "`Replay.record/3` before the status check ... Case L2 needs one record for a 503". README line 151: a recorded 503 "replays as the 0003 `status_mismatch` atom".
- DL-121 (decision-log.md line 668) is a real claim: "The build compiles the generated decode code and calls it over every stored record; the check result equals the REPLAY RUN result." For a 503 record the REPLAY RUN stops at `status_mismatch` and never decodes; the check blocks. The claim fails.
- My D2 gets worse with C2: the DL-102 help line asks for a MIGRATE STEP for a record where nothing changed.

### Item 1b: C3 (DRIFT status ignores outcome classes): confirmed, with one nuance, observed

- Promise: slice6b-records-v2 `spec.md` line 35: "`repaired_all` reads this GEN replay and is `true`." D6B-96 (README line 1535) gives the per-row evidence shape only.
- Documented limit: the slice 6a review RC1 (`review.md` line 186 to 190) and README line 1561: "`run.py` ... Its `drift` step does not read `repaired_all`. A full-suite `pass` thus holds no 6a acceptance." Class outcomes "recorded, not asserted" is the slice 1 Undo D12 (`workflow/2026-11-06/notes.md` line 116). So "status ignores classes" is a documented design, not an unbacked claim.
- Unbacked part: the run `results/20261107T171545190446Z` (status `pass`, `repaired_all` true, `untyped_crash` for R, N, Q) entered the repository with the step 12 GREEN commit `237a4578`. No README line, register row, log entry or ledger names it (`rg` over the repository outside `results/`: only `rt-correctness.md`). A crash run lies silent in retained evidence.
- Verdict: C3 stands as high. The "pass" is a documented limit for `repaired_all`, and an unreported fact for the crash run.

### Item 2: "full suite 14 of 14" reads as slice 6 coverage: new finding D10, medium, observed

- Places that put "full suite 14 of 14" beside slice 6 results with no limit line:
  - `wiki/log.md:359` (step 6a), `wiki/log.md:363` (step 11), `wiki/log.md:371` (steps 12 and 12b): "[Verified] ... passed TEST and review: full suite ... 14 of 14, slice 6 files N of N".
  - `wiki/planning/research-and-development.md:46` to `:49`: register rows 6a, 11, 12/12b, 13 cite "[Full suite] ... 14 of 14" as the evidence of "Implemented, tests green".
  - `experiments/0004-generated-replay/README.md:1675` and `:1760` (steps 12, 12b, 13): result tables with "Full suite ... 14 of 14" and "172 of 172". The steps 12 and 13 limit lists have no RV6A-2 or N1 line.
  - Commit `050d6801`: "PASS, full 0004 suite 14 of 14, slice6 172 of 172".
- Places that state the limit: README `:1561` (6a, RV6A-2 and RC1) and `:1616` (step 11, N1) only.
- Not found: `docs/index.html` and `wiki/planning/roasting-rounds.md` do not cite the full suite.
- Consequence: false pass for a reader of the log or the register. The 172 slice 6 results have no retained `results/<ts>` directory (C4).
- Smallest text decision: one limit line beside each "14 of 14": "`run.py` runs no slice 6 file".

### Item 3: D1 against C1 (enum constructor swap): confirmed, nothing checks it, observed

- Probe: `slice6/decode-ctor/orders.beaml` with clause 11 `"ok", _ -> Pending` and clause 18 `"pending" -> Authorized` (swap). `--stored slice6/decode-ctor/stored.jsonl` gives exit 0, the same as the base source. Stored `ok` and `pending` records now replay with swapped variants.
- Cause: the lost-literal rule reads `literal_fields` only (`main.rs:3851`). An enum constructor without a failure TYPE makes no Elixir call (D6B-104). With a failure TYPE, C1 gives a run error for every record, which also hides the swap.
- So under an enum constructor nothing checks a swap or a lost mapping today: silent pass without `!`, a run error with `!`. D1 widens to both enum forms. Severity stays high.

### Item 4: D7 (Migrate defaults built before the OWNER answers): stands, observed

- Search for "slice default", "default A", "builds A", "plan default" over the decision log, AGENTS.md, the skill and the register. Hits: the slice 6d register rows only (D021 to D024), DL-102 line 522 ("plan default D6B-38"), DL-104 line 541 ("The plan default D6B-43 holds").
- DL-104 and DL-102 show that plans carry defaults and that the OWNER decides them later. No entry allows building a Migrate default before the answer.
- Against it: DL-097 ("A step stops at the first Migrate or Answer question"), DL-041 ("stop only at Migrate").
- D7 does not drop. Severity stays medium: the D021 trigger "before slice 6d closes" limits the damage to rework.

### Severity changes

- D1: stays high; scope now includes enum constructors (item 3).
- D2: stays high; C2 adds a second false DL-102 block with the same dead-end help line.
- D7: stays medium.
- D10: new, medium (item 2).

### Item 5: B6 (DL-032 against DL-124): confirmed, observed

- DL-032 (decision-log.md line 154 to 156): "returns counts, not record identities. Because: a record identity can link to a person." Its header: "(proposal, not yet an OWNER decision)".
- DL-124 (line 690): "names ... the record count and the record source lines (`S:N`)". Ledger `slice6b-stored-elixir/decisions.md:101`: "one `record source: S:N (line N)` line per record".
- No entry reconciles them. DL-124 says "DL-032 gets no exception" and reads DL-032 as "no stored value" only.
- Under DL-032's own wording a source line is an identity: `S:N` points to exactly one record, so it links that record, and the fact that it failed, to whoever owns it.
- The contradiction is also inside one page: `migrate-fates.md:77` "Source lines `S:N` of the records, as in DL-124" next to `:78` "never a record identity in the report (DL-032, DL-124)".
- Extra point: DL-122, DL-124 and the fate concept rest on DL-032, which is still a proposal. The OWNER has not decided the rule they cite.

### Item 6: B7 (stale `docs/index.html`): confirmed for the text side; B7 and D9 are one finding

- DL-095 (line 466) makes the page a progress view: "Each part shows its state (verified, decided, concept) and its next steps. The roadmap lives in README.md and on a small GitHub Pages site."
- No DL entry, skill line or DOCS ledger requires a page refresh per DOCS phase (`rg docs/index.html` over `workflow/` and `wiki/` finds only the RED TEAM files). The page has a status role and no update rule.
- I did not run the sample source compile probe myself; I accept B7's observed probe.
- D9 is a subset of B7. Merge into B7. Severity medium (B7), because the page also shows a sample that does not compile.
