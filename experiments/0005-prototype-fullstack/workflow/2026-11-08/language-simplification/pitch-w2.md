# Pitch W2: the operator (fewer ways to go wrong in production)

**[Proposal]** Every statement in this file is a proposal. Nothing is built, nothing is decided. Stance: ten years of STORED ROWS, many modules, long MIGRATE CHAINS, on-call at 3am. Labels inside: observed (line read), inferred, unknown. By: Opus (W2) for every judgement.

## 1. Failure modes per construct (count, evidence)

| Construct | # | Ways to go wrong (evidence) |
|---|---|---|
| RETIRE LINE, `retire f keep N days` | 5 | `keep 0 days` deletes at deploy, nothing unmakes it (DL-055); delete vs leave differs between DL-125 and `migrate-fates.md:72` (red team D5, M5 parked D036); under DL-137 the same line deletes domain rows; row meaning unknown, N28b skipped (0004 README `:2297`); overlaps `quarantine`, so two fates on one record (`migrate-fates.md` §5) |
| ENUM CONSTRUCTOR (DL-082 C2) | 5 | `!` makes every `--stored` fail (C1 = B1); non-record failure TYPE hides DL-102 (B2); swapped clauses pass (D1); lost constructor mappings unchecked (D6B-109, 0004 README `:1770`); DL-140 needs the old literal table, undefined for code |
| VERSION MARK and SQUASH | 5 | mark disagrees with chain (error M1, slice 5); a mark without a chain switches the decode form, so `fmt` had to be fenced (DL-104); a backup restored after SQUASH blocks, help says "restore from version control" (DL-056, slice 5 help); chain gaps (F8c); `u32` overflow corner (slice 5) |
| One table `records`, TYPE name as key | 5 | `BeamlDb.list(table, "Order", query)` has no module (0004 README `:2251`), so two modules with `type Order` read each other's rows: inferred; one bad row fails the whole list (QDB-4); `db.get` matches raw, not migrated value (0005 O2); orphan rows need a RETIRE LINE (M5 unknown); the table String can only be `"records"` (PDB-04) |
| REDACTED FIELD, `with`, `redact f`, D039 | 6 | derived copy reaches the store with no `with` (6c O1); DL-116 interim; DL-125 misstates DL-116 (D3); D039 option 2 keeps PII decryptable; a keyed hash puts a key into a build that reads production live (DL-151, D039 note); `with` has two meanings, grammar reserves it, compiler accepts it as a name (B8) |
| `with ... do ... else ... end` | 1 | shares the keyword with the PII release (B8); observed: no `.beaml` under `experiments/` holds `<-` or a line ending in ` do` |
| ENTRY LINE head + drift rule | 2 | drift is a compile error, 0 run-time modes (DL-130); a source that gains its first ENTRY LINE renames its module (0004 README `:2194`) |
| MIGRATE CHAIN on read | 3 | every old row runs the chain on every read, forever; `--stored` must check every version forever; fates must hold at check time and at read time (DL-102, DL-137) |

## 2. Proposals (ranked)

Cells: Y yes · Yc yes with change · N no · ? unknown.

### P1. Storage is never deleted by the build: `retire` parks, `quarantine` is the only parking fate

`retire f keep N days` goes; `quarantine f` stays as the one parking fate. The RETIRE LINE becomes `retire <op>` without `keep`. Deletion stays only in `redact f` (DL-111, eager, field-level). Fate set: `map`, `redact`, `quarantine`. Rule: one fate line per field; a record with a quarantined field is quarantined.

```beaml
// Vorschlag, nicht gebaut
retire payments.authorize
migrate Order v2 -> v3 { quarantine amount }
```

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y | Y retired record still rejects with a typed reason | Y | Yc exits are `map`, `quarantine`; no `retire f` | Y `redact` stays | Y | Y | Yc host owns purge |

→ Lost: automatic retention limit for RESPONSE RECORDS (DL-055 reason, DL-029 privacy). A purge becomes a host job outside the build, the thing DL-102 ("no hand edit") avoids.
→ Breaks: a production rule "delete payment records after 30 days" without host code. Removes: `keep 0 days`, M5, two fates on one record.

### P2. Remove the ENUM CONSTRUCTOR; enums decode only by ENUM LITERAL plus KEEP-VALUE VARIANT

Multi-key or logic decode moves into the parent record constructor (the DL-099 flat-body pattern). DL-122 and DL-140 become a pure diff of two literal tables.

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y `Channel` is literals | Y | Y | Yc DL-140 is a table diff; `map` covers all | Y | Y | Y | Y |

→ Lost: `fn PaymentState "ok", _ -> ...` (DL-082 C2, DL-100); two wire Strings for one variant (normalisation) only via the parent constructor.
→ Breaks: a provider that sends `"OK"` and `"ok"` for one state, when no parent record constructor exists. Removes: C1, B2, D1 for clauses, D6B-109.

### P3. Remove VERSION MARK and SQUASH; the chain always starts at v1

The DEAD LINE warning stays. `--remove-dead` removes RETIRE LINES only. A TYPE VERSION number follows from the chain alone.

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y `Note` has no mark | Y | Y backup rows always decode | Y | Y | Y | Y | Y |

→ Lost: DL-070, DL-071, DL-080, DL-081, DL-104; the chain grows forever (DL-056 reason).
→ Breaks: a TYPE with hundreds of steps stays long in the source. Removes: M1, the DL-104 decode switch, the post-SQUASH backup block.

### P4. One owning module per ROW TYPE; the row key is module-qualified; no table String

ROW CORE `type` and the `BeamlDb` TYPE argument read `Orders.Order`. `db.put("records")` becomes `db.put`. Another module reads rows only through an EFFECT of the owner (ties to D040).

```beaml
// Vorschlag, nicht gebaut
effect orders.save Order -> Order ! StoreError = db.put
```

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Yc old rows need the new key once | Y | Yc check per owner | Y | Y | Y | Y no cross-module row reads | Yc `BeamlDb` gets the qualified name |

→ Lost: one module reading another's rows directly; a record format change (DL-139: OWNER sign-off).
→ Breaks: a reporting module that lists `Order` rows with its own `type Order`. Removes: the cross-module literal-table and chain clash on one row.

### P5. Remove the `with ... do ... else ... end` expression; `with` means only "release"

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y | Y | Y | Y | Y one reading of `with` | Y | Y | Y |

→ Lost: an `else` arm that recovers from a failure inside BEAML. Failures go to the caller through `! A | B`.
→ Breaks: "payment declined, write a pending row instead" in one fn. Unknown: whether the compiler parses a source `with ... do` today.

### P6. A REDACTED FIELD is stored as absent only; DL-116 becomes permanent

D039 options 1 (hash) and 2 (encrypt) go. No rule runs over an absent value; DL-116 leaves the fate list (red team M3 option A).

| U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 |
|---|---|---|---|---|---|---|---|
| Y | Y `:redacted` (DL-115) | Y nothing clear to read | Yc DL-116 off the fate list | Yc D039 closes as absent | Y | Y | Y |

→ Lost: "this value was entered here" (D039 option 1); a redacted field of a constructor TYPE in an EFFECT output.
→ Breaks: a validated, redacted e-mail in a RESPONSE RECORD. Removes: a reversible PII store, a key in the build path.

## 3. Considered, not proposed

→ ENTRY LINE head TYPES: drift is compile-time only (DL-130); OWNER chose E' over E.
→ Chain on read vs eager rewrite: an eager rewrite of RESPONSE RECORDS makes a REPLAY RUN lie (DL-102). For rows: open question for round 2.
→ `T.new/1` at the host: removal breaks seeds, tests and non-UI entries; B5 forgery stays a check gap.

## Decisions (By: Opus (W2))

**Undo**
→ Pitch limited to six proposals, ranked by failure modes removed.
→ Counts are per construct, from cited evidence only.

**Repair**
→ `quarantine` kept statt `retire f`, weil it never deletes.
→ Chain on read kept statt eager, weil replay must not lie.
→ `T.new/1` kept statt removed, weil seeds and jobs need it.

**Migrate (the OWNER chooses)**
→ P1, P2, P3, P4, P6 reverse or narrow OWNER decisions (DL-055, DL-082, DL-070/071, DL-127/129, D039).

## Round 2

**[Proposal]** Every statement is a proposal. By: Opus (W2) for every verdict.

### 1. Attacks

| Foreign | Strongest case against (evidence) | Verdict |
|---|---|---|
| W1 P1 (fates are MIGRATE CHANGES; `quarantine` → `retire f`) | Category merge is harmless. The fold is the problem: parked and deleting differ by two tokens of one verb. W1's own example adds `keep 30 days` in a later step to records already parked, so a deletion arrives through the chain. A grep for `retire` at 3am mixes operations, parked records and timed deletes. M5 (delete vs leave, red team D5) stays open inside the same word. Under DL-137 it deletes domain rows | narrows it: one verb is fine only if a field fate never takes `keep` |
| W1 P2 (drift is the body check) | Only the error text changes; both forms fail at compile time (DL-130). No run-time mode | stands |
| W1 P3 / W3 P2 (host surface derived from ENTRY LINE heads, no D040 word) | With ten modules, exposure is transitive and silent. `Order` in a head projects `Amount` and every nested TYPE. A new field in a head TYPE widens the public surface with no reviewed line. A TYPE shared by two modules has no owner for `project_<type>/1` (W1 U7 and W3 U7 both `unknown`). The compiler cannot see host calls of `T.new/1` (0004 README `:2196`: the host build reports, not BEAML). The OWNER asked for an explicit opt-in (D040, DL-154) | narrows it: derived is the default, the build lists the full surface per module, D040 opt-in stays an OWNER choice |
| W1 P4 / W3 P4 (literals only) | Several spellings per variant need a parent constructor or a new form (W1 `unk`) | stands (= my P2) |
| W1 P5 (one mark form, above v1 only) | Removing the unversioned form (DL-104) is good. SQUASH stays, so the backup-after-SQUASH block (DL-056, slice 5 help "restore from version control") and M1 stay | narrows it: take "every TYPE is versioned", drop SQUASH |
| W3 P1 (ENTRY LINE body is the flow, no target fn) | The flow loses its name. `Replay.entry` dispatches `run(op, …)` to one flow with one EFFECT (Q6E-4, 0004 README `:2166`). Spans name fns (DL-108, DL-119). A unit test calls `place` without the String-key decode; an inline pipe is testable only through `ui_place/1`. A shared flow (D6B-207) keeps the fn, so there are two body forms, which is more to explain. Deriving the event String from the operation couples the host `handle_event("place")` to a durable record key with no rename form (W3 C5) | narrows it: drop the repeated `"place"` String; keep the target fn |
| W3 P3 (`retire X [keep N days]`) | Same case as W1 P1. "Without `keep`, never" is one optional clause away from deletion | narrows it, as W1 P1 |
| W3 P5 (drop `with … do`) | None. W3 observed that the compiler parses `with` only on an EFFECT line (`main.rs:692`), which closes my `unknown` | stands (= my P5) |
| W3 P6 (mark required above v1) | Mark and chain state the version twice, so every new MIGRATE STEP needs a second edit, and M1 becomes the most common error. It fails at compile time only | narrows it: one source of the number, the chain |
| W3 P7 (`Rejected` carries the `!` value) | DL-105 allows a redacted field in a failure TYPE when it is redacted there too. Live, that struct holds the clear value, and the host logs `Rejected` (`action_log.ex:28`, `:32`). If the value enters the ENTRY RECORD `reason`, PII reaches the store (DL-141 keeps `reason` a word) | narrows it: the host gets the value with redacted fields as `:redacted`; the ENTRY RECORD keeps the word only |

**What an operator loses at 3am**
→ W1/W3 `retire f`: one grep for parked records is not possible, and a parked record is one token away from deletion.
→ W2 (no `keep` on field fates): deletion by field rule is not possible. A purge is a host job (P1 "Lost").

### 2. Revised own pitch

→ P1 **narrowed**: the verb can be `retire f` (W1/W3) and `quarantine` can go. A field fate never takes `keep`. The top-level `retire op keep N days` stays (DL-055, OWNER).
→ P2 **kept**: all three pitches agree.
→ P3 **narrowed**: every TYPE is versioned (W1 P5, DL-104 option B). SQUASH and the mark go; the chain is the only source of the number.
→ P4 **kept**: no other pitch handles two modules over one `records` table.
→ P5 **kept**: now observed through W3 `main.rs:692`.
→ P6 **kept, plus one rule**: `drop f: redacted T` without `redact f` is a compile error. This answers W3 C12.
→ Chain on read vs eager rewrite, rows: the chain stays on read (DL-127 option J, one decode for records and rows, DL-143). Eager applies only where a value must leave the store (`redact`). The cost: `--stored` checks every version forever, which P3 accepts. **[Unknown]** whether eager would fix 0005 O2 (`db.get` matches the raw value) more cheaply than a migrated-key read.

### 3. Sharpest disagreement

W1 and W3 let a field-level fate carry a delete timer (`retire f keep N days`). W2 keeps every deletion out of MIGRATE STEPS except `redact`, because a line in a chain step should never delete whole records.

### Decisions, round 2 (By: Opus (W2))

**Undo**
→ Verdicts only "kills / narrows / stands"
→ None killed; seven narrowed

**Repair**
→ `retire f` word accepted statt `quarantine`, weil only `keep` matters
→ Chain-only number statt mark, weil M1 disappears
→ Target fn kept statt inline pipe, weil replay and tests name it

**Migrate (the OWNER chooses)**
→ Field fate with `keep` (W1, W3) or without (W2)
→ Host surface derived (W1, W3) or explicit D040 opt-in
