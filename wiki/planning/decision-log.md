---
id: planning-decision-log
kind: planning
status: active
updated: 2026-11-06
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

**DL-090 · Migrate · User-defined wrapper types with a constructor (T1)**
→ Question: how is a type such as `NonZeroInt` defined?
→ Options: T1, a wrapper type `type NonZeroInt(Int)` with hand-written constructor clauses; T2, a condition in the type (`where self != 0`) and a generated constructor; plus the earlier N2, a condition on `Int` at the parameter.
→ Chose: T1. A wrapper is a real type: an `Int` is not a `NonZeroInt`; the constructor is the only way in and may fail with a declared failure TYPE. Over: T2 and N2.
→ Because: OWNER choice; the same form as the enum constructor (DL-082), any check logic is possible.

### Process

**DL-041 · Repair · Continue without a pause**
→ Chose: after a slice, start the next slice whose content is already decided, and stop only at Migrate. Every decision goes into this log, with details in the step ledger, README or wiki.

**DL-042 · Repair · Slice 3 content**
→ Chose: slice 3 implements `add` with a constant and `drop` with a TYPE in the MIGRATE CHAIN. Over: `Unknown`, PII or division.
→ Because: only these forms have syntax and rules decided (DL-022, DL-023, DL-028). `Unknown` needs `enum` and `case`; PII needs a syntax.

### Open research (not decided)

→ Lazy migration on read or eager rewrite; batches or a stream of batches; rollback windows for lossy steps.
→ Where production stores report their TYPE VERSIONS (O5).
→ Novelty against schema registries, Ecto migrations and lens-based migration.
