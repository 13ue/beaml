# Pitch W3, the newcomer: fewer things to explain

**[Proposal]** Every statement in this file is a proposal, except lines marked observed. Nothing is built or decided. By: Opus (W3).
Stance: an engineer from Elixir or TypeScript, or an AUTHORING AGENT, reads `app/beaml/orders.beaml` cold.

## 0. Cold read: what does not fit in one sentence

| # | Looks like one, is two (or the reverse) | Evidence |
|---|---|---|
| C1 | `fn Amount` and `fn place`: same keyword, the capital letter switches on six hidden rules (only way in, pure, called by decode, by `--stored`, `new/1`, signature names = wire keys) | orders.beaml:8-10, DL-084, DL-092, DL-101, DL-106, DL-120, DL-121 |
| C2 | `fn Channel` (enum constructor) and `fn Amount` (record constructor): same form, opposite rule (not / only way in) | DL-100 vs DL-092 |
| C3 | `effect … = db.put(…)` goes out; `effect … = ui.event(…) \|> place` comes in. Only the transport name tells the direction. The inbound head repeats the fn types, so a drift rule must guard it | orders.beaml:41-50, DL-130 |
| C4 | `"place"` three times, plus `ui_place/1`: `ui.place`, `ui.event("place")`, `place` | orders.beaml:47 |
| C5 | `notes.save` stands in `orders.beaml`, module `Orders`: the dotted prefix is not the module | orders.beaml:43, README 0004 "Module name" |
| C6 | `! BadAmount` is declared, but the UI gets `Rejected{reason: "constructor"}`: the declared failure is lost at the entry | DL-133; observed `action_log.ex:28` |
| C7 | `with card_holder` (release a field) and `with … do … else … end` (handle failures): one keyword, two meanings | grammar.js:58, 124 |
| C8 | `retire op keep N days` (top level, an operation) and `retire f keep N days` (fate, failing records of a field); `quarantine f` is a third "leaves the replay set" | grammar.js:84, DL-125 |
| C9 | `type Order {}` and `type Order v1 {}` select two decode forms; the mark and the chain both state the version | DL-080, DL-104, marks.beaml |
| C10 | four "who sees this" tools: `redacted`, `with`, D040 visibility, DL-154 projection | DL-059, DL-089, D040, DL-154 |
| C11 | `Unknown(String)` must be written by hand, but only where outside data meets the enum | DL-062, DL-065, G6D-12 |
| C12 | `drop card_holder: redacted String` reads as "gone", but the chain runs on read; the stored value can stay | **[Inference]** DL-127 (chain on read), DL-111 (only `redact` is eager) |

Observed: the compiler parses `with` only on an EFFECT line (`main.rs:692`); no tracked `.beaml` source uses `with … do` (rg, 2026-11-08). The expression lives in grammar.js and DL-014 only.

## 1. Proposals

Key: U1 demo · U2 replay · U3 `--stored` live · U4 interim blocks and fates · U5 redacted · U6 entry drift · U7 modules · U8 host interface.

### P1. The ENTRY LINE body is the flow; no target fn, no drift rule (C3, C4)

```beaml
effect ui.place PlaceForm -> Order ! StoreError = ui.event |> to_order |> orders.save // Vorschlag, nicht gebaut
```

Change: the body after `ui.event` is any pipe; the event name comes from the operation (`ui.place` gives `"place"` and `ui_place/1`). The head is the only signature. DL-130 (one `effect` form, typed head) stays.

| U | Works? | Reason |
|---|---|---|
| U1 | yes with change | four lines rewrite; `place`, `list_orders`, `save_note`, `list_notes` go |
| U2 | yes | `Replay.entry` runs the pipe as it runs the fn today |
| U3 | yes | ENTRY RECORDS keep `operation` and `value` |
| U4 | yes | unchanged |
| U5 | yes | the DL-112 check walks a pipe already |
| U6 | yes, by removal | no second signature, nothing can drift |
| U7 | yes | |
| U8 | yes | `ui_<event>/1` unchanged |

Lost: a named, separately testable flow fn; a flow shared by two ENTRY LINES (D6B-207) must stay a fn, so "target is one fn" stays legal as a one-step pipe. Event names that differ from the operation need the String back (unknown if any host needs that).

### P2. One release rule at every boundary (C10)

Change: `redacted` hides a field from every audience: records, spans, wire, host. `with f` releases it across that one EFFECT line, outbound (wire) or inbound (host return). The host sees an ENTRY LINE output only through the DL-105 projection; the DL-154 `project_<type>/1` is that projection. D040 needs no keyword: the host surface is the TYPES in ENTRY LINE heads; everything else is internal.

| U | Works? | Reason |
|---|---|---|
| U1 | yes with change | O3: page calls the projection, not `__beaml_encode_order/1` |
| U2 | yes | `:redacted` in replay as DL-115 |
| U3 | yes | DL-151 unchanged |
| U4 | yes | |
| U5 | yes | DL-089, DL-112 unchanged; `with` gains the host direction |
| U6 | yes | |
| U7 | unknown | a TYPE shared by two modules: which module projects it |
| U8 | yes with change | `T.new/1` stays for tests only; observed: 0005 host never calls it |

Lost: a host that needs a non-entry TYPE (admin page, export) needs an ENTRY LINE for it. A field-level "internal but not PII" level does not exist; `redacted` is the only field mark.

### P3. One word for "leaves the replay set": `retire X [keep N days]` (C8)

Change: `quarantine f` becomes `retire f` with no `keep`: parked until a later MIGRATE STEP gives a new fate. `retire f keep N days` and the top-level `retire op keep N days` stay. Rule: "`retire` takes records out of the replay set; `keep` says when they are deleted; without `keep`, never."

| U | Works? | Reason |
|---|---|---|
| U1 | yes | N9 reads `retire amount` |
| U2 | yes | retired and quarantined records both get no REPLAY RUN |
| U3 | yes | |
| U4 | yes with change | DL-102 exits: total rule, `retire f`, `retire f keep N days` |
| U5 | yes | `redact` stays its own word: it deletes a value, not a record |
| U6-U8 | yes | |

Lost: the word "quarantine" says "rescue expected"; `retire` says "ending". The OBSERVATORY view must tell parked from deleting by the `keep` part.

### P4. Literals only for enums; `fn <Capital>` means record constructor only (C1, C2)

Change: remove the ENUM CONSTRUCTOR. Several spellings or several wire keys go through the constructor of the record that holds the field (DL-099 already routes flat bodies there).

| U | Works? | Reason |
|---|---|---|
| U1 | yes | 0005 uses literals only |
| U2 | yes with change | slice 6 fixtures with `fn PaymentState` rewrite |
| U3 | yes | |
| U4 | yes, simpler | DL-122, DL-140 compare literal tables only; "swapped constructor clauses" (DL-140) goes |
| U5-U8 | yes | |

Lost: an enum field whose wire value is an object with several keys must become a record TYPE; DL-088 becomes moot.

### P5. Remove `with … do … else … end` until a real case (C7)

Change: delete the rule from grammar.js and DL-014; `with` keeps one meaning. A later failure-handling form gets its own keyword. All U1-U8: yes (observed: no source and no compiler code use it). Lost: the DL-015 plan "`else` is exhaustive"; local failure handling has no form until a case needs it.

### P6. Every TYPE is versioned; the mark is required above v1 (C9)

Change: take DL-104 option B (`type T {}` is v1) and require `vN` when N > 1, so a reader never counts steps. Flips DL-081 (fmt removes the mark).
U1-U5, U8: yes with change: every unversioned output and the byte pins move once (memory: six pin sites). U6, U7: yes. Lost: the slice 1 decode form.

### P7. `Rejected` carries the constructor's failure value (C6)

Change: `Rejected{reason: "constructor", failure: %BadAmount{}}`. One sentence: "`!` is what the caller gets." U1, U8: yes with change (host pattern widens); U5: yes, DL-105 rule for redacted fields in failure TYPES applies; others yes. Lost: nothing known; record format unchanged (DL-141 keeps `reason`).

### Not proposed, flagged
→ C11 `Unknown(String)`: keep explicit (DL-062 OWNER rejected the implicit form); write the rule as one sentence.
→ C5 and operation names: an operation name is a durable key in every record, with no rename form. Renaming `notes.save` = retire + new. **[Unknown]** whether a `rename` for operations is needed before several modules (U7).
→ C12: decide whether `drop` of a `redacted` field implies `redact`. **[Unknown]** today.

## 2. BEAML in ten sentences (after P1-P7)

1. A `type` is a record; an `enum` is a closed set of variants, mapped from Strings by literals.
2. An enum that meets outside data ends with a keep-value variant such as `Unknown(String)`.
3. A `fn` named like a `type` is its constructor: the only, pure way in, and its `!` failure reaches every caller, the UI included.
4. Other `fn`s are clauses, tried top to bottom; a line without `=` is the signature.
5. `|>` passes a value on; a failure after `!` stops the pipe and goes to the caller.
6. An `effect` line is a typed boundary: `http.*` and `db.*` go out, `ui.event` comes in and runs its pipe.
7. Every boundary call writes one record; a REPLAY RUN reads it back, and `--stored` checks today's code against yesterday's records and rows.
8. A `redacted` field is never stored and never shown; `with f` releases it across one effect line.
9. `type T vN` is the newest version; `migrate` steps (`rename`, `add`, `drop`, `map`, `redact`) say how older records become it.
10. `retire` takes records out of the replay set, by operation or by failing field; `keep N days` says when they are deleted.

Test result: today the same list needs at least four more sentences (enum constructor, drift rule, `with … do`, quarantine vs retire, mark-or-chain) and two exceptions (`Rejected` vs `!`, host projection vs D040). **[Inference]**

## Decisions (W3)
→ Took orders.beaml and the order_v2 variant as the cold-read text. By: Opus (W3)
→ Rated P1 to P3 top: they remove a rule, not only a word. By: Opus (W3)
→ Kept `Unknown(String)` explicit, because DL-062 is an OWNER choice with a reason. By: Opus (W3)
→ Stated "with … do unused" from grep only; no build run (brief rule). By: Opus (W3)

## Round 2

**[Proposal]** Every statement below is a proposal. Input: pitch-w1.md, pitch-w2.md. By: Opus (W3).

### 1. Attacks on the foreign proposals

| Proposal | Strongest honest case against it | Verdict |
|---|---|---|
| W1 P1: fates become MIGRATE CHANGES, `quarantine` folds into `retire f` | `retire amount` reads like "remove the field amount", the way `drop` does. It actually removes whole failing records (W1's own inf line). A newcomer misreads it next to `drop amount: …`. The top-level `keep` is required, the field-level `keep` is optional: one word with two defaults. That asymmetry is justified, though: a RETIRE LINE with no timer keeps PII forever (DL-055 reason, DL-029) | narrows it (and narrows my P3): wording risk; keep the asymmetry |
| W1 P2: drift becomes the ordinary body check; the target fn stays | Against it: the TYPES are still written twice (head and fn), so the newcomer still types every ENTRY signature twice. For it: "drift" stops being a concept with no grammar change. The fn keeps its span (DL-108), its own test, the one-EFFECT-per-flow unit (Q6E-4) and two ENTRY LINES on one flow (D6B-207). My P1 loses all four | stands, and it beats my P1 as the first step |
| W1 P3: `redacted` plus release lists; host exposure is derived | D040 asks for "explicit opt-in to expose". The OWNER may not read an ENTRY LINE as that opt-in (W1 marks it unk). U7 is open: a TYPE that another module uses | stands (same as my P2) |
| W1 P4 = W2 P2: literals only | A provider that sends `"OK"` and `"ok"` needs a parent constructor per use, or a new `A = "ok" \| "authorized"` form. That second spelling brings back what P4 removes. Observed (W1 count): 9 enums use a constructor, all `PaymentState` fixtures; 0005 uses none | stands; no multi-literal form until a real provider needs one |
| W1 P5: every TYPE is versioned; mark only when the chain starts above v1 | With a chain v1 to v7, the reader counts seven steps to learn the version. The version is the one number every stored record carries (`type.version`, record v3) | narrows it: same direction as my P6; we differ only on whether the mark is required above v1 |
| W2 P1: `retire` parks; `quarantine` is the only fate; the build never deletes | Safer for one class: no `keep 0 days`, nothing at deploy is irreversible (DL-055). But: DL-111 (OWNER) rejected a keep window for PII ("would leave the value there for weeks"), and DL-055 chose deletion for privacy. A host purge job is a hand edit outside the build (DL-102: rescue is a code change), on a table that BEAML owns (DL-127). It is also harder to explain: two words for one record state, and "where deletion lives" moves to host code that no check sees | narrows it: take the safety half only: remove `keep 0 days`, so deletion needs a window of at least one day; otherwise kills the removal of `keep` |
| W2 P2 | see W1 P4 | stands |
| W2 P3: remove the VERSION MARK and SQUASH | DL-056 (OWNER): "the chain must not grow forever". W2's own table lists "every old row runs the chain on every read, forever" as a failure mode, and P3 makes it permanent. The backup-after-SQUASH block is loud and safe (DL-056: the record blocks the build again), so it is no reason to remove SQUASH. The decode switch W2 cites goes away with DL-104 B (W1 P5, my P6) | kills it |
| W2 P4: module-qualified row key, `db.put` with no argument | For the bare `db.put`: the String may only be `"records"` (PDB-04), so it is a fake choice, and a newcomer learns nothing from it. One sentence explains the bare form ("db effects use the BEAML-owned row table"). Against the module key: the module comes from the file stem (0004 README "Module name"), so renaming `orders.beaml` re-keys every stored row. The first ENTRY LINE also renames the module (0004 README :2194). A file rename becomes a data migration with no `rename` form. The one-time key rewrite is an eager rewrite of rows, which W2 itself rejects ("chain on read kept") | narrows it: drop the String (stands); replace the module key with a build error when two modules declare the same ROW TYPE name for `db.*` |
| W2 P5 = my P5 | Production wants "declined → write a pending row" inside BEAML (DL-015 exhaustive `else`). Nothing handles that today | stands as "parked", not "never" |
| W2 P6: redacted is stored as absent only; DL-116 is permanent; D039 closes | DL-116 is an OWNER interim, and D039 option 1 (hash) is the OWNER's stated default. Closing both reverses two OWNER ideas. Loss: a constructor-validated redacted output field, for example an e-mail. For it: "redacted = never stored" is the shortest true sentence, and a keyed hash puts a secret in a build that reads production live (DL-151, D039 note). That is the strongest safety point in either pitch | stands, as a Migrate option for the OWNER, not as a team default |

### 2. Revised own pitch

→ P1 entry body is the flow: **narrowed** to "derive the event String from the operation" (`ui.event` with no argument, C4). The fn removal is withdrawn in favour of W1 P2, because the fn carries the span, the tests and D6B-207.
→ P2 one release rule: **kept**, merged with W1 P3. `T.new/1` stays host-visible for seeds and jobs (W2 §3), so my "tests only" line is withdrawn.
→ P3 one `retire`: **narrowed**. Top-level `keep` stays required (W1). No `keep 0 days` (W2 safety half). The field form needs a reading that does not look like `drop`. **[Unknown]** spelling; options for the OWNER: `retire amount` or `retire failing amount` // Vorschlag, nicht gebaut.
→ P4 literals only: **kept**. All three pitches agree on it.
→ P5 remove `with … do`: **kept** as "parked". All three agree.
→ P6 versioned, mark above v1: **kept**. W2 P3 is the opposite and is killed above.
→ P7 `Rejected` carries the failure: **kept**. It fits W1 P2 ("Rejected is the transport failure").
→ New, from W2 P4: drop the `"records"` String from `db.*`, plus the duplicate ROW TYPE build error.

### Ten sentences, rerun

1. A `type` is a record; an `enum` is a closed set of variants, mapped from Strings by literals.
2. An enum that meets outside data ends with a keep-value variant such as `Unknown(String)`.
3. A `fn` named like a `type` is its constructor: the only, pure way in, and its `!` failure reaches every caller, the UI included.
4. Other `fn`s are clauses, tried top to bottom; a line without `=` is the signature.
5. `|>` passes a value on; a failure after `!` stops the pipe and goes to the caller.
6. An `effect` line is a typed boundary whose body must have the head's TYPES: `http.*` and `db.*` go out, `ui.event` comes in and calls one fn.
7. Every boundary call writes one record; a REPLAY RUN reads it back, and `--stored` checks today's code against yesterday's records and rows.
8. A `redacted` field is never stored and never shown; `with f` releases it across one effect line.
9. `type T vN` is the newest version; `migrate` steps (`rename`, `add`, `drop`, `map`, `redact`) say how older records become it.
10. `retire` takes records out of the replay set, by operation or by failing field; only a written `keep N days` (N ≥ 1) deletes them.

Test result: still ten sentences. Sentence 6 absorbs the drift rule, sentence 8 assumes W2 P6, sentence 10 absorbs the W2 safety rule. **[Inference]**

### 3. Sharpest disagreement

May the build delete stored records at all? W2 P1 says never and moves the purge to the host. W1 P1 and W3 P3 keep deletion in the source behind `keep N days`. This decides whether privacy retention (DL-055, DL-111) is a BEAML guarantee or host code.

### Decisions (W3, round 2)
→ Withdrew the P1 fn removal statt keeping it, weil W1 P2 keeps span, tests and D6B-207 at zero grammar cost. By: Opus (W3)
→ Took the W2 safety half (no `keep 0 days`) statt the full W2 P1, weil DL-111 wants PII deleted from the store. By: Opus (W3)
→ Rated W2 P3 "kills it" on DL-056 and W2's own failure table. By: Opus (W3)
→ Marked W2 P6 an OWNER option, not a team default, because it reverses D039 option 1. By: Opus (W3)
