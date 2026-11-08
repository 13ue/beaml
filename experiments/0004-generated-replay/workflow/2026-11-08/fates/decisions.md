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

**PF-24 · Undo · Superseded by DL-160 (By: 13ue; RED repair R-5, 2026-11-08).** Original text: `redact f` means "the field becomes absent"; it never skips a rule; DL-116 stays (M3 lean A).
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


## Rulings by the main agent after the plan check (2026-11-08)

- **QF-1 → answered by the OWNER as DL-157**: skip and count by default; the host learns the skipped count (plan a2 decides the carrier: a field on the list result or a second return value); record reason `quarantined`; fetch option later. By: 13ue (DL-157).
- **QF-3 → form A** (`type Amount v2 { … }` + `migrate Amount v1 -> v2 { quarantine value }`). The OWNER signed the three-example picture of 2026-11-08 that shows exactly this form (DL-155 "wird von mir so unterschrieben"); the site cards FATE and FATE-NEXT that show `quarantine amount` on `Order` are worker sketches and get corrected. By: Fable (ruling on evidence), class Repair.
- **QF-7 → DL-125 words**, confirmed by the same signed picture (`quarantine`, `map "old" -> Variant`, `enum Channel v2`, `migrate Channel v1 -> v2`). By: Fable (ruling on evidence).
- **DEAD LINE rule on a nested fate-only step (O1 probe)**: RED F7/F7b; a fate-only step is never dead. By: Fable, Repair.
- **a1 exit 1 when a fate line is hit (O2)**: accepted; a1 alone must not produce a green build that crashes at run time; a2 lifts the exit. By: Fable, Repair.
- **O3**: V18b (`P2_BASE`) and `slice6_m4_test` `rename_text` join the pin/help list; ENUM CONSTRUCTOR help defined in RED; PF-16 reworded to "sources with a fate line"; N9 evidence path fixed; fixtures follow the N13 filter. By: Fable, Repair.
- **DL-140 swap detection in fates-b (PF-01)**: narrows DL-156; presented to the OWNER as its own question (A keep in fates-a, needs the previous literal table QF-8; B fates-b). Open.
- All missing RED cases from plan-review.md are added in RED a1.

## RED decisions (fates-a1, 2026-11-08)

Pinned in `tests/slice6_fates_test.py`; evidence in [red-output.md](red-output.md). A GREEN that needs another text changes
the constant and records why. By: Opus (RED fates-a1) for every entry.

**RF-01 · Repair · The a1 stop lines are `error: a quarantine line is hit, but quarantine at run time is not built yet (fates-a2, DL-157)` and `error: a map line is hit, but map at run time is not built yet (fates-a2)`.**
Chose: an `error:` line after the `fate:` lines. Over: the plan-review wording `fate: quarantine at run time …`. Because: `fate:` is
the count-line prefix; a stop line must read as an error. Commits us to: a2 RED removes both and expects exit 0.
→ By: Opus (RED fates-a1)

**RF-02 · Repair · The owner form `migrate Order … { quarantine amount }` is an error that names the constructor TYPE step.**
Text: `quarantine amount: write the quarantine line in the MIGRATE STEP of the constructor TYPE: type Amount v2 and migrate Amount v1 -> v2 { quarantine <parameter> } (QF-3 A)`.
Over: no text (QF-3 C "not built"). Because: the corrected site cards showed this form; an agent must get from it to form A.
→ By: Opus (RED fates-a1)

**RF-03 · Repair · `quarantine channel` (an enum field) is an error: `quarantine of an enum field is not built; write map channel "<old literal>" -> <Variant>`.**
Over: lift DL-122 by quarantine. Because: the plan builds `quarantine` for DL-102 only; PF-08 "no ENUM LITERAL" left it open.
Commits us to: the open OWNER line below.
→ By: Opus (RED fates-a1)

**RF-04 · Repair · Duplicate fate lines are counted per (field, literal) for `map`, per field for `quarantine`.**
Texts: `two map lines name "app" of field channel`, `two map lines name "app"` (bare), `two fate lines name the field value`,
`one quarantine line per constructor TYPE; Amount has two (PF-11)`. Over: PF-08 "two fate lines name the field f" for any
two lines. Because: two removed literals of one field need two map lines (F2 subTest builds them).
→ By: Opus (RED fates-a1)

**RF-05 · Repair · A bare `map "app"` in the enum step and a qualified `map channel "app"` in the owner step is an error in the owner step: `"app" has a map line in migrate Channel v1 -> v2 too; keep one`.**
Over: a precedence rule. Because: two lines for one literal can disagree; one line is the least rule.
→ By: Opus (RED fates-a1)

**RF-06 · Repair · QF-6 A texts.** `map "app" -> Unknown`: `Unknown carries a payload; map to a variant without payload (QF-6 A)`
(PF-08 "or quarantine the field" dropped, RF-03). `map "app" -> Unknown("x")`: parse error `a map target takes no payload (QF-6 A) at byte N`.
→ By: Opus (RED fates-a1)

**RF-07 · Undo · No case for "a field of Amount that is not a parameter of fn Amount".**
Because: unreachable in db sources: PDB-13 needs a first signature that takes the String fields by name (HEAD probe with
`fn Amount v: String, c: String` gives the PDB-13 error). `quarantine nope` covers "no field".
→ By: Opus (RED fates-a1)

**RF-08 · Repair · The DL-155 help names the newest TYPE VERSION + 1, also when the mark has no step into it.**
`type Amount v2` alone gives `type Amount v3 and migrate Amount v2 -> v3`; `enum Channel v2` alone gives `enum Channel v3 …`.
Over: name `migrate v1 -> v2` for a bare mark. Because: a chain may start at vN (slice 4) and versions are never renumbered
(DL-058); the plan rule "vN newest, vN+1 next". Commits us to: S3 pins it.
→ By: Opus (RED fates-a1)

**RF-09 · Repair · Help per DL-102 site (plan repair 5).** The DL-155 help only where a fates-a line lifts the block (a failed
constructor rule, a lost literal). An ENUM CONSTRUCTOR with no matching signature: `no fate line covers an ENUM CONSTRUCTOR yet (D041 open); restore a signature of fn E that reads these records`.
A constructor TYPE with no matching signature: `no fate line covers a value that matches no signature of C (a decode fault); restore a signature of fn C that reads these records`.
"No String value" and "no variant" keep the DL-102 help (S5 guard). Over: the DL-155 help at all six sites. Because: a help
must not name a line that the checker then does not accept as a lift. Commits us to: V18b moves four pairs, not five.
→ By: Opus (RED fates-a1)

**RF-10 · Undo · S1e and S1f do not pin whether a quarantine `fate:` line prints beside another block.**
Because: the constructor run starts only after the static pass has no error (D6B-105); either output is acceptable.
→ By: Opus (RED fates-a1)

**RF-11 · Undo · F4, F5, F6 accept a compile error with or without the `error: ` prefix.**
Because: `derive_versions` texts print without it, later checks with it; the rest of the text is exact.
→ By: Opus (RED fates-a1)

**RF-12 · Repair · An enum step with `rename`, `add`, `drop` or a qualified `map` gives one text: `an enum MIGRATE STEP holds bare map lines only (PF-06)`.**
Because: PF-06 had no text.
→ By: Opus (RED fates-a1)

**RF-13 · Undo · Fixture bases: `stricter_v1` is the 0005 `stricter` source (ui.place, PlaceForm, rows); `channel_v1/v2` replace `App` by `Mobile`.**
Because: a3 copies the same forms into 0005 (`variants/stricter_v1/`, `variants/stricter/`, `variants/channel_v2/`).
→ By: Opus (RED fates-a1)

**RF-14 · Undo · PF-24 ("DL-116 stays") is stale after DL-160 (By: 13ue).** No a1 test changes: a1 rejects `redact` (PF-09).
→ By: Opus (RED fates-a1)

## Open OWNER lines (Migrate, after RED a1)

→ **DL-156 scope:** DL-140 swap detection in fates-a (needs the previous literal table, QF-8) or in fates-b (PF-01). Open.
→ **Quarantine of a lost literal:** may `quarantine channel` park rows whose channel literal is gone, beside `map`? RF-03 makes it an error for now.
→ **QF-2:** a1 builds the default A (the nested TYPE VERSION is source-only; a fate line counts by today's rule). Open.
→ **QF-5 texts:** the help and `fate:` texts of RF-01 to RF-09 are RED defaults, not OWNER texts. Open.

## OWNER and main-agent decisions during GREEN fates-a1 (2026-11-08)

**DL-162 · Migrate (OWNER) · `quarantine` may park a lost ENUM LITERAL; supersedes RF-03 and the QUAR-LITERAL card.**
Forms: bare `quarantine "fax"` in the enum step, `quarantine channel "fax"` in the owner step; a map line and a
quarantine line on one literal is an error; a bare `quarantine channel` (field only) on an enum field stays an error.
→ By: 13ue (DL-162)

**Q1 ruling · Repair · The DL-161 previous literal table comes from an older declaration in the source (form A).**
`enum Channel v1 { … }` stays beside `enum Channel v2 { … }` while v1 values exist. An enum chain without the older
declaration is an error (`enum Channel v1 is not declared; …`), never a silent gap. Forms B (literal changes in the step)
and C (lock file, previous artifact) are not built. OWNER card ENUM-V1-DECL opened.
→ By: Fable (ruling on DL-155 wording), class Repair, OWNER card ENUM-V1-DECL opened

**Q2 ruling · Undo · One `fate:` line form for every fate line (the RED form of PF-13 / RF-01).**
→ By: Fable (ruling on Q2)

## GREEN decisions (fates-a1, 2026-11-08)

By: Opus (GREEN fates-a1) for every entry below. Evidence: [green-output.md](green-output.md).

**GF-01 · Repair · An older enum declaration needs its MIGRATE STEP: `enum Channel v1 has no MIGRATE STEP to v2; add migrate Channel v1 -> v2 { ... } or remove enum Channel v1 (DL-155)`.**
Over: accept an unused old declaration. Because: an old table without a step is a dead declaration and cannot be read.
Commits us to: F5 `old_declaration_without_step`.

**GF-02 · Repair · The swap check uses the table of the version before the newest (the `from` of the last enum step) for every stored value.**
Over: per-value enum versions. Because: QF-2 A (built default) keeps the nested version source-only, so a stored value
does not say its enum version. Limit: in a chain of two or more enum steps, a value of an older version is compared with
the last table only. Commits us to: QF-2 decides the upgrade.

**GF-03 · Repair · A moved literal blocks with one DL-140 block per literal that names the literal, the old and the new variant: `… has the ENUM LITERAL "web" of field channel, which was Web in enum Channel v1 and is App now (DL-140)` and `help: declare the fate of "web" in migrate Channel v1 -> v2 (DL-161): map "web" -> <Variant> or quarantine "web"`.**
Over: the DL-122 text with a placeholder. Because: both literals are source text in the two declarations (DL-124 holds);
the task asks that the block names both. Text is a default (QF-5 open).

**GF-04 · Repair · A fate line on a current literal is valid only when the literal moved since the previous declaration; otherwise: `"web" is a current ENUM LITERAL of Channel that keeps its variant; a fate line names a literal that left or moved (DL-161)`.**
Over: the RED text "a swap waits for the previous literal table (DL-140, QF-8)". Because: DL-161 builds the table.
A map line on a literal that no declaration holds (F2 `"tablet"`) stays valid (no check).

**GF-05 · Repair · `fate:` lines print beside a block too, before the block lines.**
Over: print them only when the build passes. Because: S2d (R-1) asks for the count beside the `"tablet"` block; a parked
row stays visible in the report. RF-10 left this open.

**GF-06 · Repair · Help texts at the sites without a fates-a exit.** A failed rule of an ENUM CONSTRUCTOR:
`help: no fate line covers an ENUM CONSTRUCTOR yet (D041 open); restore the constructor rule of fn E that reads these records`
(new; RF-09 named only the no-signature case). Over: the no-signature text for both. Because: "restore a signature" is
wrong for a failed rule. Commits us to: redteam_c1 C1d, C1e pin it.

**GF-07 · Repair · ENTRY RECORDS use the same literal, constructor, help and fate code as rows and RESPONSE RECORDS (`check_entries` fills a `ValueChecks` and calls `value_errors`).**
Over: a third copy. Because: one rule per DL-134; the entry texts were already the same form. Limit: entries still skip
the shape and DL-103 checks (they fill only the literal and constructor maps).

**GF-08 · Undo · V18b re-pin: five pairs change only their help line (`HELP_REPIN` in record_v3_test.py), not four.**
The fifth, `stored-elixir/order.jsonl`, is a failed `Amount` rule; the plan missed it. `decode/stored-fail` keeps its
text. Also V14b and the help constants in eight test files (list in green-output.md).

**GF-09 · Undo · `quarantine` and `map` lines emit no Elixir in a1 (`ponytail:` at the emit site).** A hit fate line
stops the build (RF-01), so no generated module runs with them. fates-a2 builds the decode.

**GF-10 · Undo · The parse error for an unknown MIGRATE word names the fate words: `… a MIGRATE CHANGE is rename, add or drop, a fate line is quarantine, map, redact or retire`.**
No test pins the old text (searched).

**GF-11 · Repair · Not built in a1: the SQUASH block of the Q1 ruling ("removing `enum E v1` and the step is allowed only when the snapshot holds no v1 value").**
Because: a stored value does not carry its enum version (QF-2 A), so the build cannot count v1 values; a removal that
leaves a lost or moved literal is already blocked by DL-122 / DL-140 through the `enum E v2` mark alone (S3 enum case).
Commits us to: the main agent decides whether that suffices or a QF-2 record format is needed.

**GF-12 · Undo · `fmt` (HEAD rule DL-104) removes `type Amount v2` / `type Order v3` from a chain that starts at v1; `enum E vN` marks stay.**
Not changed in a1 (a4 owns fmt). The three fixtures stay unformatted on purpose (S3 needs the mark). A second `fmt`
run prints nothing.

**GF-13 · Repair · QM4-1 text retired with DL-166: no step keeps it.**
`renamed_onto` fires only for `rename`; `drop` and `add` of a non-String field stop earlier at K6 / K4 ("supports String
fields only"). With DL-166 (By: 13ue) the check and its text are deleted; K4 / K6 stay the only error for such fields.
Not built in a1: DL-166 is step a1b (fresh worker after the a1 commit).
→ By: Fable (ruling on DL-166 scope, Repair), observed by Opus (GREEN fates-a1)

**GF-14 · Undo · The PF-05 K8 text moves `slice3_types_test.py` `EMPTY_STEP` (a token check) to `… rename, add, drop or fate line`.**
Found by the first full run (slice3-types failed only there).

## Open OWNER lines after GREEN a1

→ **ENUM-V1-DECL** (opened by Fable): the older enum declaration in the source (Q1 ruling).
→ **QF-2** (built default A): nested versions are source-only; also limits GF-02 and GF-11.
→ **QF-5** texts: the helps, `fate:` lines, stop lines, GF-03, GF-04, GF-06 are defaults.
