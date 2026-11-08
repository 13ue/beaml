---
id: planning-decision-log
kind: planning
status: active
updated: 2026-11-08
---

# Decision log

Append-only record of closed decisions: what was chosen, over what, and why.
Open decisions stay in [decisions to be made](decisions-to-be-made.md) until the OWNER closes them.

**Rules**

- One entry per decision. Never edit an old entry; add a new entry that supersedes it and link back.
- Each entry: ID, date, Decision4 class, question, options, choice, reason, trigger, link to the detail.
- Keep entries short. Details live in the linked document.
- Controlled English. No chat quotes. Roles, not names.
- When this file passes about 800 lines, move closed months to `decision-log-YYYY-MM.md` and link them here.

**Classes** (see Decision4): Undo = a revert fixes it. Repair = work inside the team. Migrate = others must change. Answer = the outcome leaves the team and cannot be unmade.

## 2026-11-06

Entries DL-001 to DL-035 were written after the fact on 2026-11-06 from the session ledgers, READMEs and commits of that day. Their order follows the work, not exact times.

### Working process

**DL-001 · Repair · Branches**
→ Question: work on feature branches or on `main`?
→ Chose: commit directly on `main`. Over: feature branches.
→ Because: one OWNER works alone; branches only added a merge step and a misleading diff view.

**DL-002 · Repair · Commit rhythm**
→ Chose: commit at the end of every phase (plan, RED, GREEN, TEST, review, docs); workers never commit. Over: commit at the end of a task.
→ Because: a clean tree between phases; a worker's half-written files never enter a commit.

**DL-003 · Undo · Overview pages**
→ Chose: local HTML pages in the repo, served by a local HTTP server, following the system color scheme. Over: published online pages.
→ Because: the OWNER wants nothing online; `file://` pages render light only.

**DL-004 · Repair · RED review**
→ Chose: the main agent reviews every RED result and a fresh-context agent checks the review. Over: the OWNER reviews RED.
→ Because: RED review is mechanical work; the OWNER decides only what needs the OWNER.

**DL-005 · Repair · Decision handoff**
→ Chose: Decision4 classes (Undo, Repair, Migrate, Answer); Undo and Repair run through, Migrate and Answer stop for the OWNER. Over: ask the OWNER on every decision.
→ Because: pace without silent decisions; every answer ends with a decisions block.
→ Source: Decision4 1.0.1, Habitat Thinking, CC BY 4.0.

**DL-006 · Repair · Devil's Advocate checkpoints** (superseded by DL-007)
→ Chose: Devil's Advocate at plan, RED review and final review.

**DL-007 · Repair · Devil's Advocate only at the final review**
→ Chose: Devil's Advocate only at the final review of a slice, plus on OWNER request in concept phases. Plan and RED get a normal fresh-agent check. Over: DL-006.
→ Because: too many review rounds; the one result that changed the direction came from the final review.

**DL-008 · Undo · Code display**
→ Chose: BEAML code shown syntax-highlighted in the chat, with the project grammar. New forms are colored by hand until the grammar knows them.

**DL-009 · Undo · Repo text**
→ Chose: OWNER statements enter the repo as distilled controlled English. Over: chat text or German.

**DL-010 · Undo · This log**
→ Chose: one append-only decision log with links to details. Over: decisions spread over wiki pages, READMEs, ledgers and commits only.
→ Because: the OWNER wants to trace later which decision was made when and why.

### EXPERIMENT 0003

**DL-011 · Migrate · Replay outside the router**
→ Chose: the REPLAY RUN is a separate runner that shares the generated decode. Replay errors are typed tool errors; the body digest is checked. Over: a replay branch in the live router with HTTP 502.
→ Because: replay is a debug tool, not an HTTP path.
→ Detail: [EXPERIMENT 0003](../../experiments/0003-source-linked-replay/README.md).

### EXPERIMENT 0004 slice 1: language forms

**DL-012 · Migrate · Applications in BEAML**
→ Chose: applications are written in BEAML; only the UI layer (LiveView) stays in Elixir. BEAML does HTTP itself; the decode comes from the TYPE.

**DL-013 · Migrate · `effect` keyword**
→ Chose: one keyword, `effect`, for everything that leaves a function. The formatter aligns arrows and `=` of consecutive `effect` lines.

**DL-014 · Migrate · Pipe and `with`**
→ Chose: the pipe `|>` and `with ... do ... else ... end` are part of the language.

**DL-015 · Migrate · Failure TYPES**
→ Chose: `!` failure TYPES on effects and functions, with propagation. The compiler checks that `else` is exhaustive and that each pipe failure appears in the function's `!` list. The Elixir output is a `name` / `name!` pair with typed struct errors.

**DL-016 · Repair · Decode strict** (superseded by DL-017)
→ Chose: reject unknown response keys.

**DL-017 · Repair · Decode tolerant with a hint**
→ Chose: accept unknown keys and record them as `unknown_keys`. Over: DL-016.
→ Because: a producer may add fields; BAML v1 does the same (flags extra keys, strict path optional).

**DL-018 · Repair · Comparison rules**
→ Chose: a crash without a typed reason counts as a missed DRIFT; no kill switch; the LIB arm runs in parallel as the strongest fair library, frozen before GEN is judged.

**DL-019 · Repair · Slice 1 verdict**
→ Chose: the slice 1 claim is rejected under its own rule (manual change sites GEN 0 = LIB 0). The rule is superseded for slice 2.
→ Because: a library with no TYPE facts needs no edit after a field change, so the count cannot favor GEN. The only arm difference came from the old transport, not from the TYPE.
→ Trigger: final review (Devil's Advocate). Detail: [0004 README, slice 1 verdict](../../experiments/0004-generated-replay/README.md).

### Goal and concept

**DL-020 · Migrate · Vertical integration is the goal**
→ Chose: BEAML owns the path from source to production (types, typed errors, tests, evals, traces, dashboards, alerts, flags) so that agents make fewer errors. Over: measure only hand edits against a library.
→ Detail: [vertical integration](../concepts/vertical-integration.md).

**DL-021 · Migrate · Breaking TYPE changes fail at compile time**
→ Chose: the compiler knows the TYPE VERSIONS of stored records; a breaking change fails the build.

**DL-022 · Migrate · Migration syntax**
→ Question: how to declare a rename and later changes?
→ Options: alias on the field; separate `rename` line; versioned TYPES with `@n`; a `migrate` block per version step.
→ Chose: the `interface` is always the newest version; history is a chain `migrate Payment 1 -> 2 { rename status -> state }` with `rename`, `add` and `drop`.
→ Because: one form for all changes; old versions follow from the chain, so no TYPE is declared twice.

**DL-023 · Repair · `drop` names the TYPE**
→ Chose: `drop amount_cents: Int`. Over: `drop amount_cents`.
→ Because: without the TYPE, old versions are not fully typed and old records cannot be checked.

**DL-024 · Migrate · V1 blocks on every migration failure**
→ Chose: in V1 any migration failure in any environment blocks. Lower-priority environments come later.

**DL-025 · Migrate · Totality**
→ Chose: no crash; every value is handled. Only effects carry `!`. Termination is not guaranteed (BEAM processes loop by design).

**DL-026 · Repair · Fallbacks with acceptance** (superseded by DL-028)
→ Chose: marked fallbacks; hits counted per environment; a human accepts known records; a new hit blocks again, also at deploy.
→ Trigger: Devil's Advocate round 1 (a fully total chain makes the build check blind).

**DL-027 · Repair · Compiler checks TYPE VERSIONS only by default**
→ Chose: the default build reads only stored TYPE VERSIONS; a run over stored values is a separate step on request. Over: every build reads production values.
→ Because: privacy, build time, and a hotfix that one bad record would block.
→ Trigger: Devil's Advocate round 1.

**DL-028 · Migrate · No guessing; Unknown keeps the value**
→ Chose: no fallback that invents a value. Closed TYPES are matched exhaustively. Open TYPES end with a branch that keeps the original value (`other -> Unknown(other)`), and every user of that TYPE must handle `Unknown`. `add` with a constant stays allowed as a statement about old data. Over: DL-026.
→ Because: a guess that never fails is invisible, and an agent that may accept its own hits turns the check into a formality.
→ Trigger: Devil's Advocate round 2.

**DL-029 · Migrate · PII in the compiler**
→ Chose: PII is declared on `interface` fields; the compiler keeps PII out of logs, traces and reports, including values derived from PII by a branch. Implicit flow is a target, not the next slice.
→ Because: privacy is the highest goal.

**DL-030 · Migrate · Division**
→ Chose: offer both forms: a `DivByZero` failure TYPE, or a non-zero integer TYPE for the divisor.
→ Because: integer division by zero raises on the BEAM (verified), which breaks "no crash".

**DL-031 · Migrate · What blocks a deploy**
→ Chose: a deploy blocks only when an environment stores a TYPE VERSION with no path through the chain to the newest version. `Unknown` counts are reported, not blocking. The deploy repeats the check, because data can change after the build.

**DL-032 · Repair · Value report shows counts only** (proposal, not yet an OWNER decision)
→ Chose: the value run executes inside each environment and returns counts, not record identities.
→ Because: a record identity can link to a person.

### EXPERIMENT 0004 slice 2

**DL-033 · Repair · Slice 2 scope**
→ Chose: only `rename`. A rename without a `migrate` line is a compile error; with it, old records replay correctly. Over: also `add`, `drop`, `Unknown`, PII.
→ Because: the smallest slice that tests the deploy rule (DL-031).

**DL-034 · Repair · Source of stored TYPE VERSIONS in slice 2**
→ Chose: the compiler reads a RECORD SNAPSHOT (`--stored`); each RESPONSE RECORD carries its TYPE version and fingerprint. Over: a lock file. A missing `--stored` input is an error, not an empty store.
→ Because: one source of truth; an unknown store is not empty. The production source stays open (O5).

**DL-035 · Repair · Adding a field without a migration**
→ Chose: in slice 2, adding a field without `migrate ... { add ... }` is a compile error.
→ Because: it follows from DL-031; stored records would have no path.

**DL-036 · Repair · A misspelled rename is a path error**
→ Chose: a `rename` whose old field is in no derived version fails through the path check, and the message names both fields. Over: a rule "old field in no stored version".
→ Because: with an empty RECORD SNAPSHOT that rule would reject every chain.
→ Detail: 0004 notes.md, "Slice 2 RED", S4.

**DL-037 · Repair · The fingerprint decides**
→ Chose: when the `fields` of a stored record and its fingerprint disagree, the fingerprint decides; `fields` serve only the message. Over: trust `fields`.
→ Because: the plan compares fingerprints; a compiler that never computes them must not pass.
→ Trigger: fresh RED check of slice 2. Detail: notes.md, "Slice 2 RED repair", S12.

**DL-038 · Repair · Overlay change table gains three rows**
→ Chose: add three rows to the change table of `overlay_diff_test.py` for the `--stored` argument in three GEN copies of 0003 tests. Over: leave the copies unchanged.
→ Because: the copies gain only a harness argument, and the table must list every changed line. Check logic unchanged.

**DL-039 · Repair · No compiler dependencies**
→ Chose: the compiler has its own SHA-256 and JSON reader. Over: `sha2` and `serde_json`.
→ Because: the compiler builds offline with no dependencies. Tests recompute fingerprints with a standard library.

**DL-040 · Repair · A stored record without a reader fails the build**
→ Chose: a stored record for an operation that has no `effect` in the source fails the build. Over: ignore it.
→ Because: no runner can read it, which is a missing path in a wider sense. Under review at the slice 2 final review.

**DL-043 · Repair · Decode by TYPE VERSION** (supersedes the decode form of slice 2 GREEN)
→ Chose: replay applies the `rename` steps from the record's version to the newest; a live body gets none. Over: read an old name when the current name is missing; or forbid name reuse in a chain.
→ Because: the fallback form swapped values for a rotation (`a -> c`, `b -> a`, `c -> b`) and rejected live bodies after a reuse. Records carry their version, and name reuse is legal.
→ Trigger: slice 2 final review (Devil's Advocate), BLOCK. Detail: 0004 notes.md, "Slice 2 final review repair".

### EXPERIMENT 0004 slice 3 plan

**DL-044 · Repair · Slice 3 limits to the existing TYPES**
→ Chose: `add` takes a String field with a string literal; `drop` takes String or a declared TYPE. Over: `Int`, record or enum literals now.
→ Because: the compiler knows only String and declared TYPES. `drop amount_cents: Int` from the concept sketch waits for an `Int` TYPE.

**DL-045 · Repair · `add` and `drop` of the same field across steps are legal**
→ Chose: allow `add` then `drop`, and `drop` then `add` (name reuse). Over: forbid it.
→ Because: records of the middle version can exist; decode by version (DL-043) handles reuse.

**DL-046 · Repair · Dropped values are checked against their TYPE**
→ Chose: replay of an old record checks the dropped value against the TYPE named in `drop`. Over: remove it unchecked.
→ Because: DL-023 says old versions are fully typed.

**DL-047 · Undo · A value in the old body wins over the `add` constant**
→ Chose: if an old record already holds the added field, its value wins over the constant. Same rule as C12 (current name wins).
→ Detail: 0004 README, "Slice 3".

**DL-048 · Repair · The `add` constant always wins in a replay** (supersedes DL-047; DL-047 was wrongly classed Undo)
→ Chose: in a REPLAY RUN, `add` always puts the constant; a body key with the same name goes into `unknown_keys`. A `rename` removes the old key from the working body. Over: DL-047 (a body value wins).
→ Because: DL-047 read a stray key as typed data, which is decode by key presence (rejected in DL-043), and it overrode the constant, which DL-028 makes a statement about all old records.
→ Trigger: fresh check of the slice 3 plan.

**DL-049 · Repair · `drop` takes String only in slice 3** (narrows DL-044; DL-046 then checks String values)
→ Chose: `drop` accepts String fields only; any other TYPE is a source error with a help line. Over: `drop` with a declared TYPE.
→ Because: the decode checks String values only, so a declared-TYPE drop could not be replayed honestly.
→ Trigger: fresh check of the slice 3 plan.

**DL-050 · Repair · Chain checks run before the effect checks**
→ Chose: the consistency checks of the MIGRATE CHAIN (K1–K12) run in the version derivation, before the effect checks. Over: drop K2 and K4.
→ Because: the effect check rejects non-String fields first, which made K2 and K4 unreachable.

### EXPERIMENT 0004 slice 3 GREEN

**DL-051 · Repair · UTF-8 locale in the test VM**
→ Chose: `orders_env` in `arms_test.py` sets `LANG` and `LC_ALL` to UTF-8. Over: an ASCII-escaped report.
→ Because: the generated code was right; the test VM without a locale wrote Latin-1. The worker raised it as Migrate; the main agent lowered it to Repair, because only the own test harness changes.

**DL-052 · Repair · Fingerprint checked at run time**
→ Chose: a REPLAY RUN checks the record fingerprint against its version. Over: trust the version number only.
→ Because: the version picks the steps, the fingerprint validates (DL-037, DL-043).

**DL-053 · Repair · `unknown_keys` lists stored body keys only**
→ Chose: `unknown_keys` holds keys of the stored body that the decode does not read. Over: every key a step removes.
→ Because: the README defines the hint on body keys.

**DL-054 · Repair · Type the stored body by its version before any step** (supersedes C12 "current name wins" and refines DL-048)
→ Chose: a REPLAY RUN first checks the stored body against its own TYPE VERSION: every field of that version is type-checked, and every other key goes to `unknown_keys`. Only then do the steps run, on typed data. Over: run the steps on the raw body and let the current name win (C12); or let a key made by a step beat a stray key.
→ Because: on the raw body a stray key could win over an `add` constant that a later `rename` moves, without a trace, and old fields were not fully typed (DL-023). This is decode by version (DL-043) carried through.
→ Trigger: slice 3 final review (Devil's Advocate), BLOCK.

### Deleted effects and dead code

**DL-055 · Migrate · A deleted effect with stored records**
→ Question: an `effect` leaves the source, but an environment still stores its records. Block or warn?
→ Options: block; warn; block until the effect is retired explicitly.
→ Chose: block until `retire <effect> keep <duration>` is declared. Retired records stay stored and are not replayable; after the duration they are deleted. `keep 0 days` deletes at deploy; the deploy report states the deletion loudly, because it cannot be undone. Over: a warning only.
→ Because: nothing becomes unreadable without an explicit statement in the source, the same pattern as `add` with a constant. A retention limit serves privacy (DL-029).
→ Supersedes the GREEN rule in DL-040, which blocked with no way out.

**DL-056 · Migrate · Dead code warnings and automatic removal**
→ Chose: the compiler warns when a `retire` line or a `migrate` step is no longer needed, because no environment stores records of that effect or version. A command removes such lines on request. A record that appears again later (for example from a backup) blocks the build again.
→ Because: the chain must not grow forever, and the removal must stay safe.

### EXPERIMENT 0004 slice 4 plan

**DL-057 · Repair · Slice 4 forms**
→ Chose: `retire <operation> keep <n> days` (`n` an unsigned integer, unit `days` only). `--remove-dead` runs after `--stored`, prints a diff, rechecks and writes atomically. Dead-line warnings go to stderr with exit 0. RETIRED RECORDS skip the path check and keep no step alive. Over: more units, a separate cleanup tool, warnings as errors.
→ Because: the smallest form that tests DL-055 and DL-056. Detail: 0004 README, "Slice 4".

**DL-058 · Repair · The last `migrate` step is never dead** (until O6 is decided)
→ Chose: never warn on the last step. Over: let the version fall back to 1.
→ Because: the last step carries the newest version number; removing it would renumber stored records.

### Redacted fields

**DL-059 · Migrate · `redacted` marks PII on a field**
→ Chose: the word `redacted` before the field TYPE: `interface Payment { order_id: String  card_holder: redacted String }`. Over: `pii` after the TYPE.
→ Because: OWNER choice. The word says what the compiler does with the value (DL-029).

### Declarations

**DL-060 · Migrate · `type` declares variants and records** (closes D001)
→ Question: keep `enum` (and `interface` for records), or use `type`?
→ Options: `enum` for variants and `interface` for records (Rust, Swift, Scala 3 style); `type` for both (Gleam, OCaml, Elm style).
→ Chose: `type` for variants and records together. The exact record and variant shapes under `type` are the next question.
→ Context: in most non-ML languages `type` means an alias; in the ML family and in Gleam (a BEAM language) it declares data. The comparison came from training knowledge and was not checked against documentation.

**DL-061 · Migrate · `type` for records, `enum` for variants** (supersedes DL-060)
→ Chose: `type` declares a record (replaces `interface`); `enum` keeps declaring variants. `interface` stays free for behaviour contracts later. Over: DL-060 (`type` for both).
→ Because: OWNER choice after the question of what `interface` and contracts should mean. DL-060 read a two-part option as one answer; the main agent should have asked.

**DL-062 · Migrate · `Unknown` is a declared variant**
→ Question: how does an `enum` keep a value it does not know?
→ Options: U1, declare `Unknown(String)` as a normal variant; U2, mark the enum open and let the compiler add `Unknown` (forms `enum E from String { A = "a" }` and `enum E<String> { A }`).
→ Chose: U1. No literals inside an `enum`; the mapping from a String to a variant is written as function clauses. The compiler checks that the last clause over an open TYPE keeps the original value. Over: U2.
→ Because: OWNER rejected the `from String` form and literals in an `enum`; `<String>` would read as a generic argument once generics arrive.

**DL-063 · Repair · Slice 4 claim needs a RECORD SNAPSHOT**
→ Chose: the slice 4 claim holds only with `--stored`; harness check H1 tests that every GEN build passes it. Over: require `--stored` for every source.
→ Because: `payments.beaml` (no effect) must stay byte-identical, and the compiler cannot tell a source without effects from one whose last effect was deleted. The deploy check (DL-031) is the final guard.

**DL-064 · Repair · `--remove-dead` output contract**
→ Chose: the diff keeps CRLF line ends, the count is the number of removed declarations, the event field is `removed`, and the usage text names `--remove-dead`.
→ Detail: 0004 notes.md, "Slice 4 plan repair and RED", S4-4.

**DL-065 · Migrate · Where the last branch must keep the value**
→ Question: does "the last branch over an open TYPE keeps the original value" hold everywhere?
→ Options: strict, in every match over an open TYPE; targeted, only where data comes from outside or from the past.
→ Chose: targeted. The rule holds in `migrate` steps and in the decode of data from outside (effect responses, stored records). Ordinary code may use a deliberate default (`fn greeting other: String -> String = "Hello"`).
→ Because: a guess is dangerous where data is stored or comes from another system; in ordinary code a default is a design choice.

### EXPERIMENT 0004 slice 4 GREEN

**DL-066 · Repair · Retired check after `select`**
→ Chose: `Replay.run/3` checks for a RETIRED RECORD with a `with` step right after `select/2`. Over: a separate first clause of `run/3`.
→ Because: the record is known only after `select`. Commits `prepare/1` to run before the reject.

**DL-067 · Repair · `--remove-dead` diff is a port of difflib**
→ Chose: a faithful port of Python difflib. Over: a direct deletion diff. Because: the contract is byte equality with difflib (150 random layouts, LF and CRLF, matched).

**DL-068 · Repair · Live operation keeps the `payments` namespace in random-name tests**
→ Chose: fix the test harness. Over: a new port-key rule in the compiler.
→ Because: the generated EFFECT reads `<namespace>_port`, and the harness sets only `payments_port`; a new port rule would be a language decision.

**DL-069 · Repair · Harden `--remove-dead` after the slice 4 final review**
→ Chose: (1) `--remove-dead` refuses to remove a step or retire line when the snapshot holds no record of that TYPE or operation, unless the flag `--assume-complete` is given; (2) resolve symlinks before the atomic rename and refuse a source that is not writable; (3) a unit test forces the recheck failure and asserts that nothing is written. Over: note the risks only.
→ Because: an agent with an empty or partial snapshot could cut a chain that production still needs; the review saw a symlink replaced and a read-only file rewritten.
→ Trigger: slice 4 final review (Devil's Advocate), PASS WITH NOTES.

**DL-070 · Migrate · The version number sits on the type** (answers O6; will supersede DL-058)
→ Question: where does the newest TYPE VERSION number live when dead `migrate` steps are removed?
→ Options: (a) the last step is never dead; (b) an anchor line `migrate Payment 3`; (c) the version on the type line; (d1) implicit in the stored records; (d2) a compiler-written lock file.
→ Chose: (c) in the form `type Payment v3 { … }`. Version numbers only grow; dead steps may be removed, and `--remove-dead` writes the number onto the type line.
→ Because: one visible source of truth in the code, reproducible and reviewable. Prior art (Protobuf, Confluent, Lamdera, Django, Flyway, Kubernetes) never resets a counter; see `raw/research/type-versioning-prior-art-2026-11-06.md`.
→ Open detail: when the `vN` mark is required, and whether `migrate` lines use `v1 -> v2`.

**DL-071 · Migrate · The `vN` mark appears only after a squash**
→ Chose: while the MIGRATE CHAIN is complete, the newest version follows from the chain and the type line has no mark. `--remove-dead` writes `vN` onto the type line when it removes steps. If both a mark and a chain exist, they must agree. Over: the mark required from version 2 on.
→ Because: OWNER choice; less to write while the history is in the source.

**DL-072 · Migrate · `v` on every version number**
→ Chose: `migrate Payment v3 -> v4 { … }` and `type Payment v3 { … }`. Over: plain numbers in `migrate` lines.
→ Because: one spelling for a version everywhere; a search for `v3` finds every use. Fixtures and tests of slices 2–4 change mechanically.

### Tooling

**DL-073 · Undo · Grammar covers the decided forms**
→ Chose: the Tree-sitter grammar parses and highlights `effect`, `|>`, `!` lists, `type Name [vN]`, `interface` (kept until slice 5), `enum`, `redacted`, `migrate` (plain and `v` numbers), `retire … keep … days`. The grammar is more tolerant than the compiler (optional commas in `migrate`; `with` clause shapes are a guess because no source uses them yet). Version numbers use the constructor colour.
→ Evidence: 0 ERROR nodes in 28 real sources; corpus and highlight tests pass.

### EXPERIMENT 0004 slice 5 plan (OWNER away; Undo-class only)

**DL-074 · Undo · `interface` and plain numbers become errors with help lines**
→ Chose: `interface` is a hard error with a help line naming `type`; a plain number in `migrate` is an error with a help line naming `v`. Over: a transition alias.
→ Because: DL-061 keeps `interface` free for behaviour contracts; an alias would occupy it. DL-072 fixes the `v` spelling.

**DL-075 · Undo · Version spelling and the squash rewrite**
→ Chose: a version is `v` plus digits (no leading zero, no `v0`, fits in u32). Stored `type.version` stays a JSON integer. `--remove-dead` inserts ` v<n>` right after the TYPE name and changes no other byte; a recheck guards against a version reset. Compiler messages write `v` and `type`.

**DL-076 · Undo · Re-snapshot one line of the `payments.beaml` output**
→ Chose: accept one changed line (declaration offsets move by 10 bytes because `interface` becomes `type`); a check proves no other line changes. Over: keep `interface` in that source.
→ Because: DL-061 replaces `interface` everywhere.

### EXPERIMENT 0004 slice 5 GREEN (OWNER away; Undo-class only)

**DL-077 · Undo · O7 provisional default: any agreeing mark is legal**
→ Chose: until the OWNER answers O7, one function (`mark_form_allowed`, marked PENDING OWNER O7) allows any VERSION MARK that agrees with the chain and a chain without a mark (option a). The tests for option (b) stay skipped.
→ Because: the most permissive form forbids nothing the OWNER may want; one function changes the rule.

**DL-078 · Undo · Two slice 5 RED test faults fixed by the main agent**
→ Chose: the B5 fixture guard compares with the new syntax; F23 clears the action log per layout. Over: leave the tests red.
→ Detail: 0004 notes.md, "Slice 5 GREEN follow-up (test faults)".

**DL-079 · Undo · Slice 5 review notes closed**
→ Chose: the N1 version check runs before the TYPE name check (no backwards help line); the grammar version regex is `v[1-9][0-9]*` with ERROR corpus tests for `interface` and plain numbers; `run.py` runs the slice 2–5 test files; the rewrite audit compares the GREEN commit `bdc79ecc` with its base instead of the working tree.
→ Because: slice 5 final review (Devil's Advocate), PASS WITH NOTES. The audit scope was raised as Migrate by a worker and lowered to Undo by the main agent: only our own test changes.

### Decisions after the unattended run

**DL-080 · Migrate · O7: any VERSION MARK that agrees with the chain is legal** (closes O7; DL-077 becomes final)
→ Question: when may `type T vN` appear?
→ Options: (a) any mark that agrees with the chain, and a chain without a mark; (b) a mark only after a squash; (c) like (b), and a chain above v1 must have a mark.
→ Chose: (a). Over: (b) and (c).
→ Because: OWNER choice. The compiler checks only agreement (M1); `--remove-dead` still writes the mark when it removes steps (DL-071).

**DL-081 · Migrate · `beaml fmt` writes the default mark form (b)**
→ Chose: the compiler accepts any agreeing mark (DL-080); `beaml fmt` normalizes to option (b): it removes a mark when the chain is complete from v1 or when there is no chain, and writes the mark when the chain starts above v1. No warning. Over: a compiler warning.
→ Because: OWNER choice; the formatter keeps one form without blocking work. `beaml fmt` does not exist yet; it also owns the alignment rule of DL-013.

**DL-082 · Migrate · String to variant: enum literals or an enum constructor** (narrows DL-062: literals in an `enum` become legal)
→ Question: how does the decode of outside data map a String to an `enum` variant?
→ Options: by signature (the one `fn String -> E`); C2, by name (a function named like the enum, a constructor); C3, named on the field; L, literals in the enum.
→ Chose: both L and C2. L: `enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }` for a 1:1 mapping. C2: a constructor function named like the enum, with any logic and several inputs, e.g. `fn PaymentState "ok", _ -> PaymentState = Authorized`. The last clause over outside data keeps the value (DL-065).
→ Because: OWNER choice. L is the short form for the simple case; the constructor covers several spellings, several fields and variants with a payload.
→ Open: how a constructor with several inputs gets its body keys; what happens when an enum has both literals and a constructor.

**DL-083 · Migrate · `beaml fmt` aligns clause columns** (extends DL-013)
→ Chose: for consecutive clauses of one function, `beaml fmt` aligns every argument column, the `->` and the `=`, so the clauses read as a table. Same rule as the aligned `effect` lines (DL-013).
→ Because: OWNER choice; the cases of a constructor or a match can be compared line by line.

**DL-084 · Migrate · Constructor inputs come from its parameter names (K1)**
→ Question: how does the decode know which body keys a constructor with several inputs gets?
→ Options: K1, the parameter names of a signature line are the body keys; K2, the field names the keys (`state: PaymentState(status, decline_reason)`).
→ Chose: K1. A signature line `fn PaymentState status: String, decline_reason: String -> PaymentState` names the keys; the clauses below match by position. Several signatures of one constructor are allowed (polymorphism).
→ Because: OWNER choice; the `type` stays plain.
→ Open: how the decode picks one of several signatures; lists as an external return TYPE (later).

**DL-085 · Migrate · The first matching signature wins**
→ Question: a constructor has several signatures; which one does the decode use?
→ Options: S1, the one whose keys are all in the body (longest first); S2, one per TYPE VERSION; S3, exactly one may match, else a compile error.
→ Chose: top to bottom, the first signature that matches is used, like Elixir function clauses. Over: S1 longest match, S2, S3.
→ Because: OWNER choice; the order in the source is the rule.
→ Note: a signature below one whose keys are a subset of it can never match; the compiler can report it, as Elixir reports a clause that cannot match.

**DL-086 · Migrate · Pipe in any expression, constructors as steps** (extends DL-014)
→ Chose: the pipe `|>` is allowed in any expression, not only as a whole body. Enum constructors and variants may be pipe steps: `reason |> DeclineReason |> Declined`. The TYPE check per step and the `!` rule stay.
→ Because: OWNER choice; a value reads left to right instead of inside out.

**DL-087 · Migrate · An unreachable signature or clause is a compile error**
→ Chose: a constructor signature or a function clause that an earlier one always matches first does not compile. Over: a warning.
→ Because: OWNER choice; with "first match wins" (DL-085) such a line is dead and misleading.

**DL-088 · Migrate · One decode path per enum**
→ Chose: an `enum` with literals and a constructor function at the same time is a compile error. Over: the constructor wins; literals first, then the constructor.
→ Because: OWNER choice; exactly one way to build each enum from outside data.

**DL-089 · Migrate · Effects get redacted fields only when they name them (R3)**
→ Question: a `redacted` field must reach Payments but not an audit queue. How?
→ Options: R1, every effect may carry it, only telemetry is cleaned; R2, an effect must declare `carries redacted`, else a compile error; R3, the compiler strips redacted fields from every effect input unless the effect names the field.
→ Chose: R3, in the form `effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") with card_holder`. Spans, logs and records never hold the value (DL-029).
→ Because: OWNER choice; the safe default needs no extra work, and every release of a redacted value is visible at the effect.

**DL-090 · Migrate · User-defined wrapper types with a constructor (T1)** (withdrawn by DL-091: recorded too early)
→ Question: how is a type such as `NonZeroInt` defined?
→ Options: T1, a wrapper type `type NonZeroInt(Int)` with hand-written constructor clauses; T2, a condition in the type (`where self != 0`) and a generated constructor; plus the earlier N2, a condition on `Int` at the parameter.
→ Chose: T1. A wrapper is a real type: an `Int` is not a `NonZeroInt`; the constructor is the only way in and may fail with a declared failure TYPE. Over: T2 and N2.
→ Because: OWNER choice; the same form as the enum constructor (DL-082), any check logic is possible.

**DL-091 · Undo · DL-090 withdrawn**
→ The main agent recorded T1 as a decision after the OWNER said only that T1 looks good. The OWNER wants to walk through the whole example first. T1 is the leading option; the decision is open.

**DL-092 · Migrate · One type form; a constructor makes itself the only way in** (replaces the T1/T2 question of DL-090)
→ Question: do wrapper types need a form of their own (`type NonZeroInt(Int)`)?
→ Options: a separate wrapper form with a constructor (T1); a condition in the type (T2); one form `type X { … }` for every type, with an optional constructor.
→ Chose: one form. `type NonZeroInt { value: Int }` is a record; a constructor function named like the type (`fn NonZeroInt …`) is optional. When a type has a constructor, the record literal `NonZeroInt { … }` is allowed only inside the constructor's own clauses; everywhere else the constructor is the only way in. The constructor may fail with a failure TYPE after `!`.
→ Because: OWNER choice; one syntax, and every type (records, wrappers, enums via DL-082) gets the same checked-constructor pattern.
→ Clarified: `!` marks a position in a signature, not a kind of type. Any type can stand on the failure side.

**DL-093 · Migrate · Success and failure types never overlap (E1)**
→ Question: how does a clause tell success from failure when both sides could have the same TYPE?
→ Options: E1, the TYPE decides and the same TYPE on both sides is forbidden; E2, a failure is always marked with `fail`; both.
→ Chose: E1. No `fail` keyword. The success TYPE must not appear in the failure list: `-> String ! String` and `-> String ! Int | String` are compile errors; `-> String ! Int` is legal. The help line names the overlapping TYPE and suggests a TYPE of its own for the failure or no `!`.
→ Because: OWNER reasoning: a value of the same TYPE as the result is no failure, only another result; a real failure means something else and deserves its own TYPE. Generic functions (`-> T ! E`) need the same check at the call; that is for later.

**DL-094 · Migrate · Production TYPE VERSIONS come from a live query first (O5)**
→ Question: where does the compiler get the stored TYPE VERSIONS of a production store?
→ Options: P1, an export file per environment; P2, a live query of the deployed BEAM nodes; P3, a type registry service that collects all environments.
→ Chose: all three over time, in this order. Start with P2. P2 can grow into P3 later, for optimization. Exports (P1) follow after that. A later option: a dev machine registers itself, and production sends it a notice when its stored TYPE VERSIONS change.
→ Because: OWNER choice; P2 is the simplest start and always current. The other forms are optimizations of the same data.
→ Kept: every form reports only TYPE VERSIONS, fingerprints and counts, never values (DL-032). `--stored PATH` stays for tests and offline builds.
→ Open: how the build gets access to the nodes (network, credentials, which environments).
→ By: 13ue

**DL-095 · Repair · Roadmap structure follows the six parts of vertical integration**
→ Question: how is the public roadmap organized?
→ Options: A, one section per part of vertical integration (type system, types at runtime, typed errors, modules, tests and evals, production); B, milestones in time order.
→ Chose: A. Each part shows its state (verified, decided, concept) and its next steps. The roadmap lives in README.md and on a small GitHub Pages site.
→ Because: OWNER choice; the six parts are the owner goal (see wiki/concepts/vertical-integration.md), and progress is visible per part.
→ By: 13ue

**DL-096 · Repair · Developer and agent experience is the seventh roadmap part**
→ Question: where do the language server, formatter, editor integration and CLI sit on the roadmap?
→ Options: under part 1 (type system and compiler); a seventh part of its own.
→ Chose: a seventh part, "Developer and agent experience" (DX and AX). It is maintained with every other part, not as a later phase. The CLI and its JSON output are the agent interface; the editor shows the same facts to people.
→ Because: OWNER choice; the agent interface is the core of the project, and DX cuts across all six parts (migration errors in the editor, traces beside the source).
→ Order (proposal): grammar (slice 6a), compiler for the decided forms, `beaml fmt` and `beaml check --json`, then a language server on that JSON with diagnostics and hover first; Zed first, then VS Code.
→ By: 13ue

**DL-097 · Repair · Build every decided item unattended; record every decision**
→ Question: how does the pipeline run while the OWNER is away?
→ Chose: workers build every item whose decisions are recorded (DL-062, DL-065, DL-081 to DL-093), one code-writing worker at a time, in bounded steps with a ledger each. A step stops at the first Migrate or Answer question and hands it back. Every decision of every class, Undo and Repair included, goes into the step's `notes.md` with its class, choice, alternative and reason. Repair decisions that change language behaviour or a check also get a decision-log entry at the end of the phase.
→ Because: OWNER instruction of 2026-11-07. The OWNER must find no silent decision, small ones included.
→ By: 13ue

**DL-098 · Repair · Slice 6a grammar: worker decisions**
→ Chose: a signature line is a `fn` clause with an optional `= body` (DL-084). Over: a separate signature rule.
→ Chose: a variant has a payload or an ENUM LITERAL, not both (DL-082).
→ Chose: `with` on an `effect` takes a comma list of fields; a `fn` has no `with` (DL-089).
→ Chose: an uppercase `fn` name, an uppercase pipe step and a bare uppercase name are constructors (class `c`). Lowercase stays `function`.
→ Chose: integer literals in expressions (DL-092 `fn NonZeroInt 0 …`).
→ Chose: highlight tests put ` // anchor` after a target at the end of a line. Over: a test that passes on a borrowed class.
→ Chose: every `tree-sitter test` runs with `--rebuild`. Over: the shared cache, which gave a false pass in RED.
→ Because: smallest grammar that parses the decided forms. Details: [slice 6a ledger](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6-grammar/notes.md), [review](../../experiments/0004-generated-replay/workflow/2026-11-07/slice6-grammar/review.md).
→ By: Opus (slice 6a workers), accepted by Fable

**DL-099 · Migrate · Enum constructor inputs come from the field's own value (Q6B-1, B)**
→ Question: a field `state: PaymentState` has a constructor with parameters `status` and `decline_reason` (DL-084). From which JSON object does the decode read these keys?
→ Options: A, the keys of the object that holds the field (flat body, `state` is not a wire key); B, the keys inside the field's own value (`"state": {"status": …, "decline_reason": …}`); a one-parameter constructor reads the field's value directly, like an ENUM LITERAL.
→ Chose: B. The wire shape follows the TYPE structure. A flat body is declared with a constructor on the parent record, whose parameters are the flat wire keys (DL-092: the constructor is the way in).
→ Because: OWNER choice after analysis. Under A the field list no longer describes the wire shape, so the fingerprint, the derived old TYPE VERSIONS and `unknown_keys` need extra rules; under B the per-level rule of today holds, and literal and constructor read the same place. B can express A, A cannot express B.
→ Unblocks: slice 6b step 8 (decode through an enum constructor). The call form of a constructor with several arguments inside a record constructor is a sketch, not decided.
→ By: 13ue

**DL-100 · Migrate · An enum constructor is the decode path only (Q6B-2, B)**
→ Question: does an enum constructor (`fn PaymentState …`) make itself the only way to build the variants of its enum, as a record constructor does (DL-092)?
→ Options: A, yes: a bare variant as an expression is legal only inside the constructor's clauses, code calls the constructor; B, no: the constructor is the path for outside data and `migrate` only, code builds variants directly.
→ Chose: B. Code writes `Pending`; the constructor maps wire values to variants. Patterns stay free in both.
→ Because: OWNER choice. Variants are finite and named, so they are valid by construction; a record constructor checks values, an enum constructor only translates. Under A code would need the wire string (`"pending"`) to build a variant, which is outside knowledge, not domain knowledge.
→ Effect: slice 6b step 9 (enum only-way-in check) is dropped. Step 4 builds no restriction.
→ By: 13ue

**DL-101 · Migrate · The decode of outside data calls the record constructor (Q6B-3, A)**
→ Question: a record TYPE with a constructor (DL-092) stands in an EFFECT position. Does the generated decode call the constructor?
→ Options: A, yes: the decode calls the constructor and its failure becomes a typed reject; B, no: constructor TYPES are rejected in every EFFECT position, the constructor is called later in a `fn` on a plain TYPE.
→ Chose: A. One rule everywhere: the constructor is the only way in, also for outside data. The interim reject D6B-19 is replaced by the decode path.
→ Because: OWNER choice; the compiler knows every stage, so it also checks this one. B needs a raw TYPE per checked TYPE.
→ Commits us to: the replay questions on stored records (D6B-30, D6B-32, D6B-38) include a changed constructor against stored RESPONSE RECORDS: a new check can make an old record fail at replay. The OWNER wants that thought through together with those questions.
→ Open: the reject reason for a constructor failure in a decode (`decode` or a reason of its own).
→ By: 13ue

**DL-102 · Migrate · A stored record that fails a new rule blocks the build until a MIGRATE STEP declares its fate**
→ Question: a TYPE keeps its field shape but gets a new rule (a record constructor, DL-101; a changed enum mapping, DL-082), and a stored RESPONSE RECORD of an earlier deploy fails that rule today. What does the build do, and what does a REPLAY RUN show?
→ Options: ignore stored records; count and report only (plan default D6B-38 for enum mappings); block until a MIGRATE STEP declares the fate of the failing records.
→ Chose: block. The check runs the new constructors and mappings over the stored records of every environment and reports counts and reasons, never values (DL-032). When any record fails, the build fails until a MIGRATE STEP to a new TYPE VERSION says what happens to those records: a total rule (checked by the compiler), `quarantine` (the record keeps a typed reason and waits, visible in the dashboard), or `retire` with a keep window. A rule change that hits stored records therefore makes a new TYPE VERSION even though the field list is unchanged. Rescue is a code change, never a hand edit in a REPL or CLI.
→ Replay: a stored record is typed by its version and goes through the chain, then through today's code (the existing design, DL-043). There is no second replay mode "as it happened then"; that result is in the record itself.
→ Because: OWNER choice. A failing old record is the same situation as a missing MIGRATE STEP: the compiler sees it, so it must block (DL-031). Quarantine is no guess and no fallback: the record is not reinterpreted, it waits.
→ Supersedes: D6B-38 (count only) and D6B-32/D6B-30 need a new reading in the plan. The syntax of `quarantine` and of `retire` for a TYPE VERSION is a sketch, not decided.
→ Open: a mapping change that does not fail but changes the outcome (an old `Unknown("refunded")` that a new literal maps to `Refunded`): is that a hit that needs a step, or a plain improvement?
→ By: 13ue

**DL-103 · Migrate · A mapping change that only resolves Unknown values needs no MIGRATE STEP**
→ Question: a new ENUM LITERAL or constructor clause maps a wire value that an older deploy kept as `Unknown(value)`. The stored record does not fail; its outcome changes (`Unknown("refunded")` becomes `Refunded`). Is that a hit under DL-102?
→ Options: strict, every outcome change on stored records needs a MIGRATE STEP; relaxed, only a failing record is a hit.
→ Chose: relaxed. `Unknown` is the declared promise to keep the value until a rule exists; the new variant is that rule. The build reports the count of resolved records per environment and does not block.
→ Because: OWNER choice. DL-065 keeps the value for exactly this case.
→ Limit: a change that moves a value from one known variant to another known variant is not covered here; it fails no record either, and stays open until a case shows up.
→ By: 13ue

**DL-104 · Migrate · `beaml fmt` never changes the TYPE VERSION (Q6B-5, A; narrows DL-081)**
→ Question: DL-081 says `fmt` removes a VERSION MARK when there is no chain. After a SQUASH the mark is the only source of the version (`type Payment v3 { }`), and `v1` without a chain selects the versioned decode while `type Payment { }` selects the slice 1 form.
→ Options: A, `fmt` never changes the newest version or the decode form: it removes a mark only when the chain already implies it, keeps a mark without a chain (`v3` and `v1` alike), writes a mark when the chain starts above v1; B, make `type T { }` mean `v1` everywhere (every record versioned), then `v1` is redundant.
→ Chose: A. The plan default D6B-43 holds. B is a separate decision for later (an own slice: it changes the output of every unversioned TYPE).
→ Because: OWNER choice; a formatter must not renumber stored records or switch a decode form. The literal DL-081 text is superseded for the no-chain case.
→ By: 13ue

**DL-105 · Answer · The RESPONSE RECORD holds the typed projection, never the raw body (Q6B-4, O2)**
→ Question: a `redacted` field in an EFFECT output TYPE is a core feature and must be allowed. Today the RESPONSE RECORD stores the raw response body (`body_base64`), so it holds the redacted value and every undeclared key the service echoes. What does the record hold?
→ Options: O1, the raw body minus the redacted keys (undeclared echoes stay raw); O2, the typed projection: declared, non-redacted fields with their values, redacted fields as a marker, unknown keys as names only, a digest of the projection; O3, no body for EFFECTS with redacted output (no replay).
→ Chose: O2. The raw body is stored nowhere. A REPLAY RUN decodes the projection; a field added later is absent in old records, which is the existing `add` with a constant case. A redacted field replays as absent and marked. Spans, logs, events and dashboards keep the rules of DL-089 (never the value; counts only).
→ Because: OWNER choice after the walkthrough. Privacy is structural, not a filter: a value that is never stored cannot leak. A compile error (the interim D6B-34) would forbid a basic feature and still not protect the raw body against echoes.
→ Consequences: the RESPONSE RECORD contract changes (`value`, `redacted`, `unknown_keys`, a digest of the projection; names are a sketch); the replay compare uses the projection; a decode change cannot be replayed against an old raw body. A failure TYPE may carry a redacted field only when that field is `redacted` there too. Derived values (`"Hello " + c.holder`) are PII by flow; the implicit-flow check stays a later compiler target.
→ Supersedes: D6B-34 (compile error) and the D6B-30/D6B-32 readings in the plan; step 6 of slice 6b is replanned on this basis.
→ By: 13ue

**DL-106 · Migrate · The generated wrapper is the only entry for constructor TYPES at the host (Q6B-6, B)**
→ Question: in generated Elixir a host could pass `%{"value" => 0}` where BEAML requires `NonZeroInt`; the wrapper checked the shape, not the rule. Does "the constructor is the only way in" (DL-092) also cover host calls?
→ Options: A, out of scope: the host is a trusted boundary; B, constructor TYPES are structs at the host, built only through a generated constructor function (`new/1`, `{:ok, struct}` or `{:error, failure}`), and the host input check requires the struct, also in nested fields.
→ Chose: B. Success values of constructor TYPES become structs like the failure records of step 2; plain records without a constructor keep their form for now.
→ Because: OWNER choice. The TYPE holds up to the last boundary the compiler generates; this removes the accidental error (a map that happens to fit).
→ Limit, stated: Elixir has no private constructors, so a host can still write the struct literal on purpose. B stops the accidental forgery, not a deliberate one. Anything beyond that is a separate decision.
→ Effect: a new slice 6b step (struct codegen, `new/1`, the input check); the step 3 tests that expect `{:ok, %{"value" => 3}}` change to the struct form.
→ By: 13ue

**DL-107 · Repair · Every decision names who made it**
→ Chose: from this entry on, every decision in this log, in a step ledger (`notes.md`, `decisions.md`) and in a review carries a `By:` line: `13ue` for the OWNER, or the model that decided (`Fable` for the main agent, `Opus` for a worker, with the phase and ledger). Earlier entries are attributed by class: Migrate and Answer choices were made by `13ue`; Undo and Repair choices by the agent of that phase, which its ledger names.
→ By: 13ue (rule), Fable (the backfill-by-class reading).
→ Because: OWNER instruction of 2026-11-07. A decision without an author cannot be questioned or revisited.

**DL-108 · Migrate · A span follows the effect, transitively; reachability is inferred (Q6B-7, C)**
→ Question: since slice 6b step 3 (D6B-28) a pipe gets spans only when an EFFECT step stands in it. A pipe that reaches an EFFECT through another `fn` lost its spans, so the trace broke at every helper.
→ Options: A, keep (span only where the EFFECT step is visible); B, span every pipe in a module with an EFFECT; C, a step gets a span when it can reach an EFFECT transitively (the compiler knows the call graph).
→ Chose: C. The compiler infers for every `fn` which EFFECTS it can reach. Pure steps stay silent; steps on a path to an EFFECT get a span; `ProbeSupport` goes into every module on such a path. Reachability is inferred, not declared; a declared form in the signature is a later decision, after modules (roadmap part 4).
→ By: 13ue
→ Because: OWNER choice for maximum vertical integration. The same reachability feeds replay (pure `fn`s need no capture), tests and evals (pure `fn`s run without stubs), the PII flow check (EFFECTS are the sinks), dead-EFFECT detection and the IDE hover.
→ Effect: a new slice 6b step (call graph with recursion; spans per reachability; generated outputs with indirect pipes change, Repair). Higher-order functions do not exist yet; when they come, the graph needs an approximation.

**DL-109 · Repair · The RESPONSE RECORD key `unknown_fields` holds field names whose value went to the keep-value variant**
→ Question: DL-103 reports how many stored records a new ENUM LITERAL resolves from `Unknown`. The record must say which fields were Unknown at capture time.
→ Options: a record key `unknown_fields` with field NAMES only; no key (the DL-103 count is then impossible); the literals in the `type` key (a TYPE VERSION change per literal, against DL-103).
→ Chose: the key, names only, never values; written only for literal outputs so older outputs stay byte-equal; additive for old records. Built in slice 6b step 7. It joins the record version 2 of DL-105 (step 6a).
→ By: Fable (class and choice; the step 7 review asked for the register entry), built by Opus (GREEN, slice6b-decode-literals).
→ Because: Repair, not Migrate: the record format is the compiler's own and pre-production, and the key holds no value. Reversible until the first production store.

**DL-110 · Migrate · The GEN against LIB arm comparison ends before the projection records (Q6B-10, B)**
→ Question: DL-105 removes the raw body from every GEN RESPONSE RECORD; the frozen LIB arm of experiment 0003 keeps it. The byte lines of the arm comparison (body length, digest, body tamper) lose their meaning.
→ Options: A, rewrite the GEN copies with projection rows, LIB stays raw; B, the arm comparison ends with slice 6b step 6a, slice 1 to 5 results stay retained evidence, the 0003 copy run and the overlay diff leave the check list; C, LIB stays frozen, byte lines become not applicable, compare outcomes and counts only.
→ Chose: B. The LIB arm had one job: show that generated code does what the hand-written library does. That is shown through slice 5. From 6a on GEN does something different on purpose.
→ By: 13ue
→ Because: OWNER choice; a comparison that filters out the difference checks little. The README gets a clear cut: "LIB comparison up to slice 6b step 5; evidence retained".

**DL-111 · Migrate · A field that becomes redacted is a new TYPE VERSION; `redact f` removes the stored values eagerly (Q6B-11, 1A + 2A)**
→ Question: a field becomes `redacted` while stored RESPONSE RECORDS hold its value (in `value` for an output field, in `request` for an input field). Part 1: is `redacted` part of the TYPE VERSION? Part 2: what is the exit from the DL-102 block?
→ Options: 1A, yes, a new TYPE VERSION like every rule change with hits; 1B, no, only the value check blocks. 2A, a MIGRATE CHANGE `redact f` whose deploy removes the value from the stored records and reports the count; 2B, no own change, only `retire` or `quarantine`.
→ Chose: 1A and 2A. The deploy removes the values eagerly; the store is clean after the deploy. The input case follows the same rule through the value check in `request` (an input TYPE has no version in the record).
→ By: 13ue
→ Because: OWNER choice; with PII what counts is what lies in the store, and a keep window would leave the value there for weeks. This is also the first concrete answer to "lazy or eager": for redaction, eager.
→ Open: the syntax `redact f` is a sketch; `quarantine` is a sketched fate (DL-102), no keyword exists yet.

**DL-112 · Answer · A direct copy of a redacted value into a non-redacted field is a compile error everywhere (Q6B-12, A)**
→ Question: `Receipt { holder: card_holder }` turns a redacted value into a plain field; the next EFFECT needs no `with`, so the value reaches the wire, the span and the record. DL-105 named only failure TYPES.
→ Options: A, the 6c check applies to every record literal and variant payload; B, failure TYPES only now, other copies wait for the flow check.
→ Chose: A. The help line asks to mark the target field `redacted` or not to copy the value. Only the direct copy is caught; a derived value (`"" + card_holder`) is the implicit flow, a later compiler target (DL-029).
→ By: 13ue
→ Because: OWNER choice; who copies PII declares it. The evidence and challenges are in `wiki/planning/decisions-to-be-made.md` (D010).

**DL-113 · Answer · A same-named plain output field beside a redacted input field is allowed; the declaration decides (Q6B-13, C)**
→ Question: an EFFECT takes `Order { card_holder: redacted String }` and returns `Receipt { card_holder: String }`. A service that echoes the input puts the value into the record `value`. Compile error, warning, or allowed?
→ Options: A, compile error on the same name; B, warning; C, allowed, the output field declaration decides like for every other field.
→ Chose: C. A name rule is a heuristic that any other name bypasses, and it would block a legal display field. The OWNER who declares the output field plain has decided; a redacted output field is protected by DL-105.
→ By: 13ue
→ Because: OWNER choice. The evidence and challenges are in `wiki/planning/decisions-to-be-made.md` (D011). Limit: the record then holds a value that the input marks as PII; that is a declared choice, not an accident.

**DL-114 · Migrate · `beaml fmt`: a signature line ends an alignment group (Q6B-9, A)**
→ Question: DL-083 aligns consecutive clauses of one fn as a table. What happens to a signature line without body above the clauses?
→ Options: A, the signature line stays as written and ends the group; only the clauses below align; B, the signature line is the header row of the table, its parameter columns set the widths.
→ Chose: A. Built in slice 6b step 10; the fixture `slice6/fmt/header` encodes it.
→ By: 13ue
→ Because: OWNER choice; compact, and the columns follow the values. B gets wide with long TYPE names.

**DL-115 · Migrate · A REPLAY RUN shows a redacted field as the atom `:redacted` (Q6B-14, A)**
→ Question: the record holds no value for a redacted field (DL-105). What does the host see for that field in a REPLAY RUN?
→ Options: A, the atom `:redacted` in the field; the generated TYPE check accepts it only for a redacted field in a replay; B, the key is absent and the result carries a `redacted` list.
→ Chose: A. The result keeps its shape; the marker says "there was a value, you may not see it". In BEAML code nobody sees the marker: without `with` the field is not readable, and with `with` the value only goes into an EFFECT, which a replay substitutes anyway.
→ By: 13ue
→ Because: OWNER choice. Known consequence: host code that branches on `is_binary` takes another branch in a replay; a pure step that computes with the value can raise. With DL-106 the host sees typed structs, where a marker atom fits.

**DL-116 · Migrate · Interim: `redacted` in an EFFECT output only on String and Int fields without a constructor (Q6B-15, A)**
→ Question: the record holds no value for a redacted field (DL-105), so DL-102 cannot run a constructor or literal rule over an old value, and a replay decode cannot call a constructor with the marker. Which field TYPES may be redacted in an EFFECT output?
→ Options: A, interim compile error for every redacted output field that is not a String or Int field of a TYPE without a constructor; nested fields allowed because each level stands for itself; B, any TYPE, with replay and DL-102 skipping the rules of a marked field.
→ Chose: A. The error text names it as a slice limit with a help line. B would make a replay silently skip a rule.
→ By: 13ue
→ Because: OWNER choice, in line with every earlier choice: a loud compile error over a silent gap. Lifted when a rule over an absent value is defined.

**DL-117 · Migrate · `T.new/1` takes one map with atom keys, also for one parameter (Q6B-16, B with atom keys)**
→ Question: DL-106 names `new/1`. A record constructor can have several parameters and several signatures. Which form does the host call take?
→ Options: A, positional `T.new/n`, the arity picks the signature; B, one map with String keys as in the decode form (DL-099); B with atom keys, one map `%{cents: 500}`, the keys pick the signature; C, a keyword list.
→ Chose: B with atom keys. Every constructor TYPE gets `T.new/1` with one map, also a one-parameter TYPE: `NonZeroInt.new(%{n: 3})`, not `NonZeroInt.new(3)`. The keys are the parameter names of a signature; the first signature whose keys match runs. A map with String keys matches no signature and fails with a help line: keys must be atoms; outside data goes through the EFFECT decode.
→ By: 13ue
→ Because: generated code stays regular: one form, one map, one pattern match per signature, no conversion. The input map reads like the result struct without its tag (DL-106). The String-key decode form never reaches `new/1`: outside data runs through the EFFECT decode. A naked one-parameter call would be a second form.
→ Effect: step 11 (host structs) generates `new/1` with atom-key maps; the DL-106 example `NonZeroInt.new(3)` becomes `NonZeroInt.new(%{n: 3})`. Closes D014.

**DL-118 · Repair · DRIFT keeps its GEN checks; the 0003 copy replay leaves its repair check (step 6a, O1)**
→ Question: DL-110 removes the LIB arm comparison and the 0003 copy run before step 6a. The DRIFT repair check still runs the 0003 8-case replay in the repaired tree, which fails once records carry version 2. Does DRIFT leave too?
→ Chose: DRIFT stays for the GEN arm. Its repair check counts the edited hunks and runs the GEN replay of the repaired tree; the 0003 copy replay leaves with the copy run. `repaired_all` reads that GEN replay. The LIB arm leaves DRIFT with DL-110.
→ Over: removing DRIFT, or keeping the 0003 copy alive only for DRIFT.
→ By: Fable (step 6a RED, worker open point O1)
→ Because: DRIFT (f) is the evidence that a TYPE change repairs through the generated code; that evidence does not need the 0003 copy. One record form (DL-110) means one replay path.
→ Commits us to: the step 6a GREEN changes `run.py` DRIFT repair accordingly; the README DRIFT section follows in the docs phase.

**DL-119 · Migrate · Span default is the EFFECT path per step; the span resolution becomes an OBSERVATORY setting (Q6B-17, S)**
→ Question: DL-108 says spans follow an EFFECT transitively. Which steps of a reaching pipe get a span: every step of the pipe (P), only steps that are or reach an EFFECT (S), or a hybrid (H)?
→ Options: P, S, H as in D015; E, every call, also pure functions that reach no EFFECT.
→ Chose: S as the default. A step gets a span only when it is an EFFECT or reaches one. Spans nest by call, so the trace is a tree. The resolution itself is not a compiler rule: the compiler knows the whole call tree, and which spans a run writes becomes a runtime setting of the OBSERVATORY (part 4), see D018. P, H and E are candidate settings there, not language rules.
→ By: 13ue
→ Because: a default must not be opinionated; the EFFECT path is the smallest set that still shows every contact with the world. The OWNER wants full resolution on demand, per part of an application and for a limited time, and an opt-out that writes no data. DL-108 looked only outward (calls an EFFECT); seen inward, every live function in a web application lies on a path from an inbound EFFECT, so a fixed "pure steps stay silent" rule would hide live code. That rule now holds for the default only.
→ Effect: step 12 E2 builds S; the GEN query and the fixtures change as the plan says. D015 closes. D018 opens with the OBSERVATORY notes.

**DL-120 · Migrate · A constructor is pure: a constructor that reaches an EFFECT is a compile error (Q6B-18, a)**
→ Question: a constructor clause can call an EFFECT today, directly or through a called function. The COMPILER calls constructors itself: in the decode of outside data (DL-101), in the `--stored` check at build time and behind the host `T.new/1` (DL-106, DL-117). What holds?
→ Options: a, every constructor that reaches an EFFECT is a compile error; b, reject only where the COMPILER calls it (decode field, `--stored`, `new/1`); c, allow, with spans and a REPLAY RUN that substitutes the inner EFFECT.
→ Chose: a. A constructor is pure, transitively (the DL-108 reach analysis gives the answer). A function may call an EFFECT and pass its result into a constructor; the constructor itself never touches the world. The error names the constructor, the EFFECT and the path.
→ By: 13ue
→ Because: a constructor is the only way into a TYPE (DL-092); when the COMPILER walks that way in a decode or a build, it must not make a network call. One rule for every call site is simpler than two faces of one constructor (b). c would make a decode a side effect.
→ Effect: step 12b RED builds the reject. Closes D016. Open and noted: where outside callers enter BEAML (an inbound EFFECT or entry point) is not defined yet; today the host calls an exported `fn`. That question joins D018 (inward view).

**DL-121 · Migrate · The `--stored` check runs the generated Elixir constructor over the stored values (Q6B-19, b)**
→ Question: the `--stored` check (DL-102) reads only the static body TYPE of a constructor clause. A failure inside a called pipe step passes the build and fails at runtime (P11, review probe 6, observed). How does the build run constructor clauses?
→ Options: a, the COMPILER interprets constructor bodies with its own evaluator; b, the build runs the generated Elixir constructor over the stored values; c, a constructor used by a decode may only use forms the static check understands, other forms are a compile error.
→ Chose: b. The build compiles the generated decode code and calls it over every stored record; the check result equals the REPLAY RUN result. The static check stays as a fast first pass; the Elixir run decides. A build without an Elixir toolchain fails the `--stored` check with a clear error, it does not pass silently.
→ By: 13ue
→ Because: one semantics from source to production: the code that checks old data at build time is the code that runs in production. a would be a second evaluator that drifts with every new form; c would make the language grow at two speeds. The Elixir toolchain is already a build requirement of the EXPERIMENT. D019 (Rust NIF backend) stays open as an architecture question and does not change this contract.
→ Effect: a new slice 6b step "stored check through Elixir" (plan, RED from review probe 6: exit 1 with the reject text, GREEN, TEST). Build time grows by one Elixir compile and one run over the records; the step measures it. Closes D017. P11 closes with that step.

**DL-122 · Migrate · A removed or changed ENUM LITERAL with stored values blocks the build (Q6B-8, A)**
→ Question: when an ENUM LITERAL is removed, or its String changes, a stored record with that value replays as the KEEP-VALUE VARIANT (`Unknown("pending")`). DL-102 does not fire (no rule failed) and DL-103 does not count (it counts only Unknown to known). The deploy changes the replay result with no block and no count. What holds?
→ Options: A, block under DL-102 until a MIGRATE STEP declares the fate; B, count and report, do not block; C, no check, the `Unknown` promise covers it.
→ Chose: A. The `--stored` check treats a stored value whose literal no longer exists as a DL-102 hit: a compile error that names the enum, the lost literal, the count of records and the help line "declare the fate in a MIGRATE STEP". Interim, as in DL-116: no MIGRATE STEP form exists for this case yet (D6B-39), so the block holds until the fate syntax arrives.
→ By: 13ue
→ Because: a lost meaning in stored data is the same case as a failed rule (DL-102): yesterday stored, today read differently. A loud compile error over a silent change, in line with DL-102, DL-112 and DL-116.
→ Effect: a small slice 6b step (RED: fixture with a stored value whose literal is removed, `--stored` exit 1 with the text; GREEN in the static pass of `--stored`, also reachable from step 13). Closes D007. The fate syntax concept (quarantine, redact, retire per TYPE VERSION) lifts the interim.

**DL-123 · Repair · Host-facing details of `T.new/1` (D6B-97 to D6B-101) are a Repair, not a Migrate**
→ Question: DL-117 (OWNER) fixes the input form of `T.new/1`. The step 11 RED chose the failure shape: no matching signature gives `{:error, {:no_signature, "T.new/1: no signature takes these keys"}}` (D6B-97); the help line "keys must be atoms; decode outside data through the EFFECT" appears only when a key is not an atom (D6B-98); keys must equal the parameter names exactly (D6B-99); a non-map argument raises `invalid BEAML input` (D6B-100); the first signature whose key set matches runs, with no fallback (D6B-101). The RED review (M1) and the TEST review (N2) asked for the class.
→ Chose: Repair, By: Fable (step 11 RED, 2026-11-07). The defaults shape DL-117, they do not widen it. A host tells the cases apart by the error value and text. Recorded here so the choice is in the log, and in the README with the step 11 section.
→ Over: Migrate (OWNER choice before GREEN).
→ Because: no one outside the team is affected yet; a later change of the error shape is a Repair inside the generated code and its tests.
→ Commits us to: the README names the five rules; a later change raises its own entry.

**DL-124 · Repair · The DL-122 block names the field, enum, TYPE VERSION, count and record lines, never the stored String**
→ Question: DL-122 says the compile error "names the enum, the lost literal, the count of records". The lost literal exists at that point only inside stored records, so printing it prints a stored value. DL-032 forbids stored values in compiler output.
→ Chose: the message names the TYPE VERSION, the operation, the field, the enum, the record count and the record source lines (`S:N`), plus the help line. It never prints the stored String (step 13 D6B-124). The error stays a build block.
→ Over: printing the literal (DL-122 wording), or printing it only when `unknown_fields` exists.
→ By: Fable (step 13 plan repair, 2026-11-07)
→ Because: DL-032 gets no exception; a stored String can be outside data. The OWNER asked for a loud compile error, which this keeps.
→ Commits us to: DL-122 reads with this narrowing; the README states the text.

**DL-125 · Migrate · The fate of a stored record is a declarative operation in the MIGRATE STEP; expressions only when a real case needs them**
→ Question: three interim blocks wait for a fate syntax: a stored record that fails a new rule (DL-102), a redacted field without a constructor (DL-116), a lost ENUM LITERAL (DL-122). Which form does the fate take in `migrate T vN -> vM { … }`?
→ Options: 1, fate operations beside `rename`, `add`, `drop`: `redact f` (DL-111), `quarantine f` (records whose field fails its rule are parked, no REPLAY RUN, listed by the build), `retire f keep N days` (such records leave the replay set after N days), `map f "old" -> Variant(...)` for a lost literal; 2, clauses per field with a pattern, an expression over the old value and a failure branch `! fate` (1 is a subset of 2); 3, expressions plus a separate `on fail` block.
→ Chose: 1. The most declarative form: every line says what happens to a field, never how. No variables, no expressions, no order dependence. Expressions (form 2) come only when a real case needs a computed value; form 1 stays valid then, because it is a subset of 2.
→ By: 13ue
→ Because: declarative first: an agent derives the line from the error text and the decision; fewer places to make an error. The three interim blocks need nothing more than 1.
→ Effect: a concept page for the fate operations, then grammar (slice 6c or 7) and a slice 6b follow-up that lifts the interim blocks. The REPLAY RUN rule stays DL-102: chain to vM, then today's code; a quarantined record does not run. Scope note: a MIGRATE STEP governs RESPONSE RECORDS today; whether it also governs BEAML-owned persistence later is open (D020).

**DL-126 · Migrate · Design principle: declarative for shape and policy, expressions for computation**
→ Question: how far does BEAML push the declarative paradigm?
→ Chose: declarations carry shape and policy: TYPES and VERSIONS, enum literals, redaction, EFFECT signatures and their transport, MIGRATE STEPS and fates (DL-125), RETIRE LINES, entry points, retention, tracing resolution. Expressions carry computation only: fn bodies, pipes, constructor clauses. The COMPILER derives everything else (decode, structs, spans, replay) and never asks for it in source. Every new declaration needs a compiler semantics and keeps an expression escape hatch, so it is never magic.
→ Options: push declarations into computation too (rules as expressions everywhere); keep the current mix without a stated line.
→ By: 13ue
→ Because: policy as lines is diff-able and checkable by an agent; computation stays small. The three fate blocks and the span default showed that the line already exists in practice.
→ Effect: six roadmap candidates (concept, not decided): entry points declared (`route`/`on`, closes the inward view of D018); policy on EFFECT lines (retry, timeout, idempotent); simple rules on a TYPE field (`where`), the constructor stays for the complex case; examples in the source as tests and replay fixtures; retention per TYPE (`keep N days`); trace resolution per subtree, time-limited (D018). Recorded on the roadmap page and in the vertical-integration concept.

**DL-127 · Migrate · Prototype: Postgres holds BEAML records in one JSONB table; BEAML owns the rows (option J)**
→ Question: the first full-stack PROTOTYPE is Postgres at one end, LiveView at the other, BEAML between. Who owns the rows in Postgres?
→ Options: J, one table `records(id, type, version, value jsonb, inserted_at)`, every row a record as in the JSONL store today, the MIGRATE CHAIN applies on read, `--stored` reads the table (DL-094 live query), no Ecto schema and no Ecto migration; E, classic Ecto tables per TYPE, Postgres only an EFFECT (`db.get`, `db.put`), schema migrations stay with the host.
→ Chose: J.
→ By: 13ue
→ Because: the smallest build, and it shows the thesis: a TYPE change travels from the source to the table with no second migration system. E would break the vertical line at the place the PROTOTYPE should show. E can come later as a second arm when SQL over fields is needed.
→ Effect: EXPERIMENT 0005 (register entry to come): one Phoenix project, one domain (Orders/Payments from 0004), one LiveView page, one table. BEAML owns TYPES and VERSIONS, constructors, `migrate`, EFFECTS and the flow; the host owns Phoenix setup, router, LiveView template, Repo and deploy. D020 moves: for records in this table, a MIGRATE STEP governs stored state. Open details follow in the walk-through.

**DL-128 · Migrate · Prototype: the UI event enters BEAML through a declared inbound EFFECT (option b)**
→ Question: how does a LiveView click reach BEAML? a, the host builds the struct (`Order.new/1`, DL-117) and calls the generated flow; b, BEAML declares the entry, the COMPILER generates the decode of the event params (the DL-101 path, String keys), the call and the root span, and the host calls one generated entry function.
→ Options: a first, b later; b at once.
→ Chose: b at once. The entry is an EFFECT in the inbound direction: it is declared in the source, it decodes outside data, it opens the root span, it returns a result or a failure TYPE to the UI. Sketch, not grammar: `on ui "place" Order -> place`.
→ By: 13ue
→ Because: it makes the vertical line complete: the first thing the PROTOTYPE shows is where the ins and the outs are. It closes the inward view of D018 (every live function is reachable from a declaration) and the D6B-127 follow-up (a declared entry gives the root span). a would leave the entry in the host, the one place the PROTOTYPE should show.
→ Effect: a new slice before EXPERIMENT 0005 (inbound EFFECT declaration: grammar, decode of params through DL-101, root span, failure TYPE to the caller, REPLAY RUN of an inbound event; plan with RED/GREEN as usual). The HTTP request entry follows the same form later. Roadmap part 6 candidate "entry points declared" moves from concept to decided.

**DL-129 · Migrate · Prototype: Postgres is reached through three fixed transports, `db.put`, `db.get`, `db.list` (option T)**
→ Question: with one JSONB table that BEAML owns (DL-127), how does BEAML read and write it?
→ Options: T, three fixed transports on ordinary `effect` lines (`effect orders.save Order -> Order = db.put("records")`, `effect orders.load OrderId -> Order ! NotFound = db.get("records")`, `effect orders.list Query -> Orders = db.list("records")`), the host implements one module with these three functions once, no Ecto schema; S, a generic `db.query` with SQL text in the source.
→ Chose: T.
→ By: 13ue
→ Because: input and output of every database call are TYPES, so the type check, spans, RESPONSE RECORDS, REPLAY RUN and `--stored` apply as for any EFFECT. `Query` is a BEAML TYPE, not a query language: a new filter is a field, and a TYPE change runs through `migrate`. S would put column names into a String that no check sees and would break the vertical line at the database. S can come later as a fourth transport when a real case needs it.
→ Effect: EXPERIMENT 0005 host module (`BeamlDb` or a better name) with `put`, `get`, `list`; one Ecto migration for the table; the compiler needs the three transport names (a small slice or part of 0005 setup: transport names are strings today, so `db.put` may already parse; the RED decides). Open for 0005: the `get` key (id field of the TYPE), `list` order and limit, a `List` TYPE for `Orders`.

**DL-130 · Migrate · ENTRY LINE form: an inbound EFFECT is written like an outbound EFFECT (Q6D-1, option E', register option B)**
→ Question: which line form declares the UI event entry (DL-128)?
→ Options: A `on ui "place" PlaceOrder -> place` (slice default, new keyword); D `effect in ui "place" PlaceOrder -> place`; E `effect ui.place = ui.event("place") |> place` (no TYPE in the head); E' `effect ui.place PlaceForm -> Order ! PlaceError = ui.event("place") |> place` (the register's option B: head with input, output and failure TYPE, body with the inbound transport and the target fn).
→ Chose: E'. Inbound like outbound.
→ By: 13ue
→ Because: every outbound EFFECT carries input TYPE, output TYPE and failure TYPE in its head. E would be the only EFFECT without a TYPE in the head; A and D add a second line form. One `effect` form for both directions keeps the grammar, the highlighter, the RESPONSE RECORD and the REPLAY RUN on one path.
→ Drift rule (By: Fable, Repair): the head TYPEs must equal the target fn's input, output and failure TYPE; a difference is a compile error. This closes the register's trade-off "stand twice and can drift". The slice 6d RED tests this.
→ Effect: D021 closed. Slice 6d plan D6B-128 and the tree-sitter rule move from A to E'; the RED builds E'. `ui.event("…")` is the inbound transport call; the event name is a String as in `http.post("…")`.

**DL-131 · Migrate · The host calls one generated function per ENTRY LINE (Q6D-2, option A)**
→ Question: which generated function does the host (LiveView `handle_event`) call for a UI event?
→ Options: A, one function per ENTRY LINE, `Orders.ui_place(params)`, the host writes one `handle_event("place", params, socket)` clause per event; B, one dispatch function `Orders.entry(event, params)` with one host clause for every event and a runtime `unknown_event` reject.
→ Chose: A.
→ By: 13ue
→ Because: a renamed or deleted ENTRY LINE is an undefined remote call in the host build, not a runtime surprise. The vertical line stops at build time.
→ Effect: D022 closed. Slice 6d generates `ui_<event>/1` per ENTRY LINE; the RED probes the host build with `--warnings-as-errors` for a removed entry.

**DL-132 · Migrate · BEAML has one comment form: `//` to the end of the line**
→ Question: sketches in this session used `//`, `#` and `--`; which comment form does BEAML have?
→ Options: `//` (grammar `comment: token(seq("//", /[^\n]*/))`, 270 of 300 corpus sources, no `#` or `--` in any source); `#` or `--` as an addition.
→ Chose: `//` only. The `#` and `--` forms came from main-agent sketches, not from the language.
→ By: 13ue
→ Because: one comment form, already in the grammar, the highlighter and every fixture. A second form adds nothing.
→ Effect: every sketch, picture and fixture uses `//`. No compiler change.

**DL-133 · Migrate · A decode reject at the host is a generated `Rejected` struct, apart from the fn's failure TYPE (Q6D-3, option A)**
→ Question: how does the host see a UI event whose Decode-Form fails the decode or a constructor?
→ Options: A, `{:error, %BeamlSpike.Rejected{reason: "decode" | "constructor"}}`, a generated struct apart from domain failures; B, the fn's failure TYPE with `reason: "decode"`, as the outbound EFFECT does; C, a plain tuple `{:error, {:rejected, "decode"}}`.
→ Chose: A.
→ By: 13ue
→ Because: the UI must tell "the form is broken" from "the flow failed"; B merges both into one struct and fails for a fn without `!`; C is no TYPE, a host pattern on structs misses it.
→ Effect: D023 closed. Slice 6d generates the `Rejected` struct once per build; reasons are `"decode"` and `"constructor"` (D6B-132, D6B-143).
→ Note (docs, 2026-11-07): `BeamlSpike.Rejected` named the shape; with several modules per build the name is `<Module>.Rejected` (Q6E-2, default, open)

**DL-134 · Migrate · `--stored` also checks stored ENTRY RECORDS; DL-102 covers every record stream (Q6D-4, option A)**
→ Question: when the input TYPE of an ENTRY LINE gets a stricter constructor or loses an ENUM LITERAL, does the build see the stored UI events?
→ Options: A, `beaml build --stored` also reads `entries.jsonl` and runs the field constructors and literals of the input TYPE over each stored value; a failure blocks the build until a MIGRATE STEP names the fate (DL-102, DL-122); B, no build check over ENTRY RECORDS in slice 6d, the gap stays recorded as interim (D6B-146).
→ Chose: A.
→ By: 13ue
→ Because: every later record stream copies this answer. B keeps the build green while stored events break at the REPLAY RUN, which breaks the vertical line at the first inbound stream.
→ Effect: D024 closed. Slice 6d adds the `--stored` case for ENTRY RECORDS and an N-test; the DL-124 text rule applies (no stored value is printed). The MIGRATE STEP forms of DL-125 apply to entry fields.

**DL-135 · Migrate · The DRIFT status pins the outcome classes; a crash, a build failure or an open repair is `fail` (RED TEAM 01 M7, option A)**
→ Question: what does `DRIFT: pass` mean in a full `run.py` run? Today only the freeze hash of the LIB modules decides it; a retained run with `untyped_crash` on R, N and Q was `pass` (C3). No slice 6 test runs in the full run (C4).
→ Options: A, pin the expected class per derivative in `drift_test.py`, make `run.py drift` fail on a build failure, a crash class or `repaired_all` false, add the slice 6 test files to `run.py`; B, keep "recorded, not asserted" and put a limit line beside every "14 of 14".
→ Chose: A.
→ By: 13ue
→ Because: a green crash run is a false pass, the thing the vertical line must prevent. The pin cost is known from the byte pins.
→ Effect: C3 and C4 go to GREEN (`redteam_c3_test.py`, D6B-189, D6B-190 unblocked). D10 limit lines become unnecessary once the slice 6 files run in `run.py`. A wanted class change moves the pin with a diff proof, as the byte pins do.

**DL-136 · Migrate · `--stored` checks only the records that the REPLAY RUN decodes; non-200 and bad-digest records are counted, not checked (RED TEAM 01 M1, option A)**
→ Question: `--stored` blocks on a 503 record or a record with a wrong digest although `Replay.run` rejects both before it reads `value` (C2, C5). Which records does the check read?
→ Options: A, the check uses the replay rule: it skips non-200 and bad-digest records and prints one count line ("N records, K checked, M not replayable"); B, the check blocks as today and DL-121 is narrowed to 200 records; C, the check reads `status` and the digest and gives a separate non-blocking note per record.
→ Chose: A.
→ By: 13ue
→ Because: DL-121 ("the check result equals the REPLAY RUN result") becomes true again. A recorded outage is not a TYPE change and asks for no MIGRATE STEP.
→ Effect: one shared "replayable record" rule in the compiler for `--stored` and the REPLAY RUN (rt-correctness R2-3). The count line never prints a stored value (DL-124). Scope: RESPONSE RECORDS only; stored database rows are D020.

**DL-137 · Migrate · One `migrate` block governs RESPONSE RECORDS and BEAML-owned database rows with the same fates (D020, option A)**
→ Question: BEAML owns the rows of the PROTOTYPE table (DL-127) and reads them through `db.get` and `db.list` (DL-129). When a TYPE changes, what governs the stored rows?
→ Options: A, the same `migrate T vN -> vM` block governs both streams with the same fates: `map` applies on read, `quarantine` parks the row, `retire` takes it out of the read set after the keep window, `redact` removes the field; the build blocks until every old row has a fate; B, rows get only the value mapping of the MIGRATE CHAIN (`add`, `drop`, `map`) and no fates; C, a separate block for rows (for example `state T vN -> vM { … }`).
→ Chose: A.
→ By: 13ue
→ Because: the thesis is that a TYPE change travels from the source to the table with no second migration system. B leaves a non-mappable row with no declared fate; C is a second syntax for one question.
→ Effect: D020 closed. `--stored` reads the table live (DL-127) and applies DL-102, DL-122, DL-134 and DL-136 to rows: only rows that `db.get` or `db.list` would decode are checked. The `retire` meaning for rows follows M5. The fate forms of DL-125 are one slice for both streams. Open for any persistence form other than the DL-127 table.

**DL-138 · Repair · A stored ENTRY RECORD carries its capture outcome; `--stored` checks only accepted entries (slice 6d RED review O1)**
→ Chose: the ENTRY RECORD gets an `outcome` key (`"accepted"` or `"rejected"` with the reject reason), written at capture; `--stored` runs constructors and literals only over accepted entries and prints the DL-136 count line ("N entries, K checked, M rejected at capture"). Over: no reject records (loses the evidence of bad UI events), or a check against the base source (a second build).
→ By: Fable (after the slice 6d RED review, Opus)
→ Because: DL-136 fixed the same rule for RESPONSE RECORDS, and DL-134 says every record stream copies that answer. A rejected UI event is not a TYPE change and asks for no MIGRATE STEP. Class Repair: the choice follows two OWNER decisions; a different reading would need the OWNER (recorded here so it can be questioned).
→ Effect: slice 6d RED repair adds a reject record fixture, the `outcome` key, a `null` value case that must not crash the check, and the count line. O2: the help text must not name a TYPE VERSION (D6B-130). O3: a removed ENTRY LINE with stored entries behaves as a removed EFFECT with stored RESPONSE RECORDS does today (parity, pinned by a test); if today's behaviour is undefined, the repair reports it as a question.

**DL-139 · Migrate · A slice may build and pin a Migrate default, except for syntax and record formats (RED TEAM 01 M6, option B with a limit)**
→ Question: DL-097 and DL-041 stop a step at the first Migrate question; slice 6d planned to build its defaults before the OWNER answered (D7). May a slice build a default?
→ Options: A, always ask first, no built default; B, build the default, pin it with a test and a decision-log entry "default, By: Opus, open", and log the question; a different OWNER answer triggers a repair step.
→ Chose: B with a limit: a slice may build a default only when a different answer stays inside one repair step. Syntax (grammar, line forms, keywords), record formats (stored record keys, RESPONSE RECORD and ENTRY RECORD layout) and anything that host code calls wait for the OWNER.
→ By: 13ue
→ Because: two of the four Q6D answers differed from the slice default; Q6D-1 would have rebuilt the parser and the grammar. Everything else is a bounded repair and should not wait a night.
→ Effect: DL-097 is extended, not replaced. A built default carries `By: Opus (default, open)` in the log and in the ledger; the OWNER's answer closes it as "confirmed" or "repaired". The main agent decides the limit per question and records that call with `By: Fable`.
→ OWNER addition (13ue, same day): every built default is presented to the OWNER explicitly, as its own question with a picture and the options, never only as a line in a list or a log. The OWNER must never find a built default by chance. A built default stays open until the OWNER has signed it off; the main agent repeats the question in every later walk-through until the OWNER confirms or changes it. Silence is not a sign-off (see DL-107).

**DL-145 · Repair · Ingest the PL syntax sentiment research; decide its tensions after the first example applications**
→ ID note: first written as DL-140 by a parallel session; renumbered to DL-145 on 2026-11-07 because DL-140 was already taken (M2). References in the syntax pages updated.
→ Question: ingest the PL syntax sentiment research (loved and hated features, BEAML lens) into the wiki, and when to decide its tensions and gaps?
→ Options: ingest now and decide the tensions now; ingest now and decide them after the first example applications; keep it as temporary research outside the wiki.
→ Chose: ingest now, decide the tensions after the first example applications.
→ By: 13ue
→ Because: not too late, not too early. BEAML wants the best syntax ever built and wants to innovate, so the research must stay present in the design process. An example application gives the evidence that a decision today lacks.
→ Trigger: research handed back 2026-11-07.
→ Effect: capture under `raw/research/2026-11-07-pl-syntax-sentiment/`, [source page](../sources/pl-syntax-sentiment-2026.md), [concept page](../concepts/syntax-sentiment.md); eight open items D026 to D033 in [decisions to be made](decisions-to-be-made.md), each with trigger "after the first example applications".

**DL-146 · Repair · Take BAML up as a topic in the syntax sentiment research**
→ ID note: first written as DL-141 by a parallel session; renumbered to DL-146 on 2026-11-07 (DL-141 is the ENTRY RECORD sign-off).
→ Question: take BAML (BoundaryML's language) up as a topic in the syntax sentiment research?
→ Options: yes, as a syntax precedent and a name question; no, the technical precedent pages suffice.
→ Chose: yes.
→ By: 13ue
→ Because: BAML exists. The shared design space and the name proximity must be visible in every syntax decision, not only in the technical precedent pages.
→ Trigger: OWNER instruction 2026-11-07 after the PL sentiment ingest.
→ Effect: capture under `raw/research/2026-11-07-baml-syntax-sentiment/`, [source page](../sources/baml-syntax-reception-2026.md), [concept section](../concepts/syntax-sentiment.md#9-baml-as-the-nearest-precedent); one open item D034 (keep or change the name BEAML) in [decisions to be made](decisions-to-be-made.md), trigger "before the first public release or external announcement".

**DL-140 · Migrate · A stored value that falls on another known variant than before blocks the build; a `map` MIGRATE STEP is required (RED TEAM 01 M2, option A)**
→ Question: a literal swap between two known variants (`Authorized = "pending"  Pending = "ok"`) passes `--stored` today, because DL-122 blocks only a literal that is no current literal any more (D1).
→ Options: A, block under DL-122 with the DL-124 text; the build is freed by a `map` MIGRATE STEP (`map state "ok" -> Pending`); B, count and note under DL-103, build green; C, every literal change needs a new TYPE VERSION.
→ Chose: A. The migration is forced.
→ By: 13ue
→ Because: "stored yesterday, read differently today" is the DL-122 reason, and the OWNER wants the mapping declared, never implicit. C punishes a typo fix with a version jump.
→ Effect: `--stored` compares the variant a stored value took under the stored source with the variant it takes now (needs the stored version's literal table, or the record's decoded variant); a difference blocks. The same for enum constructors with swapped clauses. D6B-109 and the DL-103 limit close. Slice: with the DL-125 fate forms.

**DL-141 · Migrate · The ENTRY RECORD carries `outcome` and `reason` as two fixed keys (slice 6d record format, sign-off 1 of 3)**
→ Question: DL-138 gives every ENTRY RECORD a capture outcome. How does it stand in the record? The RED worker built two keys (R6D-13); under DL-139 a record format needs the OWNER's sign-off.
→ Options: A, `outcome` (`"accepted"` or `"rejected"`) and `reason` (`null`, `"decode"` or `"constructor"`) in every record; B, one key with the reason in the value (`"rejected:decode"`); C, no outcome, only `value: null` on a reject.
→ Chose: A. The built default is confirmed.
→ By: 13ue
→ Because: every record has the same key set, `--stored` filters on one key, a later reason needs no format change. B puts a second grammar into a value. C cannot tell a reject from an accepted empty value.
→ Effect: R6D-13 closes as confirmed. Sign-off 2 (`unknown_fields`) and 3 (one format for both streams) follow.

**DL-142 · Migrate · The ENTRY RECORD keeps `unknown_keys` and `unknown_fields` as two lists (slice 6d record format, sign-off 2 of 3)**
→ Question: the RED worker gave the ENTRY RECORD both lists (R6D-05), as the RESPONSE RECORD has them. One list instead?
→ Options: A, both lists: `unknown_keys` for data keys the TYPE does not declare, `unknown_fields` for fields whose value was kept as `Unknown(...)` at capture; B, one list.
→ Chose: A. The built default is confirmed.
→ By: 13ue
→ Because: DL-122 tells "unknown already at capture" from "literal lost today" by `unknown_fields`; without it an old `Unknown` value blocks the build by mistake. Parity with the RESPONSE RECORD.
→ Effect: R6D-05 closes as confirmed.

**DL-143 · Migrate · One record format for every EFFECT stream; the RESPONSE RECORD is aligned to it in its own repair step before EXPERIMENT 0005 (slice 6d record format, sign-off 3 of 3)**
→ Question: RESPONSE RECORD (outbound HTTP) and ENTRY RECORD (inbound UI event) differ in their payload keys, and the RESPONSE RECORD has no `outcome`, `reason` or `redacted`. The database stream (DL-129) comes next.
→ Options: A, one format with a common core (head keys, `value` + `value_sha256`, `outcome` + `reason`, `unknown_keys` + `unknown_fields`, `redacted`, a span id) and transport-specific extras (`status`, `request`); the RESPONSE RECORD is aligned in its own repair step with the byte-pin proof, before EXPERIMENT 0005; B, two formats stay, every new stream decides again; C, align now inside slice 6d.
→ Chose: A.
→ By: 13ue
→ Because (OWNER): BEAML shall support any number of EFFECT transports; a transport is an interface against the language and must be implementable generically later. One record format is part of that interface. C gives slice 6d two goals.
→ Effect: a new step "record format v3" after slice 6d TEST: common core, transport extras, `--stored` and the REPLAY RUN read one shape, the four byte-pin sites move with a diff proof. The database stream gets the format from the start. Roadmap note: "EFFECT transport as an interface" (DL-126 candidate, later).
→ Note (docs, 2026-11-08): built as record format v3 at ca09d361; the RESPONSE RECORD alignment step is done.

**DL-144 · Migrate · Free run for the PROTOTYPE: EXPERIMENT 0005 is built without further OWNER answers; every decision is recorded and walked through the next day**
→ Question: the OWNER wants the Phoenix PROTOTYPE (DL-127 to DL-129) built now. Who answers the open Migrate questions of 0005 (get key, list order and limit, List TYPE, `--stored` connection, code placement, and whatever the build raises)?
→ Chose: the workers and the main agent build a default for every question, pin it with a test, and record it in the 0005 ledger with class and author (`By: Opus (default, open)` or `By: Fable (default, open)`). The DL-139 limit (syntax, record formats, host-called names) is lifted for 0005 on this run only; such defaults are marked "big" and listed first in an OWNER review file `experiments/0005-prototype-fullstack/workflow/<date>/owner-review.md`. The OWNER walks through every default the next day (DL-139 sign-off rule: each one explicit, with a picture, repeated until signed off). Nothing is lowered in class silently.
→ By: 13ue
→ Because (OWNER, 2026-11-07 evening): "free run, record every decision, we go through it tomorrow in detail; tell me the bigger ones explicitly."
→ Effect: the pipeline runs PLAN → plan check → RED → RED review → GREEN → TEST → docs for 0005 and its prerequisites (slice 6d GREEN/TEST, record format v3, the `db.*` transport step) without a stop at Migrate. Answer-class questions still stop (nothing in 0005 reaches people outside the team: the PROTOTYPE runs locally, no deploy, no real data). Parked D036 items stay parked; a step that needs one of them builds the smallest form that avoids it or marks the test as blocked.

**DL-147 · Repair · A RED test file joins `run.py` in its GREEN commit, not before**
→ Question: after DL-135 every slice 6 test file runs in the full `run.py`, so an open RED file turns the whole run `fail` and the run cannot tell an expected RED from a regression (TEST v3/multi O2, 2026-11-08).
→ Chose: a RED file is listed in `run.py` by the GREEN commit that makes it pass; until then it runs by hand in RED, RED review and GREEN. Over: an expected-RED table in `run.py` (a second source of truth for the same counts), or keeping RED files out of version control.
→ By: Fable (after the TEST v3/multi review, Opus)
→ Because: the full run must mean "everything listed passes"; a table of expected failures is a pin that drifts. The multi-effect GREEN listed the two db RED files early; the P4 GREEN closes that.
→ Effect: `redteam_c3_test` C4 keeps "every slice 6 file"; the rule reads "every slice 6 file that has a GREEN". The C4 test may need that wording; the P4 GREEN checks it.

**DL-148 · Migrate · `beaml fmt` layout rules: multi-line bodies from two members, one clause table per block**
→ Question: `orders.beaml` (EXPERIMENT 0005) shows TYPE and ENUM bodies on one line and EFFECT blocks and constructor clauses unaligned. Which layout does `fmt` write? (OWNER, 2026-11-08, reading the source in the editor.)
→ Chose: (1) a TYPE body with zero or one field stays on one line; two or more fields go one per line. (2) An ENUM body with zero or one variant stays on one line; two or more variants go one per line. (3) Every contiguous block of single-line clause lines (`fn`, also constructor clauses and signature lines, also EFFECT lines) is one table: the arguments, `->`, the error `!` part and `=` stand in the same columns across the block. A blank line, a comment line or a multi-line clause ends the block (D6B-44 rules kept).
→ By: 13ue
→ Because: the tabular form reads well and is to be carried through the whole file, not only inside one `fn` group.
→ Open: line breaks inside a clause and a maximum line length (D038), to be discussed with longer functions.
→ Detail: slice "fmt layout" ledger under `experiments/0004-generated-replay/workflow/2026-11-08/fmt-layout/`.

### Process

**DL-041 · Repair · Continue without a pause**
→ Chose: after a slice, start the next slice whose content is already decided, and stop only at Migrate. Every decision goes into this log, with details in the step ledger, README or wiki.

**DL-042 · Repair · Slice 3 content**
→ Chose: slice 3 implements `add` with a constant and `drop` with a TYPE in the MIGRATE CHAIN. Over: `Unknown`, PII or division.
→ Because: only these forms have syntax and rules decided (DL-022, DL-023, DL-028). `Unknown` needs `enum` and `case`; PII needs a syntax.

### Open research (not decided)

→ Lazy migration on read or eager rewrite; batches or a stream of batches; rollback windows for lossy steps.
→ Access of the build to the deployed nodes for the live query (DL-094).
→ Novelty against schema registries, Ecto migrations and lens-based migration.
