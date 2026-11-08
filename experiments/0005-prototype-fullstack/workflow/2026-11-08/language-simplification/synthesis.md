---
id: lang-simplify-synthesis
kind: synthesis
status: proposal
updated: 2026-11-08
---

# Language simplification: synthesis of the team round

**[Proposal]** Every statement in this file is a proposal. Nothing is built, nothing is decided. Input: [pitch-w1.md](pitch-w1.md) (the minimalist), [pitch-w2.md](pitch-w2.md) (the operator), [pitch-w3.md](pitch-w3.md) (the newcomer), each with a Round 2 of attacks. By: Fable (lead, lang-simplify).

Labels: **obs** = read in the cited file or DL entry, **inf** = inferred by a worker or the lead, **unk** = not established. Use cases U1 to U8 as in the brief: U1 0005 demo (form, ENTRY RECORD, row, list, Note v1 to v2, stricter Amount), U2 REPLAY RUN of RESPONSE RECORDS, U3 `--stored` live (DL-151), U4 interim blocks DL-102 / DL-122 / DL-140 and fates, U5 REDACTED FIELDS, U6 ENTRY LINE drift, U7 several modules, U8 host interface. Cells: Y yes, Yc yes with change, N no, ? unknown.

Ranking rule (By: Fable): first by team agreement after Round 2, then by rules removed (not only words), then by how little OWNER ground it reverses. Options A/B/C are for the OWNER; the lead recommends nothing.

## Ranked candidates

### 1. Fates are MIGRATE CHANGES; `quarantine` folds into `retire f`; deletion by a field fate is the open point

Change: no FATE OPERATION category; `redact`, `map` and `retire` stand beside `rename`, `add`, `drop` in a MIGRATE STEP. `quarantine f` becomes `retire f` with no timer (parked: stored, not replayable, typed reason). Top-level `retire <op> keep N days` stays (DL-055).

Agree: W1 P1, W3 P3, W2 P1 (Round 2: the verb `retire f` accepted). Disagree: whether a field fate may carry `keep N days`. W2: never, a chain line must not delete whole records; W1, W3: yes, retention is language policy (DL-055 "privacy", DL-111 rejects a keep window for PII). W3 adds: `retire amount` reads like `drop amount` for a newcomer (wording risk, spelling unk).

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Yc N9 reads `retire amount` | Y parked records skip the REPLAY RUN | Y counts per TYPE VERSION | Yc exits: total rule, `map`, `retire f` | Y `redact` stays its own word | Y | Y | ? OBSERVATORY view of parked records not decided (migrate-fates.md §5) |

Lost: the word "quarantine" ("rescue expected"); under option B the language-level retention of records by field rule. **obs** M5 (delete or leave, red team D5) is open under D036 in every variant. **unk** whether a parked record may take a later fate inside its N days.

OWNER options: A `retire f [keep N days]` with N >= 1 (W1, W3 plus the W2 safety half: no `keep 0 days` at field level); B `retire f` never deletes, deletion only top-level and `redact` (W2); C keep `quarantine` as its own word (DL-125 as written).
Smallest check: paper, one page: write the three interim blocks DL-102 / DL-122 / DL-140 and N9 in each of A, B, C and count the lines and the distinct words; then the fate slice RED fixture with one lost ENUM LITERAL and one `map` (migrate-fates.md §5 proposal) extended by one `retire f` line.

### 2. Enums decode by ENUM LITERALS only; the ENUM CONSTRUCTOR leaves

Change: `fn <Capital>` always means a record constructor (DL-092 rule only). Normalisation of several wire Strings goes to the parent record constructor or to a new multi-literal form.

Agree: all three (W1 P4, W2 P2, W3 P4). Narrowed by W1 in Round 2: a parent constructor makes itself the only way in for the whole record (DL-092), so one normalised enum field guards every build site of the record; several literals per variant are then needed (`Web = "web" | "WEB"` // Vorschlag, nicht gebaut).

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y `Channel` uses literals (orders.beaml:12-16) | Yc 9 `PaymentState` fixtures rewrite | Y | Yc DL-122 / DL-140 become a diff of two literal tables | Y | Y | Y | Y |

Lost: `fn PaymentState "ok", _ -> …` (DL-082 C2, DL-100), Int-to-variant mapping, DL-088. Removes: red team C1, B2, D1 (clause swap), D6B-109. **obs** 9 enums use a constructor, all fixtures (W1 count). **unk** whether a real provider needs two spellings for one state.

OWNER options: A literals only, normalisation in the parent constructor; B literals plus a multi-literal form per variant; C keep DL-082 as is.
Smallest check: paper: rewrite `slice6/enum/constructor.beaml` in A and in B and show that `--stored` DL-140 reduces to a table diff; count the lines.

### 3. The drift rule is the ordinary EFFECT body check; the target fn stays

Change: one rule for every `effect` line: the body TYPES must equal the head. For `ui.event("place") |> place` that is the DL-130 drift rule with no name of its own. `Rejected` is the implicit failure of the `ui.event` transport, as a non-200 is for `http.post`.

Agree: W1 P2; W2 and W3 both let it stand in Round 2; W3 withdrew its own P1 (body is the flow, no fn) in favour of it, because the fn carries the span (DL-108), the unit test, the one-EFFECT-per-flow replay (Q6E-4) and a shared flow (D6B-207). Open sub-point: the repeated `"place"` String (W3 C4). W2 and W3: derive the event name from the operation; W1: keep the String, because the operation name is a durable record key with no rename form (W3 C5).

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y | Y | Y | Y | Y | Yc same error at compile time, text becomes the pipe TYPE error | Y | Y `ui_<event>/1`, `Rejected` unchanged |

Lost: a drift-specific error text. **unk** whether the pipe error names both lines as clearly as the DL-130 text. **inf** No grammar change at all; a concept and an error text disappear.

OWNER options for the sub-point: A keep `ui.event("place")`; B `ui.event` with no argument, name from the operation (`ui.place` gives `"place"`, `ui_place/1`).
Smallest check: paper: list the 0004 slice 6d drift tests (`test_n10_rejects`) and state for each what the body check error would say.

### 4. Every TYPE is versioned; one source for the version number

Change: drop the unversioned decode form (DL-104 option B): `type T {}` is v1. Then either no VERSION MARK and no SQUASH (the chain is the only source) or a mark required above v1.

Agree: all three on "every TYPE versioned". Disagree on the mark: W2 P3 (no mark, no SQUASH) and W1 after Round 2 (withdrew its mark rule for W2 P3) against W3 P6 (mark required above v1, SQUASH stays). W3 rates W2 P3 "kills it" on DL-056 ("the chain must not grow forever") and on W2's own failure table (chain on read forever). W1 rates it "stands" as YAGNI: **obs** 7 corpus sources carry a mark, all fixtures; no real chain is long.

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y `Note`, `Order` chains unchanged | Yc slice 1 records read as v1; byte pins move | Yc backup rows always decode under A | Y | Y | Y | Y | Y |

Lost under A: DL-070, DL-071, DL-080, DL-081, DL-104; a long chain never shortens (reverses DL-056). Lost under B: M1 (mark disagrees with chain) stays by design; the number stands twice. **obs** Removing a step renumbers stored records (DL-058). **unk** pin cost (six pin sites).

OWNER options: A no mark, no SQUASH, chain only; B mark required above v1, SQUASH stays; C mark optional as today, only DL-104 B taken.
Smallest check: paper: take the longest fixture chain (`marks.beaml`) and write it in A and B; count what a reader must do to learn the version and what `fmt` must do.

### 5. One visibility construct: `redacted` plus `with`; the host surface is derived

Change: `redacted` on the field is the only field mark; `with f` releases it across one EFFECT line (outbound wire today; W3 adds the host return as a second sink). The DL-154 projection is the DL-105 projection and leaves REDACTED FIELDS out. D040 gets no keyword: the host surface is the TYPES in ENTRY LINE heads plus `T.new/1` (stays, DL-106, DL-117, seeds and jobs).

Agree: W1 P3, W3 P2. Narrowed by W2: with ten modules exposure is transitive and silent (`Order` in a head projects `Amount` and every nested TYPE); a new field in a head TYPE widens the surface with no reviewed line; the build should list the surface per module; the D040 opt-in the OWNER asked for stays an OWNER choice. **obs** The compiler cannot see host calls of `T.new/1` (0004 README, module name section).

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Yc page calls the projection, not `__beaml_encode_order/1` (DL-154) | Y `:redacted` (DL-115) | Y DL-151 | Y | Y DL-059, DL-089, DL-111, DL-112 unchanged | Y | ? a TYPE shared by two modules has no owner for `project_<type>/1` | Yc projection set derived, listed by the build |

Lost: an explicit opt-in word to expose (D040 asks for one); a field level "internal but not PII". **inf** An ENTRY LINE is already an explicit statement. **unk** whether the OWNER reads it as the opt-in.

OWNER options: A derived surface, build lists it, no new keyword; B explicit opt-in on the TYPE (D040 keyword), derived surface forbidden; C derived as default plus an opt-out word for a TYPE that must stay internal.
Smallest check: paper: for 0005 list the TYPES the host would see under A (heads: `PlaceForm`, `Order`, `OrderQuery`, `OrderList`, `NoteForm`, `Note`, `NoteQuery`, `NoteList`, nested `Amount`, `Channel`) and mark which the host actually uses (0005 README, "Who owns which step").

### 6. Remove the `with … do … else … end` expression until a real case needs it

Change: delete the rule from grammar.js and DL-014; `with` keeps one meaning (release).

Agree: all three (W2 P5, W3 P5, W1 Round 2 "stands"). **obs** No tracked `.beaml` source uses it; the compiler parses `with` only on an EFFECT line (W3: main.rs:692). **obs** DL-014 is an OWNER decision, so this is a Migrate.

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y | Y | Y | Y | Y one reading of `with` | Y | Y | Y |

Lost: the only planned form for recovering from a failure inside a fn ("declined, write a pending row instead"); the DL-015 "exhaustive `else`" plan. A later form gets its own keyword.

OWNER options: A remove from the grammar now; B keep as parked grammar, no compiler work; C keep and give the two `with` meanings distinct words.
Smallest check: paper: one production case that needs local recovery, written with `! A | B` to the caller and with `with … do`; compare.

### 7. Drop the `"records"` table String; a duplicate ROW TYPE across modules is a build error

Change: `db.put("records")` becomes `db.put` (**obs** only `"records"` is legal, PDB-04). Two modules that declare the same ROW TYPE name for a `db.*` EFFECT fail the build. W2's module-qualified row key is rejected by W1 and W3: **obs** the module comes from the file stem (0004 README, module name) and the first ENTRY LINE renames the module, so a file rename would re-key every stored row; it is also a record format change (DL-139).

Agree: all three on the String; W2, W3 on the duplicate error. **inf** W2's root risk stands: two modules with `type Order` would read each other's rows over the one table.

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Yc four EFFECT lines lose an argument | Y | Y | Y | Y | Y | Yc no two modules own one ROW TYPE name | Yc `BeamlDb` unchanged |

Lost: a reporting module with its own `type Order` over the same rows; a future second table without a new form. **unk** whether a stable module id (not the stem) is wanted later.

OWNER options: A drop the String plus the duplicate error; B keep the String, add only the error; C module-qualified key with a stable id (record format change, DL-139 sign-off).
Smallest check: paper: write two modules with `type Order` and a `db.list` each and state what each option reads.

### 8. REDACTED FIELDS are stored as absent only; `drop` of a redacted field needs `redact`

Change: D039 options 1 (hash) and 2 (encrypt) go; absent is the only form (**obs** already the built rule, DL-105). DL-116 becomes permanent. New rule (W2, answers W3 C12): `drop f: redacted T` without `redact f` is a compile error, because the chain runs on read and the value would stay in the store.

Agree: W2 P6; W3 "stands only as an OWNER option" (reverses D039 option 1, the OWNER's stated default); W1 narrows: absent as default, hash as a later opt-in, DL-116 stays an interim because DL-152 says every migration must be possible. Strongest safety point in the round (W3): a keyed hash puts a secret into a build that reads production live (DL-151).

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y | Y `:redacted` | Y nothing clear to read | Yc DL-116 leaves the fate list under A | Yc D039 closes as absent | Y | Y | Y |

Lost: "this value was entered here" (D039 option 1); a constructor-validated redacted field in an EFFECT output (for ever under A, for now under B).

OWNER options: A absent only, D039 closed, DL-116 permanent; B absent default, hash as explicit later opt-in, DL-116 interim; C D039 option 1 (keyed hash) as default, as stated. The `drop`-needs-`redact` rule fits every option.
Smallest check: paper: for one `redacted` field, list what each of the three streams (RESPONSE RECORD, ENTRY RECORD, STORED ROW) holds under A, B, C and where a key would live.

## Not a simplification: OWNER questions that surfaced

→ `Rejected` carries the constructor's `!` failure value (W3 P7). W1, W2: it adds a field, does not remove a construct, and a live failure struct can hold a clear PII value (DL-112, action log). Belongs to red team M8 (D036). By: Fable.
→ The ENTRY LINE body as the flow with no target fn (W3 P1). Withdrawn by W3 in Round 2. Kept here as the record of why: span, test, replay by operation, shared flow, DL-126. By: Fable.
→ An operation name is a durable key in every record with no rename form (W3 C5). **unk** whether a `rename` for operations is needed before several modules. By: Fable.

## Deliberately not touched

→ The ENTRY LINE head TYPES (DL-130 E' over E): all three keep it as the reviewable boundary contract.
→ `type` and constructor `fn` as separate constructs: several signatures need clauses (DL-084, DL-085); `where` is not added (DL-092 rejected T2).
→ `Unknown(String)` written by hand (DL-062 OWNER choice with a reason).
→ MIGRATE CHAIN on read, not eager rewrite: an eager rewrite of RESPONSE RECORDS makes a REPLAY RUN lie (DL-102); eager only for `redact` (DL-111). **unk** whether eager fixes 0005 O2 more cheaply.
→ `T.new/1` as a host entry (DL-106, DL-117; seeds and jobs).
→ `!` as a position, not a type (DL-092); `-> A ! A` error (DL-093).
→ Planned words not added: `on`, `private`, `where`, the D025 `=` / `|` form.
→ `redact` as its own word: it deletes a value, not a record.

## Sharpest disagreement

**[Proposal]** May the build delete stored records at all? W2 says never (every deletion out of MIGRATE STEPS except `redact`; a purge is a host job). W1 and W3 keep deletion in the source behind `keep N days` (DL-055 retention as privacy policy, DL-111). This decides whether retention is a BEAML guarantee or host code, and it binds DL-137 rows too. Nothing unmakes a deletion, so it is the OWNER's (candidate 1, options A/B/C).

## Limits

→ Paper only: no pitch ran a build, a test or a count beyond read-only `rg` and file reads.
→ Corpus counts (W1) exclude `results/`; the decision log was read from DL-100 onward closely, earlier entries skimmed.
→ Use case verdicts are the workers' reasoning over cited files, not executed checks.
→ Two pages per pitch limited the depth of each "does X still work" cell.

## Decisions (lead)

**Undo**
→ Eight candidates, ranked by agreement, rules removed, OWNER ground reversed. By: Fable (lead, lang-simplify)
→ W3 P7 and W3 P1 moved to "not a simplification" instead of the ranked list. By: Fable (lead, lang-simplify)
→ Round 2 sent to all three workers as resumes of the same context, W3 included after its first hand-back. By: Fable (lead, lang-simplify)

**Repair**
→ Candidate 1 merges fate-category and `quarantine` fold statt two candidates, weil every pitch treats them together. By: Fable (lead, lang-simplify)
→ Candidate 7 keeps the duplicate ROW TYPE error statt W2's module key, weil two workers showed the file-stem risk. By: Fable (lead, lang-simplify)

**Migrate (the OWNER chooses)**
→ Every candidate's options A/B/C above. No recommendation given.
