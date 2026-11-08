---
id: lang-simplify-pitch-w1
kind: pitch
status: proposal
updated: 2026-11-08
---

# Pitch W1, the minimalist

**[Proposal]** Every statement on this page is a proposal. Nothing is built, nothing is decided. By: Opus (W1).

Stance: the smallest construct set that still carries U1 to U8. Keys: **obs** = observed in the cited file, **inf** = inferred, **unk** = unknown.

**obs** Corpus count (183 tracked `.beaml` sources, `results/` excluded): `type` 642, `fn` 721, `effect` 212, `migrate` 66, `enum` 62, `with` 32, `retire` 7, VERSION MARK 7 sources, ENUM CONSTRUCTOR 9 enums (all `PaymentState` fixtures), `quarantine` / `redact` lines 0. By: Opus (W1), read-only count.

## P1. FATE OPERATIONS are MIGRATE CHANGES; `quarantine` folds into `retire`

Change: no FATE OPERATION category. A MIGRATE STEP holds MIGRATE CHANGES only. `redact f` and `map f "old" -> V` join `rename` / `add` / `drop` as changes of shape or value. `quarantine f` becomes `retire f` without `keep`. One `retire` rule for both targets.

```beaml
// Vorschlag, nicht gebaut
migrate Order v2 -> v3 { retire amount }                 // was: quarantine amount (parked, no timer)
migrate Order v3 -> v4 { retire amount keep 30 days }    // the same records, now with a delete timer
retire payments.authorize keep 30 days                  // top-level: target is an operation, keep stays required (DL-055)
```

Why the merges hold:
- **obs** `quarantine` and `retire f` give the same record state: stored, not replayable, typed reason. Only the delete timer differs (migrate-fates.md:71-72).
- **obs** `redact f` changes the field TYPE to `redacted` in a new TYPE VERSION (DL-111). That is a shape change, as `drop` is.
- **obs** `map` changes a stored value into a variant (DL-122, DL-140). That is a value change, as `add f: T = c` is.
- **inf** `retire f` is not `drop f` and not a `map` to nothing: `drop` removes one field from every record, `retire f` removes whole failing records.
- **obs** The top-level RETIRE LINE is not a MIGRATE STEP: it names an operation, and "the TYPE of a retired operation may also leave the source" (0004 README:763). One TYPE serves several operations (`Order` in `orders.save` and `ui.place`, orders.beaml:41,47).

| Use case | Still works? | Reason |
|---|---|---|
| U1 | yes with change | N9 frees by `retire amount`, not `quarantine amount` |
| U2 | yes | a parked record skips the REPLAY RUN, as before |
| U3 | yes | `--stored` counts parked records per TYPE VERSION |
| U4 | yes | DL-102: `retire f`; DL-122 / DL-140: `map` or `retire f`; DL-116: `redact` |
| U5 | yes | `redact f` unchanged, now a MIGRATE CHANGE |
| U6 | yes | not touched |
| U7 | yes | top-level target stays a qualified operation |
| U8 | unk | OBSERVATORY view of parked records not decided (migrate-fates.md:104) |

Lost: the word `quarantine`, which says "waits for rescue". **unk** Whether a RETIRED RECORD may get a later fate during its N days; P1 needs "yes".
Evidence: DL-055, DL-057, DL-102, DL-111, DL-122, DL-125, DL-137, DL-140; grammar.js:74-84.

## P2. The drift rule is the ordinary EFFECT body check; `Rejected` is the transport failure

Change: no special drift rule. Every `effect` line has one rule: the body TYPE must equal the head. `ui.event("place")` gives the head input; `|> place` must return the head output and failures. This is the outbound rule too. `Rejected` is the implicit failure of the `ui.event` transport, as a non-200 status is for `http.post`.

- **obs** ENTRY LINE and outbound EFFECT are already one grammar rule: `effect_declaration`, body `_expression` (grammar.js:48-59). Direction comes from the transport name.
- **obs** The host already receives `{:error, %Rejected{…}}` in the failure tuple (0004 README:1982). DL-133 keeps it apart from the fn failure TYPE; P2 keeps that.
- **inf** The head stays (DL-130 chose E' over E). Head without body check is the bug; body check without a second rule is enough.

| Use case | Still works? | Reason |
|---|---|---|
| U1 | yes | `ui.place` and the flow unchanged |
| U2 | yes | not touched |
| U3 | yes | not touched |
| U4 | yes | not touched |
| U5 | yes | not touched |
| U6 | yes with change | same errors, one rule; the DL-130 error text becomes the pipe TYPE error |
| U7 | yes | `ui.place` stays a qualified name |
| U8 | yes | `ui_<event>/1` and `Rejected` unchanged |

Lost: a drift-specific error text (DL-130). **unk** Whether the pipe error names both lines as clearly.
Rejected alternative: drop the head (option E). The head is the reviewable boundary contract; a fn signature change would move `ui_place/1` silently. By: Opus (W1).
Evidence: DL-130, DL-131, DL-133; 0004 README:1974.

## P3. One visibility construct: `redacted` plus release lists; host exposure derived

Change: `redacted` on the field is the only marker. Every sink releases it only by name: `with f` on an EFFECT (DL-089, built). The host projection (DL-154) leaves REDACTED FIELDS out. D040 gets no `private` keyword: a TYPE reaches the host only when an ENTRY LINE head or a host-called `T.new/1` names it (derived, DL-126). D039 hash or encrypt is a build setting, not syntax.

| Use case | Still works? | Reason |
|---|---|---|
| U1 | yes | `Order`, `OrderList` are ENTRY LINE outputs, so projected |
| U2 | yes | `:redacted` marker unchanged (DL-115) |
| U3 | yes | DL-151 keeps REDACTED FIELDS out of the build |
| U5 | yes | DL-059, DL-089, DL-111, DL-112 unchanged; D039 only a setting |
| U6 | yes | not touched |
| U7 | unk | several modules: a TYPE used by another module is no host use; needs a module rule |
| U8 | yes with change | projection set is derived; D040 TYPE-level hide has no own word |
| U4 | yes | not touched |

Lost: explicit opt-in to expose (D040 asks for it). **inf** An ENTRY LINE is already an explicit opt-in. **unk** Whether the OWNER accepts that.
Evidence: DL-089, DL-105, DL-115, DL-151, DL-154, D039, D040.

## P4. `enum` keeps literals only; the ENUM CONSTRUCTOR leaves

Change: an `enum` maps outside Strings only by ENUM LITERALS. Computed mapping (several keys, a payload variant) goes into the constructor of the parent record (DL-099 already routes flat bodies there). Rules DL-088 and the DL-100 special case go away.

- **inf** With literal tables only, DL-122 and DL-140 are a static diff of two literal tables plus the stored values.
- **obs** Only 9 enums use a constructor, all `PaymentState` fixtures (count above).

| Use case | Still works? | Reason |
|---|---|---|
| U1 | yes | `Channel` uses literals (orders.beaml:12-16) |
| U2 | yes with change | 9 fixtures move the mapping to the parent constructor |
| U4 | yes | literal diff covers DL-122 / DL-140 |
| U3, U5, U6, U7, U8 | yes | not touched |

Lost: several spellings per variant, Int-to-variant (`constructor.beaml` signature 3). **unk** Needs `A = "ok" | "authorized"` (new form) or a parent constructor per use.
Evidence: DL-082, DL-088, DL-099, DL-100; slice6/enum/constructor.beaml.

## P5. One version rule: every TYPE is versioned; the mark only when the chain starts above v1

Change: drop the unversioned decode form (`type T {}` versus `type T v1 {}`, DL-104). The compiler accepts the mark only where `fmt` writes it (DL-081 form b), not any agreeing mark (DL-080).

| Use case | Still works? | Reason |
|---|---|---|
| U1 | yes | `Note`, `Order` chains unchanged |
| U2, U3 | yes with change | slice 1 records read as v1; byte pins move |
| U4–U8 | yes | not touched |

Lost: three legal mark forms become one; the slice 1 byte form. **unk** Pin cost (six pin sites, memory note).
Evidence: DL-070, DL-071, DL-080, DL-081, DL-104.

## Do not add (planned constructs that fold into existing ones)

- `where` rule on a field: a constructor clause covers it; DL-092 rejected T2. By: Opus (W1).
- D025 `=` / `|` second form: option A, one form. By: Opus (W1).
- `on ui "place"` (DL-128 sketch): the ENTRY LINE is it. By: Opus (W1).
- `type` and constructor `fn` stay separate: several signatures (DL-084, DL-085) need clauses. By: Opus (W1).

## Result set

Top-level keywords stay six (`type`, `enum`, `fn`, `effect`, `migrate`, `retire`). MIGRATE CHANGES: `rename`, `add`, `drop`, `redact`, `map`, `retire`. Planned words removed: `quarantine`, `where`, `on`, `private`, `=`/`|` form.

## Decisions (W1)

**Repair**
→ Fold `quarantine` into `retire f`, over a separate verb, because the record state is the same. By: Opus (W1)
→ Keep the ENTRY LINE head, over option E, because of DL-130. By: Opus (W1)
→ Count the corpus without `results/`, over all files, because results hold copies. By: Opus (W1)

## Round 2

**[Proposal]** Every statement in this section is a proposal. It answers pitch-w2.md (the operator) and pitch-w3.md (the newcomer). By: Opus (W1).

### 1. Attacks

**W2 (the operator)**

| Proposal | Strongest honest case against it | Verdict |
|---|---|---|
| W2 P1 parking only, no `keep N days` | **obs** DL-055 gives a retention limit "for privacy (DL-029)", and vertical-integration.md calls privacy the highest goal. **obs** DL-149 names "the only way out of a block is an SQL delete" as a weakness of 0005. W2 P1 makes that SQL delete the permanent purge path (a host job), which DL-102 rules out ("rescue is a code change"). **inf** A parked record that is never deleted is PII kept forever by default. W2's valid point stays: the delete-or-leave question is open (red team M5, report.md:146). | kills it (the removal of deletion); the M5 point stands as an open question |
| W2 P2 no ENUM CONSTRUCTOR | Same as my P4 and W3 P4. Cost that all three skip: the parent record constructor makes itself the only way in (DL-092). Normalizing one enum field (`"OK"` and `"ok"`) adds a constructor that then guards every build site of the whole record. | narrows it: needs several literals per variant |
| W2 P3 no VERSION MARK, no SQUASH | **obs** DL-056: "the chain must not grow forever". **inf** Without SQUASH a dead step can never leave, because removing it renumbers stored records (DL-058). Against that: **obs** only 7 corpus sources carry a mark, all fixtures, and no real chain is long. The MARK-and-chain agreement (M1) and the DL-104 decode switch go with it. | stands (YAGNI until a real chain is long); it replaces my P5 mark rule |
| W2 P4 module-qualified row key, no table String | **obs** The module name comes from the file stem (0004 README:2176). **inf** Rename a file and every stored row key changes: old rows become orphans or need a migration. That ties a durable key to a file name, and it changes the record format (DL-139 needs OWNER sign-off). The table-String removal holds on its own: only `"records"` is legal (PDB-04). | narrows it: drop `("records")` now; qualify only with a stable module id, not the stem (U7 unknown) |
| W2 P5 no `with ... do ... else ... end` | **obs** Unused in every source and in the compiler (W3, main.rs:692), and only its keywords are decided (grammar.js:123). Case against: it is the only planned form for recovering from a failure inside a fn (DL-014 is an OWNER decision). | stands (Migrate: DL-014 is OWNER's) |
| W2 P6 redacted is stored as absent only; DL-116 permanent | **obs** Absent is already the built rule (DL-105). Making DL-116 permanent contradicts DL-152 (OWNER: "every migration must be possible") and bans a validated redacted field (a constructor TYPE) in an EFFECT output forever. W2's key-in-build risk is real (DL-151 reads production live). | narrows it: absent stays the default; D039 hash only as a later opt-in; DL-116 stays an interim |

**W3 (the newcomer)**

| Proposal | Strongest honest case against it | Verdict |
|---|---|---|
| W3 P1 the ENTRY LINE body is the flow, no target fn | **obs** DL-126: declarations carry shape and policy, expressions carry computation. A pipe inside an `effect` line puts computation into a declaration. **inf** A second inbound transport for the same flow (a later HTTP route, a job) copies the pipe; a named fn is shared (D6B-207 already needs one). **inf** Taking the event name from the operation ties the host String `"place"` to the durable `operation` key in every ENTRY RECORD. A UI rename then means retire + new (W3's own C5 note). The drift fix needs no body change: my P2 turns drift into the ordinary body check. | narrows it: keep the body a call to one fn; take the drift-to-body-check rule (my P2); keep the event String |
| W3 P2 one release rule at every boundary | Agrees with my P3. Against W3's cut of `T.new/1` to tests only: DL-106 and DL-117 are OWNER decisions, and W2 §3 names seeds and jobs as host callers. **inf** `with f` on an ENTRY LINE adds a new sink, the host return; that is a real new meaning, not a merge. | narrows it: `T.new/1` stays a host entry |
| W3 P3 `retire X [keep N days]` | Same as my P1. Case against: the word `retire` means "ending" for records that wait for rescue. **obs** The same open fact as M5 (report.md:146). | stands |
| W3 P4 literals only for enums | Same as W2 P2: the parent constructor guards the whole record (DL-092). | narrows it: needs several literals per variant |
| W3 P5 no `with ... do` | As W2 P5. | stands |
| W3 P6 every TYPE versioned; mark required above v1 | **inf** A required mark is a second statement of the same number; the M1 failure mode (mark disagrees with the chain, W2 table) stays by design. W2 P3 removes the duplicate instead. "Every TYPE versioned" holds: it removes the DL-104 decode switch. | narrows it: keep "every TYPE versioned", drop the mark rule |
| W3 P7 `Rejected` carries the `!` failure value | **obs** DL-133 keeps "form broken" apart from "flow failed"; a `failure` field keeps that. Case against: **inf** a decode reject has no failure value, so `Rejected` gets two shapes (`failure: nil` or a struct). A failure struct can carry form data back to the host, and DL-112 forbids a direct copy of a redacted value "everywhere". **obs** Red team M8 (the failure struct at the host, report.md:148) is parked (D036). It is a host-called shape (DL-139: OWNER sign-off). It adds a field; it removes no construct. | narrows it: OWNER question under M8, not a simplification |

### 2. Revised own pitch

→ P1 `quarantine` into `retire f`: **keep**. W3 P3 gives the same; W2 P1 is answered by DL-055 and DL-149.
→ P2 drift rule becomes the body check: **keep**. It gives W3's drift fix with no pipe in the declaration.
→ P3 one visibility construct: **narrow**. `T.new/1` stays a host entry (W2 §3); W3 adds the host-return sink.
→ P4 literals-only enums: **narrow**. Several literals per variant are needed, else DL-092 guards the whole parent record.
→ P5 version rule: **narrow**. Withdraw the mark rule for W2 P3 (no mark, no SQUASH); keep "every TYPE versioned".

```beaml
// Vorschlag, nicht gebaut: several ENUM LITERALS per variant (P4 narrowed)
enum Channel { Web = "web" | "WEB"  App = "app"  Unknown(String) }
```

### 3. Sharpest disagreement

**[Proposal]** May the build delete stored data at all? W2 P1 says never and leaves deletion to the host. W1 P1 and W3 P3 keep `keep N days` as a language-level retention policy (DL-055). That choice also binds DL-137 rows, and nothing unmakes a deletion.

### Decisions (Round 2)

**Repair**
→ Withdraw the mark rule, over keeping one mark form, because W2 P3 removes the duplicate. By: Opus (W1)
→ Keep the event String, over W3's derivation, because operation keys are durable. By: Opus (W1)
→ Rate W3 P7 as an OWNER question, over a simplification, because it adds a field (M8). By: Opus (W1)

**Migrate (the OWNER chooses)**
→ Build deletion (W2 P1) against `keep N days` (W1 P1, W3 P3): DL-055 and M5 are the OWNER's.
