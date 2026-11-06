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
