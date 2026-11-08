# Decisions: the FATE slice (fates-a plan)

**[Proposal]** PLAN phase, 2026-11-08, HEAD `5e05b5f3`. Plan: [plan.md](plan.md).
Basis: DL-125, DL-155, DL-156 (By: 13ue) and the entries named in the plan. Undo and Repair defaults run through (DL-041,
DL-144). Migrate questions are for the OWNER, each with a proposed default; nothing here closes them. DL-139: a slice may build
a Migrate default, except syntax and record formats; those questions are marked "before GREEN".

## Undo and Repair defaults

**PF-01 · Repair · Split into fates-a (quarantine, map, syntax, fmt, tree-sitter, 0005) and fates-b (redact, retire, DL-140 detection).**
Chose: fates-a closes the DL-156 loop "block → fate → green" for DL-102 and DL-122. Over: one slice for all four fates.
Because: `redact`, `retire` and DL-140 detection each wait on an OWNER answer about stored data or record formats (QF-4, QF-8,
QF-9). Commits us to: a fates-b plan; DL-156 is only partly met until then.
→ By: Opus (PLAN fates)

**PF-02 · Repair · fates-a runs as four steps a1 to a4, each RED / RED review / GREEN.**
Over: one RED / GREEN pair. Because: four separate behaviors (checker, runtime, 0005, editor). Commits us to: a1 and a2 land
before a3; the slice is not done before a3 passes (DL-150 hazard of a green build that fails at run time).
→ By: Opus (PLAN fates)

**PF-03 · Undo · New test file `tests/slice6_fates_test.py`, step `slice6-fates` in 0004 `run.py`.**
Because: the m4 pattern (DL-147).
→ By: Opus (PLAN fates)

**PF-04 · Undo · Keywords as in DL-125: `quarantine`, `retire … keep N days`, `redact`, `map`; enum mark `enum E vN`.**
Because: DL-125 and DL-155 (By: 13ue) name these forms. QF-7 asks the OWNER to confirm before a1 GREEN.
→ By: Opus (PLAN fates)

**PF-05 · Repair · A MIGRATE STEP with fate lines only is valid.**
Chose: the "needs at least one" check counts every line. Over: a fate line needs a rename, add or drop beside it.
Because: N9 needs `migrate Amount v1 -> v2 { quarantine value }` with no field change. Commits us to: new text
`a MIGRATE STEP needs at least one rename, add, drop or fate line`.
→ By: Opus (PLAN fates)

**PF-06 · Repair · An enum step holds bare `map` lines only.**
Chose: `rename`, `add`, `drop` and field-qualified lines in `migrate E …` are errors. Over: variant renames in an enum step.
Because: an enum has no fields; a variant rename is not asked for. Commits us to: a later case adds variant steps.
→ By: Opus (PLAN fates)

**PF-07 · Undo · A field-qualified line names a field of the newest TYPE VERSION.**
Because: the same rule as the `rename` check of M4 (QM4-1).
→ By: Opus (PLAN fates)

**PF-08 · Repair · One compile error per wrong form.**
Texts (default; the RED worker pins them):
- `migrate T vN -> vM: quarantine f names no field of T`
- `migrate T vN -> vM: quarantine f: the field f has no rule to fail (no constructor, no ENUM LITERAL)`
- `migrate T vN -> vM: map f: the field f is no literal enum field`
- `migrate E vN -> vM: map "old" -> V: V is no variant of E`
- `migrate E vN -> vM: map "old" -> V: V carries a payload; map to a variant without payload, or quarantine the field (QF-6)`
- `migrate E vN -> vM: map: E has an ENUM CONSTRUCTOR; map works on ENUM LITERALS only (D041 open)`
- `migrate E vN -> vM: map "old" -> V: "old" is a current ENUM LITERAL of E; a swap waits for the previous literal table (DL-140, QF-8)`
- `migrate T vN -> vM: a bare map stands only in the MIGRATE STEP of an enum; write map <field> "old" -> V`
- `migrate T vN -> vM: two fate lines name the field f`
- `migrate T vN -> vM: a fate line stands only in the last MIGRATE STEP of T (v<newest>)`
The `"old"` String is source text, not a stored value, so DL-124 holds.
→ By: Opus (PLAN fates)

**PF-09 · Repair · `redact f` and `retire f keep N days` parse, format and highlight, and the checker rejects them.**
Texts: `migrate T vN -> vM: redact f: the meaning for stored values is not built yet (fates-b, QF-9)`;
`migrate T vN -> vM: retire f keep N days: the meaning for stored values waits on M5 (QF-4)`.
Over: no syntax until fates-b. Because: one grammar change, one fmt change, one corpus; a loud error keeps a source from
building with a meaning that does not exist. Commits us to: fates-b removes these two errors.
→ By: Opus (PLAN fates)

**PF-10 · Repair · A fate line stands only in the last step of its chain.**
Over: fate lines in any step. Because: the source holds only the newest rules, so an older step's fate has no rule of its own
to run. Commits us to: a chain that grows past a fate step moves the fate line into the new last step; the in-place gap
(plan, Risks) stays until QF-8.
→ By: Opus (PLAN fates)

**PF-11 · Repair · One `quarantine` line per constructor TYPE; `f` must be a parameter of its signature line.**
Over: per-clause attribution. Because: a constructor fails as a whole; N9 needs one line. Depends on QF-3 A.
→ By: Opus (PLAN fates)

**PF-12 · Repair · A `quarantine` on a nested TYPE covers that TYPE at any depth and in every stream (rows, RESPONSE RECORDS, ENTRY RECORDS).**
Over: rows only. Because: DL-134 and DL-137 check every stream with the same rules; a fate per stream would be three lines
for one fact. Commits us to: S1c and S1d; a quarantined ENTRY RECORD gets no REPLAY RUN.
→ By: Opus (PLAN fates)

**PF-13 · Repair · A `fate:` line per (TYPE VERSION step, stream place, line) on stderr, only when the count is above 0, before the `rows:` line.**
Over: a new column in the `rows:` line. Because: no existing pin or 0005 `counted/3` helper changes; QV3-7 A prints count
lines only when M > 0. Commits us to: the open count-line print rule (owner review) covers these lines too.
→ By: Opus (PLAN fates)

**PF-14 · Undo · A quarantined row counts as checked in `rows: N rows, K checked, M not decodable`.**
Because: it was checked; it is not "not decodable" (DL-150 separation).
→ By: Opus (PLAN fates)

**PF-15 · Repair · The DL-122 help that names D6B-39 (QM4-3 default) is replaced by the DL-155 help.**
Over: keep both lines. Because: D6B-39 no longer applies to enum fields (DL-152); DL-155 names the exit. Commits us to:
QM4-3 is superseded; eight test constants change in a1 GREEN.
→ By: Opus (PLAN fates)

**PF-16 · Repair · Only TYPES and enums with a fate line change their generated bytes.**
Over: one decode form for all. Because: no pin site moves (the PM4-06 rule; two missed re-pins on 2026-11-07). Commits us to:
`ponytail:` comment at each gate; R7 guards every other source.
→ By: Opus (PLAN fates)

**PF-17 · Repair · A list RESPONSE RECORD with one quarantined item is quarantined whole.**
Over: replay the other items. Because: the record is the unit of a REPLAY RUN (DL-125 "a quarantined record does not run").
→ By: Opus (PLAN fates)

**PF-18 · Undo · The old `stricter` source moves to `variants/stricter_v1/` for N8 and N8b; `stricter` becomes the v2 form.**
Because: N8 must still prove the block, N9 the exit, against the same row.
→ By: Opus (PLAN fates)

**PF-19 · Repair · `fmt` gives a MIGRATE STEP body the DL-148 TYPE body rule (0 or 1 line on one line, 2 or more one per line, commas kept).**
Over: leave migrate bodies as written. Because: DL-148 requires a layout rule for every body; the same rule is the least new
rule. Commits us to: slice 3 to 5 sources change on their first `fmt` (unformatted on purpose, DL-148 P1). QF-7 may change it.
→ By: Opus (PLAN fates)

**PF-20 · Undo · New fate sources are db fixtures under `slice6/db/fates/` or inline strings in the test.**
Because: a tracked non-db source with new syntax fails to compile at the guard base commits and moves the hash guards.
→ By: Opus (PLAN fates)

**PF-21 · Repair · The DL-102 help suggests the first parameter with a literal pattern in the failing clause.**
Over: a fixed `<field>` placeholder. Because: `fn Amount "0", _` gives `quarantine value`, the line N9 needs; parameter names are
source text, not stored values. Depends on QF-5.
→ By: Opus (PLAN fates)

**PF-22 · Undo · The http live decode keeps `rejected` / `constructor` for a body that fails the new rule.**
Because: a live body is not stored data; quarantine is a fate of stored values.
→ By: Opus (PLAN fates)

**PF-23 · Repair · `map` targets literal enums only; an enum with `fn E` gets the PF-08 error.**
Over: map over constructor results. Because: D041 is open; this works under A, B and C. Commits us to: under D041 C a later step.
→ By: Opus (PLAN fates)

**PF-24 · Undo · `redact f` means "the field becomes absent"; it never skips a rule; DL-116 stays (M3 lean A).**
Because: the task and the D042 note. Built only in fates-b.
→ By: Opus (PLAN fates)

## Migrate questions for the OWNER

**QF-1 · Migrate · What does the running app see for a quarantined row? (before a2 GREEN: record format)**
→ A: `db.list` skips the row and counts it (span attribute); `db.get` gives `rejected` / `quarantined`; REPLAY RUN gives `{:error, :quarantined}`. A fifth reason value in the db call record.
→ B: a typed state in the TYPE: the value comes back marked (`Quarantined(Order)`, D042 A direction); every signature and page handles it.
→ C: `db.list` fails like a bad row (DL-150 B shape). Breaks N9.
→ Default: A. Because: smallest; N9 needs the list to work; the row stays distinguishable from a bad row by its reason. The OWNER leaned to "a mark, never a silent skip" for D042: A is counted, not marked.

**QF-2 · Migrate · How does a stored value say which nested TYPE VERSION it has? (`Amount v2`, `Channel v2` inside `Order` rows)**
→ A: it does not (source-only, as today): `quarantine` selects by today's rule; a bare `map "old" -> V` is an alias that also applies to live input.
→ B: the parent field TYPE text carries the version (`amount: Amount v2`): the parent fingerprint changes, so the parent needs its own next version too.
→ C: the core `type` key holds the nested versions (`nested: {Amount: 2}`): a record format change.
→ Default: A. Because: observed, nothing in a row carries `Amount`'s version; B cascades versions; C is a record format (DL-139). Limit: DL-155 says versions are visible "in every record"; A keeps that only in source.

**QF-3 · Migrate · Where does the `quarantine` line for a stricter constructor stand?**
→ A: in the constructor TYPE's own step: `type Amount v2` + `migrate Amount v1 -> v2 { quarantine value }`; any failure of `fn Amount` is quarantined, `value` names the report.
→ B: as A, but only failures whose failing clause tests `value` by a pattern.
→ C: in the owner TYPE's step: `migrate Order v1 -> v2 { quarantine amount }` (the comment in `fate_test.exs` today).
→ Default: A. Because: DL-155 and the task name `type Amount v2`. C would make every owner of `Amount` declare its own line.

**QF-4 · Migrate · What is "age" for `retire f keep N days` (M5)? (fates-b, before its GREEN: record format)**
→ A: per value: the row column `inserted_at` (host, must enter the ROW SNAPSHOT) and a new capture time key in records.
→ B: per line: N days from the first deploy that holds the line; no per-value age.
→ C: M5 B: delete after N days (needs a host delete step).
→ No default built. Because: no time key exists in any record or row core (observed).

**QF-5 · Migrate · The DL-155 gate text.**
→ A: the help names both lines with real names and a placeholder for the stored String: `type Amount v2 and migrate Amount v1 -> v2 { quarantine value }`; `map "<old literal>" -> <Variant>`.
→ B: a generic help: `declare the next TYPE VERSION and a fate line (DL-155)`.
→ Default: A. Because: an agent derives the line from the error text (DL-125 reason).

**QF-6 · Migrate · A removed literal whose natural target has a payload (`Unknown(String)`, `Refund(String)`).**
→ A: error; map only to a variant without payload; use `quarantine` otherwise.
→ B: allow `map "old" -> Unknown`, the kept String is the old literal (the DL-122 outcome made explicit, DL-103 counts it).
→ C: allow a payload from the old String (`-> Refund("old")`).
→ Default: A. Because: DL-125 "expressions only when a real case needs them"; no case needs it yet.

**QF-7 · Migrate · Keyword spelling and the migrate body layout. (before a1 GREEN: syntax)**
→ A: DL-125 words as planned (`quarantine f`, `retire f keep N days`, `redact f`, `map f "old" -> V`, `enum E v2`); body layout PF-19.
→ B: other words (for example `park f`, `map f from "old" to V`) or another layout.
→ Default: A. Because: DL-125, DL-155 (By: 13ue) use these words; the concept page still calls the spelling open.

**QF-8 · Migrate · Where does the build get the previous rule or literal table? (fates-b: DL-140 swap detection, the in-place gap)**
→ A: a committed lock file beside the source, written by the build (per TYPE VERSION: a digest of the rules and the literal table).
→ B: a digest of the rules in the stored core `type` key (record format).
→ C: the previous artifact, found by `artifact_id`.
→ No default built. Because: a stored row holds only the literal, so neither a swap nor a stricter rule on the same version is visible today.

**QF-9 · Migrate · Who removes the stored values on `redact f` (DL-111 "eager")? (fates-b)**
→ A: a generated host function that the deploy runs over rows and records.
→ B: `--stored` writes a redacted copy of the snapshot; the host swaps it in.
→ C: read side only (absent in decode), eager removal later.
→ No default built. Because: the compiler cannot write production (DL-151), and C contradicts DL-111.

## Register items, not decided here

→ D041: plan works under A, B, C (PF-23).
→ D042: out of scope; plan names what it would need (plan, Exclusions).
→ D035: out of scope; a bad digest stays "not decodable", never "quarantined".
→ M3: `redact` = field absent, no rule skip, DL-116 stays (PF-24).
→ M5: QF-4, not decided.
