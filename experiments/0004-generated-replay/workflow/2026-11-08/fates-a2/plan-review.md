# Plan check: fates-a2 (a2a record format draft 4, a2b fate lines at run time)

**[Proposal]** PLAN CHECK phase, 2026-11-08, target [plan.md](plan.md) at `0b460f9d`. Normal fresh review, not Devil's Advocate.
By: Opus (PLAN CHECK fates-a2). No production file, no test, no commit, no run.
Basis: DL-155, DL-157, DL-162, DL-165, DL-168, DL-172 ([decision log](../../../../../wiki/planning/decision-log.md));
[p2b/plan.md](../p2b/plan.md), [p2b/plan-review.md](../p2b/plan-review.md); `experiments/0001-syntax-to-beam/src/main.rs`.

## Verdict

**GO with repairs.** The split a2a / a2b and the order P2b → a2a → a2b → a4 hold. O1 (high) must be repaired in the
plan before a2a RED. O2 (high) must be repaired before a2b RED; it does not block a2a. O3 (medium): take it in the plan.

## What holds

- **Split.** [Inference] a2a alone leaves the tree green: the a1 stop lines stay, a2a adds no run-time fate code, and the
  run-time readers (`row_<t>`, versioned decode) match maps and ignore the extra key. a2b needs `type.nested`, so the
  order is forced.
- **Nested inside nested.** [Verified, `main.rs` 4679-4690] a constructor signature takes only `String` parameters
  (`__beaml_valid__(v, "String")`), so a constructor TYPE holds no constructor or enum field. An `Unknown(String)`
  payload is a String and has no TYPE VERSION. Direct fields are enough for constructor TYPES and enums.
- **SQUASH block.** Correct under DL-155 (an old version stays readable while values of it are stored). It is one reader
  check, testable by V4f. Placement in a2a is right.
- **Pin plan.** Three digest pins in GREEN (`EFFECT_OUTPUTS`, `BYTE_GUARD`, `byte-guard.json`), four hash pins in the
  commit after GREEN (`slice5_syntax` PIN, `slice6_entry` BASE, `slice6_multi` BASE, `slice6_db` P4_BASE), V17/V18b in
  GREEN, V18 as a reported Unknown. Matches RV3-14. a2b moves no pin under PF-16, with a stop rule.
- **Inline cores.** [Verified, `rg`] the 11 named test files match; the slice4 hits are TYPE VERSION 3, not record v3.
- **Bare `map` on older versions only.** Holds for rows and ENTRY RECORDS: a live `"app"` written at the newest nested
  version stays `Unknown("app")` on every later read. This is the reason DL-168 exists. Exception: O1.
- **Digest not over `nested`.** Consistent with today (`type` is outside `value_sha256`) and leaves P2b untouched. It is
  a plan option of DL-168 and is surfaced as QA2-1 C. Consequence for the card: a hand edit of `nested.amount` 2 → 1
  turns a blocking row into a parked, skipped row without a digest error.

## Objections

### O1 (high): a db.list RESPONSE RECORD carries no nested versions

- **Evidence.** [Verified, `main.rs` 2214, 4439] `db.list` returns `type OrderList { items: [Order] }`; its call record
  uses `emit_type_key(&effect.output)`, so the record `type` is `OrderList`. The plan's rule ("direct ctor and enum fields
  only") gives `nested: {}` for `OrderList`: `[Order]` is neither. The `Order` values inside `items` then carry no
  `Amount` or `Channel` version.
- **Consequence.** DL-168 "Because" is not met for list records. a2b R5, R6 and R6b replay list records; `--stored` fate
  selection (V4g) reads them too. With no version the gate must guess: "older" maps a live `Unknown("app")` to `Mobile`
  (wrong value on replay), "newest" never maps (R6 can only pass by a special case). Either way a false pass is likely.
- **Repair.** A LIST field `[T]` (and, by the same rule, a plain record field) holds the nested map of `T` as an object:
  `"nested": {"items": {"amount": 1, "channel": 1}}`. One recursive helper beside `emit_type_key`. a2a RED: V4b also
  asserts the db.list call record; V4e also refuses a malformed object value; `convert_v4.py` writes the object form.

### O2 (high, blocks a2b RED only): PA2-09 changes an OWNER-signed effect as a Repair

- **Evidence.** DL-157 (By: 13ue) Effect: "record reason `quarantined` on the skipped rows". PA2-09 replaces this with
  no per-row record and a `quarantined: n` key on the accepted call record. The technical reason (one record per trace
  for `select`) is sound.
- **Consequence.** A signed decision is lowered silently. RED would pin a behavior the OWNER did not choose.
- **Repair.** Move PA2-09 into QA2-2 (or a new card QA2-3) as a Migrate option with the `select` constraint stated:
  A count key on the call record (built default) · B one extra record per skipped row with reason `quarantined` (breaks
  `select`, needs a replay change). The OWNER answers before a2b RED.

### O3 (medium): RED and landing gaps

- **ID collision.** P2b already uses 0005 **N15** (`stored_test.exs`, SQL edit blocks). a2a's use case must be **N16**.
- **0005 assert.** `experiments/0005-prototype-fullstack/app/test/support/prototype.ex` line ~104 asserts
  `{3, "accepted"}` for every db record. It is not in §6; a2a GREEN fails `run.py run` without it.
- **False-pass guards.** Add R3c: a stored row at the newest nested version with `"app"` stays `Unknown("app")`
  (R3b covers live input only, so a build that maps every stored value passes R3 and R3b). Add V4f2: a stored nested
  version newer than the source's newest also blocks, and the help text must not say "keep enum Channel v1 and migrate".

## Decisions

### Undo
→ Split a2a / a2b and order P2b → a2a → a2b → a4 accepted. By: Opus (PLAN CHECK fates-a2)
→ Direct fields enough for ctor TYPES and enums. By: Opus (PLAN CHECK fates-a2)

### Repair
→ O1 high statt medium, weil list replay guesses values. By: Opus (PLAN CHECK fates-a2)
→ O2 high statt medium, weil a signed effect changes. By: Opus (PLAN CHECK fates-a2)
→ O3 medium statt high, weil TEST would catch it. By: Opus (PLAN CHECK fates-a2)
→ O2 blocks a2b only, not a2a, weil a2a writes no count. By: Opus (PLAN CHECK fates-a2)

### Migrate (OWNER)
→ O2: per-row record (DL-157 text) or count key (PA2-09). Before a2b RED.
→ QA2-1 card gains the O1 object form and the "hand edit of nested" consequence.
