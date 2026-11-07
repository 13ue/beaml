# PLAN CHECK: slice 6b step 11 (constructor TYPES are structs at the host)

**[Proposal]** PLAN CHECK, 2026-11-07. Fresh context. Not a Devil's Advocate. No production file changed. `run.py` not run.
Read: this ledger (`plan.md`, `plan.json`, `decisions.md`), the [step 12 ledger](../slice6b-effect-reach/plan.md), DL-092, DL-100, DL-101, DL-105, DL-106, DL-108, DL-110, the [step 6 plan](../slice6b-redacted/plan.md), the step 8 notes (S3, P2), `experiments/0001-syntax-to-beam/src/main.rs` (`structs`, `emit_structs`, `result`, `emit_chain`, `__beaml_valid__`, the decode through a constructor).
By: Opus (PLAN CHECK, slice6b-host-structs) for every entry in this file.

## Verdict

- **BLOCK on O1 only.** A one-line plan edit closes it (H1 input value, one new assert). Then the RED can start.
- No default contradicts DL-106. No default hides a Migrate or Answer item.

## Objections

**O1 · High · H1 can pass on a wrong input check.**
- **[Verified]** H1 uses `%{"value" => 0}`. The value `0` fails the constructor rule. So a GREEN that runs the constructor on the map in the input check rejects it and passes H1.
- **[Inference]** That GREEN accepts `%{"value" => 4}`: a map that happens to fit. This is the exact accidental error that DL-106 removes.
- **[Inference]** A check on atom keys without `is_struct` (`Map.get(v, :value)`) also passes H1, because `Map.get` on a String-key map gives `nil`.
- **Smallest test.** H1 uses a valid value: `BeamlSpike.keep(%{"value" => 4})` raises `invalid BEAML input`. This is RED today: the step 3 test `keep_passes` observes that it returns the map.
- Add a guard: `BeamlSpike.keep(%{value: 4})` (atom keys, no `__struct__`) raises. **[Inference]** It raises today too (its String-key field is `nil`), so it is a guard, not a RED. It fails on a GREEN that checks atom keys without `is_struct`.
- By: Opus (PLAN CHECK, slice6b-host-structs)

**O2 · Medium · The enum payload depth of D6B-76 has no test.**
- **[Verified]** D6B-76 claims that a map fails "in a nested field and in an enum payload". H3 tests a record field only.
- **[Inference]** An enum payload check goes through the same `__beaml_valid__` today, so the risk is low. But a GREEN that special-cases record fields passes H3.
- **Smallest test.** Fixture: `enum Wrap { Has(NonZeroInt) }`, `fn wrapped w: Wrap -> Wrap = w`. `BeamlSpike.wrapped({"Wrap", "Has", [%{"value" => 4}]})` raises `invalid BEAML input`. Use the binary form that the compiler writes for the tag.
- By: Opus (PLAN CHECK, slice6b-host-structs)

**O3 · Medium · H6 is a guard, not a RED. Say so.**
- **[Verified]** Today `n |> NonZeroInt` gives `p1 = %{"value" => 4}`. `result()` rebuilds `%__MODULE__.NonZeroInt{value: Map.get(p1, <<"value">>)}` (main.rs, `result`). That gives `value: 4`. So H6 passes today.
- **[Inference]** The `nil` fields appear only after D6B-75 makes `p1` a struct. D6B-77 is a consequence of step 11, not a bug in today's code. It needs no RED of its own. H6 fails on a GREEN that forgets D6B-77, so it guards the right thing.
- **Action.** Mark H6 as "passes before and after" in `plan.md`, so the RED review does not count it as RED.
- By: Opus (PLAN CHECK, slice6b-host-structs)

## Defaults checked (no change)

- D6B-73 to D6B-76, D6B-78 to D6B-83: consistent with DL-106. D6B-79 follows DL-100 (enum constructor is the decode path only).
- D6B-76: the struct check must drop `map_size(v) == N`. A struct has one more key (`__struct__`). H3 and H4 fail if a GREEN keeps it. No new test.
- D6B-78: **[Verified]** the 6a `value` key holds wire values (step 6 plan, contract table). So no struct reaches `:json` encode. The order 6a then 11 holds.
- D6B-74: two public names (`new_T_k`, `T.new`). Both run the same clauses. Not a second way around the constructor.

## Defaults to raise to Migrate

- None in step 11.

## OWNER question Q6B-16

- Options A (positional) and B (one map) are real.
- **Missing option C, keyword list.** `Pair.new(x: "x", y: "y")`. Named and order-free like B. No conflict with a `Map` field TYPE. Challenges: atom names at the host; it differs from the String-key form of the decode (DL-099).
- The interim (no `T.new` for several parameters) is safe. `new_T_k` stays as the entry.

## Order

- 6a, then 11, then 12, then 12b, then 6b, then 6c: sound. See the [step 12 review](../slice6b-effect-reach/plan-review.md) for 12 and 12b.
- Step 11 changes no arm byte, so DL-110 is not touched.
