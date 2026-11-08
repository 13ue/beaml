---
id: concept-migrate-fates
title: Fate operations of a MIGRATE STEP
kind: synthesis
status: owner-decision-concept
updated: 2026-11-08
---

# Fate operations of a MIGRATE STEP

**[Requirement]** DL-125 (OWNER) gives a stored record its fate with a declarative FATE OPERATION in the MIGRATE STEP. This page is the concept. **[Verified]** Update 2026-11-08: the compiler parses and checks `quarantine` and `map` at build time (fates step a1, see [Built status](#built-status-fates-step-a1)); nothing runs at run time yet, and the tree-sitter grammar knows no FATE OPERATION. See the [decision log](../planning/decision-log.md) and [vertical integration](vertical-integration.md).

## 1. Problem: three interim blocks wait for a fate

**[Verified]** Three OWNER decisions block the build and have no exit yet (decision log):

- DL-102: a stored RESPONSE RECORD fails a new rule (a record constructor or a changed enum mapping). The build blocks until a MIGRATE STEP declares the fate of the failing records.
- DL-116: a `redacted` field in an EFFECT output is legal only on a String or Int field of a TYPE without a constructor. The record holds no value (DL-105), so no rule can run over it. The limit is lifted when a rule over an absent value is defined.
- DL-122, narrowed by DL-124: a removed or changed ENUM LITERAL with stored values blocks the build. The error names the TYPE VERSION, operation, field, enum, record count and source lines `S:N`. It never prints the stored String.

**[Verified]** DL-102, DL-111 and DL-122 call the `quarantine`, `redact` and `retire` forms a sketch. DL-122 names the fate syntax as the thing that lifts the interim.

## 2. Decision DL-125: form 1

**[Requirement]** DL-125 chose form 1: FATE OPERATIONS inside `migrate T vN -> vM { … }`, next to `rename`, `add` and `drop`. Each line says what happens to one field, never how. There are no variables, no expressions and no order dependence.

**[Requirement]** The four operations named in DL-125:

| Operation | What it does | Source |
|---|---|---|
| `redact f` | Removes the stored value of `f` eagerly at deploy. The field becomes `redacted` in a new TYPE VERSION. | DL-111 |
| `quarantine f` | Parks each record whose field `f` fails its rule. No REPLAY RUN, a typed reason, the build lists the count per TYPE VERSION. | DL-102, DL-125 |
| `retire f keep N days` | Records whose field `f` fails its rule leave the replay set after N days. | DL-055, DL-125 |
| `map f "old" -> Variant(...)` | Maps a lost literal to a variant on purpose (a MAP OPERATION). | DL-122, DL-125 |

**[Verified]** The current grammar knows only `rename`, `add` and `drop` in a MIGRATE STEP, and `retire <name> keep <n> days` at the top level ([grammar.js](../../integrations/zed-beaml/grammar.js), `migrate_declaration`, `retire_declaration`). A real fixture uses only these forms, for example [marks.beaml](../../experiments/0004-generated-replay/slice6/fmt/marks.beaml).

**[Proposal]** One example per operation. None of this is grammar yet. The spelling follows DL-125; the field and TYPE names are invented.

```beaml
// redact: the field becomes PII; the deploy removes the stored values (DL-111).
type Payment v3 { order_id: String  card_holder: redacted String }
migrate Payment v2 -> v3 { redact card_holder }
```

```beaml
// quarantine: a new constructor on Amount fails for some stored records (DL-102).
migrate Payment v3 -> v4 { quarantine amount }
```

```beaml
// retire: records that fail the new rule leave the replay set after 30 days.
migrate Payment v4 -> v5 { retire amount keep 30 days }
```

```beaml
// map: the literal "pending" was removed from Status (DL-122); stored values map on purpose.
enum Status { Authorized = "ok"  Declined = "no"  Unknown(String) }
migrate Payment v5 -> v6 { map state "pending" -> Declined }
```

**[Inference]** A MAP OPERATION names the old String in the source. That String comes from the OWNER, not from the store, so DL-124 holds: the build output still never prints a stored value.

## 3. Semantics

**[Requirement]** The REPLAY RUN rule stays DL-102: a stored record goes through the MIGRATE CHAIN to vM, then through today's code. A quarantined record does not run (DL-125).

**[Proposal]** Per operation:

- `redact f`: the deploy removes the value from every stored record of that TYPE VERSION and reports the count (DL-111). A REPLAY RUN shows the field as `:redacted` (DL-115). With a fate for the absent value, the DL-116 limit can be lifted: the rule does not run over an absent value, and the operation says so in the source.
- `quarantine f`: the record stays stored with a typed reason (TYPE VERSION, field, failed rule). It is not reinterpreted and gets no REPLAY RUN. It is no guess and no fallback (DL-028, DL-102).
- `retire f keep N days`: the same shape as the RETIRE LINE (DL-055, DL-057), scoped to the failing records of one field. During the N days the record is a RETIRED RECORD: stored, not replayable, with a typed reason. After N days the deploy deletes only those records. `keep 0 days` deletes at deploy, and the report says so loudly, because nothing unmakes it (DL-055).
- `map f "old" -> Variant(...)`: in the chain step, a stored value `"old"` of field `f` becomes `Variant(...)`. The record then runs like any other record. The variant must exist in the target enum, else the build fails.

**[Proposal]** The build report:

- Counts per environment, TYPE VERSION, field and operation. Source lines `S:N` of the records, as in DL-124.
- Never a stored value, never a record identity in the report (DL-032, DL-124). DL-032 is itself a proposal, not an OWNER decision.
- A quarantine does not block the build once declared. It is listed on every build while records stay parked.

**[Proposal]** Lifting a quarantine: a later MIGRATE STEP from vM to vM+1 declares a new fate line for the same field, for example a `map` or a `retire`. The parked records then go through that step. Nobody edits a record by hand in a REPL or CLI (DL-102: rescue is a code change).

**[Proposal]** Interaction with the KEEP-VALUE VARIANT and DL-103:

- A value kept as `Unknown(value)` does not fail; it needs no fate. A new literal that resolves it is counted, not blocked (DL-103).
- A lost literal that falls into `Unknown` is a DL-122 hit. `map` is the explicit exit; the alternative is `quarantine` or `retire`.
- `map` to `Unknown(...)` would only restate the default. **[Unknown]** Whether that is legal, a warning, or an error.

**[Inference]** DL-056 applies too: a fate line with no stored records left in any environment is a dead line, and the compiler warns.

## 4. Scope

**[Verified]** FATE OPERATIONS govern RESPONSE RECORDS today. BEAML owns no persistence. Whether a MIGRATE STEP also governs BEAML-owned persistence later is open in [D020](../planning/decisions-to-be-made.md).

**[Requirement]** Expressions (form 2: clauses per field with a pattern, an expression over the old value and a failure branch `! fate`) come only when a real case needs a computed value. Form 1 is a subset of form 2, so form 1 stays valid then (DL-125).

**[Requirement]** DL-126 puts fates on the declarative side: declarations carry shape and policy, expressions carry computation. A fate is policy over stored data. The expression escape hatch of DL-126 is form 2.

## 5. Open questions

- **[Unknown]** Grammar and keywords: the final spelling of all four operations, and whether `retire f` shares a grammar rule with the top-level RETIRE LINE.
- **[Unknown]** Duplicate fate lines for one field in one MIGRATE STEP: an error, or the first line wins (DL-085 style)?
- **[Unknown]** A fate for a nested field: a path such as `quarantine amount.cents`, or a fate on the nested TYPE only.
- **[Unknown]** What the OBSERVATORY shows for quarantined records. D018 is closed for spans (DL-119); the view of parked records is not decided.
- **[Unknown]** The fate of a record under two failing fields with different fates (for example `quarantine a` and `retire b keep 30 days`): which fate wins, or is the pair an error?

**[Proposal]** Smallest next test: a slice 6b follow-up fixture with one lost ENUM LITERAL and one `map` line. `--stored` passes, and a REPLAY RUN of the record returns the mapped variant.

## Built status (fates step a1)

**[Verified]** GREEN `d9c1fac0`, TEST PASS `e5bbbd83` ([0004 README](../../experiments/0004-generated-replay/README.md#fates-step-a1-fate-operations-at-build-time-dl-125-dl-155-dl-161-dl-162)):

- `quarantine f`, `quarantine "lit"` (DL-162), `quarantine f "lit"`, `map [f] "lit" -> Ctor` parse and check; `redact` and `retire` parse and are rejected (fates-b).
- `enum E vN` ENUM VERSIONS; the old declaration stays until SQUASH (DL-155, DL-161).
- `--stored` lifts the DL-102 and DL-122 blocks and prints one `fate:` count per hit; a DL-140 swap blocks (DL-161).
- A hit FATE OPERATION exits 1 with a stop line until the run-time side exists.

**[Verified]** Step a1b, GREEN `018cf1ea`, TEST PASS `9d93a75c` ([0004 README](../../experiments/0004-generated-replay/README.md#fates-step-a1b-rename-onto-enum-and-constructor-fields-quarantine-per-field-dl-166-dl-172)):

- A `rename` onto an ENUM or constructor field builds (DL-166); `--stored` reads old rows by their old key.
- `quarantine <field>` lifts only the failed clauses that test that field (DL-172). QB-1 (either tested parameter lifts) and QB-2 (a catch-all is never lifted) are built defaults, open for the OWNER.
- Several quarantine lines per constructor TYPE; two fate lines on one field stay an error.

**[Requirement]** Not built: run-time skip, `map` in the decode and the REPLAY RUN reason (a2); a rename inside a constructor TYPE (a1b R4); DL-168 and the SQUASH block (a2); fmt and tree-sitter (a4). The section 2 examples stay [Proposal]; the open questions in section 5 stay open unless a decision closes them.

## Page decisions

- → Example names invented (`Payment`, `amount`, `Status`). By: Opus (DOCS, migrate-fates).
- → `retire f` deletes only failing records over the whole TYPE VERSION, because DL-125 scopes it to "such records". By: Opus (DOCS, migrate-fates).
- → A declared quarantine does not block over blocking, because DL-102 lists quarantine as an exit from the block. By: Opus (DOCS, migrate-fates).
